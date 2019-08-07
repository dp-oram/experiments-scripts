#!/usr/bin/env python3

import random
import time
from enum import Enum, auto


class Engine(Enum):
	kalepso = auto()
	mariaDB = auto()
	oracle = auto()
	microsoft = auto()

	def __str__(self):
		return self.name

	@staticmethod
	def value(key):
		try:
			return Engine[key]
		except KeyError:
			raise ValueError()


def parse():
	import argparse

	inputSizeDefault = 100
	inputSizeMin = 1
	inputSizeMax = 1000005

	def argcheckInputSize(value):
		number = int(value)
		if number < inputSizeMin or number > inputSizeMax:
			raise argparse.ArgumentTypeError(f"Input / queries size must be {inputSizeMin} to {inputSizeMax}. Given {number}")
		return number

	def argcheckInputMax(value):
		number = int(value)
		if number <= 0:
			raise argparse.ArgumentTypeError(f"Input max must be above 0. Given {number}")
		return number

	def argcheckRange(value):
		percent = float(value)
		if percent <= 0.001 or percent >= 0.9:
			raise argparse.ArgumentTypeError(f"Range must be above a percentage 1% to 90%. Given {percent}")
		return percent

	parser = argparse.ArgumentParser(description="Run simple uniform range queries on Kalepso.")

	parser.add_argument("--size", dest="size", metavar="input-size", type=argcheckInputSize, required=False, default=inputSizeDefault, help=f"The size of data [{inputSizeMin} - {inputSizeMax}]")
	parser.add_argument("--queries", dest="queries", metavar="queries-size", type=argcheckInputSize, required=False, default=int(inputSizeDefault / 10), help=f"The number of queries [{inputSizeMin} - {inputSizeMax}]")
	parser.add_argument("--max", dest="max", metavar="input-max", type=argcheckInputMax, required=False, default=inputSizeDefault, help=f"The max value of data points (min is 0) [>0]")
	parser.add_argument("--range", dest="range", metavar="range-percent", type=argcheckRange, required=False, default=0.01, help=f"The range size as percent of max-min data [0.001 - 0.9]")

	parser.add_argument("--seed", dest="seed", metavar="seed", type=int, default=123456, required=False, help="Seed to use for PRG")

	parser.add_argument('--engine', dest="engine", metavar="engine", type=Engine.value, choices=list(Engine), required=True, help="Engine to run benchmark against")
	parser.add_argument("--port", dest="port", metavar="port", type=int, required=False, help="Engine's port (not required for MS)")

	args = parser.parse_args()

	if args.engine != Engine.microsoft and not args.port:
		parser.error('--port is required when --engine is not microsoft.')

	random.seed(args.seed)

	return args.size, args.max, args.range, args.queries, args.engine, args.port


def generateLoads(dataSize, maxValue, queryRange, queriesSize):
	data = []
	queries = []
	for i in range(1, dataSize):
		data += [random.randint(0, maxValue)]

	querySize = int(maxValue * queryRange)
	for i in range(1, queriesSize):
		left = random.randint(0, maxValue - querySize)
		queries += [(left, left + querySize)]

	return data, queries


def runLoadsMySQL(data, queries, port):
	import mysql.connector as mysql

	db = mysql.connect(
		host="localhost",
		user="root",
		port=port,
		passwd="MYPASSWD"
	)

	cursor = db.cursor()
	cursor.execute("CREATE DATABASE IF NOT EXISTS experimental")
	cursor.execute("USE experimental")
	cursor.execute("DROP TABLE IF EXISTS ranges")
	cursor.execute("CREATE TABLE IF NOT EXISTS ranges (point INT, INDEX pointIndex (point))")
	cursor.execute("SET SESSION query_cache_type=0")

	db.commit()

	init = time.time()

	insert = "INSERT INTO ranges (point) VALUES (%s)"
	for point in data:
		cursor.execute(insert, (point,))
		db.commit()

	inserted = time.time()

	query = "SELECT point FROM ranges WHERE point BETWEEN %s AND %s"
	for rangeQuery in queries:
		cursor.execute(query, rangeQuery)
		records = cursor.fetchall()

	queried = time.time()

	return inserted - init, queried - inserted


def runLoadsOracle(data, queries, port):
	import cx_Oracle

	connection = cx_Oracle.connect("dmytro", "password", f"0.0.0.0:{port}/ORCLCDB.localdomain")

	cursor = connection.cursor()

	cursor.execute("BEGIN EXECUTE IMMEDIATE 'DROP TABLE ranges'; EXCEPTION WHEN OTHERS THEN NULL; END;")
	cursor.execute("CREATE TABLE ranges (point NUMBER ENCRYPT NO SALT)")
	cursor.execute("CREATE INDEX pointIndex on ranges (point)")

	connection.commit()

	init = time.time()

	cursor.execute("INSERT INTO employee (first_name, last_name, empID, salary) VALUES ('John', 'Doe', 1, 152)")

	insert = "INSERT INTO ranges (point) VALUES (:point)"
	for point in data:
		cursor.execute(insert, point=point)
		connection.commit()

	inserted = time.time()

	query = "SELECT point FROM ranges WHERE point BETWEEN :low AND :high"
	for rangeQuery in queries:
		cursor.execute(query, low=rangeQuery[0], high=rangeQuery[1])
		records = cursor.fetchall()
		# print(f"For range {rangeQuery}, the result is {len(records)} records")

	queried = time.time()

	return inserted - init, queried - inserted


def generateMSSQLLoad(data, queries):

	print(len(data))
	print(len(queries))
	for point in data:
		print(point)

	for query in queries:
		print(f"{query[0]} {query[1]}")


if __name__ == "__main__":

	dataSize, maxValue, queryRange, queriesSize, engine, port = parse()
	data, queries = generateLoads(dataSize, maxValue, queryRange, queriesSize)

	if engine == Engine.microsoft:
		generateMSSQLLoad(data, queries)
	else:
		if engine == Engine.kalepso or engine == Engine.mariaDB:
			insertionTime, queryTime = runLoadsMySQL(data, queries, port)
		else:
			insertionTime, queryTime = runLoadsOracle(data, queries, port)
		print(f"For {engine}: inserted in {int(insertionTime * 1000)} ms, queries in {int(queryTime * 1000)} ms")
