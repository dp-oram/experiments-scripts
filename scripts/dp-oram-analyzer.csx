#!/usr/bin/env dotnet script

#r "nuget: McMaster.Extensions.CommandLineUtils, 3.0.0"

using System.Text.RegularExpressions;
using McMaster.Extensions.CommandLineUtils;
using System.Threading;

[Command(
	Name = "dp-simulator",
	Description = "Script to run DP-ORAM protocol of different parameters"
)]
public class Program
{
	public static async Task<int> Entrypoint(string[] args)
		=> await CommandLineApplication.ExecuteAsync<Program>(args);

	[Option("--seed <SEED>", "Seed to use for pseudorandom operations", CommandOptionType.SingleValue)]
	public int Seed { get; } = 1305;

	[Option("--count <COUNT>", "If supplied, will make the simulator to generate synthetic inputs, otherwise, will read inputs", CommandOptionType.SingleValue)]
	public int Count { get; } = 0;

	[Option("--input <INPUT>", "a portion of input file name, such as \"UNIFORM-100-1000000\" in \"dataset-UNIFORM-100-1000000.csv\"", CommandOptionType.SingleValue)]
	public string Input { get; } = "UNIFORM-1000000-10000";

	private async Task OnExecuteAsync()
	{
		var random = new Random(Seed);

		Console.WriteLine($"Seed: {Seed}");
		Console.WriteLine($"Count: {Count}");
		Console.WriteLine($"Input: {Input}");
		Console.WriteLine();

		DeleteSimulatorCache();

		Console.WriteLine($"{DateTime.Now.ToString("MM/dd/yyyy HH:mm:ss |"),-23}{"ORAMs",-10}{"Buckets",-10}{"beta",-10}{"epsilon",-10}{"gamma",-10}{"prune",-10}Results per ORAM (real+padding+noise=total)");
		Console.WriteLine();

		Func<int, int, int, double, bool, bool, Task<(int bucket, int beta, double epsilon, bool gamma, bool prune, string log)>> simulate =
			async (int n, int buckets, int beta, double epsilon, bool gamma, bool prune) =>
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
					{ "useGamma", gamma.ToString() },
					{ "queries", 20.ToString() },
					{ "count", Count.ToString() },
					{ "levels", (prune ? 0 : 256).ToString() },
					{ "verbosity", "TRACE" },
					{ "fileLogging", true.ToString() },
					{ "dataset", $"dataset-{Input}" },
					{ "queryset", $"queries-{Input}-0.5-follow" },
					{ "seed", Seed.ToString() }
				});

				var logMessage = $"{n,-10}{buckets,-10}{$"2^{{-{beta}}}",-10}{epsilon,-10}{gamma,-10}{prune,-10}{result.real / n} + {result.padding / n} + {result.noise / n} = {result.total / n}";
				return (buckets, beta, epsilon, gamma, prune, logMessage);
			};

		foreach (var n in new List<int> { 64 })
		{
			var tasks = new List<Task<(int bucket, int beta, double epsilon, bool gamma, bool prune, string log)>>();
			var firstRun = false;

			foreach (var buckets in new List<int> { 65536 })
			{
				foreach (var beta in new List<int> { 20 })
				{
					foreach (var epsilon in new List<double> { 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.6, 0.693, 0.7, 0.8, 0.9, 1.0, 1.1, 1.3, 1.5, 2.0, 5.0, 7.5, 10.0 })
					{
						foreach (var gamma in new List<bool> { true })
						{
							foreach (var prune in new List<bool> { false })
							{
								tasks.Add(Task.Run(async () =>
								{
									await Task.Delay(random.Next(0, 1000));
									return await simulate(n, buckets, beta, epsilon, gamma, prune);
								}));
								// if it is a first simulation in a batch, we need to wait for it to complete,
								// because it generates the files that other simulation rely on
								if (!firstRun)
								{
									await Task.WhenAll(tasks);
									firstRun = true;
								}
							}
						}
					}
				}
			}

			var results = await Task.WhenAll(tasks);
			results.OrderBy(r => r.bucket).ThenBy(r => r.beta).ThenBy(r => r.epsilon).ThenBy(r => r.gamma);

			foreach (var result in results)
			{
				Console.WriteLine($"{DateTime.Now.ToString("MM/dd/yyyy HH:mm:ss |"),-23}{result.log}");
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
		var paramString = parameters.Aggregate("", (current, next) => current + $" --{next.Key} {next.Value}");

		ProcessStartInfo start = new ProcessStartInfo
		{
			FileName = Path.Combine(directory, "bin/main"),
			Arguments = paramString,
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
					var regex = new Regex(@".; \((\d+)\+(\d+)\+(\d+)=(\d+)\) records / query");
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
				else
				{
					throw new Exception($"Execution failed for {paramString}. STDERR: {stderr}. STDOUT: {result}");
				}

				return default;
			}
		}
	}
}

return await Program.Entrypoint(Args.ToArray());
