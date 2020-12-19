#!/usr/bin/env python3

from bokeh.models import Legend
from bokeh.plotting import figure, show
from bokeh.io import export_svgs

lineSize = 2
circleSize = 3


def plotEpsilons(epsilons, noises, totals):

	print(epsilons)
	print(noises)
	print(totals)

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
Seed: 1305
Count: 0
Input: PUMS-california

07/12/2020 14:27:13 |  ORAMs     Buckets   beta      epsilon   gamma     prune     Results per ORAM (real+padding+noise=total)

07/12/2020 14:27:45 |  64        65536     2^{-20}   0.01      True      False     78 + 1 + 1959 = 2039
07/12/2020 14:27:45 |  64        65536     2^{-20}   0.025     True      False     78 + 1 + 851 = 931
07/12/2020 14:27:45 |  64        65536     2^{-20}   0.05      True      False     78 + 1 + 469 = 548
07/12/2020 14:27:45 |  64        65536     2^{-20}   0.075     True      False     78 + 1 + 337 = 417
07/12/2020 14:27:45 |  64        65536     2^{-20}   0.1       True      False     78 + 1 + 270 = 350
07/12/2020 14:27:45 |  64        65536     2^{-20}   0.25      True      False     78 + 1 + 146 = 225
07/12/2020 14:27:45 |  64        65536     2^{-20}   0.5       True      False     78 + 1 + 103 = 182
07/12/2020 14:27:45 |  64        65536     2^{-20}   0.6       True      False     78 + 1 + 95 = 175
07/12/2020 14:27:45 |  64        65536     2^{-20}   0.693     True      False     78 + 1 + 90 = 170
07/12/2020 14:27:45 |  64        65536     2^{-20}   0.7       True      False     78 + 1 + 90 = 170
07/12/2020 14:27:45 |  64        65536     2^{-20}   0.8       True      False     78 + 1 + 86 = 165
07/12/2020 14:27:45 |  64        65536     2^{-20}   0.9       True      False     78 + 1 + 83 = 162
07/12/2020 14:27:45 |  64        65536     2^{-20}   1         True      False     78 + 1 + 80 = 160
"""
	# 07/12/2020 14:27:45 |  64        65536     2^{-20}   1.1       True      False     78 + 1 + 78 = 158
	# 07/12/2020 14:27:45 |  64        65536     2^{-20}   1.3       True      False     78 + 1 + 75 = 155
	# 07/12/2020 14:27:45 |  64        65536     2^{-20}   1.5       True      False     78 + 1 + 73 = 152
	# 07/12/2020 14:27:45 |  64        65536     2^{-20}   2         True      False     78 + 1 + 69 = 149
	# 07/12/2020 14:27:45 |  64        65536     2^{-20}   5         True      False     78 + 1 + 62 = 142
	# 07/12/2020 14:27:45 |  64        65536     2^{-20}   7.5       True      False     78 + 1 + 61 = 140
	# 07/12/2020 14:27:45 |  64        65536     2^{-20}   10        True      False     78 + 1 + 60 = 139

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
