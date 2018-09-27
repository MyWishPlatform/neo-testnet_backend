from app import app, db_restrictions, responses
from settings_local import FAUCET_CLI, CAPTCHA_SECRET
from flask import request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jsonrpc.proxy import ServiceProxy
from flask_jsonrpc import exceptions
import requests


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

        # check database, gives false if assets was requested
        # for supplied address in 24 hours
        if dblimits.validate_address(address=neo_address) is False:
            return responses.db_limit()

        # calling node to create transaction
        try:
            cli.sendfaucetassets(neo_address)
        except (exceptions.Error, -300) as e:
            return responses.tx_fail(e)

        return responses.send_success(neo_address)
    else:
        return responses.captcha_fail(captcha_check)


# custom error through api for ip limiter
@app.errorhandler(429)
def limit_handler(error):
    return responses.ip_limit()

# captcha responce should be sended from here
def captcha_verify(response):
    payload = {"secret": CAPTCHA_SECRET, "response": response}
    captcha_call = requests.post('https://www.google.com/recaptcha/api/siteverify', payload)
    return captcha_call.json()
