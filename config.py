import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.realpath(__file__))


class Config(object):

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    POSTGRES = {
        'user': 'neo_faucet',
        'pw':   'neo_faucet',
        'db':   'neo_faucet',
        'host': 'localhost',
        'port': '5432',
    }

    SQLALCHEMY_DATABASE_URI = 'postgresql://%(user)s:%(pw)s@%(host)s:%(port)s/%(db)s' % POSTGRES
    RATELIMIT_ENABLED = True
    DROP_AMOUNT = 1000
