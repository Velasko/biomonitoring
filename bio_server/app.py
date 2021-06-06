import datetime
import jwt
import os
import socket
import string
import time
import threading
import random

from matplotlib import pyplot as plt

from flask import Flask
from flask_restx import Api, Resource, fields
from flask_restx.model import Model
from sqlalchemy.sql.expression import and_

from database import *

app = Flask('Biomonitoring')
api = Api(app)

#-----------------REMOVE---------------
app.config['SECRET_KEY'] = 'aaaaaaaaaaaaaaaa'
app.config['session_ttl'] = 99999999
#--------------------------------------

DBsession = None

sensor_auth = Model('sensor.auth', {
	'user' : fields.Integer(description="User's id", required=True),
	'key' : fields.String(description="An user key", required=True)
})

token = Model("token", {
	'token' : fields.String(required=True)
})

for model in (sensor_auth, token):
	api.add_model(model.name, model)

size = 6
chars = string.ascii_letters + string.digits
filename_generator = lambda : ''.join(random.choice(chars) for _ in range(size))

@api.route('/sensor/auth')
class Auth(Resource):

	@api.doc("Api for sensors to autenticate")
	@api.expect(sensor_auth)
	@api.response(200, "Auth successful", model=token)
	@api.response(409, "Auth failed")
	def post(self):
		user_id = api.payload['user']
		key = api.payload['key']
		with DBsession as session:
			query = session.query(
				Key.key
			).filter(
				and_(
					Key.key == key,
					Key.user == user_id
				)
			)

			if query.count() == 0:
				return {'message' : 'Not Authorized'}, 409

			aux_func = lambda name_test: session.query(
							File.filename
						).filter(
							and_(
								File.user == user_id,
								File.filename == name_test
							)
						).count()

			filename = filename_generator()
			while aux_func(filename):
				filename = filename_generator()

			newfile = File(
				user=user_id,
				filename=filename,
				time=datetime.datetime.utcnow()
			)

			session.add(newfile)
			session.commit()

			token = jwt.encode({
					'user' : user_id,
					'filename' : filename,
					'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=app.config['session_ttl'])
				},
				app.config['SECRET_KEY']
			).decode('UTF-8')

			return {'token': token }, 200

def handle_client(conn):
	data = conn.recv(1024)

	token = data.decode()
	try:
		data = jwt.decode(token, app.config['SECRET_KEY'])

		user_id = data['user']
		filename = data['filename']

		with DBsession as session:
				query = session.query(
					File
				).filter(
					and_(
						File.user == user_id,
						File.filename == filename
					)
				) 

				if query.count() != 1:
					return

		path = f"sensor_uploads/{user_id}"
		os.makedirs(f"./{path}", exist_ok=True)

		print("file:", filename)
		start = datetime.datetime.utcnow()
		with open(f"./{path}/{filename}.temp", 'wb') as file:
			while data != b'':
				data = conn.recv(512)
				file.write(data)
		t_delta = datetime.datetime.utcnow() - start
		print("recieved in(s):", t_delta.total_seconds())

		with open(f"./{path}/{filename}.temp", 'rb') as temp:
			with open(f"./{path}/{filename}", 'w') as file:
				file.write(f"start: {start}\n")


				time_size = 3
				value_size = 2
				pkt_size = time_size + value_size

				data = temp.read(pkt_size)
				to_int = lambda v: int.from_bytes(v, byteorder='big')
				while len(data) == pkt_size:
					time, value = to_int(data[:time_size]), to_int(data[time_size:])
					file.write(f"{time}: {value}\n")
					data = temp.read(pkt_size)

		os.remove(f"./{path}/{filename}.temp")

	except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError) as e:
		#token expired or invalid
		pass
	finally:
		conn.close()

def file_host(host, port):
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
		s.bind((host, port))
		s.listen()

		while True:
			conn, addr = s.accept()

			t = threading.Thread(target=handle_client, args=(conn,))
			t.daemon = True
			t.start()

def analyze(filename):
	print(f"Analyzing {filename}")
	with open(f'./sensor_uploads/1/{filename}') as file:
		lines = file.readlines()


	#analyzing times:
	times = [ int(line.split(':')[0]) for line in lines[1:]]
	time_deltas = [ time - times[n] for n, time in enumerate(times[1:])]
	avg = sum(time_deltas)/len(time_deltas)
	var = sum([ (avg-delta)**2 for delta in time_deltas ]) / len(time_deltas)
	max_t = max(time_deltas)


	print(f'Total data: {len(times) - 1} inputs, throughout {max(times)/1000:.2f} s')
	#printing results
	print(f"""
Time info:
	avg: {avg:.2f}ms;
	var: {var:.2f};
	max: {max_t}ms, with {time_deltas.count(max_t)} time(s) occurance @ {time_deltas.index(max_t) + 1} sample
	min: {min(time_deltas)}
""")

	plt.hist(time_deltas)
	# plt.boxplot(time_deltas)
	plt.show()

if __name__ == '__main__':
	import argparse

	parser = argparse.ArgumentParser()
	parser.add_argument('--database', type=str, default='database.db')

	parser.add_argument('-d', '--debug', action='store_true', help="runs with debug")
	parser.add_argument('--host', default='127.0.0.1', help="defines the host")
	parser.add_argument('-p', '--port', type=int, default=5000, help="which port to run the application on")
	parser.add_argument('--no-reload', action='store_false', help="disable flask's reloader")
	parser.add_argument('--filename', help='File on which to be performed the opration')

	group = parser.add_argument_group("Execution mode").add_mutually_exclusive_group()
	group.add_argument('-r', '--run', action='store_true', help="runs the full REST application")
	group.add_argument('-a', '--analyze', action='store_true', help="Analyze the given or latest data")

	args = parser.parse_args()

	DBsession = SessionManager(args.database)

	if args.run:
		# file_host(args.host, args.port+100)
		t = threading.Thread(target=file_host, args=(args.host, args.port+100))
		t.daemon = True
		t.start()
		app.run(host=args.host, debug=args.debug, port=args.port, use_reloader=args.no_reload)
	elif args.analyze:
		if args.filename is None:
			with DBsession as session:
				filename = session.query(File.filename).order_by(File.time.desc()).first()[0]
		analyze(filename)
	else:
		parser.print_help()