import display
import ucollections
import settings
import time
import _thread

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

def data_collector(buffer):
    try:
        adc = ADC(Pin(36))
        adc.atten(ADC.ATTN_11DB)

        time.sleep(1)
        start = time.ticks_ms()
        time_delta = lambda: time.ticks_diff(time.ticks_ms(), start)
        time_byte = lambda data: int.to_bytes(data, 3, 'big')
        value_byte = lambda data: int.to_bytes(data, 2, 'big')
        
        await_time = .0005
        cntr = 0
        while True:
            value = adc.read()
            try:
                buffer.append(time_byte(time_delta()) + value_byte(value))
            except IndexError:
                await_time *= 2
                cntr = 0
                print("buffer filled")
                print("updating time_delta to:", await_time)
            finally:
                time.sleep(await_time)
                cntr += 1
                if cntr == 10:
                    await_time /= 2
    finally:
        _thread.exit()

def stream_data(token, buffer):
    display.write("Connecting to\napi stream")
    with api.ApiStream("velasko.ddns.net", 8100) as stream:
        display.write("sending token")
        stream.write(token.encode('utf-8'))

        display.write("stream start")
        while True:
            try:
                stream.write(b''.join([buffer.popleft() for _ in range(len(buffer))]))
            except IndexError:
                pass

        display.write("strm end")

def main():
    try:
        token = connect_api()
    except NameError:
        connect_network()
        token = connect_api()
    
    buffer = ucollections.deque((), 50, 1)
    _thread.start_new_thread(data_collector, (buffer,))
    stream_data(token, buffer)
            

if __name__ == '__main__':
    main()