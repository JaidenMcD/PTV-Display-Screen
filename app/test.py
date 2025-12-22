from models.tram_stop import TramStop
from data.gtfs_loader import build_tram_colour_map


from api.gtfs import tram_service_updates

up = tram_service_updates(5)
print(up)
exit()
stop = TramStop("Wattletree")

col = build_tram_colour_map("data/gtfs_static/tram/routes.txt")
dep = stop.get_next_departures_per_route(3)
print(dep)
