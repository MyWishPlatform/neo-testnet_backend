from app.models import AssetsRequest
from datetime import datetime, timedelta
from app import db


class DatabaseRestrictions(object):
    @staticmethod
    def is_enough_time(request_dt):
        if request_dt <= datetime.now() - timedelta(hours=24):
            return True

    @staticmethod
    def store_address(address):
        request = AssetsRequest(address=address, last_request_date=datetime.now())
        db.session.add(request)
        db.session.commit()
        return True

    @staticmethod
    def update_request(req):
        req.last_request_date = datetime.now()
        db.session.commit()
        return True

    def validate_address(self, address):
        request = AssetsRequest.query.filter_by(address=address).one_or_none()
        if request is None:
            self.store_address(address)
        else:
            if self.is_enough_time(request.last_request_date):
                self.update_request(request)
            else:
                return False
