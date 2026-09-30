USE indian_railway;

INSERT INTO data_sources (source_id, source_name, source_url, retrieved_date, description, data_type)
VALUES
(1,
 'User-provided Indian Railway train schedule export (EXP-TRAINS.json, PASS-TRAINS.json, SF-TRAINS.json)',
 NULL,
 '2025-09-15',
 'Real Indian Railways train and stop-by-stop schedule data (train number, name, category, running days, and full station-by-station route with arrival/departure/distance/day). Supplied by the user as a zip archive; exact original publisher URL was not included with the files, so it is left NULL rather than invented. File modification timestamps indicate the export was generated on 2025-09-15. Data is split into three category files by the source itself: Express, Passenger, and SuperFast.',
 'REAL_PUBLIC'
),
(2,
 'Kaggle "Indian Railways Dataset" style export (trains.csv, Trains schedule.csv)',
 'https://www.kaggle.com/datasets/sripaadsrinivasan/indian-railways-dataset',
 '2023-07-12',
 'Older (~2016-era, originally data.gov.in-derived) train and schedule export, 5,207 trains / 417,080 schedule rows, uploaded 2023-07-12. NOT imported into this database: superseded by the more complete and current 2025-09-15 export (source_id 1), which has more trains (8,490 vs 5,207), richer per-stop fields (running days, day-offset, sequence number), and is roughly two years more current. Recorded here only for provenance/audit purposes.',
 'REAL_PUBLIC'
);
