from app import app, db_restrictions, responses
from settings_local import FAUCET_CLI, CAPTCHA_SECRET
from flask import request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jsonrpc.proxy import ServiceProxy
from flask_jsonrpc import exceptions
import requests
import traceback

dblimits = db_restrictions.DatabaseRestrictions()
limiter = Limiter(app, key_func=get_remote_address)
cli = ServiceProxy(FAUCET_CLI)


@app.route('/api/request/', methods=['POST'])
# restrict number of requests by IP - 1 request for IP per day
@limiter.limit("1 per day")
def request_main():

    # fetch captcha key and validate
    response = request.get_json()
    captcha_check = captcha_verify(response['g-recaptcha-response'])

    if captcha_check["success"]:
        neo_address = response['address']

        # find address in database, if address exists and 24 hours passed since last
        # request update value in row, if address not founded - appending to new row
        db_query = dblimits.find_address(neo_address)
        if db_query is not None and dblimits.is_enough_time(db_query.last_request_date):
            send_tx(neo_address, db_query, True)
        elif db_query is None:
            db_query = dblimits.new_entry(neo_address)
            send_tx(neo_address, db_query, False)
        else:
            return False

        return responses.send_success(neo_address)
    else:
        return responses.captcha_fail(captcha_check)


def send_tx(addr, query, update):
    if relay_tx(addr):
        dblimits.parse_query(query, update)


# custom error through api for ip limiter
@app.errorhandler(429)
def limit_handler(error):
    return responses.ip_limit()


# captcha response should be send from here
def captcha_verify(response):
    payload = {"secret": CAPTCHA_SECRET, "response": response}
    captcha_call = requests.post('https://www.google.com/recaptcha/api/siteverify', payload)
    return captcha_call.json()


def relay_tx(addr):
    try:
        cli.sendfaucetassets(addr)
        return True
    except (exceptions.Error, -300) as e:
        traceback.print_exc()
        return responses.tx_fail(e)
