USE indian_railway;

-- 1. Duplicate train numbers
SELECT train_number, COUNT(*) AS cnt
FROM trains
GROUP BY train_number
HAVING COUNT(*) > 1;

-- 2. Missing train names
SELECT train_id, train_number FROM trains
WHERE train_name IS NULL OR TRIM(train_name) = '';

-- 3. Missing source station
SELECT train_id, train_number FROM trains
WHERE source_station_code IS NULL OR TRIM(source_station_code) = '';

-- 4. Missing destination station
SELECT train_id, train_number FROM trains
WHERE destination_station_code IS NULL OR TRIM(destination_station_code) = '';

-- 5. Route rows referencing a station_id that doesn't exist in stations
SELECT tr.route_id, tr.train_id, tr.station_id
FROM train_routes tr
LEFT JOIN stations s ON tr.station_id = s.station_id
WHERE s.station_id IS NULL;

-- 6. Trains with no route rows at all
SELECT t.train_id, t.train_number
FROM trains t
LEFT JOIN train_routes tr ON t.train_id = tr.train_id
WHERE tr.route_id IS NULL;

-- 7. Duplicate stop_number within the same train's route
SELECT train_id, stop_number, COUNT(*) AS cnt
FROM train_routes
GROUP BY train_id, stop_number
HAVING COUNT(*) > 1;

-- 8. Arrival time later than departure time at the same stop
SELECT route_id, train_id, station_id, arrival_time, departure_time
FROM train_routes
WHERE arrival_time IS NOT NULL
  AND departure_time IS NOT NULL
  AND arrival_time > departure_time;

-- 9. Invalid (missing/non-positive) total distance on trains
SELECT train_id, train_number, distance_km
FROM trains
WHERE distance_km IS NULL OR distance_km <= 0;

-- 10. Invalid (missing/negative) distance-from-source on route stops
SELECT route_id, train_id, distance_from_source_km
FROM train_routes
WHERE distance_from_source_km IS NULL OR distance_from_source_km < 0;

-- 11. Missing running days
SELECT train_id, train_number FROM trains
WHERE running_days IS NULL;

-- 12. Distance that decreases along a route
SELECT a.train_id, a.stop_number AS stop_a, b.stop_number AS stop_b,
       a.distance_from_source_km AS dist_a, b.distance_from_source_km AS dist_b
FROM train_routes a
JOIN train_routes b
  ON a.train_id = b.train_id AND b.stop_number = a.stop_number + 1
WHERE a.distance_from_source_km IS NOT NULL
  AND b.distance_from_source_km IS NOT NULL
  AND b.distance_from_source_km < a.distance_from_source_km;

-- Summary counts
SELECT
  (SELECT COUNT(*) FROM (SELECT train_number FROM trains GROUP BY train_number HAVING COUNT(*)>1) x) AS duplicate_train_numbers,
  (SELECT COUNT(*) FROM trains WHERE train_name IS NULL OR TRIM(train_name)='') AS missing_train_names,
  (SELECT COUNT(*) FROM trains WHERE source_station_code IS NULL OR TRIM(source_station_code)='') AS missing_source_station,
  (SELECT COUNT(*) FROM trains WHERE destination_station_code IS NULL OR TRIM(destination_station_code)='') AS missing_destination_station,
  (SELECT COUNT(*) FROM train_routes tr LEFT JOIN stations s ON tr.station_id=s.station_id WHERE s.station_id IS NULL) AS invalid_station_refs,
  (SELECT COUNT(*) FROM trains t LEFT JOIN train_routes tr ON t.train_id=tr.train_id WHERE tr.route_id IS NULL) AS trains_with_no_routes,
  (SELECT COUNT(*) FROM (SELECT train_id, stop_number FROM train_routes GROUP BY train_id, stop_number HAVING COUNT(*)>1) y) AS duplicate_route_sequences,
  (SELECT COUNT(*) FROM train_routes WHERE arrival_time IS NOT NULL AND departure_time IS NOT NULL AND arrival_time > departure_time) AS arrival_after_departure_flagged,
  (SELECT COUNT(*) FROM trains WHERE distance_km IS NULL OR distance_km<=0) AS invalid_total_distance,
  (SELECT COUNT(*) FROM train_routes WHERE distance_from_source_km IS NULL OR distance_from_source_km<0) AS invalid_route_distance,
  (SELECT COUNT(*) FROM trains WHERE running_days IS NULL) AS missing_running_days;