#!/usr/bin/env python3

import random
import time
import math
from enum import Enum, auto
import logging
import json
import numpy as np


class Engine(Enum):
	kalepso = 3306
	mariadb = 3307
	oracle = 1521
	microsoft = 1433

	def __str__(self):
		return self.name

	@staticmethod
	def valueForParse(key):
		try:
			return Engine[key]
		except KeyError:
			raise ValueError()


def parse():
	import argparse

	inputSizeDefault = 1000
	inputSizeMin = 100
	inputSizeMax = 15 * 10**5

	rangeSizeDefault = 1000
	rangeSizeMin = 10
	rangeSizeMax = 50000

	def argcheckInputSize(value):
		number = int(value)
		if (number < inputSizeMin or number > inputSizeMax) and number != -1:
			raise argparse.ArgumentTypeError(f"Input size must be {inputSizeMin} to {inputSizeMax}, or -1. Given {number}")
		return number

	def argcheckInputMax(value):
		number = int(value)
		if number <= 0:
			raise argparse.ArgumentTypeError(f"Input max must be above 0. Given {number}")
		return number

	def argcheckRange(value):
		number = int(value)
		if number < rangeSizeMin or number > rangeSizeMax:
			raise argparse.ArgumentTypeError(f"Input / queries size must be {rangeSizeMin} to {rangeSizeMax}. Given {number}")
		return number

	parser = argparse.ArgumentParser(description="Run simple uniform range queries on Kalepso.")

	parser.add_argument("--size", dest="size", metavar="input-size", type=argcheckInputSize, required=False, default=inputSizeDefault, help=f"The size of data [{inputSizeMin} - {inputSizeMax}], or -1 for using all data from CSV.")
	parser.add_argument("--queries", dest="queries", metavar="queries-size", type=argcheckInputSize, required=False, default=int(inputSizeDefault / 10), help=f"The number of queries [{inputSizeMin} - {inputSizeMax}]")
	parser.add_argument("--range", dest="range", metavar="range-size", type=argcheckRange, required=False, default=1000, help=f"The range size [{rangeSizeMin} - {rangeSizeMax}]")

	parser.add_argument("--seed", dest="seed", metavar="seed", type=int, default=123456, required=False, help="Seed to use for PRG")
	parser.add_argument("-v", "--verbose", dest="verbose", default=False, help="increase output verbosity", action="store_true")

	parser.add_argument("--epsilon", dest="epsilon", metavar="epsilon", type=int, default=10, required=False, help="Epsilon parameter used to run kalepso (needed only to name log file)")

	parser.add_argument('--engine', dest="engine", metavar="engine", type=Engine.valueForParse, choices=list(Engine), required=True, help="Engine to run benchmark against")

	args = parser.parse_args()

	logging.basicConfig(
		level=logging.DEBUG if args.verbose else logging.INFO,
		format='%(asctime)s %(levelname)-8s %(message)s',
		datefmt='%a, %d %b %Y %H:%M:%S',
	)

	random.seed(args.seed)
	np.random.seed(args.seed + 1)

	return args.size, args.range, args.queries, args.engine, args.seed, args.epsilon


def generateLoads(dataSize, queryRange, queriesSize):
	import pandas as pd

	# data = pd.read_csv("https://gist.githubusercontent.com/dbogatov/a192d00d72de02f188c5268ea1bbf25b/raw/b1e7ea9e058e7906e0045b29ad75a5f201bd4f57/state-of-california-2019.csv")
	data = pd.read_csv("extended.csv")

	if dataSize != -1 and dataSize < len(data.index):
		data = data.sample(frac=float(dataSize) / len(data.index), random_state=random.randrange(4 * 10**6))

	# sample queries from the same distribution

	hist, bins = np.histogram(data["Total Pay & Benefits"], density=True, bins=max(100, int(len(data) / 100)))
	cdf = np.cumsum(hist)
	cdf = cdf / cdf[-1]
	uniform = np.random.rand(queriesSize)

	queries = []
	for r in uniform:
		leftBin = np.argwhere(cdf == min(cdf[(cdf - r) > 0]))[0][0]
		left = (bins[leftBin + 1] - bins[leftBin]) * np.random.rand() + bins[leftBin]
		queries += [(left, left + queryRange)]

	logging.debug("Generated %d datapoints and %d queries", len(data), len(queries))

	return data, queries


def runLoadsMySQL(data, queries, engine):
	import mysql.connector as mysql

	result = {"started": time.time(), "dataSize": len(data), "querySize": len(queries), "engine": f"{engine}"}

	db = mysql.connect(host="localhost", user="root", port=engine.value, passwd="kalepso")

	logging.debug("Connected to DB over port %d", engine.value)

	result["createSchema"] = time.time()

	cursor = db.cursor()
	cursor.execute("CREATE DATABASE IF NOT EXISTS CA_public_employees_salaries_2019")
	cursor.execute("USE CA_public_employees_salaries_2019")
	cursor.execute("DROP TABLE IF EXISTS salaries")
	cursor.execute("""
		CREATE TABLE IF NOT EXISTS salaries (
			fullname VARCHAR(100),		# Employee Name
			jobtitle VARCHAR(100),		# Job Title
			salary FLOAT,				# Base Pay
			overtimepay FLOAT,			# Overtime Pay
			other FLOAT,				# Other Pay
			benefits FLOAT NULL,		# Benefits
			total FLOAT,				# Total Pay
			totalPlusBenefits FLOAT,	# Total Pay & Benefits
			year INT,					# Year
			notes VARCHAR(150) NULL,	# Notes
			agency VARCHAR(100),		# Agency
			status VARCHAR(30),			# Status

			INDEX totalPlusBenefitsIndex (totalPlusBenefits)
		)
	""")
	cursor.execute("SET SESSION query_cache_type=0")

	db.commit()

	result["createSchema"] = time.time() - result["createSchema"]

	logging.debug("(re)Created scheme")

	result["insertData"] = time.time()

	insert = """
		INSERT INTO salaries
			(fullname, jobtitle, salary, overtimepay, other, benefits, total, totalPlusBenefits, year, notes, agency, status)
		VALUES
			(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
	"""
	for index, record in data.iterrows():
		# yapf: disable
		cursor.execute(
			insert,
			(
				record["Employee Name"],
				record["Job Title"],
				float(record["Base Pay"]),
				float(record["Overtime Pay"]),
				float(record["Other Pay"]),
				0.0 if record["Benefits"] == "Not Provided" else float(record["Benefits"]),
				float(record["Total Pay"]),
				float(record["Total Pay & Benefits"]),
				int(record["Year"]),
				"" if math.isnan(record["Notes"]) else record["Notes"],
				record["Agency"],
				"" if math.isnan(record["Status"]) else record["Status"]
			)
		)
		# yapf: enable

		db.commit()

	result["insertData"] = time.time() - result["insertData"]

	logging.debug("Inserted %d records", len(data))

	result["runQueries"] = time.time()
	result["queries"] = []

	query = "SELECT * FROM salaries WHERE totalPlusBenefits BETWEEN %s AND %s"
	for rangeQuery in queries:
		start = time.time()

		cursor.execute(query, rangeQuery)
		records = cursor.fetchall()

		result["queries"] += [{"overhead": time.time() - start, "resultSize": len(records)}]

	result["runQueries"] = time.time() - result["runQueries"]

	logging.debug("Completed %d queries", len(queries))

	sizeQuery = """
		SELECT
			ROUND((DATA_LENGTH + INDEX_LENGTH)) AS `Size (B)`
		FROM
			information_schema.TABLES
		WHERE
			TABLE_SCHEMA = "CA_public_employees_salaries_2019"
		AND
			TABLE_NAME = "salaries"
		ORDER BY
			(DATA_LENGTH + INDEX_LENGTH)
		DESC
	"""

	cursor.execute(sizeQuery)
	result["dbSize"] = int(cursor.fetchall()[0][0])

	return result


def runLoadsOracle(data, queries, port):
	import cx_Oracle

	connection = cx_Oracle.connect("dmytro", "password", f"0.0.0.0:{port}/ORCLCDB.localdomain")

	cursor = connection.cursor()

	cursor.execute("BEGIN EXECUTE IMMEDIATE 'DROP TABLE ranges'; EXCEPTION WHEN OTHERS THEN NULL; END;")
	cursor.execute("CREATE TABLE ranges (point NUMBER ENCRYPT NO SALT)")
	cursor.execute("CREATE INDEX pointIndex on ranges (point)")

	connection.commit()

	init = time.time()

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


def resultToString(result):
	from functools import reduce

	sumOverKey = lambda key: float(sum(map(lambda query: query[key], result["queries"])))

	allQueriesMiss = sumOverKey("resultSize") == 0

	return f"""
For {result["engine"]}:
	Started on {time.strftime("%m/%d/%Y %H:%M:%S", time.gmtime(result["started"]))}
	Data size: {result["dataSize"]}
	Query size: {result["querySize"]}
	Epsilon: {result["epsilon"]}
	Seed: {result["seed"]}
	Overheads:
		(re)creting schema: {int(result["createSchema"] * 1000)} ms
		inserting data: {int(result["insertData"] * 1000)} ms / {int(result["insertData"] * 1000) / result["dataSize"]} ms per record
		running queries: {int(result["runQueries"] * 1000)} ms / {int(result["runQueries"] * 1000) / result["querySize"]} ms per query
		query time per return record: {1000 * sumOverKey("overhead") / sumOverKey("resultSize") if not allQueriesMiss else 0:.3f} ms {"! All queries returned 0 records !" if allQueriesMiss else ""}
	Average results per query: {reduce(lambda a, b: a + b, map(lambda x: x["resultSize"], result["queries"])) / len(result["queries"])}
	Queries with empty result: {len(list(filter(lambda x: x["resultSize"] == 0, result["queries"])))}
	Database size at the end: {result["dbSize"]} bytes
"""


if __name__ == "__main__":

	dataSize, queryRange, queriesSize, engine, seed, epsilon = parse()
	data, queries = generateLoads(dataSize, queryRange, queriesSize)

	if engine == Engine.microsoft:
		generateMSSQLLoad(data, queries)
	else:
		if engine == Engine.kalepso or engine == Engine.mariadb:
			result = runLoadsMySQL(data, queries, engine)
		else:
			insertionTime, queryTime, tableSize = runLoadsOracle(data, queries, engine.value)

		result["epsilon"] = epsilon
		result["seed"] = seed
		logging.info(resultToString(result))
		jsonFile = f"../output/{result['engine']}-{dataSize}-{epsilon}-{seed}-{time.strftime('%m-%d-%Y--%H-%M-%S', time.gmtime(result['started']))}.json"
		with open(jsonFile, 'w') as outfile:
			json.dump(result, outfile)
		logging.debug(f"JSON dumped at {jsonFile}")
