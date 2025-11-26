from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


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
