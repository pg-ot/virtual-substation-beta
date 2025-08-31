#include <stdio.h>
#include <string.h>
#include <ifaddrs.h>
#include <netinet/in.h>
#include <arpa/inet.h>

char* get_process_bus_interface() {
    struct ifaddrs *ifaddr, *ifa;
    static char interface_name[16] = "eth0";
    
    if (getifaddrs(&ifaddr) == -1) {
        return interface_name;
    }
    
    for (ifa = ifaddr; ifa != NULL; ifa = ifa->ifa_next) {
        if (ifa->ifa_addr == NULL) continue;
        
        if (ifa->ifa_addr->sa_family == AF_INET) {
            struct sockaddr_in* addr = (struct sockaddr_in*)ifa->ifa_addr;
            char ip_str[INET_ADDRSTRLEN];
            inet_ntop(AF_INET, &addr->sin_addr, ip_str, INET_ADDRSTRLEN);
            
            // Check if this is the process bus network (192.168.10.x)
            if (strncmp(ip_str, "192.168.10.", 11) == 0) {
                strncpy(interface_name, ifa->ifa_name, sizeof(interface_name)-1);
                interface_name[sizeof(interface_name)-1] = '\0';
                break;
            }
        }
    }
    
    freeifaddrs(ifaddr);
    return interface_name;
}
