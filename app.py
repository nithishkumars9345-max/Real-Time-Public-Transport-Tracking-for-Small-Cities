"""
app.py
Flask web app that serves the live tracking map and a small JSON API.

Endpoints:
    GET /            -> dashboard (map) page
    GET /api/routes  -> static route/stop geometry
    GET /api/buses   -> live bus positions (polled by the frontend)
"""

import json

from flask import Flask, jsonify, render_template

import database
import simulator

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/routes")
def api_routes():
    with open(simulator.DATA_PATH) as f:
        return jsonify(json.load(f))


@app.route("/api/buses")
def api_buses():
    return jsonify(database.get_all_positions())


if __name__ == "__main__":
    simulator.start_background_simulation()
    app.run(debug=True, port=5000)
