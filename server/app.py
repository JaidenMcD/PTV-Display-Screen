import os
import json
from flask import Flask, render_template, jsonify, request
from pathlib import Path
import server.gtfs as gtfs


app = Flask(__name__, template_folder='templates', static_folder='static', static_url_path='/static')


# Global State - shared with display process
display_state = {
    'stop': False,
    'transit-type': False,
    'display-type': 'default_display',
    'train_platforms': [],
    'running': True,
    'version': 0,
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

@app.route('/api/send-to-display', methods=['POST'])
def send_to_display():
    data = request.json
    transit_type = data.get('transitType')
    stop = data.get('stop')
    display_type = data.get('displayType')

    display_state['transit_type'] = transit_type
    display_state['stop'] = stop
    display_state['display_type'] = display_type

    display_state['version'] += 1

    
    return jsonify({'message': f'Sent {stop} ({display_type}) to display'})