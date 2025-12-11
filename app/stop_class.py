from models.stop import Stop
from api.ptv_api import get_pid_stops

S = Stop("Armadale")
dep, next_run = S.get_next_departures(2, True)
print(get_pid_stops(next_run, S.stop_id))