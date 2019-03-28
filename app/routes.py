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

asset_neo = "0xc56f33fc6ecfcd0c225c4ab356fee59390af8560be0e930faebe74a6daff7c9b"
asset_gas = "0x602c79718b16e442de58778e148d0b1084e3b2dffd5de6b7b16cee7969282de7"
asset_amount = app.config['DROP_AMOUNT']
limit_on = app.config['RATELIMIT_ENABLED']


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
        neo_address = response['address']
        neo_asset = response['asset']

        if limit_on:
            neo_query = find_address(neo_address, neo_asset)
            if neo_query and not dblimits.is_enough_time(neo_query.last_request_date):
                return responses.db_limit()

            ip = request.headers.getlist("X-Forwarded-For")[0] if request.headers.getlist("X-Forwarded-For") else request.remote_addr
            ip_query = dblimits.find_ip_address(ip)
            if ip_query and neo_query and not dblimits.is_enough_time(ip_query.last_request_date):
                return responses.ip_limit()

        relay_tx(neo_address, neo_asset)
        
        if limit_on:
            db_save_address(neo_query, neo_address, neo_asset)
            db_save_ip(ip_query, ip)

        return responses.send_success(neo_address)


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


def relay_tx(address, asset):
    ret = {}
    try:
        if asset == "NEO":
            ret = cli.sendtoaddress(asset_neo, address, asset_amount)
        elif asset == "GAS":
            ret = cli.sendtoaddress(asset_gas, address, asset_amount)
        if  ret['error'] and ret['error']['code'] == -33000:
            return responses.tx_fail(ret['error']['message'])    
    except (exceptions.Error, -300) as e:
        traceback.print_exc()
        return responses.tx_fail(e)


def find_address(address, asset):

    # find address in database, if address exists and 24 hours passed since last
    # request update value in row, if address not founded - appending to new row
    if asset == "NEO":
        return dblimits.find_neo_address(address)
    elif asset == "GAS":
        return dblimits.find_gas_address(address)


def db_save_address(query, address, asset):
    if query:
        dblimits.update_request(query)
    else:
        if asset == "NEO":
            dblimits.store_address(dblimits.new_neo_entry(address))
        elif asset == "GAS":
            dblimits.store_address(dblimits.new_gas_entry(address))


def db_save_ip(query, ip):
    if query:
        dblimits.update_request(query)
    else:
        dblimits.store_address(dblimits.new_ip_entry(ip))
