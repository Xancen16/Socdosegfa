from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import time

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(128), index=True, unique=True, nullable=False)
    last_store = db.Column(db.String(64))
    last_query = db.Column(db.String(256))
    sessions_count = db.Column(db.Integer, default=1)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    is_premium = db.Column(db.Boolean, default=False)
    user_level = db.Column(db.Integer, default=1)
    total_requests = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<User {self.uid}>'


class Sales(db.Model):
    __tablename__ = 'sales'

    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(64), nullable=False)
    event_title = db.Column(db.String(128), nullable=False)
    start_at = db.Column(db.Date, nullable=False)
    end_at = db.Column(db.Date)
    is_live = db.Column(db.Boolean, default=False)
    prob = db.Column(db.Integer, default=100)
    priority = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<Sales {self.provider} - {self.event_title}>'


class PriceCache(db.Model):
    __tablename__ = 'price_cache'

    id = db.Column(db.Integer, primary_key=True)
    search_key = db.Column(db.String(256), index=True, nullable=False)
    json_data = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.Float, default=time.time)
    expires_at = db.Column(db.Float)

    def __repr__(self):
        return f'<PriceCache {self.search_key}>'


class Blacklist(db.Model):
    __tablename__ = 'blacklist'

    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(64), nullable=False)

    def __repr__(self):
        return f'<Blacklist {self.word}>'


class AppStat(db.Model):
    __tablename__ = 'app_stats'

    id = db.Column(db.Integer, primary_key=True)
    metric_name = db.Column(db.String(64), nullable=False)
    metric_value = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<AppStat {self.metric_name}={self.metric_value}>'


class Favorite(db.Model):
    __tablename__ = 'favorites'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(128), index=True, nullable=False)
    game_name = db.Column(db.String(256), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Favorite {self.user_id}: {self.game_name}>'


class StoreCache(db.Model):
    __tablename__ = 'store_cache'

    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.String(10), unique=True, nullable=False)
    store_name = db.Column(db.String(64), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<StoreCache {self.store_name}>'