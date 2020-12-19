#!/usr/bin/env python3

from bokeh.io import show
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from bokeh.layouts import gridplot
from bokeh.transform import dodge

def make_barchart(bins, values, title, color):

	if len(values) == 3:
		del color[1]
		del color[2]
	if len(values) == 4:
		del color[2]

	source = ColumnDataSource(data=dict(bins=bins, values=values, color=["#%02x%02x%02x" % x for x in color]))

	plot = figure(x_range=bins, y_range=(0,max(values)*1.1), title=title, toolbar_location=None, tools="")

	plot.vbar(x="bins", top="values", width=0.8, color="color", legend_field="bins", source=source, alpha=0.8)

	plot.xgrid.grid_line_color = None
	plot.legend.orientation = "horizontal"
	plot.legend.location = "top_center"
	plot.legend.visible = False

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

	plot = figure(x_range=bins, y_range=(0, max(max(values1["data"], values2["data"]))*1.1), title=title, toolbar_location=None, tools="")

	plot.vbar(x=dodge('bins', -0.2, range=plot.x_range), top=values1["title"], width=0.4, source=source, color="color1", legend_label=values1["title"])
	plot.vbar(x=dodge('bins', +0.2, range=plot.x_range), top=values2["title"], width=0.4, source=source, color="color2", legend_label=values2["title"])

	plot.x_range.range_padding = 0.1
	plot.xgrid.grid_line_color = None
	plot.legend.location = "top_right"
	plot.legend.orientation = "vertical"
	plot.legend.background_fill_alpha = 0.5


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
		"bins": ["CA employees", "Uniform", "PUMS"],
		"values": [1162, 840, 1675],
		"color": colors["ochre"]
	},
	{
		"title": "Query Distribution (PUMS California)",
		"bins": ["Equi-range 1K", "Follow", "Uniform"],
		"values": [1278, 1675, 969],
		"color": colors["terracotta"]
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
		"title": "Mechanism",
		"bins": ["MySQL", "PostgreSQL", "DP-ORAM"], # , "Linear Scan"],
		"values": [97, 220, 840], # , 15000],
		"color": colors["lilac"]
	}
]

plots = []
for piece in data:
	if "values" in piece:
		plot = make_barchart(piece["bins"], piece["values"], piece["title"], piece["color"])
	else:
		plot = make_barchart_double(piece["bins"], piece["values1"], piece["values2"], piece["title"], piece["color1"], piece["color2"])
	plots += [plot]

grid = gridplot(plots, ncols=3, plot_width=350, plot_height=200)

show(grid)

# grid.output_backend="svg"
# export_svgs(plot, filename="plot.svg")
