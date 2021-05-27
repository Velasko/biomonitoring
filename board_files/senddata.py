import time
# base64 usa binascii, mas base64 não está disponivel no micropython
import binascii
from machine import Pin, ADC
try:
	# Tive que alterar o nome, pois urequests é gravada direto
	# firmware e logo tem preferencia
	import drequests as requests
except:
	import requests

import random
if 'Random' in dir(random):
	rng = random.Random()
	def random_byte():
		return rng.randint(0, 255)

else:
	def random_byte():
		return random.getrandbits(8)


GOOGLE_URL = 'https://script.google.com/macros/s/AKfycbxlVh9EgCTd2bx3vh_f-cIJMZeS70Et22lT-kIIA1KhZkXqjXs/exec'
AWS_URL = "https://er8lepjcv6.execute-api.us-east-1.amazonaws.com/default/funcao-exemplo"
AWS_API_KEY = "NbyJsU8LVY5mZufzacojW8usYw3sQl9o8ttBBqge"

# Envia os dados
def send_data(url, data, api_key=None):
	headers = {}
	if api_key:
		headers["X-API-Key"] = api_key
	return requests.post(url, data=data, headers=headers)


# Leitura de dados da porta Analogica
def generate_ADC_sample(frequency, duration):
	adc = ADC(Pin(36))
	adc.atten(ADC.ATTN_11DB)
	vec = bytearray(duration * frequency * 2)
	for i in range(len(vec)):
		if i%2 == 0:
			value = adc.read()
			vec[i] = (value>>6)&63
			vec[i+1] = value&63
    		time.sleep_ms(4)
    		#time.sleep_ms(int(1000/frequency))
	return vec


# Apenas junta os dados do registro de forma prática
class Data:

	def __init__(self, frequency, duration, sample, chunk_lenght=96):
		self.frequency = frequency
		self.duration = duration
		self.sample = sample
		self.chunk_lenght = chunk_lenght

	# O iterator é usado para converter os dados da requisição em bytes sem
	# gerar grandes alocações
	def __iter__(self):
        
        #Pegando endereço mac apartir da biblioteca do hardware
        import network
        wlan = network.WLAN(network.STA_IF)
        mac_bytes = wlan.config('mac')
        mac = ':'.join([str(hex(int(b))[2:]) for b in m])

        yield (
            mac.encode() + #ttgo02
			b',' +
			str(self.frequency).encode() +
			b',' +
			str(self.duration).encode() +
			b','
			)

		# Evita recriar uma copia inteira da amostra ao converter em base64
		# Com o objetivo de economizar memória
		index = 0
		sample_len = len(self.sample)
		while index < sample_len: 
			to = min(index + self.chunk_lenght, sample_len)
			yield binascii.b2a_base64(self.sample[index : to])[0:-1]
			index += self.chunk_lenght


def main():
	frequency = 125
	duration = 300
	# sample = generate_random_sample(frequency, duration)
	print("Start data acquisition")
	a = time.ticks_ms()
	sample = generate_ADC_sample(frequency, duration)
	b = (time.ticks_ms() - a)/1000.0
	print("Finish data acquisition, time:",b)
	a = time.ticks_ms()
	data = Data(frequency, duration, sample)
	res = send_data(AWS_URL, data, api_key = AWS_API_KEY)
	print(res.content)
	b = (time.ticks_ms() - a)/1000.0
	print("Network Overhead, time:",b)


if __name__ == '__main__':
	main()

