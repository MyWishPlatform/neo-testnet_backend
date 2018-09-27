from flask import make_response
import json


def response_callback(error_type, msg):
    payload = {
        'success': False,
        'error_type': error_type,
        'msg': msg
    }

    return make_response(json.dumps(payload))


def ip_limit():
    return response_callback("ip_limit", "IP limit: 1 request per day")


def db_limit():
    return response_callback("address_limit", "Address limit: 1 address per day")


def tx_fail(err):
    return response_callback("tx_error", err)


def captcha_fail(err):
    return response_callback("captcha_error", err)


def send_success(addr):
    return json.dumps({'success': True, 'address': addr})