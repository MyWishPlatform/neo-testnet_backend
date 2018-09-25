from app import app, db_restrictions
from flask import render_template
from flask_limiter import Limiter, RateLimitExceeded
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import request
import requests
import json


dblimits = db_restrictions.DatabaseRestrictions()
# TODO: use limiter with memcached/redis, not in-memory
limiter = Limiter(app, key_func=get_remote_address)


@app.route('/', methods=['GET', 'POST'])
# restrict number of requests by IP - 1 request for IP per day
@limiter.limit("1 per day")
def request_main():
    if request.method == 'POST':
        neo_address = request.json['address']

        if dblimits.validate_address(address=neo_address) is False:
            raise RateLimitExceeded

        # generate payload to RPC
        payload = {
            "jsonrpc": "2.0",
            "method": "sendfaucetassets",
            "params": [str(neo_address)],
            "id": "1"
        }

        # send request and fetch response
        dumped_pl = json.dumps(payload)
        asset_request = requests.post('http://127.0.0.1:40332', data=dumped_pl)
        asset_responce = asset_request.json()["result"]["vout"][0]

        return str(asset_responce)
    return render_template("form.html")

