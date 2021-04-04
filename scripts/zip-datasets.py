#!/usr/bin/env python3

import numpy as np
import random
import logging
import os


def parse():
	import argparse

	parser = argparse.ArgumentParser(description="Expand distribution")

	parser.add_argument("--left-dataset", dest="leftDataset", metavar="left-dataset", type=argparse.FileType("r"), required=True, help=f"The left dataset file.")
	parser.add_argument("--right-dataset", dest="rightDataset", metavar="right-dataset", type=argparse.FileType("r"), required=True, help=f"The right dataset file.")

	parser.add_argument("--left-queryset", dest="leftQueryset", metavar="left-queryset", type=argparse.FileType("r"), required=True, help=f"The left queryset file.")
	parser.add_argument("--right-queryset", dest="rightQueryset", metavar="right-queryset", type=argparse.FileType("r"), required=True, help=f"The right queryset file.")

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

	return args.leftDataset, args.rightDataset, args.leftQueryset, args.rightQueryset


def main():

	leftDataset, rightDataset, leftQueryset, rightQueryset = parse()
	cwd = os.path.dirname(os.path.abspath(__file__))

	counter = 0
	with leftDataset as leftIn:
		with rightDataset as rightIn:
			with open(f"{cwd}/../output/dataset-merged.csv", "w") as out:
				while True:
					leftLine = leftIn.readline()
					rightLine = rightIn.readline()
					if not leftLine or not rightLine:
						break
					out.write(f"{leftLine.rstrip()},{rightLine.rstrip()}\n")
					counter += 1

	logging.info(f"Written {counter} dataset lines!")

	counter = 0
	with leftQueryset as leftIn:
		with rightQueryset as rightIn:
			with open(f"{cwd}/../output/queryset-merged.csv", "w") as out:
				while True:
					leftLine = leftIn.readline()
					rightLine = rightIn.readline()
					if not leftLine or not rightLine:
						break
					out.write(f"{leftLine.rstrip()}\n")
					out.write(f"{rightLine.rstrip()}\n")
					counter += 2

	logging.info(f"Written {counter} queryset lines!")


if __name__ == "__main__":
	main()
