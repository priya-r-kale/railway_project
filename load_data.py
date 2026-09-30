import csv
import sys
import pymysql

DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = "admin@123"
DB_NAME = "indian_railway"
DB_PORT = 3306


def setup_database(cur):
    print("Creating database 'indian_railway' if missing...")
    cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME};")
    cur.execute(f"USE {DB_NAME};")

    try:
        with open("schema.sql", "r", encoding="utf-8") as f:
            print("Applying schema.sql to create tables...")
            schema_sql = f.read()
            for statement in schema_sql.split(";"):
                statement = statement.strip()
                if statement:
                    cur.execute(statement)
        print("Tables created successfully.")
    except FileNotFoundError:
        print("Warning: schema.sql file not found.")


def run_sql_file(cur, filename):
    print(f"\n--- Running {filename} ---")
    try:
        with open(filename, "r", encoding="utf-8") as f:
            sql_content = f.read()
            statements = [s.strip() for s in sql_content.split(";") if s.strip()]
            
            for stmt in statements:
                lines = [line for line in stmt.split("\n") if not line.strip().startswith("--")]
                clean_stmt = " ".join(lines).strip()
                
                if not clean_stmt or clean_stmt.upper().startswith("USE"):
                    continue
                
                cur.execute(clean_stmt)
                
                if clean_stmt.upper().startswith("SELECT"):
                    results = cur.fetchall()
                    print(f"\nQuery: {clean_stmt[:60]}...")
                    print(f"Returned {len(results)} rows:")
                    for row in results[:5]:
                        print(f"  {row}")
    except FileNotFoundError:
        print(f"File {filename} not found.")
    except Exception as e:
        print(f"Error executing {filename}: {e}")


def load_csv(cur, table, path, columns, batch_size=5000):
    try:
        with open(path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            placeholders = ",".join(["%s"] * len(columns))
            col_list = ",".join(columns)
            sql = f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})"
            batch = []
            count = 0
            for row in reader:
                values = [row[c] if row[c] != "" else None for c in columns]
                batch.append(values)
                if len(batch) >= batch_size:
                    cur.executemany(sql, batch)
                    count += len(batch)
                    batch = []
            if batch:
                cur.executemany(sql, batch)
                count += len(batch)
        print(f"  {table}: inserted {count} rows")
    except FileNotFoundError:
        print(f"  Error: {path} not found.")


def main():
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT,
            charset="utf8mb4",
            autocommit=True
        )
        cur = conn.cursor()
        print("Connected to MySQL Server successfully!")
    except pymysql.Error as e:
        sys.exit(f"Database connection failed: {e}")

    setup_database(cur)

    print("\nLoading stations...")
    load_csv(cur, "stations", "stations.csv",
             ["station_id", "station_code", "station_name"])

    print("Loading trains...")
    load_csv(cur, "trains", "trains.csv",
             ["train_id", "train_number", "train_name", "train_type",
              "source_station_code", "source_station_name",
              "destination_station_code", "destination_station_name",
              "departure_time", "arrival_time", "distance_km",
              "running_days", "data_source"])

    print("Loading train_import...")
    load_csv(cur, "train_import", "train_import.csv",
             ["train_number", "train_name", "train_type",
              "source_station_code", "source_station_name",
              "destination_station_code", "destination_station_name",
              "departure_time", "arrival_time", "distance_km",
              "running_days", "data_source"])

    print("Loading train_routes...")
    load_csv(cur, "train_routes", "train_routes.csv",
             ["route_id", "train_id", "station_id", "stop_number",
              "arrival_time", "departure_time", "halt_minutes",
              "distance_from_source_km"], batch_size=10000)

    # Executing extra scripts directly
    run_sql_file(cur, "data_sources.sql")
    run_sql_file(cur, "validation.sql")

    conn.close()
    print("\nDone! Entire setup, import, and validation complete.")


if __name__ == "__main__":
    main()