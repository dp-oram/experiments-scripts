#!/usr/bin/env dotnet script

#r "nuget: McMaster.Extensions.CommandLineUtils, 3.0.0"

using System.Text.RegularExpressions;
using McMaster.Extensions.CommandLineUtils;
// using System.ComponentModel.DataAnnotations;

[Command(
	Name = "dp-simulator",
	Description = "Script to run DP-ORAM protocol of different parameters"
// ShowInHelpText = true,
// UnrecognizedArgumentHandling = McMaster.Extensions.CommandLineUtils.UnrecognizedArgumentHandling.Throw,
// UsePagerForHelpText = false
)]
public class Program
{
	public static async Task<int> Entrypoint(string[] args)
		=> await CommandLineApplication.ExecuteAsync<Program>(args);

	[Option("--seed <SEED>", "Seed to use for pseudorandom operations", CommandOptionType.SingleValue)]
	public int Seed { get; } = new Random().Next();

	[Option("--count <COUNT>", "If supplied, will make the simulator to generate synthetic inputs, otherwise, will read inputs", CommandOptionType.SingleValue)]
	public int Count { get; } = 0;

	private async Task OnExecuteAsync()
	{
		Console.WriteLine($"Seed: {Seed}");
		Console.WriteLine($"Count: {Count}");
		Console.WriteLine();

		DeleteSimulatorCache();

		Console.WriteLine($"{"ORAMs",-10}{"Buckets",-10}{"beta",-10}{"epsilon",-10}Results per ORAM (real+padding+noise=total)");
		Console.WriteLine();

		// TODO parallel

		foreach (var n in new List<int> { 1, 2, 4, 8, 16, 32, 48, 64, 96 })
		{
			foreach (var buckets in new List<int> { 16, 256, 4096, 65536, 1048576 })
			{
				foreach (var beta in new List<int> { 20 })
				{
					foreach (var epsilon in new List<int> { 1 })
					{
						var result = await RunProcessAsync(new Dictionary<string, string>{
							{ "generateIndices", false.ToString() },
							{ "readInputs", (Count == 0).ToString() },
							{ "parallel", true.ToString() },
							{ "oramsNumber", n.ToString() },
							{ "oramStorage", "InMemory" },
							{ "bucketsNumber", buckets.ToString() },
							{ "virtualRequests", true.ToString() },
							{ "beta", beta.ToString() },
							{ "epsilon", epsilon.ToString() },
							{ "count", Count.ToString() },
							{ "verbosity", "TRACE" },
							{ "fileLogging", true.ToString() },
							{ "seed", Seed.ToString() }
						});

						Console.WriteLine($"{n,-10}{buckets,-10}{$"2^{{-{beta}}}",-10}{epsilon,-10}{result.real} + {result.padding} + {result.noise} = {result.total}");
					}
				}
			}

			Console.WriteLine();
			DeleteSimulatorCache();
		}
	}

	private void DeleteSimulatorCache()
	{
		foreach (var file in new DirectoryInfo("../../dp-oram/dp-oram/storage-files").GetFiles())
		{
			file.Delete();
		}
	}

	private async Task<(int real, int padding, int noise, int total)> RunProcessAsync(Dictionary<string, string> parameters)
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
}

return await Program.Entrypoint(Args.ToArray());
