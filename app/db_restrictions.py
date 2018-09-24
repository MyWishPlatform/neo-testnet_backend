from app.models import AssetsRequest
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
    def store_address(address):
        request = AssetsRequest(address=address, last_request_date=datetime.now())
        db.session.add(request)
        db.session.commit()
        return True

    # method for updating existing row
    @staticmethod
    def update_request(req):
        req.last_request_date = datetime.now()
        db.session.commit()
        return True

    # find address in database, if address exists and 24 hours passed since last
    # request update value in row, if address not founded - appending to new row
    def validate_address(self, address):
        request = AssetsRequest.query.filter_by(address=address).one_or_none()
        if request is None:
            self.store_address(address)
        else:
            if self.is_enough_time(request.last_request_date):
                self.update_request(request)
            else:
                return False
