#!/usr/bin/env python3

from __future__ import division
import numpy as np
import pandas as pd
import math
import string
import random


def histogram(salaries, filename="plot"):

	from bokeh.plotting import show
	from scipy.stats import norm
	import scipy.stats as stats
	from bokeh.io import export_svgs

	hist, edges = np.histogram(salaries, density=True, bins=100)
	x = np.linspace(salaries.min(), salaries.max(), 200)

	mu, sigma = norm.fit(salaries)
	pdf = 1 / (sigma * np.sqrt(2 * np.pi)) * np.exp(-(x - mu)**2 / (2 * sigma**2))

	plot = make_plot("Total Pay & Benefits", hist, edges, x, pdf)

	show(plot)

	plot.output_backend = "svg"
	export_svgs(plot, filename=f"{filename}.svg")


def make_plot(title, hist, edges, x, pdf):
	from bokeh.plotting import figure, output_file, show

	p = figure(title=title, tools='', background_fill_color="#fafafa")
	p.quad(top=hist, bottom=0, left=edges[:-1], right=edges[1:], fill_color="navy", line_color="white", alpha=0.5)
	p.line(x, pdf, line_color="#ff8888", line_width=4, alpha=0.7, legend_label="Normal PDF")

	p.y_range.start = 0
	p.xaxis.axis_label = 'salary'
	p.yaxis.axis_label = 'Pr(salary)'
	p.grid.grid_line_color = "white"

	p.left[0].formatter.use_scientific = False
	p.xaxis[0].formatter.use_scientific = False

	return p


def expand(salaries, n, bins=10000):

	hist, bins = np.histogram(salaries, density=False, bins=bins)
	coefficient = float(n) / float(len(salaries))

	newBins = np.array([])

	for i in range(len(hist)):
		newBins = np.append((bins[i + 1] - bins[i]) * np.random.rand(int(coefficient * hist[i])) + bins[i], newBins)

	return newBins


def addPayload(salaries, sample):

	yield ["Employee Name", "Job Title", "Base Pay", "Overtime Pay", "Other Pay", "Benefits", "Total Pay", "Total Pay & Benefits", "Year", "Notes", "Agency", "Status"]

	def stringLength(key):
		return int(np.mean(sample[key].apply(lambda value: len(value) if isinstance(value, str) else 0)))

	def randomString(length):
		letters = string.ascii_lowercase
		return ''.join(random.choice(letters) for i in range(length))

	nameLength = stringLength("Employee Name")
	jobLength = stringLength("Job Title")
	notesLength = stringLength("Notes")
	agencyLength = stringLength("Agency")
	statusLength = stringLength("Status")

	for salary in salaries:
		yield [
			randomString(nameLength),
			randomString(jobLength),
			random.uniform(0.0, 150000.0),
			random.uniform(0.0, 150000.0),
			random.uniform(0.0, 150000.0),
			random.uniform(0.0, 150000.0),
			random.uniform(0.0, 150000.0), salary, 2020,
			randomString(notesLength),
			randomString(agencyLength),
			randomString(statusLength)
		]


if __name__ == "__main__":

	data = pd.read_csv("https://gist.githubusercontent.com/dbogatov/a192d00d72de02f188c5268ea1bbf25b/raw/b1e7ea9e058e7906e0045b29ad75a5f201bd4f57/state-of-california-2019.csv")
	# data = pd.read_csv("data.csv")
	# data = pd.read_csv("extended.csv")
	# data.sort_values("Total Pay & Benefits", axis=0, ascending=True, inplace=True, na_position='last')
	salaries = data["Total Pay & Benefits"]
	# salaries = salaries[salaries.between(salaries.quantile(.05), salaries.quantile(.95))]

	# histogram(salaries, filename="original")

	salaries = expand(salaries, 10**6, bins=10**4)

	# histogram(salaries, filename="expanded")

	with open("extended.csv", "w") as out:
		for record in addPayload(salaries, data):
			out.write(','.join(map(str, record)) + "\n")
