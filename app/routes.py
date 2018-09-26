from app import app, db_restrictions
from flask import render_template, make_response
from flask_limiter import Limiter, RateLimitExceeded
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import request
import requests
import json


dblimits = db_restrictions.DatabaseRestrictions()
# TODO: use limiter with memcached/redis, not in-memory
limiter = Limiter(app, key_func=get_remote_address)


@app.route('/', methods=['POST'])
# restrict number of requests by IP - 1 request for IP per day
@limiter.limit("1 per day")
def request_main():
    if request.method == 'POST':
        responce = request.json
        captcha_result = captcha_verify(responce['g-recaptcha-responce'])
        if captcha_result["success"]:
            neo_address = responce['address']

            if dblimits.validate_address(address=neo_address) is False:
                raise RateLimitExceeded

            # generate payload to RPC
            cli_payload = {
                "jsonrpc": "2.0",
                "method": "sendfaucetassets",
                "params": [str(neo_address)],
                "id": "1"
            }

            # send request and fetch response
            dumped_pl = json.dumps(cli_payload)
            asset_request = requests.post('http://127.0.0.1:40332', data=dumped_pl)
            asset_responce = asset_request.json()["result"]["vout"]

            return str(asset_responce)
        else:
            return make_response(str(captcha_result))
    return render_template("form.html")


@app.errorhandler(429)
def limit_handler(error):
    return make_response(json.dumps({'error': True, 'code': error.code, 'msg': str(error)}), 429)


def captcha_verify(responce):
    secret = "6LdK7HEUAAAAAJkjdSQnsN9SUzDT-bBAapMn97Ve"
    payload = {"secret": secret, "responce": responce}
    captcha_request = requests.post('https://www.google.com/recaptcha/api/siteverify', payload)
    request_answer = captcha_request.json()
    return request_answer
