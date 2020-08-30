#!/usr/bin/env python3

def main():

	import datetime
	import re
	processor = re.compile("\[(\d+)/(\d+)/(\d+) (\d+):(\d+):(\d+)\]")
	
	def extractDate(line):
		match = processor.search(line)
		day = match.group(1)
		month = match.group(2)
		year = match.group(3)
		hour = match.group(4)
		minute = match.group(5)
		second = match.group(6)
		return datetime.datetime(year=int(year), month=int(month), day=int(day), hour=int(hour), minute=int(minute), second=int(second))
	
	for wiki in ["Experiments-Full", "Experiments"]:
		start = None
		total = datetime.timedelta(0)
		with open(f"../../dp-oram-paper.wiki/{wiki}.md") as fp:
			while True:
				line = fp.readline() 
				if not line:
					break

				if "INFO: Generating indices..." in line:
					start = extractDate(line)
				
				if "INFO: Log written to" in line:
					end = extractDate(line)
					elapsed = end-start
					total += elapsed
		
		print(f"{wiki}: {total}")

if __name__ == "__main__":
	main()
