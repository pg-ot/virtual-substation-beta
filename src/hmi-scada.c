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

void sigint_handler(int signalId) {
    running = 0;
}

typedef struct {
    float voltage;
    float current;
    float frequency;
    float faultCurrent;
    bool tripCommand;
    bool breakerStatus;
    bool faultDetected;
    bool overcurrentPickup;
    char lastAlarm[128];
} HMIData;

static HMIData hmiData = {0};

// Global connection for HTTP commands
static IedConnection global_con = NULL;

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
    
    printf("✅ HMI HTTP API server listening on port 8080\n");
    
    while (running) {
        if ((new_socket = accept(server_fd, (struct sockaddr *)&address, (socklen_t*)&addrlen)) < 0) {
            continue;
        }
        
        char buffer[1024] = {0};
        recv(new_socket, buffer, 1023, 0);
        
        char response[1024];
        
        if (strstr(buffer, "POST /trip")) {
            printf("\n>>> HMI HTTP: Manual Trip Command <<<\n");
            if (global_con) {
                IedClientError error;
                ControlObjectClient control = ControlObjectClient_create("simpleIOGenericIO/GGIO1.SPCSO1", global_con);
                if (control) {
                    MmsValue* ctlVal = MmsValue_newBoolean(true);
                    ControlObjectClient_operate(control, ctlVal, 0);
                    MmsValue_delete(ctlVal);
                    ControlObjectClient_destroy(control);
                    strcpy(hmiData.lastAlarm, "Manual Trip Issued via HMI");
                }
            }
            snprintf(response, sizeof(response),
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: application/json\r\n"
                "Access-Control-Allow-Origin: *\r\n"
                "\r\n"
                "{\"status\":\"trip_sent\"}");
        } else {
            // GET request - return status data
            snprintf(response, sizeof(response),
                "HTTP/1.1 200 OK\r\n"
                "Content-Type: application/json\r\n"
                "Access-Control-Allow-Origin: *\r\n"
                "\r\n"
                "{\"voltage\":%.1f,\"current\":%.0f,\"frequency\":%.3f,\"faultCurrent\":%.0f,"
                "\"tripCommand\":%s,\"breakerStatus\":%s,\"faultDetected\":%s,\"overcurrentPickup\":%s,"
                "\"lastAlarm\":\"%s\"}",
                hmiData.voltage, hmiData.current, hmiData.frequency, hmiData.faultCurrent,
                hmiData.tripCommand ? "true" : "false",
                hmiData.breakerStatus ? "true" : "false",
                hmiData.faultDetected ? "true" : "false",
                hmiData.overcurrentPickup ? "true" : "false",
                hmiData.lastAlarm);
        }
        
        send(new_socket, response, strlen(response), 0);
        close(new_socket);
    }
    
    close(server_fd);
    return NULL;
}

void reportCallbackFunction(void* parameter, ClientReport report) {
    printf("\n=== MMS REPORT RECEIVED ===\n");
    printf("Report ID: %s\n", ClientReport_getRcbReference(report));
    
    MmsValue* dataSetValues = ClientReport_getDataSetValues(report);
    if (dataSetValues) {
        printf("Real-time data updated via MMS reporting\n");
    }
    printf("==========================\n");
}

void displayHMIScreen() {
    printf("\033[2J\033[H"); // Clear screen
    printf("╔══════════════════════════════════════════════════════════════╗\n");
    printf("║                    HMI/SCADA SYSTEM                         ║\n");
    printf("║              IEC 61850 MMS CLIENT ACTIVE                    ║\n");
    printf("╠══════════════════════════════════════════════════════════════╣\n");
    printf("║ Station: MAIN_SS_132kV | Bay: LINE_01 | MMS Port: 102       ║\n");
    printf("╠══════════════════════════════════════════════════════════════╣\n");
    printf("║ REAL-TIME MEASUREMENTS (via MMS)                            ║\n");
    printf("║   Voltage L1    : %6.1f kV                                ║\n", hmiData.voltage);
    printf("║   Current L1    : %6.0f A                                 ║\n", hmiData.current);
    printf("║   Frequency     : %6.3f Hz                                ║\n", hmiData.frequency);
    printf("║   Fault Current : %6.0f A                                 ║\n", hmiData.faultCurrent);
    printf("╠══════════════════════════════════════════════════════════════╣\n");
    printf("║ PROTECTION STATUS (via MMS Data Objects)                    ║\n");
    printf("║   Trip Command  : %-8s                                   ║\n", hmiData.tripCommand ? "ACTIVE" : "Normal");
    printf("║   Breaker       : %-8s                                   ║\n", hmiData.breakerStatus ? "OPEN" : "CLOSED");
    printf("║   Fault Status  : %-8s                                   ║\n", hmiData.faultDetected ? "FAULT" : "Normal");
    printf("║   O/C Pickup    : %-8s                                   ║\n", hmiData.overcurrentPickup ? "PICKUP" : "Normal");
    printf("╠══════════════════════════════════════════════════════════════╣\n");
    printf("║ SYSTEM ALARMS                                                ║\n");
    
    if (hmiData.tripCommand) {
        printf("║   🚨 PROTECTION TRIP ACTIVE                                 ║\n");
    }
    if (hmiData.faultDetected) {
        printf("║   ⚠️  SYSTEM FAULT DETECTED                                 ║\n");
    }
    if (hmiData.overcurrentPickup) {
        printf("║   ⚡ OVERCURRENT PROTECTION PICKUP                          ║\n");
    }
    if (hmiData.current > 2000) {
        printf("║   🔥 HIGH CURRENT ALARM: %.0f A                           ║\n", hmiData.current);
    }
    if (hmiData.frequency < 49.5) {
        printf("║   📉 LOW FREQUENCY ALARM: %.3f Hz                         ║\n", hmiData.frequency);
    }
    if (!hmiData.tripCommand && !hmiData.faultDetected && !hmiData.overcurrentPickup) {
        printf("║   ✅ ALL SYSTEMS NORMAL                                     ║\n");
    }
    
    printf("╠══════════════════════════════════════════════════════════════╣\n");
    printf("║ Last Alarm: %-48s ║\n", hmiData.lastAlarm[0] ? hmiData.lastAlarm : "None");
    printf("╠══════════════════════════════════════════════════════════════╣\n");
    printf("║ MMS Commands: 't'=Trip, 'c'=Close, 'r'=Read, 'q'=Quit       ║\n");
    printf("╚══════════════════════════════════════════════════════════════╝\n");
}

int main(int argc, char** argv) {
    char* hostname = "protection_relay_ied";
    int tcpPort = 102;
    
    printf("=== IEC 61850 HMI/SCADA SYSTEM ===\n");
    printf("MMS Client connecting to: %s:%d\n", hostname, tcpPort);
    printf("Protocol: IEC 61850 MMS\n");
    printf("Network: Station Bus (192.168.20.0/24)\n\n");
    
    // Start HTTP API server for Tkinter panel
    pthread_t http_thread;
    pthread_create(&http_thread, NULL, http_server_thread, NULL);
    
    IedConnection con = IedConnection_create();
    IedClientError error;
    
    // Connect to Protection Relay MMS Server
    IedConnection_connect(con, &error, hostname, tcpPort);
    
    // Set global connection for HTTP commands
    global_con = con;
    
    if (error == IED_ERROR_OK) {
        printf("✅ MMS Connection established to %s:%d\n", hostname, tcpPort);
        
        // Install report handler for real-time updates
        IedConnection_installReportHandler(con, "simpleIOGenericIO/LLN0.RP.EventsRCB01", 
                                         NULL, reportCallbackFunction, NULL);
        
        // Note: Reporting functionality simplified for compatibility
        printf("✅ MMS Connection ready for data polling\n");
        
        signal(SIGINT, sigint_handler);
        
        printf("\n🖥️  HMI/SCADA System Ready\n");
        printf("Reading Protection Relay data via MMS...\n\n");
        
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
            
            // Update alarm status
            if (hmiData.tripCommand) {
                strcpy(hmiData.lastAlarm, "Protection Trip Active");
            } else if (hmiData.faultDetected) {
                strcpy(hmiData.lastAlarm, "System Fault Detected");
            } else if (hmiData.overcurrentPickup) {
                strcpy(hmiData.lastAlarm, "Overcurrent Pickup");
            } else {
                strcpy(hmiData.lastAlarm, "All Systems Normal");
            }
            
            // Display HMI screen
            displayHMIScreen();
            
            // Check for user commands
            fd_set readfds;
            struct timeval timeout = {2, 0}; // 2 second timeout
            
            FD_ZERO(&readfds);
            FD_SET(STDIN_FILENO, &readfds);
            
            if (select(STDIN_FILENO + 1, &readfds, NULL, NULL, &timeout) > 0) {
                char cmd = getchar();
                switch(cmd) {
                    case 't': {
                        printf("\n>>> MMS CONTROL: Manual Trip Command <<<\n");
                        ControlObjectClient control = ControlObjectClient_create("simpleIOGenericIO/GGIO1.SPCSO1", con);
                        if (control) {
                            MmsValue* ctlVal = MmsValue_newBoolean(true);
                            ControlObjectClient_operate(control, ctlVal, 0);
                            MmsValue_delete(ctlVal);
                            ControlObjectClient_destroy(control);
                            strcpy(hmiData.lastAlarm, "Manual Trip Issued via MMS");
                        }
                        break;
                    }
                    case 'c': {
                        printf("\n>>> MMS CONTROL: Manual Close Command <<<\n");
                        // Connect to circuit breaker MMS server for close command
                        IedConnection breakerCon = IedConnection_create();
                        IedClientError breakerError;
                        IedConnection_connect(breakerCon, &breakerError, "circuit_breaker_ied", 103);
                        
                        if (breakerError == IED_ERROR_OK) {
                            ControlObjectClient control = ControlObjectClient_create("simpleIOGenericIO/GGIO1.SPCSO2", breakerCon);
                            if (control) {
                                MmsValue* ctlVal = MmsValue_newBoolean(false);
                                ControlObjectClient_operate(control, ctlVal, 0);
                                MmsValue_delete(ctlVal);
                                ControlObjectClient_destroy(control);
                                strcpy(hmiData.lastAlarm, "Manual Close Issued via MMS to Breaker");
                            }
                            IedConnection_close(breakerCon);
                        } else {
                            strcpy(hmiData.lastAlarm, "Failed to connect to breaker MMS");
                        }
                        IedConnection_destroy(breakerCon);
                        break;
                    }
                    case 'r':
                        printf("\n>>> MMS READ: Refreshing all data points <<<\n");
                        strcpy(hmiData.lastAlarm, "Data Refresh via MMS");
                        break;
                    case 'q':
                        running = 0;
                        break;
                }
            }
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
