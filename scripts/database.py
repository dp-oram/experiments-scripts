#!/usr/bin/env python3

import psycopg2
import numpy as np
import logging
import random
from enum import Enum, auto


class Engine(Enum):
	mysql = auto()
	postgres = auto()

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
	import os.path

	# https://stackoverflow.com/a/11541450/1644554
	def is_valid_file(parser, arg):
		if not os.path.exists(arg):
			parser.error("The file %s does not exist!" % arg)
		else:
			return arg

	parser = argparse.ArgumentParser(description="Run Postgres experiment")

	parser.add_argument('--engine', dest="engine", metavar="engine", type=Engine.valueForParse, choices=list(Engine), required=True, help="Engine to run queries against")

	parser.add_argument("--record-size", dest="recordSize", metavar="record-size", type=int, default=4096, help=f"The size of the record in bytes.")
	parser.add_argument("--queries", dest="queries", metavar="queries-count", type=int, default=20, help=f"The number of queries to run.")
	parser.add_argument("--count", dest="count", metavar="count", type=int, default=-1, help=f"The number of datapoint to read.")
	parser.add_argument("--batch", dest="batch", metavar="batch", type=int, default=1000, help=f"The number of records to insert at a time.")

	parser.add_argument("--dataset", dest="dataset", metavar="dataset", type=lambda x: is_valid_file(parser, x), required=True, help=f"Dataset to read.")
	parser.add_argument("--queryset", dest="queryset", metavar="queryset", type=lambda x: is_valid_file(parser, x), required=True, help=f"Queryset to read.")

	parser.add_argument("-v", "--verbose", dest="verbose", default=False, help="Increase output verbosity", action="store_true")
	parser.add_argument("--password", dest="password", metavar="password", type=str, required=True, help=f"Password for PostgreSQL.")
	parser.add_argument("--host", dest="host", metavar="host", type=str, default="postgres", help=f"Host for PostgreSQL.")

	parser.add_argument("--skip-insert", dest="skipInsert", default=False, help="Skip INSERT stage", action="store_true")
	parser.add_argument("--skip-queries", dest="skipQueries", default=False, help="Skip QUERIES stage", action="store_true")

	args = parser.parse_args()

	logging.basicConfig(
		level=logging.DEBUG if args.verbose else logging.INFO,
		format='%(asctime)s %(levelname)-8s %(message)s',
		datefmt='%a, %d %b %Y %H:%M:%S',
	)

	return args.engine, args.recordSize, args.count, args.queries, args.batch, args.dataset, args.queryset, args.password, args.host, args.skipInsert, args.skipQueries


def main():
	import time
	import statistics
	import string

	engine, recordSize, count, queries, batch, dataset, queryset, password, host, skipInsert, skipQueries = parse()

	import psycopg2
	import psycopg2.extras
	import mysql.connector as mysql

	try:
		connection = None

		if engine == Engine.postgres:
			connection = psycopg2.connect(host=host, database="dporam", user="dporam", password=password)
		else:
			connection = mysql.connect(host=host, port=3306, user="root", passwd=password)

		logging.info(f"""
Record size: {recordSize}
Queries number: {queries}
Insert batch size: {batch}
Dataset: {dataset}
Queryset: {queryset}
		""")

		cursor = connection.cursor()

		if engine == Engine.postgres:
			cursor.execute("SELECT version()")
			cursor.fetchone()  # make sure no crash
		else:
			cursor.execute("CREATE DATABASE IF NOT EXISTS experiments")
			cursor.execute("USE experiments")
			cursor.execute("SET SESSION query_cache_type=0")
			connection.commit()

		if not skipInsert:

			if engine == Engine.postgres:
				cursor.execute("""
					DROP TABLE IF EXISTS experiment;
					CREATE TABLE experiment (
						salary	double precision,
						payload bytea NOT NULL
					);
					CREATE INDEX ON experiment (salary);
				""")
			else:
				cursor.execute("DROP TABLE IF EXISTS experiment")
				cursor.execute("""
					CREATE TABLE IF NOT EXISTS experiment (
						salary	DOUBLE,
						payload BLOB,

						INDEX salaryIndex (salary)
					)
				""")

			connection.commit()

			logging.info("Created table and index, inserting dataset")
			beforeInsertTime = time.time()

			toInsert = []
			readCount = 0
			with open(dataset, "r") as datasetFile:
				line = datasetFile.readline()
				while line:

					salary = float(line)
					if engine == Engine.postgres:
						payload = bytearray(random.getrandbits(8) for _ in range(recordSize))
					else:
						payload = "".join(random.choice(string.ascii_lowercase) for i in range(recordSize)).encode("utf-8")

					toInsert += [(salary, payload)]

					line = datasetFile.readline()
					readCount += 1

					if len(toInsert) == batch or not line or readCount == count:
						if engine == Engine.postgres:
							psycopg2.extras.execute_values(cursor, "INSERT INTO experiment (salary, payload) VALUES %s", toInsert)
						else:
							cursor.executemany("INSERT INTO experiment (salary, payload) VALUES (%s, %s)", toInsert)

						connection.commit()
						logging.debug(f"Inserted {len(toInsert)} records")
						toInsert = []

						if readCount == count:
							break

			beforeQueriesTime = time.time()

			logging.info(f"Finished inserting in {int((beforeQueriesTime - beforeInsertTime) * 1000)} ms.")

		if not skipQueries:
			logging.info("Will do queries.")

			overheads = []
			with open(queryset, "r") as querysetFile:
				line = querysetFile.readline()
				while line:
					endpoints = line.split(",")
					beforeQueryTime = time.time()

					cursor.execute("SELECT * FROM experiment WHERE salary BETWEEN %s AND %s;", endpoints)
					result = cursor.fetchall()

					afterQueryTime = time.time()
					overhead = int((afterQueryTime - beforeQueryTime) * 1000)
					overheads += [overhead]

					logging.info(f"Query {{{endpoints[0]}, {endpoints[1].rstrip()}}}: fetched {len(result)} records in {overhead} ms.")

					line = querysetFile.readline()
					if len(overheads) == queries:
						break

			logging.info(f"Average query time: {statistics.mean(overheads) :.3f} ms")

		cursor.close()

	except (Exception, psycopg2.DatabaseError, mysql.connector.Error) as error:
		logging.fatal(error)
	finally:
		if connection is not None:
			connection.close()
			logging.info("Database connection closed.")


if __name__ == "__main__":
	main()
