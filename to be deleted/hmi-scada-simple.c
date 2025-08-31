#include "iec61850_client.h"
#include "hal_thread.h"
#include <stdlib.h>
#include <stdio.h>
#include <signal.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <pthread.h>

static int running = 1;

typedef struct {
    float voltage;
    float current;
    float frequency;
    float faultCurrent;
    int tripCommand;
    int breakerStatus;
    int faultDetected;
    int overcurrentPickup;
} HMIData;

static HMIData hmiData = {132.0, 450.0, 50.0, 0.0, 0, 0, 0, 0};
static IedConnection con = NULL;

void sigint_handler(int signalId) {
    running = 0;
}

void* http_server_thread(void* arg) {
    int server_fd, new_socket;
    struct sockaddr_in address;
    int opt = 1;
    int addrlen = sizeof(address);
    
    if ((server_fd = socket(AF_INET, SOCK_STREAM, 0)) == 0) {
        return NULL;
    }
    
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
    
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(8080);
    
    bind(server_fd, (struct sockaddr *)&address, sizeof(address));
    listen(server_fd, 3);
    
    printf("HTTP API server listening on port 8080\n");
    
    while (running) {
        if ((new_socket = accept(server_fd, (struct sockaddr *)&address, (socklen_t*)&addrlen)) < 0) {
            continue;
        }
        
        char buffer[1024];
        int bytes = recv(new_socket, buffer, sizeof(buffer)-1, 0);
        
        if (bytes > 0) {
            buffer[bytes] = '\0';
            
            // Handle MMS control commands via HTTP
            if (strstr(buffer, "POST /mms/trip")) {
                if (con && sendMmsTrip(con) == 0) {
                    printf("MMS TRIP command sent\n");
                }
            } else if (strstr(buffer, "POST /mms/reset")) {
                if (con && sendMmsReset(con) == 0) {
                    printf("MMS RESET command sent\n");
                }
            }
        }
        
        char response[1024];
        snprintf(response, sizeof(response),
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: application/json\r\n"
            "Access-Control-Allow-Origin: *\r\n"
            "\r\n"
            "{\"voltage\":%.1f,\"current\":%.0f,\"frequency\":%.3f,\"faultCurrent\":%.0f,"
            "\"tripCommand\":%s,\"breakerStatus\":%s,\"faultDetected\":%s,\"overcurrentPickup\":%s}",
            hmiData.voltage, hmiData.current, hmiData.frequency, hmiData.faultCurrent,
            hmiData.tripCommand ? "true" : "false",
            hmiData.breakerStatus ? "true" : "false",
            hmiData.faultDetected ? "true" : "false",
            hmiData.overcurrentPickup ? "true" : "false");
        
        send(new_socket, response, strlen(response), 0);
        close(new_socket);
    }
    
    close(server_fd);
    return NULL;
}

int fetchSimulationData() {
    int sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) return -1;
    
    struct timeval timeout = {1, 0};
    setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout));
    setsockopt(sock, SOL_SOCKET, SO_SNDTIMEO, &timeout, sizeof(timeout));
    
    struct sockaddr_in server_addr;
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(3000);
    server_addr.sin_addr.s_addr = inet_addr("172.17.0.1");
    
    if (connect(sock, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
        close(sock);
        return -1;
    }
    
    const char* request = "GET /api/simulation-data HTTP/1.1\r\nHost: localhost:3000\r\nConnection: close\r\n\r\n";
    if (send(sock, request, strlen(request), 0) < 0) {
        close(sock);
        return -1;
    }
    
    char buffer[1024];
    int bytes = recv(sock, buffer, sizeof(buffer)-1, 0);
    close(sock);
    
    if (bytes > 0) {
        buffer[bytes] = '\0';
        char* json_start = strstr(buffer, "{");
        if (json_start) {
            int faultDetected, tripCommand, breakerStatus;
            sscanf(json_start, "{\"voltage\":%f,\"current\":%f,\"frequency\":%f,\"faultDetected\":%d,\"faultCurrent\":%f,\"tripCommand\":%d,\"breakerStatus\":%d",
                   &hmiData.voltage, &hmiData.current, &hmiData.frequency, &faultDetected, &hmiData.faultCurrent, &tripCommand, &breakerStatus);
            
            hmiData.faultDetected = faultDetected;
            hmiData.tripCommand = tripCommand;
            hmiData.breakerStatus = breakerStatus;
            hmiData.overcurrentPickup = (hmiData.current > 1000) ? 1 : 0;
            
            return 0;
        }
    }
    return -1;
}

// MMS Control Functions
int sendMmsTrip(IedConnection con) {
    IedClientError error;
    MmsValue* tripValue = MmsValue_newBoolean(true);
    IedConnection_writeObject(con, &error, "simpleIOGenericIO/GGIO1.SPCSO1.Oper.ctlVal", IEC61850_FC_CO, tripValue);
    MmsValue_delete(tripValue);
    return (error == IED_ERROR_OK) ? 0 : -1;
}

int sendMmsReset(IedConnection con) {
    IedClientError error;
    MmsValue* resetValue = MmsValue_newBoolean(false);
    IedConnection_writeObject(con, &error, "simpleIOGenericIO/GGIO1.SPCSO1.Oper.ctlVal", IEC61850_FC_CO, resetValue);
    MmsValue_delete(resetValue);
    return (error == IED_ERROR_OK) ? 0 : -1;
}

// Report Handler for Events (simplified)
void reportHandler(void* parameter, ClientReport report) {
    printf("\n=== MMS REPORT RECEIVED ===\n");
    printf("Report received from protection relay\n");
    printf("============================\n");
}

int main(int argc, char** argv) {
    char* hostname = "protection_relay_ied";
    int tcpPort = 102;
    
    printf("=== IEC 61850 HMI/SCADA SYSTEM ===\n");
    printf("MMS Client connecting to: %s:%d\n", hostname, tcpPort);
    printf("Protocol: IEC 61850 MMS with Reports\n");
    printf("Network: Station Bus (192.168.20.0/24)\n\n");
    
    signal(SIGINT, sigint_handler);
    
    // Start HTTP API server
    pthread_t http_thread;
    pthread_create(&http_thread, NULL, http_server_thread, NULL);
    
    con = IedConnection_create();
    IedClientError error;
    
    // Connect to Protection Relay MMS Server
    printf("🔄 Connecting to MMS Server...\n");
    IedConnection_connect(con, &error, hostname, tcpPort);
    
    if (error == IED_ERROR_OK) {
        printf("✅ MMS Connection established to %s:%d\n", hostname, tcpPort);
        printf("✅ HTTP API server started on port 8080\n");
        
        // Install report handler for events (simplified)
        printf("✅ MMS Client ready for reporting\n");
        
        printf("🔄 Reading Protection Relay data via MMS...\n\n");
        
        int cycle = 0;
        
        while (running) {
            cycle++;
            
            // Read analog measurements via MMS
            MmsValue* voltage = IedConnection_readObject(con, &error, "simpleIOGenericIO/GGIO1.AnIn1.mag.f", IEC61850_FC_MX);
            if (voltage && error == IED_ERROR_OK) {
                hmiData.voltage = MmsValue_toFloat(voltage);
                MmsValue_delete(voltage);
            }
            
            MmsValue* current = IedConnection_readObject(con, &error, "simpleIOGenericIO/GGIO1.AnIn2.mag.f", IEC61850_FC_MX);
            if (current && error == IED_ERROR_OK) {
                hmiData.current = MmsValue_toFloat(current);
                MmsValue_delete(current);
            }
            
            MmsValue* frequency = IedConnection_readObject(con, &error, "simpleIOGenericIO/GGIO1.AnIn3.mag.f", IEC61850_FC_MX);
            if (frequency && error == IED_ERROR_OK) {
                hmiData.frequency = MmsValue_toFloat(frequency);
                MmsValue_delete(frequency);
            }
            
            MmsValue* faultCurrent = IedConnection_readObject(con, &error, "simpleIOGenericIO/GGIO1.AnIn4.mag.f", IEC61850_FC_MX);
            if (faultCurrent && error == IED_ERROR_OK) {
                hmiData.faultCurrent = MmsValue_toFloat(faultCurrent);
                MmsValue_delete(faultCurrent);
            }
            
            // Read digital status via MMS
            MmsValue* tripCmd = IedConnection_readObject(con, &error, "simpleIOGenericIO/GGIO1.SPCSO1.stVal", IEC61850_FC_ST);
            if (tripCmd && error == IED_ERROR_OK) {
                hmiData.tripCommand = MmsValue_getBoolean(tripCmd);
                MmsValue_delete(tripCmd);
            }
            
            MmsValue* breakerSt = IedConnection_readObject(con, &error, "simpleIOGenericIO/GGIO1.SPCSO2.stVal", IEC61850_FC_ST);
            if (breakerSt && error == IED_ERROR_OK) {
                hmiData.breakerStatus = MmsValue_getBoolean(breakerSt);
                MmsValue_delete(breakerSt);
            }
            
            MmsValue* faultDet = IedConnection_readObject(con, &error, "simpleIOGenericIO/GGIO1.SPCSO3.stVal", IEC61850_FC_ST);
            if (faultDet && error == IED_ERROR_OK) {
                hmiData.faultDetected = MmsValue_getBoolean(faultDet);
                MmsValue_delete(faultDet);
            }
            
            MmsValue* ocPickup = IedConnection_readObject(con, &error, "simpleIOGenericIO/GGIO1.SPCSO4.stVal", IEC61850_FC_ST);
            if (ocPickup && error == IED_ERROR_OK) {
                hmiData.overcurrentPickup = MmsValue_getBoolean(ocPickup);
                MmsValue_delete(ocPickup);
            }
            
            printf("[%d] MMS Read: V=%.1fkV I=%.0fA F=%.3fHz FC=%.0fA Trip=%s Breaker=%s\n", 
                   cycle, hmiData.voltage, hmiData.current, hmiData.frequency, hmiData.faultCurrent,
                   hmiData.tripCommand ? "YES" : "NO", hmiData.breakerStatus ? "OPEN" : "CLOSED");
            
            sleep(2);
        }
        
        printf("\n🔌 Disconnecting from Protection Relay...\n");
        IedConnection_close(con);
        
    } else {
        printf("❌ Failed to connect to %s:%d\n", hostname, tcpPort);
        printf("Error: %s\n", IedClientError_toString(error));
        printf("Make sure Protection Relay MMS server is running\n");
    }
    
    IedConnection_destroy(con);
    printf("HMI/SCADA System shutdown complete.\n");
    return 0;
}