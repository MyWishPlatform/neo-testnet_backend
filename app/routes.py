from app import app, db_restrictions
from flask import render_template, make_response, request
from flask_limiter import Limiter, RateLimitExceeded
from flask_limiter.util import get_remote_address
import requests
import json


dblimits = db_restrictions.DatabaseRestrictions()
# TODO: use limiter with memcached/redis, not in-memory
limiter = Limiter(app, key_func=get_remote_address)


@app.route('/api/request/', methods=['POST'])
# restrict number of requests by IP - 1 request for IP per day
@limiter.limit("1 per day")
def request_main():
    if request.method == 'POST':
        response = request.get_json()
        captcha_result = captcha_verify(response['g-recaptcha-response'])
        if captcha_result["success"]:
            neo_address = response['address']

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
            asset_response = asset_request.get_json()["result"]["vout"]

            return str(asset_response)
        else:
            return make_response(str(captcha_result))
    return render_template("form.html")


@app.errorhandler(429)
def limit_handler(error):
    return make_response(json.dumps({'error': True, 'code': error.code, 'msg': str(error)}), 429)


def captcha_verify(response):
    secret = "6LdK7HEUAAAAAJkjdSQnsN9SUzDT-bBAapMn97Ve"
    payload = {"secret": secret, "response": response}
    captcha_request = requests.post('https://www.google.com/recaptcha/api/siteverify', payload)
    request_answer = captcha_request.json()
    return request_answer
