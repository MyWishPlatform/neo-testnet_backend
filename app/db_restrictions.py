from app.models import NeoRequest, GasRequest, TelegramAddress, IPAddress, RequestLog
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
    def find_neo_address(addr):
        return NeoRequest.query.filter_by(address=addr).one_or_none()

    @staticmethod
    def find_gas_address(addr):
        return GasRequest.query.filter_by(address=addr).one_or_none()

    @staticmethod
    def find_telegram_address(addr):
        return TelegramAddress.query.filter_by(
            telegram_address=addr).one_or_none()

    @staticmethod
    def find_ip_address(addr):
        return IPAddress.query.filter_by(ip_address=addr).one_or_none()

    @staticmethod
    def new_neo_entry(addr):
        return NeoRequest(address=addr, last_request_date=datetime.now())

    @staticmethod
    def new_gas_entry(addr):
        return GasRequest(address=addr, last_request_date=datetime.now())

    @staticmethod
    def new_telegram_entry(addr):
        return TelegramAddress(telegram_address=addr,
                               last_request_date=datetime.now())

    @staticmethod
    def new_ip_entry(addr):
        return IPAddress(ip_address=addr, last_request_date=datetime.now())

    @staticmethod
    def new_request_log(addr, account, amount, tokentype, ip):
        return RequestLog(address=addr,
                          account=account,
                          amount=amount,
                          token_type=tokentype,
                          ip_address=ip,
                          request_date=datetime.now())

    def parse_query(self, request, update):
        if update:
            self.update_request(request)
        else:
            self.store_address(request)
