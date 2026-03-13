from datetime import datetime
from flask_login import UserMixin
from app import db

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default="user")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    qrcodes = db.relationship("QRCode", backref="user", lazy=True)

    def __repr__(self):
        return f"<User {self.username}>"

class QRCode(db.Model):
    __tablename__ = "qrcodes"

    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    def __repr__(self):
        return f"<QRCode {self.id}>"
