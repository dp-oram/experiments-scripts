#!/usr/bin/env python3

import numpy as np
import random
import logging
import os

def parse():
	import argparse

	parser = argparse.ArgumentParser(description="Expand distribution")

	parser.add_argument("--left", dest="left", metavar="left-dataset", type=argparse.FileType("r"), required=True, help=f"The left dataset file.")
	parser.add_argument("--right", dest="right", metavar="right-dataset", type=argparse.FileType("r"), required=True, help=f"The right dataset file.")

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

	return args.left, args.right


def main():

	left, right = parse()
	cwd = os.path.dirname(os.path.abspath(__file__))

	counter = 0

	with left as leftIn:
		with right as rightIn:
			with open(f"{cwd}/../output/dataset-merged.csv", "w") as out:
				while True:
					leftLine = leftIn.readline()
					rightLine = rightIn.readline()
					if not leftLine or not rightLine:
						break
					out.write(f"{leftLine.rstrip()},{rightLine.rstrip()}\n")
					counter += 1

	logging.info(f"Written {counter} lines!")

if __name__ == "__main__":
	main()
