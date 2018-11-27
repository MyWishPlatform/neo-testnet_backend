from app import app, db_restrictions, responses
from settings_local import FAUCET_CLI, CAPTCHA_SECRET
from flask import request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address, get_ipaddr
from flask_jsonrpc.proxy import ServiceProxy
from flask_jsonrpc import exceptions
import requests
import traceback

dblimits = db_restrictions.DatabaseRestrictions()
limiter = Limiter(app, key_func=get_ipaddr)
cli = ServiceProxy(FAUCET_CLI)


@app.route('/api/request/', methods=['POST'])
# restrict number of requests by IP - 1 request for IP per day
# @limiter.limit("1 per day")
def request_main():


    # fetch captcha key and validate
    response = request.get_json()
    captcha_check = captcha_verify(response['g-recaptcha-response'])

    if not captcha_check["success"]:
        return responses.captcha_fail(captcha_check)
    else:





"""
# custom error through api for ip limiter
@app.errorhandler(429)
def limit_handler(error):
    return responses.ip_limit()
"""

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

def process_request(response):
    neo_address = response['address']

    # find address in database, if address exists and 24 hours passed since last
    # request update value in row, if address not founded - appending to new row
    neo_query = dblimits.find_address(neo_address)
    if neo_query and not dblimits.is_enough_time(neo_query.last_request_date):
        return responses.db_limit()
    ip = request.headers.getlist("X-Forwarded-For")[0] if request.headers.getlist(
        "X-Forwarded-For") else request.remote_addr
    ip_query = dblimits.find_ip_address(ip)
    if ip_query and not dblimits.is_enough_time(ip_query.last_request_date):
        return responses.ip_limit()
    relay_tx(neo_address)
    if neo_query:
        dblimits.update_request(neo_query)
    else:
        dblimits.store_address(dblimits.new_entry(neo_address))
    if ip_query:
        dblimits.update_request(ip_query)
    else:
        dblimits.store_address(dblimits.new_ip_entry(ip))
    return responses.send_success(neo_address)