from models.stop import Stop

S = Stop("Armadale")
print(S)
S.get_next_departures(2)