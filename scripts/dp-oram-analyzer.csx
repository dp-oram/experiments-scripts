#!/usr/bin/env dotnet script

using System.Text.RegularExpressions;

var SEED = new Random().Next();

if (Args.Count >= 2)
{
	SEED = Int32.Parse(Args[1]);
}

async Task<(int real, int padding, int noise, int total)> RunProcessAsync(Dictionary<string, string> parameters)
{
	var directory = Path.Combine(Directory.GetCurrentDirectory(), "../../dp-oram/dp-oram");

	ProcessStartInfo start = new ProcessStartInfo
	{
		FileName = Path.Combine(directory, "bin/main"),
		Arguments = parameters.Aggregate("", (current, next) => current + $" --{next.Key} {next.Value}"),
		UseShellExecute = false,
		CreateNoWindow = true,
		WorkingDirectory = directory,
		RedirectStandardOutput = true,
		RedirectStandardError = true
	};

	using (Process process = Process.Start(start))
	{
		process.WaitForExit();

		using (StreamReader reader = process.StandardOutput)
		{
			string stderr = await process.StandardError.ReadToEndAsync();
			string result = await reader.ReadToEndAsync();

			if (string.IsNullOrEmpty(stderr) && process.ExitCode == 0)
			{
				// success
				var regex = new Regex(@".; \((\d+)\+(\d+)\+(\d+)=(\d+)\) records per query");
				var match = regex.Match(result);
				if (match.Success)
				{
					return (
						real: Int32.Parse(match.Groups[1].Value),
						padding: Int32.Parse(match.Groups[2].Value),
						noise: Int32.Parse(match.Groups[3].Value),
						total: Int32.Parse(match.Groups[4].Value)
					);
				}
			}

			return default;
		}
	}
}

Console.WriteLine($"SEED: {SEED}");
Console.WriteLine();

Console.WriteLine($"{"ORAMs",-10}{"Buckets",-10}{"beta",-10}{"epsilon",-10}Results per ORAM (real+padding+noise=total)");
Console.WriteLine();

foreach (var n in new List<int> { 1, 2, 4, 8, 16, 32, 48, 64, 96 })
{
	foreach (var buckets in new List<int> { 16, 256, 4096, 65536, 1048576 })
	{
		foreach (var beta in new List<int> { 10, 15, 20, 25 })
		{
			foreach (var epsilon in new List<int> { 1, 5, 10, 20 })
			{
				var result = await RunProcessAsync(new Dictionary<string, string>{
					{ "generateIndices", true.ToString() },
					{ "readInputs", true.ToString() },
					{ "parallel", true.ToString() },
					{ "oramsNumber", n.ToString() },
					{ "bucketsNumber", buckets.ToString() },
					{ "virtualRequests", true.ToString() },
					{ "beta", beta.ToString() },
					{ "epsilon", epsilon.ToString() },
					{ "count", 10000.ToString() },
					{ "verbosity", "TRACE" },
					{ "fileLogging", true.ToString() },
					{ "seed", SEED.ToString() }
				});

				Console.WriteLine($"{n,-10}{buckets,-10}{$"2^{{-{beta}}}",-10}{epsilon,-10}{result.real} + {result.padding} + {result.noise} = {result.total}");
			}
		}

		Console.WriteLine();
	}
}
