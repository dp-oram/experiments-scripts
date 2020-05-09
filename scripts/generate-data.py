#!/usr/bin/env python3

import random
import time
import math
import logging
import json
import numpy as np


def parse():
	import argparse

	parser = argparse.ArgumentParser(description="Generate simple uniform data nd range queries.")

	parser.add_argument("--size", dest="size", metavar="input-size", type=int, required=False, default=1000, help=f"The size of data, or -1 for using all data from CSV.")
	parser.add_argument("--queries", dest="queries", metavar="queries-size", type=int, required=False, default=100, help=f"The number of queries")
	parser.add_argument("--range", dest="range", metavar="range-size", type=int, required=False, default=500, help=f"The range size")

	parser.add_argument("--seed", dest="seed", metavar="seed", type=int, default=123456, required=False, help="Seed to use for PRG")
	parser.add_argument("-v", "--verbose", dest="verbose", default=False, help="increase output verbosity", action="store_true")

	args = parser.parse_args()

	logging.basicConfig(
		level=logging.DEBUG if args.verbose else logging.INFO,
		format='%(asctime)s %(levelname)-8s %(message)s',
		datefmt='%a, %d %b %Y %H:%M:%S',
	)

	random.seed(args.seed)
	np.random.seed(args.seed + 1)

	return args.size, args.range, args.queries, args.seed


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


def storeLoads(data, queries):
	data.to_csv("data.csv", index=False, header=False)
	with open("query.csv", "w") as out:
		for query in queries:
			out.write(f"{query[0]},{query[1]}\n")


if __name__ == "__main__":

	dataSize, queryRange, queriesSize, seed = parse()
	data, queries = generateLoads(dataSize, queryRange, queriesSize)

	storeLoads(data, queries)
