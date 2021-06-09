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


time_byte = lambda data: int.to_bytes(data, 3, 'big')
value_byte = lambda data: int.to_bytes(data, 2, 'big')

class DataCollector():
    def __init__(self, buffer, counter=-1):
        self.adc = ADC(Pin(36))
        self.adc.atten(ADC.ATTN_11DB)

        start = time.ticks_ms()
        self.time_delta = lambda: time.ticks_diff(time.ticks_ms(), start)

        self.counter = counter
        self.buffer = buffer
        self.finished = False

    def __call__(self, timer):
        value = self.adc.read()
        try:
            self.buffer.append(time_byte(self.time_delta()) + value_byte(value))
        except IndexError:
            print('filled buffer @', self.time_delta())
        finally:
            if self.counter == 0:
                timer.deinit()
                print("finished")
                self.finished = True
            self.counter -= 1

def stream_data(token, collector, buffer):
    display.write("Connecting to\napi stream")
    with api.ApiStream("velasko.ddns.net", 8100) as stream:
        display.write("sending token")
        stream.write(token.encode('utf-8'))

        display.write("stream start")
        while not collector.finished:
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
    collector = DataCollector(buffer)#, counter=10000)
    timer = machine.Timer(0)
    timer.init(period=1,
               mode=machine.Timer.PERIODIC,
               callback=collector
               )
    stream_data(token, collector, buffer) 

if __name__ == '__main__':
    main()