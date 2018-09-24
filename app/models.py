from app import db


class AssetsRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(64), index=True, unique=True, nullable=False)
    last_request_date = db.Column(db.DateTime(timezone=False), nullable=False)

    def __repr__(self):
        return '<Address {addr} last requested {dt}'.format(addr=self.address, dt=self.last_request_date)
