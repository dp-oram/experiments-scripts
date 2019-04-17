#!/usr/bin/env python3

from dotmap import DotMap
import random
import time

def parse():
	import argparse

	inputSizeDefault = 100
	inputSizeMin = 10
	inputSizeMax = 100000
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
		if percent < 0.01 or percent > 0.9:
			raise argparse.ArgumentTypeError(f"Range must be above a percentage 1% to 90%. Given {percent}")
		return percent

	parser = argparse.ArgumentParser(description="Run simple uniform range queries on Kalepso.")
	parser.add_argument("--size", dest="size", metavar="input-size", type=argcheckInputSize, required=False, default=inputSizeDefault, help=f"The size of data [{inputSizeMin} - {inputSizeMax}]")
	parser.add_argument("--queries", dest="queries", metavar="queries-size", type=argcheckInputSize, required=False, default=int(inputSizeDefault / 10), help=f"The number of queries [{inputSizeMin} - {inputSizeMax}]")
	parser.add_argument("--max", dest="max", metavar="input-max", type=argcheckInputMax, required=False, default=inputSizeDefault, help=f"The max value of data points (min is 0) [>0]")
	parser.add_argument("--range", dest="range", metavar="range-percent", type=argcheckRange, required=False, default=0.3, help=f"The range size as percent of max-min data [0.01 - 0.9]")
	parser.add_argument("--seed", dest="seed", metavar="seed", type=int, default=123456, required=False, help="Seed to use for PRG")
	parser.add_argument("--kalepso-port", dest="kalepsoPort", metavar="kalepso-port", type=int, default=3306, required=False, help="Kalepso port")
	parser.add_argument("--mysql-port", dest="mysqlPort", metavar="mysql-port", type=int, default=3307, required=False, help="MySQL port")

	args = parser.parse_args()
	
	random.seed(args.seed)

	return DotMap({"size": args.size, "max": args.max, "range": args.range, "queries": args.queries, "kalepsoPort": args.kalepsoPort, "mysqlPort": args.mysqlPort})

def generateLoads(inputs):
	data = []
	queries = []
	for i in range(1, inputs.size):
		data += [random.randint(0, inputs.max)]
	
	querySize = int(inputs.max * inputs.range)
	for i in range(1, inputs.queries):
		left = random.randint(0, inputs.max - querySize)
		queries += [(left, left + querySize)]
	
	return DotMap({"data": data, "queries": queries})

def runLoads(loads, port):
	import mysql.connector as mysql
	
	db = mysql.connect(
		host = "localhost",
		user = "root",
		port = port,
		passwd = "MYPASSWD"
	)

	cursor = db.cursor()
	cursor.execute("CREATE DATABASE IF NOT EXISTS experimental")
	cursor.execute("USE experimental")
	cursor.execute("DROP TABLE IF EXISTS ranges")
	cursor.execute("CREATE TABLE IF NOT EXISTS ranges (number INT)")

	init = time.time()

	insert = "INSERT INTO ranges (number) VALUES (%s)"
	cursor.executemany(insert, list(map(lambda number: (number,), loads.data)))
	db.commit()
	
	inserted = time.time()
	
	query = "SELECT number FROM ranges WHERE number BETWEEN %s AND %s"
	for rangeQuery in loads.queries:
		cursor.execute(query, rangeQuery)
		records = cursor.fetchall()

	queried = time.time()
	
	return DotMap({"insertion": inserted - init, "queries": queried - inserted})

if __name__ == "__main__":
	inputs = parse()
	loads = generateLoads(inputs)
	
	for engine in [("Kelepso", inputs.kalepsoPort), ("MySQL", inputs.mysqlPort)]:
		times = runLoads(loads, engine[1])
		print(f"For {engine[0]}: inserted in {int(times.insertion * 1000)} ms, queries in {int(times.queries * 1000)} ms")
