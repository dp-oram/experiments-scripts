#!/usr/bin/env python3

from __future__ import division
import numpy as np
import pandas as pd
import math
import string
import random
import logging
from enum import Enum, auto


class Dataset(Enum):
	CA = auto()
	PUMS = auto()
	UNIFORM = auto()

	def __str__(self):
		return self.name

	@staticmethod
	def from_string(s):
		try:
			return Dataset[s]
		except KeyError:
			raise ValueError()


def parse():
	import argparse

	parser = argparse.ArgumentParser(description="Expand distribution")

	parser.add_argument("--size", dest="size", metavar="output-size", type=int, required=True, help=f"The size of the expanded set. -1 to keep original size.")
	parser.add_argument("--bins", dest="bins", metavar="bins-number", type=int, required=True, help=f"The number of bins to use for histogram.")

	parser.add_argument("--dataset", dest="dataset", metavar="dataset", type=lambda dataset: Dataset[dataset], choices=list(Dataset), required=True, help=f"Dataset to generate.")
	parser.add_argument("--pums", dest="pums", metavar="pums", type=str, required=False, default="us", help=f"PUMS set to use (us, nebraska, florida).")
	parser.add_argument("--min", dest="min", metavar="min", type=int, required=False, default=0, help=f"Min element for uniform generation.")
	parser.add_argument("--max", dest="max", metavar="max", type=int, required=False, default=10**6, help=f"Max element for uniform generation.")

	parser.add_argument("--crop", dest="crop", action="store_true", help=f"Whether to crop index according to min and max.")
	parser.add_argument("--hist", dest="hist", action="store_true", help=f"Whether to plot histogram.")

	parser.add_argument("-s", "--selectivities", dest="selectivities", nargs='+', help="Selectivities as percents", required=True)

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

	return args.size, args.bins, args.dataset, args.pums, args.min, args.max, args.crop, args.hist, args.selectivities


def histogram(index, bins, filename, cropped):

	from bokeh.plotting import show
	from scipy.stats import norm
	import scipy.stats as stats
	from bokeh.io import export_svgs

	logging.debug("Building histogram")

	hist, edges = np.histogram(index, density=True, bins=bins)
	x = np.linspace(index.min(), index.max(), 200)

	mu, sigma = norm.fit(index)
	pdf = 1 / (sigma * np.sqrt(2 * np.pi)) * np.exp(-(x - mu)**2 / (2 * sigma**2))

	plot = make_plot(filename, hist, edges, x, pdf, len(index))

	show(plot)

	plot.output_backend = "svg"
	export_svgs(plot, filename=f"../output/{filename}-{len(index)}{'-cropped' if cropped else ''}.svg")


def make_plot(title, hist, edges, x, pdf, count):
	from bokeh.plotting import figure, output_file, show

	p = figure(title=f"{title} ({count} items)", tools='', background_fill_color="#fafafa")
	p.quad(top=hist, bottom=0, left=edges[:-1], right=edges[1:], fill_color="navy", line_color="white", alpha=0.5)
	p.line(x, pdf, line_color="#ff8888", line_width=4, alpha=0.7, legend_label="Normal PDF (fit to dataset)")

	p.y_range.start = 0
	p.xaxis.axis_label = "value"
	p.yaxis.axis_label = 'Pr(value)'
	p.grid.grid_line_color = "white"

	p.left[0].formatter.use_scientific = False
	p.xaxis[0].formatter.use_scientific = False

	return p


def changeSize(index, n, bins=10000):
	if n == -1 or n == len(index):
		return index
	if len(index) < n:
		logging.debug("Expanding")

		hist, bins = np.histogram(index, density=False, bins=bins)
		coefficient = float(n) / float(len(index))

		newBins = np.array([])

		for i in range(len(hist)):
			newBins = np.append((bins[i + 1] - bins[i]) * np.random.rand(int(coefficient * hist[i])) + bins[i], newBins)

		return newBins
	elif len(index) > n:
		logging.debug("Contracting")

		return index.sample(frac=float(n) / len(index), random_state=random.randrange(4 * 10**6))


def generateUniform(size, _min, _max):
	return np.random.uniform(low=float(_min), high=float(_max), size=size)


def getRightEndpoint(index, left, selectivity):
	leftIndex = np.searchsorted(index, left)
	querySize = int((len(index) / 100) * float(selectivity))

	if leftIndex + querySize >= len(index):
		raise Exception("Left endpoint is too far right for given selectivity")
	right = index[leftIndex + querySize]

	return right


def generateQueries(index, bins, selectivities, follow):
	if follow:
		hist, bins = np.histogram(index, density=True, bins=bins)
		cdf = np.cumsum(hist)
		cdf = cdf / cdf[-1]
	else:
		_min = np.min(index)
		_max = np.max(index)

	for selectivity in selectivities:
		queries = []
		while True:
			r = np.random.rand()

			if follow:
				leftBin = np.argwhere(cdf == min(cdf[(cdf - r) > 0]))[0][0]
				left = int((bins[leftBin + 1] - bins[leftBin]) * np.random.rand() + bins[leftBin])
			else:
				left = np.random.randint(int(_min), int(_max))

			try:
				right = getRightEndpoint(index, left, selectivity)
			except Exception:
				continue

			queries += [(left, right)]

			if len(queries) == 100:
				break

		yield queries, selectivity


def main():

	size, bins, dataset, pums, _min, _max, crop, hist, selectivities = parse()

	if dataset == Dataset.CA:
		logging.debug("Reading CA employees dataset")

		index = pd.read_csv("../../datasets/state-of-california-2019.csv", usecols=["Total Pay & Benefits"], squeeze=True)
	elif dataset == Dataset.UNIFORM:
		logging.debug("Generating uniform dataset")

		index = generateUniform(size, _min, _max)
	elif dataset == Dataset.PUMS:
		logging.debug(f"Reading PUMS ({pums}) dataset")

		if pums == "us":
			index = pd.concat((pd.read_csv(f"../../datasets/pums-{pums}-{i}.csv", usecols=["WAGP"], squeeze=True)) for i in range(1, 5))
		else:
			index = pd.read_csv(f"../../datasets/pums-{pums}.csv", usecols=["WAGP"], squeeze=True)

		index = index[~np.isnan(index)]

	if crop:
		logging.debug(f"Cropping [{_min}, {_max}]")
		index = index[(index >= _min) & (index <= _max)]

	index = changeSize(index, size, bins=bins)
	index = index + np.random.rand(len(index))
	index = np.around(index, decimals=2)
	index = np.sort(index)

	logging.debug(f"\n{index}")
	logging.debug(f"Size: {len(index)}")

	if hist:
		histogram(index, bins, f"histogram-{dataset}{f'-{pums}' if dataset == Dataset.PUMS else ''}", crop)

	logging.debug("Writing Results")

	with open(f"../output/dataset-{dataset}-{pums if dataset == Dataset.PUMS else size}.csv", "w") as out:
		for record in index:
			out.write(f"{record}\n")

	for followDistribution in [True, False]:
		for queries, selectivity in generateQueries(index, bins, selectivities, followDistribution):
			with open(f"../output/queries-{dataset}-{pums if dataset == Dataset.PUMS else size}-{selectivity}-{'follow' if followDistribution else 'uniform'}.csv", "w") as out:
				for query in queries:
					out.write(f"{query[0]},{query[1]}\n")


if __name__ == "__main__":
	main()
