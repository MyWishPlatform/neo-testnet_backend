from app import app, db_restrictions
from flask import render_template
from flask_limiter import Limiter, RateLimitExceeded
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import request
import requests
import json


dblimits = db_restrictions.DatabaseRestrictions()
limiter = Limiter(app, key_func=get_remote_address)


@app.route('/')
def request_form():
    return render_template("form.html")


@app.route('/', methods=['POST'])
@limiter.limit("1 per day")
def request_main():
    neo_address = request.form['text']

    if dblimits.validate_address(address=neo_address) is False:
        raise RateLimitExceeded

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
