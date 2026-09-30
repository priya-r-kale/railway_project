"""
Indian Railway Database Explorer — Streamlit app
"""
import os
import pandas as pd
import pymysql
import streamlit as st

st.set_page_config(page_title="Indian Railway Explorer", page_icon="🚆", layout="wide")

# Sidebar Configuration
with st.sidebar:
    st.header("🔌 Database connection")
    host = st.text_input("Host", value=os.environ.get("DB_HOST", "localhost"))
    port = st.number_input("Port", value=int(os.environ.get("DB_PORT", 3306)))
    user = st.text_input("User", value=os.environ.get("DB_USER", "root"))
    password = st.text_input("Password", value=os.environ.get("DB_PASSWORD", "admin@123"), type="password")
    database = st.text_input("Database", value=os.environ.get("DB_NAME", "indian_railway"))


def run_query(sql, params=None):
    """Executes a query using a clean, thread-safe connection."""
    conn = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            rows = cur.fetchall()
        return pd.DataFrame(rows)
    finally:
        conn.close()


# Test Connection
try:
    test_df = run_query("SELECT 1 AS test")
except Exception as e:
    st.error(f"Couldn't connect to MySQL: {e}")
    st.info("Fill in your connection details in the sidebar. "
            "Make sure MySQL is running and `load_data.py` has executed successfully.")
    st.stop()

st.title("🚆 Indian Railway Database Explorer")

tab_overview, tab_search, tab_stations, tab_quality = st.tabs(
    ["📊 Overview", "🔍 Search Trains", "🏢 Station Explorer", "✅ Data Quality"]
)

# ----------------------------------------------------------------------
# Overview
# ----------------------------------------------------------------------
with tab_overview:
    counts = run_query("""
        SELECT
          (SELECT COUNT(*) FROM trains) AS trains,
          (SELECT COUNT(*) FROM stations) AS stations,
          (SELECT COUNT(*) FROM train_routes) AS routes
    """).iloc[0]

    c1, c2, c3 = st.columns(3)
    c1.metric("Trains", f"{int(counts['trains']):,}")
    c2.metric("Stations", f"{int(counts['stations']):,}")
    c3.metric("Route stops", f"{int(counts['routes']):,}")

    st.subheader("Trains by category")
    by_type = run_query("""
        SELECT train_type, COUNT(*) AS count
        FROM trains
        GROUP BY train_type
        ORDER BY count DESC
    """)
    if not by_type.empty:
        st.bar_chart(by_type.set_index("train_type"))

    st.subheader("Busiest stations (most trains stopping)")
    busiest = run_query("""
        SELECT s.station_name, s.station_code, COUNT(*) AS trains_stopping
        FROM train_routes tr
        JOIN stations s ON s.station_id = tr.station_id
        GROUP BY s.station_id, s.station_name, s.station_code
        ORDER BY trains_stopping DESC
        LIMIT 15
    """)
    st.dataframe(busiest, use_container_width=True, hide_index=True)

# ----------------------------------------------------------------------
# Search trains
# ----------------------------------------------------------------------
with tab_search:
    st.subheader("Find a train")
    colq, colt = st.columns([3, 1])
    query = colq.text_input("Train number or name contains…", placeholder="e.g. RAJDHANI or 12951")
    types = run_query("SELECT DISTINCT train_type FROM trains ORDER BY train_type")["train_type"].tolist()
    type_filter = colt.selectbox("Category", ["All"] + types)

    sql = """
        SELECT train_id, train_number, train_name, train_type,
               source_station_name, destination_station_name,
               departure_time, arrival_time, distance_km, running_days
        FROM trains
        WHERE 1=1
    """
    params = []
    if query:
        sql += " AND (train_number LIKE %s OR train_name LIKE %s)"
        params += [f"%{query}%", f"%{query}%"]
    if type_filter != "All":
        sql += " AND train_type = %s"
        params.append(type_filter)
    sql += " ORDER BY train_number LIMIT 200"

    results = run_query(sql, params)
    st.caption(f"{len(results)} result(s) shown (max 200)")
    st.dataframe(results, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("View full route for a train")
    train_id_input = st.number_input("Train ID (from the table above)", min_value=0, step=1, value=0)
    if train_id_input:
        route = run_query("""
            SELECT tr.stop_number, s.station_name, s.station_code,
                   tr.arrival_time, tr.departure_time, tr.halt_minutes,
                   tr.distance_from_source_km
            FROM train_routes tr
            JOIN stations s ON s.station_id = tr.station_id
            WHERE tr.train_id = %s
            ORDER BY tr.stop_number
        """, [train_id_input])
        if route.empty:
            st.warning("No route found for that train ID.")
        else:
            st.dataframe(route, use_container_width=True, hide_index=True)

# ----------------------------------------------------------------------
# Station explorer
# ----------------------------------------------------------------------
with tab_stations:
    st.subheader("Find a station")
    st_query = st.text_input("Station name or code contains…", placeholder="e.g. NDLS or DELHI")
    if st_query:
        stations = run_query("""
            SELECT station_id, station_code, station_name
            FROM stations
            WHERE station_code LIKE %s OR station_name LIKE %s
            ORDER BY station_name
            LIMIT 100
        """, [f"%{st_query}%", f"%{st_query}%"])
        st.dataframe(stations, use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("Trains passing through a station")
        station_id_input = st.number_input("Station ID (from the table above)", min_value=0, step=1, value=0)
        if station_id_input:
            passing = run_query("""
                SELECT t.train_number, t.train_name, t.train_type,
                       tr.arrival_time, tr.departure_time, tr.stop_number
                FROM train_routes tr
                JOIN trains t ON t.train_id = tr.train_id
                WHERE tr.station_id = %s
                ORDER BY tr.arrival_time
            """, [station_id_input])
            st.dataframe(passing, use_container_width=True, hide_index=True)

# ----------------------------------------------------------------------
# Data quality
# ----------------------------------------------------------------------
with tab_quality:
    st.subheader("Live data-quality checks")
    st.caption("Same checks as validation.sql, run live against the current database.")

    checks = {
        "Duplicate train numbers": """
            SELECT COUNT(*) AS n FROM (
                SELECT train_number FROM trains GROUP BY train_number HAVING COUNT(*) > 1
            ) x
        """,
        "Missing train names": "SELECT COUNT(*) AS n FROM trains WHERE train_name IS NULL OR TRIM(train_name)=''",
        "Missing source station": "SELECT COUNT(*) AS n FROM trains WHERE source_station_code IS NULL OR TRIM(source_station_code)=''",
        "Missing destination station": "SELECT COUNT(*) AS n FROM trains WHERE destination_station_code IS NULL OR TRIM(destination_station_code)=''",
        "Orphaned route→station references": """
            SELECT COUNT(*) AS n FROM train_routes tr
            LEFT JOIN stations s ON tr.station_id = s.station_id
            WHERE s.station_id IS NULL
        """,
        "Trains with zero route stops": """
            SELECT COUNT(*) AS n FROM trains t
            LEFT JOIN train_routes tr ON t.train_id = tr.train_id
            WHERE tr.route_id IS NULL
        """,
        "Duplicate stop numbers within a train": """
            SELECT COUNT(*) AS n FROM (
                SELECT train_id, stop_number FROM train_routes
                GROUP BY train_id, stop_number HAVING COUNT(*) > 1
            ) y
        """,
        "Arrival later than departure at same stop (flagged, review)": """
            SELECT COUNT(*) AS n FROM train_routes
            WHERE arrival_time IS NOT NULL AND departure_time IS NOT NULL
              AND arrival_time > departure_time
        """,
        "Invalid total distance on trains": "SELECT COUNT(*) AS n FROM trains WHERE distance_km IS NULL OR distance_km <= 0",
        "Missing running days": "SELECT COUNT(*) AS n FROM trains WHERE running_days IS NULL",
    }

    rows = []
    for label, q in checks.items():
        n = int(run_query(q).iloc[0]["n"])
        rows.append({"Check": label, "Count": n})
    quality_df = pd.DataFrame(rows)
    st.dataframe(quality_df, use_container_width=True, hide_index=True)

    st.caption(
        "The 'arrival later than departure' rows are usually legitimate overnight "
        "halts (arrive just before midnight, depart just after), not real errors — "
        "see data_quality_report.md for details."
    )

    # Footer
st.divider()
st.markdown("<p style='text-align: center;'>Made with ❤️ by <b>Priya Kale</b> | Contact: <a href='mailto:pkale3922@gmail.com'>pkale3922@gmail.com</a></p>", unsafe_allow_html=True)