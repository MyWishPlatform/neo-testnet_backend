from app.models import AssetsRequest, TelegramAddress
from datetime import datetime, timedelta
from app import db


class DatabaseRestrictions(object):
    # check if 24 hours passed since last request
    @staticmethod
    def is_enough_time(request_dt):
        if request_dt <= datetime.now() - timedelta(hours=24):
            return True

    # add new entry in db
    @staticmethod
    def store_address(req):
        db.session.add(req)
        db.session.commit()
        return True

    # method for updating existing row
    @staticmethod
    def update_request(req):
        req.last_request_date = datetime.now()
        db.session.commit()
        return True

    @staticmethod
    def find_address(addr):
        return AssetsRequest.query.filter_by(address=addr).one_or_none()

    @staticmethod
    def find_telegram_address(addr):
        return TelegramAddress.query.filter_by(telegram_address=addr).one_or_none()

    @staticmethod
    def new_entry(addr):
        return AssetsRequest(address=addr, last_request_date=datetime.now())

    @staticmethod
    def new_telegram_entry(addr):
        return TelegramAddress(telegram_address=addr, last_request_date=datetime.now())

    def parse_query(self, request, update):
        if update:
            self.update_request(request)
        else:
            self.store_address(request)
