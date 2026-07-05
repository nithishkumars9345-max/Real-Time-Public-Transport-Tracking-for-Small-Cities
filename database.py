"""
database.py
Lightweight SQLite persistence layer for buses and their live positions.
"""

import os
import sqlite3
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "transport.db")


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS buses (
                id TEXT PRIMARY KEY,
                route_id TEXT NOT NULL,
                name TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS positions (
                bus_id TEXT PRIMARY KEY,
                lat REAL NOT NULL,
                lng REAL NOT NULL,
                heading REAL DEFAULT 0,
                speed_kmh REAL DEFAULT 0,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (bus_id) REFERENCES buses (id)
            )
            """
        )
        conn.commit()


def upsert_bus(bus_id, route_id, name):
    with get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO buses (id, route_id, name) VALUES (?, ?, ?)",
            (bus_id, route_id, name),
        )
        conn.commit()


def update_position(bus_id, lat, lng, heading, speed_kmh, timestamp):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO positions (bus_id, lat, lng, heading, speed_kmh, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(bus_id) DO UPDATE SET
                lat=excluded.lat,
                lng=excluded.lng,
                heading=excluded.heading,
                speed_kmh=excluded.speed_kmh,
                updated_at=excluded.updated_at
            """,
            (bus_id, lat, lng, heading, speed_kmh, timestamp),
        )
        conn.commit()


def get_all_positions():
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT b.id, b.name, b.route_id, p.lat, p.lng,
                   p.heading, p.speed_kmh, p.updated_at
            FROM buses b
            LEFT JOIN positions p ON b.id = p.bus_id
            """
        ).fetchall()
        return [dict(row) for row in rows]
