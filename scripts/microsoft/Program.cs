using System;
using System.Data;
using System.Data.SqlClient;
using System.IO;
using System.Collections.Generic;

namespace microsoft
{
	class Program
	{
		static private readonly string _connectionString = "Data Source=cs-dmytro.bu.edu;Initial Catalog=master;User Id=sa;Password=Password123!;Column Encryption Setting=Enabled;";
		static private readonly string _dataFile = "//Mac/Home/Desktop/ms-data.txt";

		static void ExecNonQuery(SqlCommand sqlCmd)
		{
			using (sqlCmd.Connection = new SqlConnection(_connectionString))
			{
				sqlCmd.Connection.Open();
				sqlCmd.ExecuteNonQuery();
			}
		}

		static void Main()
		{
			// Windows Certificate Store Vault Provider is initialized automatically

			// Recreate the table
			ExecNonQuery(new SqlCommand("DROP TABLE IF EXISTS [dbo].[ranges];"));
			ExecNonQuery(new SqlCommand(@"
				CREATE TABLE [dbo].[ranges](
					[point] [int] ENCRYPTED WITH (
						COLUMN_ENCRYPTION_KEY = WinCEKiMac,
						ENCRYPTION_TYPE = DETERMINISTIC,
						ALGORITHM = 'AEAD_AES_256_CBC_HMAC_SHA_256'
					) NOT NULL
				) ON [PRIMARY];
			"));

			var points = new List<int>();
			var ranges = new List<(int, int)>();
			using (StreamReader sr = File.OpenText(_dataFile))
			{
				int pointsNum = int.Parse(sr.ReadLine());
				int rangesNum = int.Parse(sr.ReadLine());

				for (int i = 0; i < pointsNum; i++)
				{
					points.Add(int.Parse(sr.ReadLine()));
				}

				for (int i = 0; i < rangesNum; i++)
				{
					var range = sr.ReadLine().Split(' ');
					ranges.Add((int.Parse(range[0]), int.Parse(range[1])));
				}
			}

			Console.WriteLine("Construction stage");

			var insertion = System.Diagnostics.Stopwatch.StartNew();
			foreach (var point in points)
			{
				InsertPoint(point);
			}
			insertion.Stop();

			Console.WriteLine("Queries stage");

			var queries = System.Diagnostics.Stopwatch.StartNew();
			foreach (var range in ranges)
			{
				RangeQuery(range.Item1, range.Item2);
			}
			queries.Stop();

			Console.WriteLine($"For MS: inserted in {insertion.ElapsedMilliseconds} ms, queries in {queries.ElapsedMilliseconds} ms");
			Console.WriteLine("Done. Press Enter to exit...");
			Console.ReadLine();
		}

		static void InsertPoint(int point)
		{
			string sqlCmdText = @"INSERT INTO [dbo].[ranges] (point) VALUES ( @point );";

			SqlCommand sqlCmd = new SqlCommand(sqlCmdText);

			SqlParameter paramPoint = new SqlParameter(@"@point", point);
			paramPoint.SqlDbType = SqlDbType.Int;
			paramPoint.Direction = ParameterDirection.Input;

			sqlCmd.Parameters.Add(paramPoint);

			ExecNonQuery(sqlCmd);
		}

		/// <summary>
		/// Return the number of points
		/// </summary>
		static int RangeQuery(int from, int to)
		{
			int result = 0;

			SqlCommand sqlCmd = new SqlCommand("SELECT [point] FROM [dbo].[ranges]", new SqlConnection(_connectionString));

			using (sqlCmd.Connection = new SqlConnection(_connectionString))
			{
				sqlCmd.Connection.Open();
				SqlDataReader reader = sqlCmd.ExecuteReader();

				if (reader.HasRows)
				{
					while (reader.Read())
					{
						int returned = (int)reader[0];

						if (returned >= from && returned <= to)
						{
							result++;
						}
					}
				}
			}

			return result;
		}
	}
}
