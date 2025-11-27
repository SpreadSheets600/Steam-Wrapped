from uuid import uuid4

from app.db import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    steam_id = db.Column(db.String(64), unique=True, nullable=False)
    username = db.Column(db.String(128))
    avatar_url = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    last_updated = db.Column(
        db.DateTime, server_default=db.func.now(), onupdate=db.func.now()
    )

    def __repr__(self):
        return f"<User {self.username}>"


class WrappedShare(db.Model):
    __tablename__ = "wrapped"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(
        db.String(32), unique=True, nullable=False, default=lambda: uuid4().hex[:16]
    )
    steam_id = db.Column(db.String(64), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    payload = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    user = db.relationship("User", backref=db.backref("wrapped_shares", lazy=True))

    def regenerate_slug(self):
        self.slug = uuid4().hex[:16]

