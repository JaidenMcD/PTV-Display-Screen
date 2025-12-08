import os
import requests
from google.transit import gtfs_realtime_pb2
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

key = os.getenv("OPENDATA_KEY")
stop_id = os.getenv("TRAIN_STOP_ID")

URL = "https://api.opendata.transport.vic.gov.au/opendata/public-transport/gtfs/realtime/v1/metro/trip-updates"

response = requests.get(URL, headers={"KeyID": key})

feed = gtfs_realtime_pb2.FeedMessage()

try:
    feed.ParseFromString(response.content)
except Exception as e:
    print("Failed to parse protobuf data!")
    print("Raw content preview:", response.content[:200])
    raise e

def get_updates_for_stop(feed, target_stop_id: str):
    results = []

    for entity in feed.entity:
        if not entity.HasField("trip_update"):
            continue

        tu = entity.trip_update

        # loop through all stop_time_updates
        for stu in tu.stop_time_update:
            if stu.stop_id == target_stop_id:

                arrival = stu.arrival.time if stu.HasField("arrival") else None
                departure = stu.departure.time if stu.HasField("departure") else None
                delay = stu.arrival.delay if stu.HasField("arrival") else None

                results.append({
                    "trip_id": tu.trip.trip_id,
                    "route_id": tu.trip.route_id,
                    "direction_id": tu.trip.direction_id,
                    "schedule_relationship": tu.trip.schedule_relationship,
                    "stop_id": stu.stop_id,
                    "arrival_time": arrival,
                    "departure_time": departure,
                    "delay": delay,
                })

    return results
def get_next_departure_stop_sequence(feed, stop_id: str):
    """
    Returns the stop sequence AFTER a given stop_id for the next upcoming trip.
    Includes skipped stops and real-time arrival times.
    
    Output:
    [
        {"stop_id": "1010", "status": "SCHEDULED", "arrival_time": 1234567890},
        {"stop_id": "1022", "status": "SKIPPED",   "arrival_time": None},
        ...
    ]
    """

    now_ts = datetime.now(timezone.utc).timestamp()
    candidates = []

    for entity in feed.entity:
        if not entity.HasField("trip_update"):
            continue

        tu = entity.trip_update
        trip = tu.trip

        # Skip cancelled trips entirely
        if trip.schedule_relationship == trip.CANCELED:
            continue

        # Step 1 — locate target stop within the trip
        target_index = None
        for i, stu in enumerate(tu.stop_time_update):
            if stu.stop_id == stop_id:
                # Must be a *future* departure
                if stu.HasField("departure") and stu.departure.time > now_ts:
                    target_index = i
                break

        if target_index is None:
            continue

        # Step 2 — evaluate departure time at stop_id
        departure_time = (
            tu.stop_time_update[target_index].departure.time
            if tu.stop_time_update[target_index].HasField("departure")
            else None
        )

        if departure_time is None:
            continue

        # Add candidate trip
        candidates.append((departure_time, tu))

    # No upcoming trips
    if not candidates:
        return []

    # Step 3 — choose the soonest departure
    candidates.sort(key=lambda x: x[0])
    _, next_trip = candidates[0]

    # Step 4 — extract remaining stops AFTER stop_id
    remaining = []
    passed_target = False
    for stu in next_trip.stop_time_update:
        # Skip until we pass target stop
        if not passed_target:
            if stu.stop_id == stop_id:
                passed_target = True
            continue

        # Determine status
        if stu.schedule_relationship == stu.SKIPPED:
            status = "SKIPPED"
            arrival = None
        else:
            status = "SCHEDULED"
            arrival = stu.arrival.time if stu.HasField("arrival") else None

        remaining.append({
            "stop_id": stu.stop_id,
            "status": status,
            "arrival_time": arrival
        })

    return remaining


stops = get_next_departure_stop_sequence(feed, "26506")  # Flinders St example
print(stops)