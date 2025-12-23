import os
import json
from flask import Flask, render_template, jsonify, request
from pathlib import Path

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
    return render_template('index.html')