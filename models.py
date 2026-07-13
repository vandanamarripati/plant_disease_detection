"""
Database models for LeafScan.
Uses Flask-SQLAlchemy with a local SQLite file (no external DB needed).
"""

from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Farmer(UserMixin, db.Model):
    __tablename__ = "farmers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(160), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    scans = db.relationship("ScanHistory", backref="farmer", lazy=True,
                             order_by="ScanHistory.created_at.desc()")

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)


class ScanHistory(db.Model):
    __tablename__ = "scan_history"

    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey("farmers.id"), nullable=False)

    plant = db.Column(db.String(80))
    label = db.Column(db.String(160))
    status = db.Column(db.String(20))       # healthy / diseased
    severity = db.Column(db.String(20))
    confidence = db.Column(db.Float)
    image_url = db.Column(db.String(255))
    fertilizer_summary = db.Column(db.Text)  # short text of the recommended fertilizer, if any
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))