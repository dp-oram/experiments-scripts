#!/usr/bin/env python3

from bokeh.io import show, export_svgs
from bokeh.models import ColumnDataSource, LabelSet, Legend, FactorRange, FuncTickFormatter
from bokeh.plotting import figure
from bokeh.layouts import gridplot
from bokeh.transform import dodge, factor_cmap
import svg_stack as ss
import subprocess

default_height = 200
default_width = 300

export_to_figures = True
# export_to_figures = False

no_title = True

def configure_plot(plot, title):
	if title == "Epsilon effect" or title == "Scalability":
		plot.legend.background_fill_alpha = 0.0
		plot.legend.border_line_color = None
		plot.legend.label_text_font_size = "8pt"
		plot.legend.label_text_font = "libertine"

	plot.title.align = "center"
	plot.title.offset = 20
	plot.title.vertical_align = "top"
	plot.title.text_font = "libertine"
	plot.xaxis.major_label_text_font = "libertine"
	plot.yaxis.major_label_text_font = "libertine"

	if no_title:
		plot.title = None

	plot.yaxis[0].axis_label_standoff=10
	if title == "Epsilon effect":
		plot.yaxis[0].axis_label="Number of records"
	elif title == "Linear Scan":
		plot.yaxis[0].axis_label="Query overhead in s"
	else:
		plot.yaxis[0].axis_label="Query overhead in ms"

	return plot

def make_barchart(bins, values, title, color, width, height):

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

	plot = figure(x_range=bins, y_range=(0, max(values)*coefficient), title=title, toolbar_location=None, tools="", plot_width=width, plot_height=height)

	plot.vbar(x="bins", top="values", width=0.8, color="color", legend_field="bins", source=source, alpha=0.8)

	plot.xgrid.grid_line_color = None
	plot.legend.orientation = "horizontal"
	plot.legend.location = "top_center"
	plot.legend.visible = False

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

	# hack!
	if title == "Mechanism":
		plot.xaxis.major_label_orientation = 1

	return plot

def make_barchart_double(bins, values1, values2, title, color1, color2, width, height):

	source = ColumnDataSource(
		data={
			'bins': bins,
			values1["title"]: values1["data"],
			values2["title"]: values2["data"],
			"color1": ["#%02x%02x%02x" % x for x in color1],
			"color2": ["#%02x%02x%02x" % x for x in color2],
		}
	)

	plot = figure(x_range=bins, y_range=(0, max(max(values1["data"], values2["data"]))*1.4), title=title, toolbar_location=None, tools="", plot_width=width, plot_height=height)

	plot.vbar(x=dodge('bins', -0.2, range=plot.x_range), top=values1["title"], width=0.4, source=source, color="color1", legend_label=values1["title"], alpha=0.8)
	plot.vbar(x=dodge('bins', +0.2, range=plot.x_range), top=values2["title"], width=0.4, source=source, color="color2", legend_label=values2["title"], alpha=0.8)

	plot.x_range.range_padding = 0.1
	plot.xgrid.grid_line_color = None
	plot.legend.location = "top_center"
	plot.legend.orientation = "horizontal"

	labels1 = LabelSet(
		x='bins',
		y=values1["title"],
		text=values1["title"],
		level='glyph',
		x_offset=-30,
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
		x_offset=5,
		y_offset=5,
		source=source,
		render_mode='canvas',
		text_font_size="7pt"
	)

	plot.add_layout(labels1)
	plot.add_layout(labels2)

	return plot

def epsilons_plot(title, colors, width, height):
	epsilons = ['0.01', '0.025', '0.05', '0.075', '0.1', '0.25', '0.5', '0.6', '0.693', '0.7', '0.8', '0.9', '1']
	noises = ['1959', '851', '469', '337', '270', '146', '103', '95', '90', '90', '86', '83', '80']
	totals = ['2039', '931', '548', '417', '350', '225', '182', '175', '170', '170', '165', '162', '160']

	lineSize = 2
	circleSize = 3

	plot = figure(
		title=title,
		plot_width=width,
		plot_height=height
	)

	rNoises = plot.line(epsilons, noises, line_width=lineSize, color="#%02x%02x%02x" % colors[0])
	rNoisesMarkers = plot.circle(epsilons, noises, size=circleSize, color="#%02x%02x%02x" % colors[0])

	rTotals = plot.line(epsilons, totals, line_width=lineSize, color="#%02x%02x%02x" % colors[1])
	rTotalsMarkers = plot.circle(epsilons, totals, size=circleSize, color="#%02x%02x%02x" % colors[1])

	plot.add_layout(Legend(items=[("Noise records    ", [rNoises, rNoisesMarkers]), ("Total records    ", [rTotals, rTotalsMarkers])]))

	return plot

def plot_strawman(title, colors, width, height):
	categories = ["Record size", "Data size", "Threads"]
	factors = [
		(categories[0], "1KB"),
		(categories[0], "4KB"),
		(categories[0], "16KB"),
		#
		(categories[1], "100K"),
		(categories[1], "1M"),
		(categories[1], "10M"),
		#
		(categories[2], "16"),
		(categories[2], "32"),
		(categories[2], "64"),
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

	del colors[1]
	del colors[2]

	plot = figure(x_range=FactorRange(*factors), y_axis_type="log", y_range=(10, max(x)*5), title=title, plot_height=height, plot_width=width, toolbar_location=None, tools="")

	plot.vbar(x=factors, fill_color=factor_cmap('x', palette=["#%02x%02x%02x" % c for c in colors], factors=categories, end=1), top=x, width=0.9, alpha=0.8, bottom=0.1)

	labels = LabelSet(
		x="factors",
		y="x",
		text='labels',
		level='glyph',
		x_offset=-10,
		y_offset=5,
		source=ColumnDataSource(
			data=dict(
				x=x,
				factors=factors,
				labels=[f"{round(value / 1000, 1) if value < 4000 else int(value / 1000)} s" for value in x]
			)
		),
		render_mode='canvas',
		text_font_size="8pt"
	)

	plot.add_layout(labels)

	plot.xaxis.major_label_orientation = 1
	plot.xgrid.grid_line_color = None
	plot.xaxis.group_text_font = "libertine"

	plot.yaxis.formatter = FuncTickFormatter(code='''
return 10 +
	(Math.log10(tick).toString()
	.split('')
	.map(function (d) { return d === '-' ? '⁻' : '⁰¹²³⁴⁵⁶⁷⁸⁹'[+d]; })
	.join(''));
''')

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
	],
	"orange": [
		(204, 125, 74),
		(215, 152, 111),
		(225, 169, 134),
		(239, 195, 168),
		(254, 217, 194)
	],
	"storm": [
		(55, 67, 87),
		(73, 87, 109),
		(108, 124, 151),
		(141, 156, 182),
		(177, 191, 215)
	],
	"greyscale": [
		(62, 62, 62),
		(110, 110, 110),
		(161, 161, 161)
	],
}

data = [
	{
		"title": "Epsilon",
		"bins": ["0.1", "0.5", "ln(2)", "1.0", "ln(3)"],
		"values": [2293, 868, 840, 816, 783],
		"color": colors["blue"],
		"width": default_width,
		"height": default_height
	},
	{
		"title": "Scalability",
		"bins": ["8", "16", "32", "64", "96"],
		"values1": {
			"title": "Gamma method       ",
			"data": [4576, 2618, 1571, 840, 1012]
		},
		"values2": {
			"title": "No Gamma method",
			"data": [7626, 6967, 4874, 4699, 5857]
		},
		"color1": colors["dusty"],
		"color2": colors["turquoise"],
		"width": default_width*2,
		"height": default_height
	},
	{
		"title": "Selectivity",
		"bins": ["0.1%", "0.25%", "0.5%", "1%", "2%"],
		"values": [393, 605, 840, 1216, 2139],
		"color": colors["green"],
		"width": default_width*2,
		"height": default_height
	},
	{
		"title": "Record Size",
		"bins": ["1KB", "4KB", "16KB"],
		"values": [323, 840, 3610],
		"color": colors["ochre"],
		"width": default_width,
		"height": default_height
	},
	{
		"title": "Data Size",
		"bins": ["100K", "1M", "10M"],
		"values": [294, 840, 6442],
		"color": colors["orange"],
		"width": default_width,
		"height": default_height
	},
	{
		"title": "Domain Size",
		"bins": ["100", "10K", "1M"],
		"values": [5396, 840, 1030],
		"color": colors["terracotta"],
		"width": default_width,
		"height": default_height
	},
	{
		"title": "Data Distribution",
		"bins": ["CA empl.", "Uniform", "PUMS"],
		"values": [1162, 840, 1675],
		"color": colors["rose"],
		"width": int(default_width*1.2),
		"height": default_height
	},
	{
		"title": "Query Distribution",
		"bins": ["Range 1K", "Follow", "Uniform"],
		"values": [1278, 1675, 969],
		"color": colors["maroon"],
		"width": int(default_width*1.2),
		"height": default_height
	},
	{
		"title": "Mechanism",
		"bins": ["MySQL", "PostgreSQL", "Epsolute", "Linear Scan"],
		"values": [97, 220, 840, 2000],
		"color": colors["violet"],
		"width": int(default_width*(0.33/0.5)),
		"height": default_height
	},
	{
		"special": "epsilons",
		"title": "Epsilon effect",
		"color": (colors["lilac"][0], colors["lilac"][4]),
		"width": default_width,
		"height": default_height
	},
	{
		"special": "strawman",
		"title": "Linear Scan",
		"color": colors["storm"],
		"width": int(default_width*(0.66/0.5)),
		"height": default_height
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

def export_pdf(title, put_to_paper):
	subprocess.Popen(
		[
			"/Applications/Inkscape.app/Contents/MacOS/inkscape",
			"-D",
			"-T",
			f"../output/{title}.svg",
			"-o",
			f"../output/{title}.pdf"
		],
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE
	).communicate()

	if put_to_paper:
		subprocess.Popen(["cp", f"../output/{title}.pdf", "../../dp-oram-paper/document/graphics"]).communicate()


def export_pdf_latex(title, put_to_paper):
	subprocess.Popen(
		[
			"/Applications/Inkscape.app/Contents/MacOS/inkscape",
			"-D",
			f"../output/{title}.svg",
			"-o",
			f"../output/{title}.pdf",
			"--export-latex"
		],
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE
	).communicate()

	# FIXES
	with open(f"../output/{title}.pdf_tex", "r") as file :
		filedata = file.read()

		# superscripts
		chars = "⁰¹²³⁴⁵⁶⁷⁸⁹"
		for i in range(len(chars)):
			filedata = filedata.replace(f"10{chars[i]}", f"$10^{i}$")

		# extra pages
		from PyPDF2 import PdfFileReader
		pdf = PdfFileReader(open(f"../output/{title}.pdf", "rb"))
		num = pdf.getNumPages()

		# print(f"{num} pages in {title}")
		for page in range(num + 1, 50):
			filedata = filedata.replace(f"\\includegraphics[width=\\unitlength,page={page}]{{{title}.pdf}}", "")

	with open(f"../output/{title}.pdf_tex", "w") as file:
		file.write(filedata)

	if put_to_paper:
		subprocess.Popen(["cp", f"../output/{title}.pdf", "../../dp-oram-paper/document/graphics"]).communicate()
		subprocess.Popen(["cp", f"../output/{title}.pdf_tex", "../../dp-oram-paper/document/figures/pdf_tex"]).communicate()

	if export_to_figures:
		f = open(f"../../dp-oram-paper/document/figures/fig-{title}.tex", "w+")
		f.write(f"""
\\begin{{figure}}
	\small
	\centering
	\def\svgwidth{{0.5\columnwidth}}
	\input{{figures/pdf_tex/{title}.pdf_tex}}
\end{{figure}}
""")
		f.close()
		print(f"\includeExperimentPlot{{\\normalsize}}{{0.5}}{{{title}}}{{{title}}}")

doc = ss.Document()

layout = ss.VBoxLayout()
count = 0
layout_horizontal = ss.HBoxLayout()

for piece in data:
	if count == 3 or count == 8:
		layout.addLayout(layout_horizontal)
		layout_horizontal = ss.HBoxLayout()

	plot = None
	if "values" in piece:
		plot = make_barchart(piece["bins"], piece["values"], piece["title"], piece["color"].copy(), piece["width"], piece["height"])
	elif "values1" in piece:
		plot = make_barchart_double(piece["bins"], piece["values1"], piece["values2"], piece["title"], piece["color1"].copy(), piece["color2"].copy(), piece["width"], piece["height"])
	elif "special" in piece and piece["special"] == "epsilons":
		plot = epsilons_plot(piece["title"], piece["color"], piece["width"], piece["height"])
	elif "special" in piece and piece["special"] == "strawman":
		plot = plot_strawman(piece["title"], piece["color"].copy(), piece["width"], piece["height"])
	plot = configure_plot(plot, piece["title"])
	plot.output_backend="svg"
	title_sanitized = piece['title'].lower().replace(' ', '-').replace('(', '').replace(')', '')
	name = f"../output/{title_sanitized}.svg"
	export_svgs(plot, filename=name)
	# export_pdf_latex(title_sanitized, True)
	export_pdf(title_sanitized, True)

	layout_horizontal.addSVG(name, alignment=ss.AlignTop|ss.AlignHCenter)

	count += 1

layout.addLayout(layout_horizontal)
doc.setLayout(layout)
doc.save("../output/plots.svg")

# export_pdf_latex("plots", False)
