import re

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy import Date, DateTime

class SessionManager():
	def __init__(self, engine_uri, *args, **kwargs):
		engine = create_engine(f'sqlite:///{engine_uri}')
		self._ssn_mkr = scoped_session(sessionmaker(bind=engine, *args, **kwargs))

	def __call__(self):
		return self._ssn_mkr()

	def wrapper(self, func):
		def wrapped(*args, **kwargs):
			with self as session:
				if len(args) == 0 or not func.__name__ in dir(args[0]):
					return func(session, *args, **kwargs)
				return func(args[0], session, *args[1:], **kwargs)
		return wrapped

	def __enter__(self):
		session = self._ssn_mkr()
		try:
			session.recursivity += 1
		except AttributeError:
			session.recursivity = 1

		return session

	def __exit__(self, *args):
		session = self._ssn_mkr()
		session.recursivity -= 1
		if session.recursivity == 0:
			self._ssn_mkr.remove()

Base = declarative_base()

class Tables(list):
	def __init__(self):
		import database as scheme
		for line in open(__file__):
			m = re.match("class (.+)\(Base\):*", line)
			if not m is None:
				self.insert(0, getattr(scheme, m.groups()[0]))

class User(Base):
	__tablename__ = 'Users'

	id = Column(Integer, primary_key=True)
	name = Column(String(255), nullable=False)
	age = Column(Integer)
	phone = Column(String(16), unique=True, nullable=False)

class File(Base):
	__tablename__ = 'Files'

	user =  Column(Integer, ForeignKey('Users.id', ondelete='RESTRICT', onupdate='CASCADE'), primary_key=True)
	filename = Column(String(16), primary_key=True)
	time = Column(DateTime)

class Key(Base):
	__tablename__ = 'Keys'

	user =  Column(Integer, ForeignKey('Users.id', ondelete='RESTRICT', onupdate='CASCADE'), primary_key=True)
	key = Column(String(255), primary_key=True)

if __name__ == '__main__':
	import argparse

	parser = argparse.ArgumentParser()
	parser.add_argument('--filename', type=str, default='database.db')

	group = parser.add_mutually_exclusive_group()
	group.add_argument('--create_scheme', action='store_true', help="Generates the scheme inside the database.")
	group.add_argument('--delete_scheme', action='store_true', help="Deletes the scheme inside the database.")

	args = parser.parse_args()

	database_uri = f'sqlite:///{args.filename}'

	engine = create_engine(database_uri)
	if args.create_scheme:
		Base.metadata.create_all(engine)
		print("scheme created")

	elif args.delete_scheme:

		for table in Tables():
			try:
				table.__table__.drop(engine)
			except Exception as e:
				print("An exception has occured with", table.__tablename__)
			else:
				print(table.__tablename__, "dropped")

	else:
		parser.print_help()