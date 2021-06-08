import display
import machine
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

class DataCollector():
    def __init__(self, buffer):
        self.adc = ADC(Pin(36))
        self.adc.atten(ADC.ATTN_11DB)

        time.sleep(1)
        start = time.ticks_ms()
        self.time_delta = lambda: time.ticks_diff(time.ticks_ms(), start)
        self.time_byte = lambda data: int.to_bytes(data, 3, 'big')
        self.value_byte = lambda data: int.to_bytes(data, 2, 'big')

        self.counter = 0
        self.buffer = buffer

    def __call__(self, n):
        if self.counter == 0:
            print("First call")
        elif self.counter == 50000:
            return
        value = self.adc.read()
        try:
            self.buffer.append(self.time_byte(self.time_delta()) + self.value_byte(value))
        except IndexError:
            pass
        finally:
            self.counter += 1
            if self.counter == 50000:
                print("finished")


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
    timer = machine.Timer(0)
    timer.init(period=1,
               mode=machine.Timer.PERIODIC,
               callback=DataCollector(buffer)
               )
    stream_data(token, buffer)
            

if __name__ == '__main__':
    main()