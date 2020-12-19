#!/usr/bin/env python3

from bokeh.io import show, export_svgs
from bokeh.models import ColumnDataSource, LabelSet, Legend, FactorRange
from bokeh.plotting import figure
from bokeh.layouts import gridplot
from bokeh.transform import dodge, factor_cmap
import svg_stack as ss

def make_barchart(bins, values, title, color):

	width = 300
	coefficient = 1.2

	if len(values) == 3:
		del color[1]
		del color[2]
		width = int(width * 3 / 5)
	if len(values) == 4:
		del color[2]
		coefficient = 1.0

	data=dict(
		bins=bins,
		values=values,
		color=["#%02x%02x%02x" % x for x in color],
		labels=values.copy()
	)
	# hack!
	if title == "Mechanism":
		data["labels"][3] = 15000

	source = ColumnDataSource(data=data)

	plot = figure(x_range=bins, y_range=(0, max(values)*coefficient), title=title, toolbar_location=None, tools="", plot_width=width, plot_height=200)

	plot.vbar(x="bins", top="values", width=0.8, color="color", legend_field="bins", source=source, alpha=0.8)

	plot.xgrid.grid_line_color = None
	plot.legend.orientation = "horizontal"
	plot.legend.location = "top_center"
	plot.legend.visible = False
	plot.title.align = "center"
	plot.title.offset = 20
	plot.title.vertical_align = "top"

	labels = LabelSet(
		x='bins',
		y='values',
		text='labels',
		level='glyph',
		x_offset=-10,
		y_offset=5,
		source=source,
		render_mode='canvas',
		text_font_size="8pt"
	)

	plot.add_layout(labels)

	return plot

def make_barchart_double(bins, values1, values2, title, color1, color2):

	source = ColumnDataSource(
		data={
			'bins': bins,
			values1["title"]: values1["data"],
			values2["title"]: values2["data"],
			"color1": ["#%02x%02x%02x" % x for x in color1],
			"color2": ["#%02x%02x%02x" % x for x in color2],
		}
	)

	plot = figure(x_range=bins, y_range=(0, max(max(values1["data"], values2["data"]))*1.4), title=title, toolbar_location=None, tools="", plot_width=300, plot_height=200)

	plot.vbar(x=dodge('bins', -0.2, range=plot.x_range), top=values1["title"], width=0.4, source=source, color="color1", legend_label=values1["title"])
	plot.vbar(x=dodge('bins', +0.2, range=plot.x_range), top=values2["title"], width=0.4, source=source, color="color2", legend_label=values2["title"])

	plot.x_range.range_padding = 0.1
	plot.xgrid.grid_line_color = None
	plot.legend.location = "top_center"
	plot.legend.orientation = "horizontal"
	plot.legend.background_fill_alpha = 0.0
	plot.legend.border_line_color = None
	plot.legend.label_text_font_size = "8pt"
	plot.title.align = "center"
	plot.title.offset = 20
	plot.title.vertical_align = "top"

	labels1 = LabelSet(
		x='bins',
		y=values1["title"],
		text=values1["title"],
		level='glyph',
		x_offset=-23,
		y_offset=5,
		source=source,
		render_mode='canvas',
		text_font_size="7pt"
	)
	labels2 = LabelSet(
		x='bins',
		y=values2["title"],
		text=values2["title"],
		level='glyph',
		x_offset=-2,
		y_offset=5,
		source=source,
		render_mode='canvas',
		text_font_size="7pt"
	)

	plot.add_layout(labels1)
	plot.add_layout(labels2)

	return plot

def epsilons_plot(title):
	epsilons = ['0.01', '0.025', '0.05', '0.075', '0.1', '0.25', '0.5', '0.6', '0.693', '0.7', '0.8', '0.9', '1']
	noises = ['1959', '851', '469', '337', '270', '146', '103', '95', '90', '90', '86', '83', '80']
	totals = ['2039', '931', '548', '417', '350', '225', '182', '175', '170', '170', '165', '162', '160']

	lineSize = 2
	circleSize = 3

	plot = figure(title=title, x_axis_label="Epsilon value", y_axis_label="Records number", plot_width=300, plot_height=200)
	plot.xaxis.axis_label_text_font = "normal"
	plot.yaxis.axis_label_text_font = "normal"
	plot.title.align = "center"
	plot.title.offset = 20
	plot.title.vertical_align = "top"

	rNoises = plot.line(epsilons, noises, line_width=lineSize)
	rNoisesMarkers = plot.circle(epsilons, noises, size=circleSize)

	rTotals = plot.line(epsilons, totals, line_width=lineSize, color="dodgerblue")
	rTotalsMarkers = plot.circle(epsilons, totals, size=circleSize, color="dodgerblue")

	plot.add_layout(Legend(items=[("Noise records", [rNoises, rNoisesMarkers]), ("Total records", [rTotals, rTotalsMarkers])]))

	plot.legend.background_fill_alpha = 0.0
	plot.legend.border_line_color = None
	plot.legend.label_text_font_size = "8pt"

	return plot

def plot_strawman(title):
	categories = ["1M 64 threads", "4KB 64 threads", "1M 4KB"]
	factors = [
		("1M 64 threads", "1KB"),
		("1M 64 threads", "4KB"),
		("1M 64 threads", "16KB"),
		#
		("4KB 64 threads", "100K"),
		("4KB 64 threads", "1M"),
		("4KB 64 threads", "10M"),
		#
		("1M 4KB", "16"),
		("1M 4KB", "32"),
		("1M 4KB", "64"),
	]

	x = [
		3884,
		15000,
		48000,
		#
		922,
		15000,
		147000,
		#
		22000,
		15000,
		15000,
	]

	plot = figure(x_range=FactorRange(*factors), y_axis_type="log", y_range=(10, max(x)*1.3), title=title, plot_height=200, plot_width=300, toolbar_location=None, tools="")

	# put your own colors in RGB hex format
	colors = ["#6d8ef9", "#7460e6", "#cc397e"]

	plot.vbar(x=factors, fill_color=factor_cmap('x', palette=colors, factors=categories, end=1), top=x, width=0.9, alpha=0.5, bottom=0.1)

	plot.xaxis.major_label_orientation = 1
	plot.xgrid.grid_line_color = None
	plot.title.align = "center"
	plot.title.offset = 20
	plot.title.vertical_align = "top"

	return plot


colors = {
	"turquoise": [
		(49, 87, 84),
		(79, 123, 120),
		(109, 153, 150),
		(133, 179, 175),
		(161, 206, 202)
	],
	"green": [
		(104, 137, 101),
		(127, 162, 124),
		(148, 188, 145),
		(174, 211, 170),
		(199, 231, 196)
	],
	"blue": [
		(80, 112, 139),
		(101, 136, 165),
		(131, 166, 196),
		(151, 184, 212),
		(187, 216, 240)
	],
	"dusty": [
		(92, 121, 133),
		(128, 155, 167),
		(149, 178, 191),
		(172, 200, 211),
		(190, 214, 224)
	],
	"rose": [
		(143, 54, 71),
		(156, 71, 87),
		(171, 95, 109),
		(203, 127, 141),
		(238, 179, 190)
	],
	"terracotta": [
		(176, 104, 90),
		(207, 134, 119),
		(223, 156, 142),
		(236, 177, 165),
		(233, 194, 185)
	],
	"maroon": [
		(115, 75, 92),
		(144, 102, 120),
		(158, 117, 134),
		(175, 137, 153),
		(199, 157, 175)
	],
	"ochre": [
		(184, 125, 60),
		(193, 142, 86),
		(197, 155, 107),
		(211, 178, 141),
		(228, 199, 167)
	],
	"violet": [
		(114, 90, 139),
		(140, 117, 165),
		(155, 127, 184),
		(176, 152, 201),
		(204, 184, 224)
	],
	"lilac": [
		(75, 78,115),
		(96, 99, 139),
		(118, 121, 162),
		(144, 147, 192),
		(160, 163, 205)
	]
}

data = [
	{
		"title": "Epsilon",
		"bins": ["0.1", "0.5", "ln(2)", "1.0", "ln(3)"],
		"values": [2293, 868, 840, 816, 783],
		"color": colors["blue"]
	},
	{
		"title": "Scalability",
		"bins": ["8", "16", "32", "64", "96"],
		"values1": {
			"title": "Gamma method",
			"data": [4576, 2618, 1571, 840, 1012]
		},
		"values2": {
			"title": "No Gamma method",
			"data": [7626, 6967, 4874, 4699, 5857]
		},
		"color1": colors["rose"],
		"color2": colors["maroon"]
	},
	{
		"title": "Selectivity",
		"bins": ["0.1%", "0.25%", "0.5%", "1%", "2%"],
		"values": [393, 605, 840, 1216, 2139],
		"color": colors["violet"]
	},
	{
		"title": "Record Size",
		"bins": ["1KB", "4KB", "16KB"],
		"values": [323, 840, 3610],
		"color": colors["dusty"]
	},
	{
		"title": "Data Size",
		"bins": ["100K", "1M", "10M"],
		"values": [294, 840, 6442],
		"color": colors["turquoise"]
	},
	{
		"title": "Domain Size",
		"bins": ["100", "10K", "1M"],
		"values": [5396, 840, 1030],
		"color": colors["green"]
	},
	{
		"title": "Data Distribution",
		"bins": ["CA empl.", "Uniform", "PUMS"],
		"values": [1162, 840, 1675],
		"color": colors["ochre"]
	},
	{
		"title": "Query Distribution",
		"bins": ["Range 1K", "Follow", "Uniform"],
		"values": [1278, 1675, 969],
		"color": colors["terracotta"]
	},
	{
		"title": "Mechanism",
		"bins": ["MySQL", "PostgreSQL", "DP-ORAM", "Linear Scan"],
		"values": [97, 220, 840, 1000],
		"color": colors["lilac"]
	},
	{
		"special": "epsilons",
		"title": "Epsilon effect",
	},
	{
		"special": "strawman",
		"title": "Linear Scan",
	},
]

# plots = []
# for piece in data:
# 	if "values" in piece:
# 		plot = make_barchart(piece["bins"], piece["values"], piece["title"], piece["color"])
# 	else:
# 		plot = make_barchart_double(piece["bins"], piece["values1"], piece["values2"], piece["title"], piece["color1"], piece["color2"])
# 	plots += [plot]

# grid = gridplot(plots, ncols=3, plot_width=350, plot_height=200)

# show(grid)

doc = ss.Document()

layout = ss.VBoxLayout()
count = 0
layout_horizontal = ss.HBoxLayout()

for piece in data:
	if count == 3 or count == 8:
		layout.addLayout(layout_horizontal)
		layout_horizontal = ss.HBoxLayout()

	if "values" in piece:
		plot = make_barchart(piece["bins"], piece["values"], piece["title"], piece["color"].copy())
	elif "values1" in piece:
		plot = make_barchart_double(piece["bins"], piece["values1"], piece["values2"], piece["title"], piece["color1"].copy(), piece["color2"].copy())
	elif "special" in piece and piece["special"] == "epsilons":
		plot = epsilons_plot(piece["title"])
	elif "special" in piece and piece["special"] == "strawman":
		plot = plot_strawman(piece["title"])
	plot.output_backend="svg"
	name = f"../output/{piece['title'].lower().replace(' ', '-').replace('(', '').replace(')', '')}.svg"
	export_svgs(plot, filename=name)

	layout_horizontal.addSVG(name, alignment=ss.AlignTop|ss.AlignHCenter)

	count += 1

layout.addLayout(layout_horizontal)
doc.setLayout(layout)
doc.save("../output/plots.svg")
