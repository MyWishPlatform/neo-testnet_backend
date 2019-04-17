import os
from datetime import timedelta
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.realpath(__file__))


class Config(object):

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    POSTGRES = {
        'user': 'neo_faucet',
        'pw': 'neo_faucet',
        'db': 'neo_faucet',
        'host': 'localhost',
        'port': '5432',
    }

    SQLALCHEMY_DATABASE_URI = 'postgresql://%(user)s:%(pw)s@%(host)s:%(port)s/%(db)s' % POSTGRES
    RATELIMIT_ENABLED = False
    DROP_AMOUNT = 1000

    # flask config
    SECRET_KEY = os.urandom(
        24)  # session secret key,init random string when app start
    PERMANENT_SESSION_LIFETIME = timedelta(seconds=1200)  # session expire time

    # Github config
    GITHUB_CLIENT_ID = '205be6d17715fd71c4b2'
    GITHUB_CLIENT_SECRET = '083391b15a1e7e36f12732c7f40b028f00b1e8aa'
