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
#include "model_alias.h"

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

// Prototypes for helper/server
static void* http_status_thread(void* arg);
static void build_status_json(char* body, size_t len);
static void relay_latch_trip(const char* reason);
static void relay_reset_trip(void);

// Lightweight HTTP status server (port 8082) for GUI
static void* http_status_thread(void* arg) {
    int server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd < 0) return NULL;
    int opt = 1;
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
    struct sockaddr_in address;
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(8082);
    if (bind(server_fd, (struct sockaddr*)&address, sizeof(address)) < 0) {
        close(server_fd);
        return NULL;
    }
    listen(server_fd, 5);
    printf("✅ Relay HTTP status server listening on port 8082\n");
    while (running) {
        struct sockaddr_in client; socklen_t clen = sizeof(client);
        int sock = accept(server_fd, (struct sockaddr*)&client, &clen);
        if (sock < 0) continue;
        char buffer[512] = {0};
        recv(sock, buffer, sizeof(buffer)-1, 0);
        // Minimal routing for local GUI: POST /trip, POST /reset, GET /
        if (strstr(buffer, "POST /trip")) {
            // Latch trip and publish GOOSE
            relay_latch_trip("Manual Trip (GUI)");
            const char* resp = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\n\r\n{\"status\":\"trip_latched\"}";
            send(sock, resp, strlen(resp), 0);
        } else if (strstr(buffer, "POST /reset")) {
            // Clear trip and all pickups and publish GOOSE
            relay_reset_trip();
            const char* resp = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\n\r\n{\"status\":\"reset_done\"}";
            send(sock, resp, strlen(resp), 0);
        } else {
            // Respond with JSON of current measured and status values
            char body[512];
            build_status_json(body, sizeof(body));
            char response[1024];
            snprintf(response, sizeof(response),
                "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\n\r\n%s", body);
            send(sock, response, strlen(response), 0);
        }
        close(sock);
    }
    close(server_fd);
    return NULL;
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
// RX supervision for breaker status GOOSE (received by relay)
static uint32_t br_rx_count = 0;
static uint64_t br_last_rx_ms = 0;
// TX supervision for relay GOOSE publish
static uint32_t rl_tx_count = 0;
static uint64_t rl_last_tx_ms = 0;

// Build JSON body for HTTP status
static void build_status_json(char* body, size_t len) {
    uint64_t now = Hal_getTimeInMs();
    bool rx_ok = (br_last_rx_ms != 0) && ((now - br_last_rx_ms) < 5000);
    bool tx_ok = (rl_last_tx_ms != 0) && ((now - rl_last_tx_ms) < 5000);
    snprintf(body, len,
        "{\"voltage\":%.1f,\"current\":%.0f,\"frequency\":%.3f,\"faultCurrent\":%.0f,\"faultDetected\":%s,\"tripCommand\":%s,\"breakerStatus\":%s,\"rxCount\":%u,\"lastRxMs\":%llu,\"rxOk\":%s,\"txCount\":%u,\"lastTxMs\":%llu,\"txOk\":%s}",
        simData.voltage, simData.current, simData.frequency, simData.faultCurrent,
        (prot_state.overcurrent_pickup || prot_state.ground_fault_pickup) ? "true" : "false",
        prot_state.trip_active ? "true" : "false",
        g_breaker_status_from_goose ? "true" : "false",
        br_rx_count,
        (unsigned long long) br_last_rx_ms,
        rx_ok ? "true" : "false",
        rl_tx_count,
        (unsigned long long) rl_last_tx_ms,
        tx_ok ? "true" : "false");
}

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
    int size = values ? MmsValue_getArraySize(values) : 0;
    if (values && size >= 1) {
        MmsValue* breakerPos = MmsValue_getElement(values, 0);
        if (breakerPos && MmsValue_getType(breakerPos) == MMS_BOOLEAN) {
            g_breaker_status_from_goose = MmsValue_getBoolean(breakerPos);
            printf(">>> GOOSE Breaker Status Received: %s\n", 
                   g_breaker_status_from_goose ? "OPEN" : "CLOSED");
            br_rx_count++;
            br_last_rx_ms = Hal_getTimeInMs();
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

    // Determine if test mode is active for Quality.test flag
    bool test_mode = false;
    const char* testEnv = getenv("TEST_MODE");
    if (testEnv && (strcmp(testEnv, "1") == 0 || strcmp(testEnv, "true") == 0 || strcmp(testEnv, "TRUE") == 0)) {
        test_mode = true;
    }


    // Dataset: 4 booleans (stVal only) to match generator-friendly SCL
    LinkedList_add(dataSetValues, MmsValue_newBoolean(prot_state.trip_active));
    LinkedList_add(dataSetValues, MmsValue_newBoolean(g_breaker_status_from_goose));
    LinkedList_add(dataSetValues, MmsValue_newBoolean(prot_state.overcurrent_pickup || prot_state.ground_fault_pickup));
    LinkedList_add(dataSetValues, MmsValue_newBoolean(prot_state.overcurrent_pickup));

    GoosePublisher_publish(goosePublisher, dataSetValues);
    // Update TX supervision
    rl_last_tx_ms = Hal_getTimeInMs();
    rl_tx_count++;

    LinkedList_destroyDeep(dataSetValues, (LinkedListValueDeleteFunction) MmsValue_delete);
}

ControlHandlerResult
controlHandler(ControlAction action, void* parameter, MmsValue* ctlVal, bool test) {
    if (ControlAction_isSelect(action)) {
        bool tripCmd = MmsValue_getBoolean(ctlVal);
        if (tripCmd) {
            printf("\n>>> MMS CONTROL: Manual Trip Received <<<\n");
            relay_latch_trip("Manual Trip (MMS)");
            printf(">>> GOOSE TRIP PUBLISHED: %s\n", prot_state.trip_reason);
        } else {
            printf("\n>>> MMS CONTROL: Trip Reset Received <<<\n");
            relay_reset_trip();
            printf(">>> PROTECTION RESET via MMS\n");
        }
        return CONTROL_RESULT_OK;
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

    IedServer_setControlHandler(iedServer, IEDMODEL_LD0_PTRC1_Tr_DO, 
                               (ControlHandler) controlHandler, NULL);
    // Install RCB event handler for reporting supervision/logging
    IedServer_setRCBEventHandler(iedServer, (IedServer_RCBEventHandler) rcbEventHandler, NULL);
    printf("✅ MMS Control Handler for Manual Trip installed\n");
    
    IedServer_start(iedServer, 102);
    if (!IedServer_isRunning(iedServer)) {
        printf("❌ MMS Server failed to start on port 102\n");
        exit(-1);
    }
    printf("✅ MMS Server started on port 102\n");
    
    CommParameters gooseCommParameters;
    gooseCommParameters.appId = 1000; // match ln_ied.icd APPID
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
        GoosePublisher_setGoCbRef(goosePublisher, "GenericIO/LLN0$GO$gcbEvents");
        // Generator-friendly SCL DataSetRef: GenericIO/LLN0$Events
        GoosePublisher_setDataSetRef(goosePublisher, "GenericIO/LLN0$Events");
        GoosePublisher_setConfRev(goosePublisher, 1);
        GoosePublisher_setTimeAllowedToLive(goosePublisher, 5000);
        printf("✅ GOOSE Publisher initialized on eth0 (DataSet=LLN0$Events)\n");
    } else {
        printf("❌ GOOSE Publisher failed to initialize\n");
    }
    
    gooseReceiver = GooseReceiver_create();
    GooseReceiver_setInterfaceId(gooseReceiver, "eth0");
    printf(">>> GOOSE Receiver set to eth0\n");
    
    GooseSubscriber breakerSubscriber = GooseSubscriber_create("LD0/LLN0$GO$gcbStatus", NULL);
    uint8_t breakerMac[6] = {0x01, 0x0c, 0xcd, 0x01, 0x00, 0x02};
    GooseSubscriber_setDstMac(breakerSubscriber, breakerMac);
    GooseSubscriber_setAppId(breakerSubscriber, 1001); // match ln_breaker.icd APPID
    GooseSubscriber_setListener(breakerSubscriber, breakerStatusListener, NULL);
    
    GooseReceiver_addSubscriber(gooseReceiver, breakerSubscriber);
    GooseReceiver_start(gooseReceiver);
    
    printf("✅ GOOSE Status monitoring ready\n");
    
    printf("✅ MMS Reporting framework ready\n");
    
    running = 1;
    signal(SIGINT, sigint_handler);

    // Start HTTP status server for GUI
    pthread_t http_thread;
    pthread_create(&http_thread, NULL, http_status_thread, NULL);
    

    
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
        
        IedServer_updateBooleanAttributeValue(iedServer, IEDMODEL_LD0_PTRC1_Tr_stVal, prot_state.trip_active);
        IedServer_updateBooleanAttributeValue(iedServer, IEDMODEL_LD0_XCBR1_Pos_stVal, g_breaker_status_from_goose);
        IedServer_updateBooleanAttributeValue(iedServer, IEDMODEL_LD0_PTOC1_Op_stVal, (prot_state.overcurrent_pickup || prot_state.ground_fault_pickup));
        IedServer_updateBooleanAttributeValue(iedServer, IEDMODEL_LD0_PTOC1_Str_stVal, prot_state.overcurrent_pickup);

        // Update Quality attributes to GOOD (and TEST if requested)
        Quality q = 0;
        Quality_setValidity(&q, QUALITY_VALIDITY_GOOD);
        const char* testEnv = getenv("TEST_MODE");
        if (testEnv && (strcmp(testEnv, "1") == 0 || strcmp(testEnv, "true") == 0 || strcmp(testEnv, "TRUE") == 0)) {
            Quality_setFlag(&q, QUALITY_TEST);
        }
        IedServer_updateQuality(iedServer, IEDMODEL_LD0_PTRC1_Tr_q, q);
        IedServer_updateQuality(iedServer, IEDMODEL_LD0_XCBR1_Pos_q, q);
        IedServer_updateQuality(iedServer, IEDMODEL_LD0_PTOC1_Op_q, q);
        IedServer_updateQuality(iedServer, IEDMODEL_LD0_PTOC1_Str_q, q);
        
        IedServer_updateFloatAttributeValue(iedServer, IEDMODEL_LD0_MMXU1_PhV_mag_f, simData.voltage);
        IedServer_updateFloatAttributeValue(iedServer, IEDMODEL_LD0_MMXU1_Amp_mag_f, simData.current);
        IedServer_updateFloatAttributeValue(iedServer, IEDMODEL_LD0_MMXU1_Hz_mag_f, simData.frequency);
        // Fault current placeholder mapping (extend model if needed)
        
        IedServer_updateUTCTimeAttributeValue(iedServer, IEDMODEL_LD0_PTRC1_Tr_t, timestamp);
        IedServer_updateUTCTimeAttributeValue(iedServer, IEDMODEL_LD0_XCBR1_Pos_t, timestamp);
        IedServer_updateUTCTimeAttributeValue(iedServer, IEDMODEL_LD0_PTOC1_Op_t, timestamp);
        IedServer_updateUTCTimeAttributeValue(iedServer, IEDMODEL_LD0_PTOC1_Str_t, timestamp);
        
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
        if (heartbeat_counter >= 2) {  // Every ~1 second
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

// Helper implementations
static void relay_latch_trip(const char* reason) {
    prot_state.trip_active = 1;
    if (reason && reason[0]) strcpy(prot_state.trip_reason, reason);
    publishGooseMessage(true);
}

static void relay_reset_trip(void) {
    prot_state.trip_active = 0;
    prot_state.overcurrent_pickup = 0;
    prot_state.ground_fault_pickup = 0;
    prot_state.pickup_time = 0;
    strcpy(prot_state.trip_reason, "Normal");
    publishGooseMessage(true);
}
