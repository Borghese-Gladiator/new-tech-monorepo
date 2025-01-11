# DuckDB
DuckDB is an open-source, in-process SQL database management system designed for analytical workloads. Often referred to as the "SQLite for analytics," DuckDB is lightweight, embeddable, and optimized for fast query execution on large datasets.

It saves to an arbitrary file (eg: `my_database.duckdb`)

Features
1. **Embedded Design**  
   DuckDB is embedded directly into your application, eliminating the need for a separate server process. This reduces deployment complexity and makes it highly portable.

2. **Optimized for Analytical Workloads**  
   DuckDB excels at executing complex queries, especially those involving aggregations, joins, and filtering on large datasets.

3. **Columnar Storage**  
   DuckDB uses a columnar data layout, which improves performance for analytical queries by reducing the amount of data read into memory.

4. **SQL Compliance**  
   Supports a wide range of SQL functionality, including window functions, complex joins, subqueries, and Common Table Expressions (CTEs).

5. **Interoperability**  
   DuckDB can read and write common file formats such as CSV, Parquet, and JSON, making it easy to integrate with existing data workflows.

6. **Integration with Data Science Ecosystems**  
   DuckDB has seamless bindings for Python, R, and other programming languages, enabling smooth integration into data science and analytics pipelines.

7. **In-Memory and Disk Operations**  
   DuckDB can operate entirely in-memory for fast computations or use disk-based storage for larger datasets.

## Usage

Tables and Queries
```python
import duckdb

# Create an in-memory database
con = duckdb.connect()
# Create a table
con.execute("CREATE TABLE users (id INTEGER, name TEXT, age INTEGER)")
# Insert data
con.execute("INSERT INTO users VALUES (1, 'Alice', 30), (2, 'Bob', 25)")
# Query data
result = con.execute("SELECT * FROM users WHERE age > 25").fetchall()

print(result)  # Output: [(1, 'Alice', 30)]
```

File Access
```python
# Query a Parquet file
con.execute("SELECT * FROM 'data.parquet' WHERE value > 100")
```

DataFrames Integration
```python
import pandas as pd
import duckdb

# Create a DataFrame
df = pd.DataFrame({'id': [1, 2, 3], 'value': [10, 20, 30]})
# Query the DataFrame
result = duckdb.query("SELECT id, value FROM df WHERE value > 15").to_df()

print(result)
```

## Extensions
DuckDB's Python API provides functions for installing and loading extensions (which perform `INSTALL` and `LOAD` SQL commands, respectively)

```
con = duckdb.connect()
con.install_extension("spatial")
con.load_extension("spatial")
```

To load [community extensions](https://duckdb.org/community_extensions/), add `repository="community"`
```
con = duckdb.connect()
con.install_extension("h3", repository="community")
con.load_extension("h3")
```