"""
simulator.py
Simulates GPS movement of buses along predefined routes.

This stands in for a real GPS feed. In production, replace
`run_simulation` with a reader for real device pings (e.g. from a
GPS tracker on each bus, or a GTFS-Realtime feed) that calls
`database.update_position(...)` the same way.
"""

import json
import math
import os
import threading
import time
from datetime import datetime, timezone

import database

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "routes.json")
UPDATE_INTERVAL = 2      # seconds between position updates
DEFAULT_SPEED_KMH = 25   # simulated constant bus speed


def haversine(p1, p2):
    """Distance in meters between two (lat, lng) points."""
    R = 6371000
    lat1, lon1 = math.radians(p1[0]), math.radians(p1[1])
    lat2, lon2 = math.radians(p2[0]), math.radians(p2[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def bearing(p1, p2):
    """Compass heading in degrees from p1 to p2."""
    lat1, lon1 = math.radians(p1[0]), math.radians(p1[1])
    lat2, lon2 = math.radians(p2[0]), math.radians(p2[1])
    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


class Bus:
    """Tracks a bus's progress (in meters traveled) along a looped path."""

    def __init__(self, bus_id, name, route_id, path, offset_m=0):
        self.id = bus_id
        self.name = name
        self.route_id = route_id
        self.path = path
        self.distance_traveled = offset_m
        self.segment_lengths = [
            haversine(path[i], path[i + 1]) for i in range(len(path) - 1)
        ]
        self.total_length = sum(self.segment_lengths) or 1

    def position_at(self, distance):
        distance = distance % self.total_length
        for i, seg_len in enumerate(self.segment_lengths):
            if distance <= seg_len or i == len(self.segment_lengths) - 1:
                ratio = (distance / seg_len) if seg_len else 0
                ratio = min(max(ratio, 0), 1)
                p1, p2 = self.path[i], self.path[i + 1]
                lat = p1[0] + (p2[0] - p1[0]) * ratio
                lng = p1[1] + (p2[1] - p1[1]) * ratio
                heading = bearing(p1, p2)
                return lat, lng, heading
            distance -= seg_len
        return self.path[0][0], self.path[0][1], 0

    def advance(self, meters):
        self.distance_traveled += meters
        return self.position_at(self.distance_traveled)


def load_routes():
    with open(DATA_PATH) as f:
        return json.load(f)


def build_buses():
    routes = load_routes()
    buses = []
    for route in routes["routes"]:
        path = [(p["lat"], p["lng"]) for p in route["stops"]]
        bus_configs = route["buses"]
        total_len = sum(haversine(path[j], path[j + 1]) for j in range(len(path) - 1))
        for i, bus_cfg in enumerate(bus_configs):
            offset = (total_len / len(bus_configs)) * i
            buses.append(Bus(bus_cfg["id"], bus_cfg["name"], route["id"], path, offset))
    return buses


def run_simulation(stop_event, speed_kmh=DEFAULT_SPEED_KMH):
    database.init_db()
    buses = build_buses()
    for bus in buses:
        database.upsert_bus(bus.id, bus.route_id, bus.name)

    meters_per_tick = (speed_kmh * 1000 / 3600) * UPDATE_INTERVAL

    while not stop_event.is_set():
        for bus in buses:
            lat, lng, heading = bus.advance(meters_per_tick)
            database.update_position(
                bus.id, lat, lng, heading, speed_kmh,
                datetime.now(timezone.utc).isoformat(),
            )
        time.sleep(UPDATE_INTERVAL)


def start_background_simulation():
    """Starts the simulator in a daemon thread and returns its stop event."""
    stop_event = threading.Event()
    thread = threading.Thread(target=run_simulation, args=(stop_event,), daemon=True)
    thread.start()
    return stop_event
