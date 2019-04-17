from flask import make_response
import json


def response_callback(error_type, msg):
    payload = {
        'success': False,
        'code': error_type,
        'msg': msg
    }

    return make_response(json.dumps(payload))


def ip_limit():
    return response_callback(601, "IP limit: 1 request per day")


def db_limit():
    return response_callback(602, "Address limit: 1 address per day")


def tx_fail(err):
    return response_callback(603, err)


def captcha_fail(err):
    return response_callback(604, err)

def balance_fail(err):
    return response_callback(605,err)

def login_fail(err):
    return response_callback(401,err)

def send_success(addr):
    return json.dumps({'success': True, 'address': addr})

def success(obj):
    return make_response(json.dumps({
        'success': True,
        'data':obj
    }))
