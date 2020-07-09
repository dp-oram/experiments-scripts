#!/usr/bin/env python3

import psycopg2
import numpy as np
import logging
import random


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

	parser.add_argument("--record-size", dest="recordSize", metavar="record-size", type=int, default=4096, help=f"The size of the record in bytes.")
	parser.add_argument("--queries", dest="queries", metavar="queries-count", type=int, default=20, help=f"The number of queries to run.")
	parser.add_argument("--batch", dest="batch", metavar="batch", type=int, default=1000, help=f"The number of records to insert at a time.")

	parser.add_argument("--dataset", dest="dataset", metavar="dataset", type=lambda x: is_valid_file(parser, x), required=True, help=f"Dataset to read.")
	parser.add_argument("--queryset", dest="queryset", metavar="queryset", type=lambda x: is_valid_file(parser, x), required=True, help=f"Queryset to read.")

	parser.add_argument("-v", "--verbose", dest="verbose", default=False, help="increase output verbosity", action="store_true")
	parser.add_argument("--password", dest="password", metavar="password", type=str, required=True, help=f"Password for PostgreSQL.")

	args = parser.parse_args()

	logging.basicConfig(
		level=logging.DEBUG if args.verbose else logging.INFO,
		format='%(asctime)s %(levelname)-8s %(message)s',
		datefmt='%a, %d %b %Y %H:%M:%S',
	)

	return args.recordSize, args.queries, args.batch, args.dataset, args.queryset, args.password


def main():
	import psycopg2
	import psycopg2.extras
	import time
	import statistics

	recordSize, queries, batch, dataset, queryset, password = parse()

	try:
		connection = psycopg2.connect(host="postgres.bogatov.dev", database="dporam", user="dporam", password=password)

		cursor = connection.cursor()
		cursor.execute("SELECT version()")
		cursor.fetchone() # make sure no crash
		logging.info(f"""
Record size: {recordSize}
Queries number: {queries}
Insert batch size: {batch}
Dataset: {dataset}
Queryset: {queryset}
		""")

		cursor.execute("""
			DROP TABLE IF EXISTS experiment;
			CREATE TABLE experiment (
				salary	double precision,
				payload bytea NOT NULL
			);
			CREATE INDEX ON experiment (salary);
		""")

		connection.commit()

		logging.info("Created table and index, inserting dataset")
		beforeInsertTime = time.time()

		toInsert = []
		with open(dataset, "r") as datasetFile:
			line = datasetFile.readline()
			while line:
				salary = float(line)
				payload = bytearray(random.getrandbits(8) for _ in range(recordSize))
				toInsert += [(salary, payload)]

				line = datasetFile.readline()

				if len(toInsert) == batch or not line:
					psycopg2.extras.execute_values(cursor, "INSERT INTO experiment (salary, payload) VALUES %s", toInsert)
					connection.commit()
					logging.debug(f"Inserted {len(toInsert)} records")
					toInsert = []

		beforeQueriesTime = time.time()

		logging.info(f"Finished inserting in {int((beforeQueriesTime - beforeInsertTime) * 1000)} ms. Will do queries.")

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

		logging.info(f"Average query time: {statistics.mean(overheads) :.3f} ms")

		cursor.close()

	except (Exception, psycopg2.DatabaseError) as error:
		logging.fatal(error)
	finally:
		if connection is not None:
			connection.close()
			logging.info("Database connection closed.")


if __name__ == "__main__":
	main()
