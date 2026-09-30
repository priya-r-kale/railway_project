-- ============================================================
-- Indian Railway Reference Database - Schema
-- Source: user-provided dataset (EXP-TRAINS.json, PASS-TRAINS.json,
--         SF-TRAINS.json), file timestamps 2025-09-15.
-- ============================================================

CREATE DATABASE IF NOT EXISTS indian_railway;
USE indian_railway;

-- ------------------------------------------------------------
-- 1. Data source documentation
-- ------------------------------------------------------------
DROP TABLE IF EXISTS data_sources;
CREATE TABLE data_sources (
    source_id INT PRIMARY KEY AUTO_INCREMENT,
    source_name VARCHAR(255),
    source_url TEXT,
    retrieved_date DATE,
    description TEXT,
    data_type VARCHAR(50)
);

-- ------------------------------------------------------------
-- 2. Staging table (raw import target, one row per train)
-- ------------------------------------------------------------
DROP TABLE IF EXISTS train_import;
CREATE TABLE train_import (
    train_number VARCHAR(20),
    train_name VARCHAR(255),
    train_type VARCHAR(100),
    source_station_code VARCHAR(20),
    source_station_name VARCHAR(255),
    destination_station_code VARCHAR(20),
    destination_station_name VARCHAR(255),
    departure_time TIME,
    arrival_time TIME,
    distance_km DECIMAL(10,2),
    running_days VARCHAR(50),
    data_source VARCHAR(50)
);

-- ------------------------------------------------------------
-- 3. Normalized reference tables
-- ------------------------------------------------------------
DROP TABLE IF EXISTS train_routes;
DROP TABLE IF EXISTS trains;
DROP TABLE IF EXISTS stations;

CREATE TABLE stations (
    station_id INT PRIMARY KEY,
    station_code VARCHAR(20) NOT NULL,
    station_name VARCHAR(255),
    UNIQUE KEY uq_station_code (station_code)
);

CREATE TABLE trains (
    train_id INT PRIMARY KEY,
    train_number VARCHAR(20) NOT NULL,
    train_name VARCHAR(255),
    train_type VARCHAR(100),          -- Express / Passenger / SuperFast (from source category)
    source_station_code VARCHAR(20),
    source_station_name VARCHAR(255),
    destination_station_code VARCHAR(20),
    destination_station_name VARCHAR(255),
    departure_time TIME,
    arrival_time TIME,
    distance_km DECIMAL(10,2),
    running_days VARCHAR(50),
    data_source VARCHAR(50),
    UNIQUE KEY uq_train_number (train_number),
    KEY idx_source (source_station_code),
    KEY idx_destination (destination_station_code)
);

CREATE TABLE train_routes (
    route_id INT PRIMARY KEY,
    train_id INT NOT NULL,
    station_id INT NOT NULL,
    stop_number INT,
    arrival_time TIME NULL,
    departure_time TIME NULL,
    halt_minutes INT NULL,
    distance_from_source_km DECIMAL(10,2),
    KEY idx_train (train_id),
    KEY idx_station (station_id),
    UNIQUE KEY uq_train_stop (train_id, stop_number),
    CONSTRAINT fk_route_train FOREIGN KEY (train_id) REFERENCES trains(train_id),
    CONSTRAINT fk_route_station FOREIGN KEY (station_id) REFERENCES stations(station_id)
);
