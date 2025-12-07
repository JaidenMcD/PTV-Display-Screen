import os
import requests
from google.transit import gtfs_realtime_pb2

METRO_URL = "https://api.opendata.transport.vic.gov.au/opendata/public-transport/gtfs/realtime/v1/metro/vehicle-positions"

def gtfsrequest():
    key = os.getenv("OPENDATA_KEY")
    response = requests.get(METRO_URL, headers={"KeyID": key})
    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(response.content)
    print(feed)
    return feed

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
