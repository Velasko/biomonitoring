import display
import settings
import time

from machine import ADC, Pin

import network_manager as network
import drequests as requests

import api_connection as api

def connect_network():
    display.write("Connecting to\nnetwork")
    ssid = network.connect(settings.known_networks)
    display.write("Connected to\n\"{}\"".format(ssid))

def connect_api():
    display.write("Connecting to\napi")
    try:
        token = api.connect("http://velasko.ddns.net:8000")
    except Exception as e:
        display.write("{}\n\"{}\"".format(type(e).__name__, str(e)))
    else:
        display.write("Connected to\napi")

    return token

def stream_data(token):
    display.write("Connecting to\napi stream")
    with api.ApiStream("velasko.ddns.net", 8100) as stream:
        display.write("sending token")
        stream.write(token.encode('utf-8'))

        adc = ADC(Pin(36))
        adc.atten(ADC.ATTN_11DB)

        time_delta = lambda: time.ticks_diff(time.ticks_ms(), start)
        int_byte = lambda data: int.to_bytes(data, 2, 'big')
        display.write("stream start")

        start = time.ticks_ms()
        for _ in range(10000):
            value = adc.read()
            stream.write(int_byte(time_delta()) + int_byte(value))

        display.write("strm end")

def main():
#    connect_network()

    token = connect_api()
    
    stream_data(token)
    

if __name__ == '__main__':
    main()