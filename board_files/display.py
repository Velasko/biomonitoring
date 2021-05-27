import st7789

from machine import Pin, ADC, SPI
import NotoSans_32 as font1

spi = SPI(
    1,
    baudrate=30000000,
    sck=Pin(18),
    mosi=Pin(19)
)

display = st7789.ST7789(
    spi, 135, 240,
    reset=Pin(23, Pin.OUT),
    cs=Pin(5, Pin.OUT),
    dc=Pin(16, Pin.OUT),
    backlight=Pin(4, Pin.OUT),
    rotation=3)
display.init()

def write(data, size=10):
    display.fill(st7789.BLACK)
    for n, line in enumerate(data.split('\n')):
        display.write(font1, line, 10, n*42)