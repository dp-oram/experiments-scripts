using System;
using System.Data;
using System.Data.SqlClient;
using System.IO;

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
						COLUMN_ENCRYPTION_KEY = WinCEK,
						ENCRYPTION_TYPE = DETERMINISTIC,
						ALGORITHM = 'AEAD_AES_256_CBC_HMAC_SHA_256'
					) NOT NULL
				) ON [PRIMARY];
			"));

			System.Diagnostics.Stopwatch insertion, queries;

			using (StreamReader sr = File.OpenText(_dataFile))
			{
				int points = int.Parse(sr.ReadLine());
				int ranges = int.Parse(sr.ReadLine());

				Console.WriteLine("Construction stage");

				insertion = System.Diagnostics.Stopwatch.StartNew();
				for (int i = 0; i < points; i++)
				{
					InsertPoint(int.Parse(sr.ReadLine()));
				}
				insertion.Stop();

				Console.WriteLine("Queries stage");

				queries = System.Diagnostics.Stopwatch.StartNew();
				for (int i = 0; i < ranges; i++)
				{
					var range = sr.ReadLine().Split(' ');
					RangeQuery(int.Parse(range[0]), int.Parse(range[1]));
				}
				queries.Stop();
			}

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
