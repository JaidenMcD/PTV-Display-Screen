import csv

def read_stops_data(filename):
    stops = []

    with open(filename, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Clean quotes if present
            clean_row = {k: v.strip().strip('"') for k, v in row.items()}

            stops.append({
                "stop_id": clean_row["\ufeffstop_id"],
                "stop_name": clean_row["stop_name"],
                "stop_lat": clean_row["stop_lat"],
                "stop_lon": clean_row["stop_lon"],
                "location_type": clean_row["location_type"],
                "parent_station": clean_row["parent_station"],
                "wheelchair_boarding": clean_row["wheelchair_boarding"],
                "level_id": clean_row["level_id"],
                "platform_code": clean_row["platform_code"],
            })

    return stops

    
def extract_stop_names(filename):
    stops = []

    with open(filename, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Clean quotes if present
            clean_row = {k: v.strip().strip('"') for k, v in row.items()}

            stops.append(clean_row["stop_name"])

    # Remove duplicates
    stops = list(set(stops))
    return stops

