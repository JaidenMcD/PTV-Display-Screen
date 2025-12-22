import os
import requests
from google.transit import gtfs_realtime_pb2

METRO_URL = "https://api.opendata.transport.vic.gov.au/opendata/public-transport/gtfs/realtime/v1/metro/vehicle-positions"

def gtfsrequest(url):
    key = os.getenv("OPENDATA_KEY")
    response = requests.get(url, headers={"KeyID": key})
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(response.content)
    return feed

def extract_route_number(gtfs_route_id):
    """
    Extract the numeric route number from GTFS route_id
    Example: 'aus:vic:vic-03-64:' -> '64'
    """
    if not gtfs_route_id:
        return None
    parts = gtfs_route_id.split(":")
    if len(parts) < 3:
        return None
    # get the second-to-last part, e.g., 'vic-03-64'
    last_part = parts[-2]
    # split by '-' and take the last segment
    return last_part.split("-")[-1]

def tram_service_updates(route_numbers):
    URL = "https://api.opendata.transport.vic.gov.au/opendata/public-transport/gtfs/realtime/v1/tram/service-alerts"
    feed = gtfsrequest(URL)
    alerts = []

    route_numbers_set = set(str(r) for r in route_numbers)

    for entity in feed.entity:
        if entity.HasField("alert"):
            alert = entity.alert
            alert_routes = [extract_route_number(ie.route_id) for ie in alert.informed_entity]

            if any(r in route_numbers_set for r in alert_routes):
                header = alert.header_text.translation[0].text if alert.header_text.translation else ""
                description = alert.description_text.translation[0].text if alert.description_text.translation else ""
                url = alert.url.translation[0].text if alert.url.translation else ""
                alerts.append({
                    "routes": alert_routes,
                    "header": header,
                    "description": description,
                    "url": url
                })
    return alerts

def fetchVehiclePositons_MetroTrain():
    """ URL WEB JSON """
    resourceURL = "https://opendata.transport.vic.gov.au/dataset/2d9a7228-5b81-40d3-8075-ae7a3da42198/resource/e2158e21-e6cb-4611-919f-90117b36a610/download/gtfsr_metro_train_vehicle_positions.openapi.json"
    try:
        response = requests.get(resourceURL)
        response.raise_for_status()  # Raises an error for 4xx or 5xx responses
        data = response.json()       # Parse response body as JSON
    except requests.exceptions.RequestException as e:
        print(f"Error fetching JSON: {e}")
    url = data['servers'][0]['url'] + '/vehicle-positions'

    """ API Request """
    key = os.getenv("OPENDATA_KEY")
    print(f'Making request at {url}')
    response = requests.get(url, headers={"KeyID": key})

    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(response.content)
    entities = []
    for entity in feed.entity:
        v = entity.vehicle
        entities.append({
            'id': entity.id,
            'lat': v.position.latitude,
            'lon': v.position.longitude,
            'bearing': v.position.bearing,
            'trip_id': v.trip.trip_id,
            'route_id': v.trip.route_id,
            'start_time': v.trip.start_time,
            'start_date': v.trip.start_date,
            'vehicle_id': v.vehicle.id,
            'timestamp': v.timestamp
        })
    return entities
