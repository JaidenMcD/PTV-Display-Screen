import os
import json
from flask import Flask, render_template, jsonify, request
from pathlib import Path
import server.gtfs as gtfs


app = Flask(__name__, template_folder='templates', static_folder='static', static_url_path='/static')


# Global State - shared with display process
display_state = {
    'active_display' : 0,
    'tram_enabled': False,
    'train_enabled': False,
    'tram_stop': None,
    'train_stop': None,
    'train_platforms': [],
    'display_list': []
}

@app.route('/')
def index():
    Metropolitan_Train_Stops = gtfs.extract_stop_names('server/gtfs/Metropolitan-Train-Stops.txt')
    return render_template('index.html', Metropolitan_Train_Stops = Metropolitan_Train_Stops)

@app.route('/api/stops')
def api_stops():
    t = request.args.get('type')
    p = Path(f'server/data/{t}-Stops.json')
    if not p.exists():
        return jsonify
    with p.open('r', encoding='utf-8') as fh:
        data = json.load(fh)
    return jsonify(data)