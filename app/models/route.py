from dataclasses import dataclass, field
from typing import Optional, Dict
from api.ptv_api import send_ptv_request

@dataclass
class Route:
    route_id_ptv: int
    route_id_gtfs: str
    route_name: str

