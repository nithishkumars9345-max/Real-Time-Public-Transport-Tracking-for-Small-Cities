# Real-Time Public Transport Tracking for Small Cities

A lightweight Flask web app that tracks buses in real time on an interactive
map — built for small cities/towns that don't have an expensive existing
transit-tracking system (or a real GPS feed yet).

It ships with a **GPS simulator** that moves buses along defined routes so
the whole thing works out of the box with no hardware. Swap the simulator
for a real GPS/GTFS-Realtime feed later without touching the frontend.

## Features

- Live map (Leaflet + OpenStreetMap) showing bus positions, updated every
  few seconds
- Multiple routes with stops, each with its own color
- Simple REST API (`/api/routes`, `/api/buses`) that any frontend can consume
- SQLite storage — zero external services required
- Simulator that realistically moves buses along route polylines with
  correct heading/speed, easy to swap for real device data

## Project structure

```
transport-tracker/
├── app.py              # Flask app + API routes
├── simulator.py        # Simulates GPS movement (swap for real feed later)
├── database.py         # SQLite persistence layer
├── data/
│   └── routes.json     # Route/stop definitions + buses per route
├── templates/
│   └── index.html      # Dashboard page
├── static/
│   ├── css/style.css
│   └── js/map.js        # Leaflet map + polling logic
├── requirements.txt
└── .gitignore
```

## Getting started

```bash
# 1. Clone / enter the project folder
cd transport-tracker

# 2. Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python app.py
```

Open **http://127.0.0.1:5000** — you'll see buses moving live along their
routes.

## Customizing routes

Edit `data/routes.json` to describe your own city:

```json
{
  "id": "blue",
  "name": "Blue Line - Downtown Loop",
  "color": "#2563eb",
  "stops": [
    {"name": "Central Station", "lat": 42.2808, "lng": -83.7430},
    {"name": "Market Street",   "lat": 42.2850, "lng": -83.7400}
  ],
  "buses": [
    {"id": "blue-1", "name": "Blue 01"}
  ]
}
```

Make the first and last stop identical to create a closed loop route.

## Moving from simulation to real GPS data

Replace the loop in `simulator.run_simulation()` with code that reads real
positions (from a GPS tracker on each bus, a phone app, or a GTFS-Realtime
feed) and calls `database.update_position(bus_id, lat, lng, heading, speed_kmh, timestamp)`
the same way. The frontend and API don't need to change at all.

## Roadmap ideas

- ETA predictions for each stop
- Rider-facing "how far is my bus" view
- GTFS-Realtime feed ingestion for cities with existing GPS hardware
- Push notifications when a bus is approaching a chosen stop
- Admin panel to add/edit routes without touching JSON directly

## License

MIT — free to use and adapt for your city.
