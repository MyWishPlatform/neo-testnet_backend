from app import app
from flask import render_template
from flask_sqlalchemy import SQLAlchemy, request
import requests
import json

@app.route('/')
def test_form():
    return render_template("form.html")

@app.route('/', methods=['POST'])
def test_post():
    neo_address = request.form['text']
    payload = {
        "jsonrpc": "2.0",
        "method": "sendfaucetassets",
        "params": [str(neo_address)],
        "id": "1"
    }

    dumped_pl = json.dumps(payload)

    asset_request = requests.post('http://127.0.0.1:40332', data=dumped_pl)
    asset_responce = asset_request.json()["result"]["vout"][0]

    return str(asset_responce)
