#!/usr/bin/env python3

from bokeh.models import Legend
from bokeh.plotting import figure, show
from bokeh.io import export_svgs
import numpy as np

lineSize = 2
circleSize = 3


def plotEpsilons(epsilons, noises, totals):

	plot = figure(title="Epsilons", x_axis_label="Epsilons", y_axis_label="Records")
	plot.xaxis.axis_label_text_font = "normal"
	plot.yaxis.axis_label_text_font = "normal"
	plot.xaxis.ticker.desired_num_ticks = 30
	plot.title.align = "center"

	rNoises = plot.line(epsilons, noises, line_width=lineSize)
	rNoisesMarkers = plot.circle(epsilons, noises, size=circleSize)

	rTotals = plot.line(epsilons, totals, line_width=lineSize, color="dodgerblue")
	rTotalsMarkers = plot.circle(epsilons, totals, size=circleSize, color="dodgerblue")

	plot.add_layout(Legend(items=[("Noises", [rNoises, rNoisesMarkers]), ("Totals", [rTotals, rTotalsMarkers])]))

	show(plot)

	plot.output_backend = "svg"
	export_svgs(plot, filename=f"../output/plot-epsilons.svg")


def main():
	input = """
$ ./dp-oram-analyzer.csx
Seed: 1305
Count: 0

07/12/2020 00:20:05 |  ORAMs     Buckets   beta      epsilon   gamma     prune     Results per ORAM (real+padding+noise=total)

07/12/2020 00:20:41 |  64        65536     2^{-20}   0.01      True      False     78 + 0 + 2813 = 2892
07/12/2020 00:20:41 |  64        65536     2^{-20}   0.025     True      False     78 + 0 + 1205 = 1283
07/12/2020 00:20:41 |  64        65536     2^{-20}   0.05      True      False     78 + 0 + 651 = 730
07/12/2020 00:20:41 |  64        65536     2^{-20}   0.075     True      False     78 + 0 + 462 = 540
07/12/2020 00:20:41 |  64        65536     2^{-20}   0.1       True      False     78 + 0 + 365 = 443
07/12/2020 00:20:41 |  64        65536     2^{-20}   0.25      True      False     78 + 0 + 185 = 263
07/12/2020 00:20:41 |  64        65536     2^{-20}   0.5       True      False     78 + 0 + 123 = 201
07/12/2020 00:20:41 |  64        65536     2^{-20}   0.6       True      False     78 + 0 + 112 = 191
07/12/2020 00:20:41 |  64        65536     2^{-20}   0.693     True      False     78 + 0 + 105 = 184
07/12/2020 00:20:41 |  64        65536     2^{-20}   0.7       True      False     78 + 0 + 104 = 183
07/12/2020 00:20:41 |  64        65536     2^{-20}   0.8       True      False     78 + 0 + 98 = 177
07/12/2020 00:20:41 |  64        65536     2^{-20}   0.9       True      False     78 + 0 + 94 = 172
"""
	# 07/12/2020 00:20:41 |  64        65536     2^{-20}   1         True      False     78 + 0 + 90 = 169
	# 07/12/2020 00:20:41 |  64        65536     2^{-20}   1.1       True      False     78 + 0 + 87 = 166
	# 07/12/2020 00:20:41 |  64        65536     2^{-20}   1.3       True      False     78 + 0 + 83 = 161
	# 07/12/2020 00:20:41 |  64        65536     2^{-20}   1.5       True      False     78 + 0 + 79 = 158
	# 07/12/2020 00:20:41 |  64        65536     2^{-20}   2         True      False     78 + 0 + 74 = 153
	# 07/12/2020 00:20:41 |  64        65536     2^{-20}   5         True      False     78 + 0 + 64 = 142
	# 07/12/2020 00:20:41 |  64        65536     2^{-20}   7.5       True      False     78 + 0 + 61 = 140
	# 07/12/2020 00:20:41 |  64        65536     2^{-20}   10        True      False     78 + 0 + 60 = 139

	import re

	processor = re.compile("\}\s+([0-9]+\.?[0-9]*).*\+ (\d+) \= (\d+)", re.MULTILINE)

	epsilons = []
	noises = []
	totals = []
	for match in processor.finditer(input):
		epsilons += [match.group(1)]
		noises += [match.group(2)]
		totals += [match.group(3)]

	plotEpsilons(epsilons, noises, totals)


if __name__ == "__main__":
	main()
