import csv

GTFS_HEADSIGNS = {}

with open("data/trips.txt", newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        GTFS_HEADSIGNS[row["trip_id"]] = row["trip_headsign"]