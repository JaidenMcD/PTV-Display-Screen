import csv

GTFS_HEADSIGNS = {}

with open("data/trips.txt", newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        GTFS_HEADSIGNS[row["trip_id"]] = row["trip_headsign"]

def load_route_data(filename):
    routes = []

    with open(filename, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Clean quotes if present
            clean_row = {k: v.strip().strip('"') for k, v in row.items()}

            routes.append({
                "route_id": clean_row["\ufeffroute_id"],
                "agency_id": clean_row["agency_id"],
                "short_name": clean_row["route_short_name"],
                "long_name": clean_row["route_long_name"],
                "type": int(clean_row["route_type"]) if clean_row["route_type"] else None,
                "color": clean_row["route_color"],
                "text_color": clean_row["route_text_color"]
            })

    return routes

def get_GTFS_stop_ids(station_name):
    result = []
    with open('data/gtfs_static/stops.txt', "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # case-insensitive match
            if row["stop_name"].lower() == station_name.lower():
                result.append({
                    'platform': row['platform_code'],
                    'gtfs_stop_id': row['\ufeffstop_id']
                })
    return result

def build_colour_map(routes_path):
    routeinfo = load_route_data(routes_path)
    colourMap = {}
    for route in routeinfo:
        route_id = route['route_id'].split('-0')[1]
        # Remove bus replacements
        if '-R' in route_id:
            continue
        route_id = route_id.split(':')[0]
        colourMap[route_id] = "#" + route['color']
    return colourMap
        