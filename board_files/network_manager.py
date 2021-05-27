import network
import utime

def connect(known_networks, scan_range=10, connection_attemps=15):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    wlan.disconnect()
    networks = wlan.scan()
       
    best_net, best_rssi = None, float('-inf')
    for netwk in networks[:scan_range]:
        if netwk[0] in known_networks and netwk[3] > best_rssi:
            best_net, best_rssi = netwk[0], netwk[3]

    try:
        wlan.connect(best_net, known_networks[best_net])
    except KeyError:
        return None
        
    for _ in range(connection_attemps):
        utime.sleep(1)
        if wlan.isconnected(): return best_net.decode()

    return None

def ifconfig(*args, **kwargs):
    wlan = network.WLAN(network.STA_IF)
    return wlan.ifconfig(*args, **kwargs)

if __name__ == '__main__':
    import settings
    print(connect(settings.known_networks, True))