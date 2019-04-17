from app import db
from enum import Enum

# Address field - needed to check if request is duplicate
# Time since last request - compare to this value before sending payload, limiting to 1 address per day
# class AssetsRequest(db.Model):
#     __tablename__ = "neo_faucet"
#     id = db.Column(db.Integer, primary_key=True)
#     address = db.Column(db.String(64), index=True, unique=True, nullable=False)
#     last_request_date = db.Column(db.DateTime(timezone=False), nullable=False)
#
#     def __repr__(self):
#         return '<Address {addr} last requested {dt}'.format(addr=self.address, dt=self.last_request_date)


class NeoRequest(db.Model):
    __tablename__ = "neo_asset"
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(64), index=True, unique=True, nullable=False)
    last_request_date = db.Column(db.DateTime(timezone=False), nullable=False)

    def __repr__(self):
        return '<Address {addr} last requested {dt}'.format(
            addr=self.address, dt=self.last_request_date)


class GasRequest(db.Model):
    __tablename__ = "gas_asset"
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(64), index=True, unique=True, nullable=False)
    last_request_date = db.Column(db.DateTime(timezone=False), nullable=False)

    def __repr__(self):
        return '<Address {addr} last requested {dt}'.format(
            addr=self.address, dt=self.last_request_date)


class TelegramAddress(db.Model):
    __tablename__ = "telegram_address"
    id = db.Column(db.Integer, primary_key=True)
    telegram_address = db.Column(db.String(64),
                                 index=True,
                                 unique=True,
                                 nullable=False)
    last_request_date = db.Column(db.DateTime(timezone=False), nullable=False)


class IPAddress(db.Model):
    __tablename__ = "ip_address"
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(40),
                           index=True,
                           unique=True,
                           nullable=False)  # 40 for v6
    last_request_date = db.Column(db.DateTime(timezone=False), nullable=False)


class TokenType(Enum):
    NEO = 1
    GAS = 2


class RequestLog(db.Model):
    __tablename__ = "request_log"
    id = db.Column(db.Integer, primary_key=True)
    token_type = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    address = db.Column(db.String(64), index=True, nullable=False)
    ip_address = db.Column(db.String(40),index=True, nullable=False)  # 40 for v6
    account = db.Column(db.String(50), index=True, nullable=False) # github login account
    request_date = db.Column(db.DateTime(timezone=False),index=True, nullable=False)
