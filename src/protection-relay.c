#include "iec61850_server.h"
#include "goose_publisher.h"
#include "goose_receiver.h"
#include "goose_subscriber.h"
#include "hal_thread.h"
#include "linked_list.h"
#include "mms_value.h"
#include <signal.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <pthread.h>
#include <netdb.h>
#include "static_model.h"

static int running = 0;
static IedServer iedServer = NULL;
static GoosePublisher goosePublisher = NULL;
static GooseReceiver gooseReceiver = NULL;
static int http_server_fd = -1;

// Forward declarations
static ControlHandlerResult
controlHandler(ControlAction action, void* parameter, MmsValue* value, bool test);
void publishGooseMessage(bool is_state_change);

void sigint_handler(int signalId) {
    running = 0;
}

// MMS Report Event Handler (simplified)
void rcbEventHandler(void* parameter, ReportControlBlock* rcb, ClientConnection connection, 
                    IedServer_RCBEventType eventType, const char* parameterName, MmsDataAccessError serviceError) {
    printf("\n=== MMS REPORT EVENT ===\n");
    printf("RCB Event Type: %d\n", eventType);
    printf("Client connected for reporting\n");
    printf("========================\n");
}

typedef struct {
    float voltage;
    float current;
    float frequency;
    float faultCurrent;
} SimulationData;

typedef struct {
    int overcurrent_pickup;
    int ground_fault_pickup;
    int trip_active;
    char trip_reason[64];
    uint64_t pickup_time;
} ProtectionState;

static ProtectionState prot_state = {0, 0, 0, "Normal", 0};
static SimulationData simData = {132.0, 450.0, 50.0, 0.0};
static volatile bool g_breaker_status_from_goose = false;

// GOOSE state tracking for proper stNum/sqNum management
static struct {
    int last_trip_active;
    int last_breaker_status;
    int last_fault_detected;
    int last_overcurrent_pickup;
    bool data_changed;
    uint32_t stNum;     // Status number - increments on data change
    uint32_t sqNum;     // Sequence number - increments on retransmission
} goose_state = {0, 0, 0, 0, false, 1, 0};

static void breakerStatusListener(GooseSubscriber subscriber, void* parameter) {
    MmsValue* values = GooseSubscriber_getDataSetValues(subscriber);
    if (values && MmsValue_getArraySize(values) >= 2) {
        MmsValue* breakerPos = MmsValue_getElement(values, 0);
        if (breakerPos && MmsValue_getType(breakerPos) == MMS_BOOLEAN) {
            g_breaker_status_from_goose = MmsValue_getBoolean(breakerPos);
            printf(">>> GOOSE Breaker Status Received: %s\n", 
                   g_breaker_status_from_goose ? "OPEN" : "CLOSED");
        }
    }
}

int fetchSimulationData(SimulationData* data) {
    int sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) return -1;
    
    struct timeval timeout = {1, 0};
    setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout));
    
    const char* simulator_host = getenv("SIMULATOR_HOST");
    if (!simulator_host) simulator_host = "localhost";
    
    struct sockaddr_in server_addr;
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(3000);
    
    struct hostent* host_entry = gethostbyname(simulator_host);
    if (host_entry == NULL) {
        close(sock);
        return -1;
    }
    server_addr.sin_addr = *((struct in_addr*)host_entry->h_addr_list[0]);
    
    if (connect(sock, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
        close(sock);
        return -1;
    }
    
    const char* request = "GET /api/simulation-data HTTP/1.1\r\nHost: localhost:3000\r\nConnection: close\r\n\r\n";
    send(sock, request, strlen(request), 0);
    
    char buffer[1024];
    int bytes = recv(sock, buffer, sizeof(buffer)-1, 0);
    close(sock);
    
    if (bytes > 0) {
        buffer[bytes] = '\0';
        char* json_start = strstr(buffer, "{");
        if (json_start) {
            sscanf(json_start, "{\"voltage\":%f,\"current\":%f,\"frequency\":%f,\"faultCurrent\":%f", 
                   &data->voltage, &data->current, &data->frequency, &data->faultCurrent);
            return 0;
        }
    }
    return -1;
}

void* http_server_thread(void* arg) {
    struct sockaddr_in address;
    int opt = 1;
    
    http_server_fd = socket(AF_INET, SOCK_STREAM, 0);
    setsockopt(http_server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
    
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(8082);
    
    bind(http_server_fd, (struct sockaddr*)&address, sizeof(address));
    listen(http_server_fd, 3);
    
    printf("✅ HTTP Server listening on port 8082\n");
    
    while (running) {
        int client_fd = accept(http_server_fd, NULL, NULL);
        if (client_fd >= 0) {
            char buffer[1024] = {0};
            recv(client_fd, buffer, 1023, 0);

            if (strstr(buffer, "POST /trip")) {
                printf("\n>>> MANUAL TRIP via HTTP <<<\n");
                prot_state.trip_active = 1;
                strcpy(prot_state.trip_reason, "Manual Trip (GUI)");
                
                // Immediately publish GOOSE message
                publishGooseMessage(true);  // State change
                printf(">>> GOOSE TRIP PUBLISHED: %s\n", prot_state.trip_reason);

                char response[] = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n{\"status\":\"trip_sent\"}";
                send(client_fd, response, strlen(response), 0);
            } 
            else {
                char response[1024];
                snprintf(response, sizeof(response),
                    "HTTP/1.1 200 OK\r\n"
                    "Content-Type: application/json\r\n"
                    "Access-Control-Allow-Origin: *\r\n"
                    "\r\n"
                    "{\"voltage\":%.1f,\"current\":%.0f,\"frequency\":%.3f,\"faultCurrent\":%.0f,\"tripCommand\":%s,\"breakerStatus\":%s,\"faultDetected\":%s,\"overcurrentPickup\":%s,\"tripReason\":\"%s\"}",
                    simData.voltage, simData.current, simData.frequency, simData.faultCurrent,
                    prot_state.trip_active ? "true" : "false",
                    g_breaker_status_from_goose ? "true" : "false",
                    (prot_state.overcurrent_pickup || prot_state.ground_fault_pickup) ? "true" : "false",
                    prot_state.overcurrent_pickup ? "true" : "false",
                    prot_state.trip_reason);
                
                send(client_fd, response, strlen(response), 0);
            }
            close(client_fd);
        }
    }
    return NULL;
}

void publishGooseMessage(bool is_state_change) {
    if (!goosePublisher) return;
    
    // Update sequence numbers per IEC 61850-8-1
    if (is_state_change) {
        // Use proper libiec61850 API to increment stNum and reset sqNum
        uint64_t newStNum = GoosePublisher_increaseStNum(goosePublisher);
        printf(">>> GOOSE STATE CHANGE: stNum incremented to %lu\n", newStNum);
        fflush(stdout);
    } else {
        // For heartbeats, libiec61850 automatically increments sqNum
        printf(">>> GOOSE HEARTBEAT: sqNum auto-incremented\n");
        fflush(stdout);
    }
    
    LinkedList dataSetValues = LinkedList_create();
    
    LinkedList_add(dataSetValues, MmsValue_newBoolean(prot_state.trip_active));
    LinkedList_add(dataSetValues, MmsValue_newUtcTimeByMsTime(Hal_getTimeInMs()));
    
    LinkedList_add(dataSetValues, MmsValue_newBoolean(g_breaker_status_from_goose));
    LinkedList_add(dataSetValues, MmsValue_newUtcTimeByMsTime(Hal_getTimeInMs()));
    
    LinkedList_add(dataSetValues, MmsValue_newBoolean(prot_state.overcurrent_pickup || prot_state.ground_fault_pickup));
    LinkedList_add(dataSetValues, MmsValue_newUtcTimeByMsTime(Hal_getTimeInMs()));
    
    LinkedList_add(dataSetValues, MmsValue_newBoolean(prot_state.overcurrent_pickup));
    LinkedList_add(dataSetValues, MmsValue_newUtcTimeByMsTime(Hal_getTimeInMs()));
    
    GoosePublisher_publish(goosePublisher, dataSetValues);
    
    LinkedList_destroyDeep(dataSetValues, (LinkedListValueDeleteFunction) MmsValue_delete);
}

ControlHandlerResult
controlHandler(ControlAction action, void* parameter, MmsValue* ctlVal, bool test) {
    if (ControlAction_isSelect(action) || !ControlAction_isSelect(action)) {
        if (MmsValue_getBoolean(ctlVal)) {
            printf("\n>>> MMS CONTROL: Manual Trip Received <<<\n");
            prot_state.trip_active = 1;
            strcpy(prot_state.trip_reason, "Manual Trip (MMS)");
            
            // Immediately publish GOOSE message
            publishGooseMessage(true);  // State change
            printf(">>> GOOSE TRIP PUBLISHED: %s\n", prot_state.trip_reason);
            
            return CONTROL_RESULT_OK;
        }
    }
    return CONTROL_RESULT_FAILED;
}

int main(int argc, char** argv) {
    printf("=== IEC 61850 PROTECTION RELAY ===\n");
    printf("Device: PROT_REL_001 | Station: MAIN_SS_132kV\n");
    printf("MMS Server: Port 102 | GOOSE Publisher: Active\n");
    printf("Networks: Process Bus + Station Bus\n\n");
    
    IedServerConfig config = IedServerConfig_create();
    iedServer = IedServer_createWithConfig(&iedModel, NULL, config);
    IedServerConfig_destroy(config);

    IedServer_setControlHandler(iedServer, IEDMODEL_GenericIO_GGIO1_SPCSO1, 
                               (ControlHandler) controlHandler, NULL);
    printf("✅ MMS Control Handler for Manual Trip installed\n");
    
    IedServer_start(iedServer, 102);
    if (!IedServer_isRunning(iedServer)) {
        printf("❌ MMS Server failed to start on port 102\n");
        exit(-1);
    }
    printf("✅ MMS Server started on port 102\n");
    
    CommParameters gooseCommParameters;
    gooseCommParameters.appId = 4096;
    gooseCommParameters.dstAddress[0] = 0x01;
    gooseCommParameters.dstAddress[1] = 0x0c;
    gooseCommParameters.dstAddress[2] = 0xcd;
    gooseCommParameters.dstAddress[3] = 0x01;
    gooseCommParameters.dstAddress[4] = 0x00;
    gooseCommParameters.dstAddress[5] = 0x01;
    gooseCommParameters.vlanId = 0;
    gooseCommParameters.vlanPriority = 4;
    
    goosePublisher = GoosePublisher_create(&gooseCommParameters, "eth0");
    if (goosePublisher) {
        printf("✅ GOOSE Publisher created on eth0\n");
    } else {
        printf("❌ GOOSE Publisher failed on lo\n");
    }
    if (goosePublisher) {
        GoosePublisher_setGoCbRef(goosePublisher, "simpleIOGenericIO/LLN0$GO$gcbEvents");
        GoosePublisher_setDataSetRef(goosePublisher, "simpleIOGenericIO/LLN0$dataset");
        GoosePublisher_setConfRev(goosePublisher, 1);
        GoosePublisher_setTimeAllowedToLive(goosePublisher, 3000);
        printf("✅ GOOSE Publisher initialized on eth0\n");
    } else {
        printf("❌ GOOSE Publisher failed to initialize\n");
    }
    
    gooseReceiver = GooseReceiver_create();
    GooseReceiver_setInterfaceId(gooseReceiver, "eth0");
    printf(">>> GOOSE Receiver set to eth0\n");
    
    GooseSubscriber breakerSubscriber = GooseSubscriber_create("circuitBreakerIO/LLN0$GO$gcbStatus", NULL);
    uint8_t breakerMac[6] = {0x01, 0x0c, 0xcd, 0x01, 0x00, 0x02};
    GooseSubscriber_setDstMac(breakerSubscriber, breakerMac);
    GooseSubscriber_setAppId(breakerSubscriber, 4097);
    GooseSubscriber_setListener(breakerSubscriber, breakerStatusListener, NULL);
    
    GooseReceiver_addSubscriber(gooseReceiver, breakerSubscriber);
    GooseReceiver_start(gooseReceiver);
    
    printf("✅ GOOSE Status monitoring ready\n");
    
    printf("✅ MMS Reporting framework ready\n");
    
    running = 1;
    signal(SIGINT, sigint_handler);
    
    pthread_t http_thread;
    pthread_create(&http_thread, NULL, http_server_thread, NULL);
    
    int cycle = 0;
    
    while (running) {
        cycle++;
        uint64_t timestamp = Hal_getTimeInMs();
        
        if (fetchSimulationData(&simData) == 0) {
            printf("[%d] Simulation Input: V=%.1fkV I=%.0fA F=%.3fHz FC=%.0fA\n", 
                   cycle, simData.voltage, simData.current, simData.frequency, simData.faultCurrent);
        }
        
        int trip_issued = 0;
        
        if (simData.current < 1000 && simData.faultCurrent < 300 && 
            simData.frequency > 49.5 && simData.frequency < 50.5) {
            if (prot_state.overcurrent_pickup || prot_state.ground_fault_pickup) {
                printf(">>> PROTECTION RESET - Normal conditions\n");
                prot_state.overcurrent_pickup = 0;
                prot_state.ground_fault_pickup = 0;
                prot_state.pickup_time = 0;
                strcpy(prot_state.trip_reason, "Normal");
            }
        }
        
        if (simData.current >= 2500) {
            if (!prot_state.trip_active) {
                printf(">>> 50 INSTANTANEOUS O/C: %.0fA - TRIP\n", simData.current);
                strcpy(prot_state.trip_reason, "50-Instantaneous O/C");
                prot_state.trip_active = 1;
                trip_issued = 1;
            }
        } else if (simData.current >= 1000) {
            if (!prot_state.overcurrent_pickup) {
                printf(">>> 51 O/C PICKUP: %.0fA - Timer started\n", simData.current);
                prot_state.overcurrent_pickup = 1;
                prot_state.pickup_time = timestamp;
            } else if ((timestamp - prot_state.pickup_time) > 1000 && !prot_state.trip_active) {
                printf(">>> 51 TIME O/C TRIP: 1.0s expired - TRIP\n");
                strcpy(prot_state.trip_reason, "51-Time O/C");
                prot_state.trip_active = 1;
                trip_issued = 1;
            }
        }
        
        if (simData.faultCurrent >= 800) {
            if (!prot_state.trip_active) {
                printf(">>> 50G INSTANTANEOUS GF: %.0fA - TRIP\n", simData.faultCurrent);
                strcpy(prot_state.trip_reason, "50G-Instantaneous GF");
                prot_state.trip_active = 1;
                trip_issued = 1;
            }
        } else if (simData.faultCurrent >= 300) {
            if (!prot_state.ground_fault_pickup) {
                printf(">>> 51G GF PICKUP: %.0fA - Timer started\n", simData.faultCurrent);
                prot_state.ground_fault_pickup = 1;
                prot_state.pickup_time = timestamp;
            } else if ((timestamp - prot_state.pickup_time) > 500 && !prot_state.trip_active) {
                printf(">>> 51G TIME GF TRIP: 0.5s expired - TRIP\n");
                strcpy(prot_state.trip_reason, "51G-Time GF");
                prot_state.trip_active = 1;
                trip_issued = 1;
            }
        }
        
        if (simData.frequency < 48.5) {
            if (!prot_state.trip_active) {
                printf(">>> 81U UNDERFREQUENCY: %.3fHz - TRIP\n", simData.frequency);
                strcpy(prot_state.trip_reason, "81U-Underfrequency");
                prot_state.trip_active = 1;
                trip_issued = 1;
            }
        }
        
        if (prot_state.trip_active && g_breaker_status_from_goose) {
            printf(">>> TRIP RESET - Breaker opened (GOOSE feedback)\n");
            prot_state.trip_active = 0;
            strcpy(prot_state.trip_reason, "Normal");
        }
        
        IedServer_lockDataModel(iedServer);
        
        IedServer_updateBooleanAttributeValue(iedServer, IEDMODEL_GenericIO_GGIO1_SPCSO1_stVal, prot_state.trip_active);
        IedServer_updateBooleanAttributeValue(iedServer, IEDMODEL_GenericIO_GGIO1_SPCSO2_stVal, g_breaker_status_from_goose);
        IedServer_updateBooleanAttributeValue(iedServer, IEDMODEL_GenericIO_GGIO1_SPCSO3_stVal, (prot_state.overcurrent_pickup || prot_state.ground_fault_pickup));
        IedServer_updateBooleanAttributeValue(iedServer, IEDMODEL_GenericIO_GGIO1_SPCSO4_stVal, prot_state.overcurrent_pickup);
        
        IedServer_updateFloatAttributeValue(iedServer, IEDMODEL_GenericIO_GGIO1_AnIn1_mag_f, simData.voltage);
        IedServer_updateFloatAttributeValue(iedServer, IEDMODEL_GenericIO_GGIO1_AnIn2_mag_f, simData.current);
        IedServer_updateFloatAttributeValue(iedServer, IEDMODEL_GenericIO_GGIO1_AnIn3_mag_f, simData.frequency);
        IedServer_updateFloatAttributeValue(iedServer, IEDMODEL_GenericIO_GGIO1_AnIn4_mag_f, simData.faultCurrent);
        
        IedServer_updateUTCTimeAttributeValue(iedServer, IEDMODEL_GenericIO_GGIO1_SPCSO1_t, timestamp);
        IedServer_updateUTCTimeAttributeValue(iedServer, IEDMODEL_GenericIO_GGIO1_SPCSO2_t, timestamp);
        IedServer_updateUTCTimeAttributeValue(iedServer, IEDMODEL_GenericIO_GGIO1_SPCSO3_t, timestamp);
        IedServer_updateUTCTimeAttributeValue(iedServer, IEDMODEL_GenericIO_GGIO1_SPCSO4_t, timestamp);
        
        IedServer_unlockDataModel(iedServer);
        
        // Check for data changes and publish GOOSE accordingly
        int current_trip = prot_state.trip_active;
        int current_breaker = g_breaker_status_from_goose ? 1 : 0;
        int current_fault = (prot_state.overcurrent_pickup || prot_state.ground_fault_pickup) ? 1 : 0;
        int current_oc = prot_state.overcurrent_pickup;
        
        bool data_changed = (current_trip != goose_state.last_trip_active) ||
                           (current_breaker != goose_state.last_breaker_status) ||
                           (current_fault != goose_state.last_fault_detected) ||
                           (current_oc != goose_state.last_overcurrent_pickup);
        
        if (data_changed) {
            printf(">>> GOOSE DATA CHANGE: Trip=%d->%d, Breaker=%d->%d, Fault=%d->%d, OC=%d->%d\n",
                   goose_state.last_trip_active, current_trip,
                   goose_state.last_breaker_status, current_breaker,
                   goose_state.last_fault_detected, current_fault,
                   goose_state.last_overcurrent_pickup, current_oc);
            
            goose_state.last_trip_active = current_trip;
            goose_state.last_breaker_status = current_breaker;
            goose_state.last_fault_detected = current_fault;
            goose_state.last_overcurrent_pickup = current_oc;
            
            publishGooseMessage(true);  // State change
            printf(">>> GOOSE PUBLISHED: %s\n", prot_state.trip_reason);
        }
        
        // Always publish GOOSE for heartbeat (libiec61850 manages stNum/sqNum)
        static int heartbeat_counter = 0;
        heartbeat_counter++;
        if (heartbeat_counter >= 6) {  // Every 3 seconds
            publishGooseMessage(false);  // Retransmission/heartbeat
            printf(">>> GOOSE HEARTBEAT\n");
            heartbeat_counter = 0;
        }
        
        if (trip_issued) {
            printf(">>> PROTECTION TRIP: %s\n", prot_state.trip_reason);
        }
        
        Thread_sleep(500);
    }
    
    if (goosePublisher) {
        GoosePublisher_destroy(goosePublisher);
    }
    
    IedServer_stop(iedServer);
    IedServer_destroy(iedServer);
    return 0;
}