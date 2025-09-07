#include "goose_receiver.h"
#include "goose_subscriber.h"
#include "goose_publisher.h"
#include "linked_list.h"
#include "mms_value.h"
#include "hal_thread.h"
#include "iec61850_server.h"
#include "static_model.h"
#include <stdlib.h>
#include <stdio.h>
#include <signal.h>
#include <sys/select.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <string.h>
#include <pthread.h>
#include <time.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

void publishBreakerStatus(bool is_state_change);

static int running = 1;
static bool breaker_open = false;
static bool trip_received = false;
static int server_fd = -1;
static GoosePublisher statusPublisher = NULL;
static IedServer iedServer = NULL;
static pthread_mutex_t breaker_mutex = PTHREAD_MUTEX_INITIALIZER;

// GOOSE message tracking
static uint32_t last_stnum = 0;
static uint32_t last_sqnum = 0;
static uint32_t goose_msg_count = 0;
static char last_goose_time[32] = "--:--:--";
static uint64_t last_goose_ms = 0;

// GOOSE sequence management for publisher
static struct {
    bool last_breaker_open;
    uint32_t stNum;     // Status number - increments on data change
    uint32_t sqNum;     // Sequence number - increments on retransmission
} breaker_goose_state = {false, 1, 0};

// Lightweight HTTP status server (port 8081)
static void* http_status_thread(void* arg) {
    int server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd < 0) return NULL;

    int opt = 1;
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    struct sockaddr_in address;
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(8081);

    if (bind(server_fd, (struct sockaddr*)&address, sizeof(address)) < 0) {
        close(server_fd);
        return NULL;
    }
    listen(server_fd, 5);

    while (running) {
        struct sockaddr_in client;
        socklen_t clen = sizeof(client);
        int sock = accept(server_fd, (struct sockaddr*)&client, &clen);
        if (sock < 0) continue;

        char buffer[512] = {0};
        recv(sock, buffer, sizeof(buffer) - 1, 0);

        char response[1024];
        // Basic route handling
        if (strstr(buffer, "POST /trip")) {
            pthread_mutex_lock(&breaker_mutex);
            breaker_open = true; trip_received = true;
            pthread_mutex_unlock(&breaker_mutex);
            publishBreakerStatus(true);
            snprintf(response, sizeof(response),
                "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\n\r\n{\"status\":\"trip\"}");
            send(sock, response, strlen(response), 0);
        } else if (strstr(buffer, "POST /close")) {
            pthread_mutex_lock(&breaker_mutex);
            breaker_open = false; trip_received = false;
            pthread_mutex_unlock(&breaker_mutex);
            publishBreakerStatus(true);
            snprintf(response, sizeof(response),
                "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\n\r\n{\"status\":\"close\"}");
            send(sock, response, strlen(response), 0);
        } else {
            // Status JSON
            pthread_mutex_lock(&breaker_mutex);
            uint64_t now = Hal_getTimeInMs();
            bool rx_ok = (last_goose_ms != 0) && ((now - last_goose_ms) < 5000);
            static uint32_t br_tx_count = 0; // total publishes
            static uint64_t br_last_tx_ms = 0;
            // Note: updated in publishBreakerStatus via externs below
            const char* json_fmt =
                "{\"stNum\":%u,\"sqNum\":%u,\"messageCount\":%u,\"lastTime\":\"%s\",\"breakerOpen\":%s,\"position\":\"%s\",\"tripReceived\":%s,\"rxOk\":%s,\"lastRxMs\":%llu,\"txCount\":%u,\"lastTxMs\":%llu,\"txOk\":%s}";
            char body[512];
            snprintf(body, sizeof(body), json_fmt,
                     last_stnum, last_sqnum, goose_msg_count, last_goose_time,
                     breaker_open ? "true" : "false",
                     breaker_open ? "OPEN" : "CLOSED",
                     trip_received ? "true" : "false",
                     rx_ok ? "true" : "false",
                     (unsigned long long) last_goose_ms,
                     br_tx_count,
                     (unsigned long long) br_last_tx_ms,
                     ((br_last_tx_ms != 0) && ((now - br_last_tx_ms) < 5000)) ? "true" : "false");
            pthread_mutex_unlock(&breaker_mutex);
            snprintf(response, sizeof(response),
                     "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\n\r\n%s",
                     body);
            send(sock, response, strlen(response), 0);
        }
        close(sock);
    }

    close(server_fd);
    return NULL;
}

// MMS control handler for breaker open/close commands
ControlHandlerResult controlHandler(ControlAction action, void* parameter, MmsValue* ctlVal, bool test) {
    if (ControlAction_isSelect(action)) {
        bool openCmd = MmsValue_getBoolean(ctlVal);
        pthread_mutex_lock(&breaker_mutex);
        
        if (openCmd && !breaker_open) {  // Open command (true = open)
            printf("\n>>> MMS OPEN COMMAND RECEIVED <<<\n");
            breaker_open = true;
            trip_received = false;
            pthread_mutex_unlock(&breaker_mutex);
            publishBreakerStatus(true);
            return CONTROL_RESULT_OK;
        } else if (!openCmd && breaker_open) {  // Close command (false = close)
            printf("\n>>> MMS CLOSE COMMAND RECEIVED <<<\n");
            breaker_open = false;
            trip_received = false;
            pthread_mutex_unlock(&breaker_mutex);
            publishBreakerStatus(true);
            return CONTROL_RESULT_OK;
        }
        pthread_mutex_unlock(&breaker_mutex);
    }
    return CONTROL_RESULT_FAILED;
}

static void sigint_handler(int signalId) {
    running = 0;
}

void publishBreakerStatus(bool is_state_change) {
    pthread_mutex_lock(&breaker_mutex);
    printf(">>> Breaker Status: Position=%s, TripReceived=%s\n", 
           breaker_open ? "OPEN" : "CLOSED", trip_received ? "YES" : "NO");
    
    if (!statusPublisher) {
        printf(">>> ERROR: statusPublisher is NULL!\n");
        pthread_mutex_unlock(&breaker_mutex);
        return;
    }
    
    // Update sequence numbers per IEC 61850-8-1
    if (is_state_change) {
        uint64_t newStNum = GoosePublisher_increaseStNum(statusPublisher);
        printf(">>> BREAKER STATE CHANGE: stNum incremented to %lu\n", newStNum);
        fflush(stdout);
    } else {
        printf(">>> BREAKER HEARTBEAT: sqNum auto-incremented\n");
        fflush(stdout);
    }
    
    LinkedList dataSetValues = LinkedList_create();
    // LN-based BrkStatus dataset contains only XCBR1.Pos.stVal (boolean)
    LinkedList_add(dataSetValues, MmsValue_newBoolean(breaker_open));
    
    if (is_state_change) {
        // IEC 61850-8-1: GOOSE burst - multiple rapid publishes
        for (int i = 0; i < 4; i++) {
            GoosePublisher_publish(statusPublisher, dataSetValues);
            printf(">>> GOOSE BURST %d/4: %s\n", i+1, breaker_open ? "OPEN" : "CLOSED");
            if (i < 3) Thread_sleep(4); // 4ms delay
        }
    } else {
        GoosePublisher_publish(statusPublisher, dataSetValues);
        printf(">>> GOOSE HEARTBEAT: %s\n", breaker_open ? "OPEN" : "CLOSED");
    }
    
    LinkedList_destroyDeep(dataSetValues, (LinkedListValueDeleteFunction) MmsValue_delete);
    
    // Mirror position to MMS XCBR1.Pos (ST): stVal (Dbpos)/q/t
    if (iedServer) {
        IedServer_lockDataModel(iedServer);
        // Dbpos: OFF(1)=OPEN, ON(2)=CLOSED
        IedServer_updateDbposValue(iedServer, IEDMODEL_GenericIO_XCBR1_Pos_stVal,
                                   breaker_open ? DBPOS_OFF : DBPOS_ON);
        Quality q = 0; Quality_setValidity(&q, QUALITY_VALIDITY_GOOD);
        IedServer_updateQuality(iedServer, IEDMODEL_GenericIO_XCBR1_Pos_q, q);
        IedServer_updateUTCTimeAttributeValue(iedServer, IEDMODEL_GenericIO_XCBR1_Pos_t, Hal_getTimeInMs());
        IedServer_unlockDataModel(iedServer);
    }
    // Update local TX supervision counters
    static uint32_t* p_tx_count = NULL;
    static uint64_t* p_last_tx_ms = NULL;
    // initialize static pointers to ensure single storage
    if (p_tx_count == NULL) {
        static uint32_t tx_count_storage = 0; p_tx_count = &tx_count_storage;
    }
    if (p_last_tx_ms == NULL) {
        static uint64_t last_tx_ms_storage = 0; p_last_tx_ms = &last_tx_ms_storage;
    }
    (*p_tx_count)++;
    (*p_last_tx_ms) = Hal_getTimeInMs();
    pthread_mutex_unlock(&breaker_mutex);
}



static void gooseListener(GooseSubscriber subscriber, void* parameter) {
    static uint32_t lastStNum = 0;
    static uint32_t lastSqNum = 0;
    
    // First, log that the listener was called at all
    printf("\n*** GOOSE LISTENER CALLED ***\n");
    fflush(stdout);
    
    uint32_t stNum = GooseSubscriber_getStNum(subscriber);
    uint32_t sqNum = GooseSubscriber_getSqNum(subscriber);
    
    // Always log GOOSE messages (including heartbeats)
    printf("\n=== GOOSE MESSAGE RECEIVED ===\n");
    printf("Publisher: %s\n", GooseSubscriber_getGoCbRef(subscriber));
    printf("StNum: %u | SqNum: %u | TTL: %ums\n", stNum, sqNum, GooseSubscriber_getTimeAllowedToLive(subscriber));
    
    // Check for state changes
    if (stNum != lastStNum) {
        printf("*** STATE CHANGE DETECTED *** (StNum: %u -> %u)\n", lastStNum, stNum);
    }
    if (sqNum != lastSqNum) {
        printf("*** SEQUENCE CHANGE *** (SqNum: %u -> %u)\n", lastSqNum, sqNum);
    }
    
    // Update global tracking variables
    pthread_mutex_lock(&breaker_mutex);
    last_stnum = stNum;
    last_sqnum = sqNum;
    goose_msg_count++;
    // Update RX supervision timestamp on every message
    last_goose_ms = Hal_getTimeInMs();
    
    // Update timestamp
    time_t now = time(NULL);
    struct tm* tm_info = localtime(&now);
    strftime(last_goose_time, sizeof(last_goose_time), "%H:%M:%S", tm_info);
    pthread_mutex_unlock(&breaker_mutex);
    
    lastStNum = stNum;
    lastSqNum = sqNum;
    
    MmsValue* values = GooseSubscriber_getDataSetValues(subscriber);
    
    if (values && MmsValue_getArraySize(values) >= 4) {
        // Parse GOOSE dataset
        MmsValue* tripSignal = MmsValue_getElement(values, 0);      // SPCSO1 - Trip Command
        MmsValue* breakerPos = MmsValue_getElement(values, 1);      // SPCSO2 - Breaker Position
        MmsValue* faultDet = MmsValue_getElement(values, 2);        // SPCSO3 - Fault Detected
        MmsValue* ocPickup = MmsValue_getElement(values, 3);        // SPCSO4 - OC Pickup
        
        bool trip = (tripSignal && MmsValue_getType(tripSignal) == MMS_BOOLEAN) ? 
                   MmsValue_getBoolean(tripSignal) : false;
        bool fault = (faultDet && MmsValue_getType(faultDet) == MMS_BOOLEAN) ? 
                    MmsValue_getBoolean(faultDet) : false;
        bool oc = (ocPickup && MmsValue_getType(ocPickup) == MMS_BOOLEAN) ? 
                 MmsValue_getBoolean(ocPickup) : false;
        
        printf("GOOSE Data:\n");
        printf("  Trip Command: %s\n", trip ? "*** ACTIVE ***" : "Normal");
        printf("  Fault Status: %s\n", fault ? "*** DETECTED ***" : "Normal");
        printf("  OC Pickup: %s\n", oc ? "*** ACTIVE ***" : "Normal");
        pthread_mutex_lock(&breaker_mutex);
        printf("  Breaker: %s\n", breaker_open ? "OPEN" : "CLOSED");
        
        // AUTOMATIC TRIP LOGIC
        if (trip && !breaker_open) {
            printf("\n🚨 TRIP COMMAND RECEIVED - OPENING BREAKER 🚨\n");
            breaker_open = true;
            trip_received = true;
            printf(">>> Circuit Breaker OPENED automatically\n");
    pthread_mutex_unlock(&breaker_mutex);
    
    // Track last receive time (ms)
    last_goose_ms = Hal_getTimeInMs();
            publishBreakerStatus(true);  // State change
        } else if (!trip && trip_received) {
            // Reset trip flag when trip command goes away
            trip_received = false;
            printf(">>> Trip command cleared\n");
            pthread_mutex_unlock(&breaker_mutex);
        } else {
            pthread_mutex_unlock(&breaker_mutex);
        }
        
    } else {
        printf("❌ Invalid GOOSE dataset received (size: %d)\n", 
               values ? MmsValue_getArraySize(values) : 0);
    }
    
    printf("===============================\n");
    fflush(stdout);  // Force log output
}

int main(int argc, char** argv) {
    printf("=== IEC 61850 CIRCUIT BREAKER ===\n");
    printf("Device: CB_LINE_01_001 | Bay: LINE_01\n");
    printf("GOOSE Subscriber: Process Bus (192.168.10.0/24)\n");
    printf("Interface: eth0 | AppId: 4096\n");
    printf("Commands: 't'=trip, 'c'=close, 'q'=quit\n\n");
    
    GooseReceiver receiver = GooseReceiver_create();
    GooseReceiver_setInterfaceId(receiver, "eth0");
    printf(">>> GOOSE Receiver set to eth0\n");
    
    // Subscribe to Protection Relay GOOSE messages
    GooseSubscriber subscriber = GooseSubscriber_create("simpleIOGenericIO/LLN0$GO$gcbEvents", NULL);
    
    uint8_t dstMac[6] = {0x01, 0x0c, 0xcd, 0x01, 0x00, 0x01};
    GooseSubscriber_setDstMac(subscriber, dstMac);
    GooseSubscriber_setAppId(subscriber, 1000); // match ln_ied.icd APPID
    GooseSubscriber_setListener(subscriber, gooseListener, NULL);
    
    GooseReceiver_addSubscriber(receiver, subscriber);
    printf("🔄 Starting GOOSE Receiver on eth0...\n");
    
    // Add debug info before starting
    printf("DEBUG: Receiver created, interface set to eth0\n");
    printf("DEBUG: Subscriber configured for GoCbRef: %s\n", "simpleIOGenericIO/LLN0$GO$gcbEvents");
    printf("DEBUG: AppId: %d, MAC: %02x:%02x:%02x:%02x:%02x:%02x\n", 
           4096, dstMac[0], dstMac[1], dstMac[2], dstMac[3], dstMac[4], dstMac[5]);
    
    GooseReceiver_start(receiver);
    
    if (!GooseReceiver_isRunning(receiver)) {
        printf("❌ GOOSE Receiver failed to start\n");
        printf("Check network interface and permissions\n");
        printf("Try: sudo setcap cap_net_raw+ep ./circuit-breaker\n");
        exit(-1);
    }
    
    printf("✅ GOOSE Receiver started successfully\n");
    
    printf("🔍 GOOSE Receiver Debug Info:\n");
    printf("   Interface: eth0\n");
    printf("   Subscriber GoCbRef: simpleIOGenericIO/LLN0$GO$gcbEvents\n");
    printf("   AppId: 4096\n");
    printf("   MAC: 01:0c:cd:01:00:01\n");
    printf("   Waiting for GOOSE messages...\n");
    
    printf("✅ GOOSE Subscriber active on eth0\n");
    printf("✅ Listening for Protection Relay messages\n");
    printf("DEBUG: Waiting for GOOSE messages from protection relay...\n");
    printf("DEBUG: Expected publisher GoCbRef: simpleIOGenericIO/LLN0$GO$gcbEvents\n");
    
    // Initialize GOOSE Publisher for status feedback (match protection relay pattern)
    CommParameters statusCommParameters;
    statusCommParameters.appId = 1001;  // Match ln_breaker.icd APPID
    statusCommParameters.dstAddress[0] = 0x01;
    statusCommParameters.dstAddress[1] = 0x0c;
    statusCommParameters.dstAddress[2] = 0xcd;
    statusCommParameters.dstAddress[3] = 0x01;
    statusCommParameters.dstAddress[4] = 0x00;
    statusCommParameters.dstAddress[5] = 0x02;
    statusCommParameters.vlanId = 0;
    statusCommParameters.vlanPriority = 4;
    
    statusPublisher = GoosePublisher_create(&statusCommParameters, "eth0");
    if (statusPublisher) {
        printf("✅ GOOSE Status Publisher created on eth0\n");
        GoosePublisher_setGoCbRef(statusPublisher, "LD0/LLN0$GO$gcbStatus");
        GoosePublisher_setDataSetRef(statusPublisher, "LD0$BrkStatus");
        GoosePublisher_setConfRev(statusPublisher, 1);
        GoosePublisher_setTimeAllowedToLive(statusPublisher, 5000);
        printf("✅ GOOSE Status Publisher initialized on eth0\n");
    } else {
        printf("❌ GOOSE Status Publisher failed on eth0\n");
    }
    
    // Initialize simple MMS server for breaker control
    IedServerConfig config = IedServerConfig_create();
    iedServer = IedServer_createWithConfig(&iedModel, NULL, config);
    IedServerConfig_destroy(config);
    
    // Install control handler for CSWI1.Op (breaker open/close)
    IedServer_setControlHandler(iedServer, IEDMODEL_GenericIO_CSWI1_Op, 
                               (ControlHandler) controlHandler, NULL);
    
    // Start MMS server on different port to avoid conflict
    IedServer_start(iedServer, 103);
    if (IedServer_isRunning(iedServer)) {
        printf("✅ MMS Control Server started on port 103\n");
    }
    
    printf("✅ Circuit breaker ready\n");
    // Start HTTP status server thread
    pthread_t http_thread;
    pthread_create(&http_thread, NULL, http_status_thread, NULL);

    printf("Breaker Status: %s\n\n", breaker_open ? "OPEN" : "CLOSED");
    

    
    signal(SIGINT, sigint_handler);
    
    // Add heartbeat timer
    static int heartbeat_counter = 0;
    // Supervision publish timer
    static int supervision_counter = 0;
    
    while (running) {
        // Heartbeat every 3 seconds
        heartbeat_counter++;
        if (heartbeat_counter >= 10) {
            publishBreakerStatus(false); // Heartbeat
            heartbeat_counter = 0;
        }
        
        // Update simple GOOSE supervision every ~500ms (internal only)
        supervision_counter++;
        if (supervision_counter >= 5) {
            supervision_counter = 0;
            bool rx_ok = false;
            uint64_t now = Hal_getTimeInMs();
            if (last_goose_ms != 0 && (now - last_goose_ms) < 5000) rx_ok = true; // within 5s
            // Optionally expose rx_ok via an LN attribute if needed (e.g., LPHD1.Proxy)
            // Currently, we keep it internal and serve via HTTP diagnostics only.
        }
        
        Thread_sleep(100); // 100ms sleep
    }
    
    printf("\n🔌 Stopping GOOSE Receiver...\n");
    GooseReceiver_stop(receiver);
    GooseReceiver_destroy(receiver);
    
    if (iedServer) {
        IedServer_stop(iedServer);
        IedServer_destroy(iedServer);
    }
    
    pthread_mutex_destroy(&breaker_mutex);
    
    return 0;
}
