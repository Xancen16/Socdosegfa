import json
import time
from config import Config


class CacheService:
    def __init__(self, cache_model, db, logger):
        self.cache_model = cache_model
        self.db = db
        self.logger = logger
        self.ttl = Config.CACHE_TTL

    def get(self, search_key):
        cache_entry = self.cache_model.query.filter_by(search_key=search_key).first()

        if cache_entry:
            if (time.time() - cache_entry.created_at) < self.ttl:
                try:
                    data = json.loads(cache_entry.json_data)
                    self.logger.info(f"Cache hit for: {search_key}")
                    return data.get('val')
                except json.JSONDecodeError:
                    self.logger.error(f"Invalid cache data for: {search_key}")
                    return None

        self.logger.info(f"Cache miss for: {search_key}")
        return None

    def set(self, search_key, value, image_url=None):
        try:
            cache_data = json.dumps({'val': value, 'img': image_url or ''})

            existing = self.cache_model.query.filter_by(search_key=search_key).first()

            if existing:
                existing.json_data = cache_data
                existing.created_at = time.time()
            else:
                new_cache = self.cache_model(
                    search_key=search_key,
                    json_data=cache_data,
                    created_at=time.time()
                )
                self.db.session.add(new_cache)

            self.db.session.commit()
            self.logger.info(f"Cached data for: {search_key}")
            return True

        except Exception as e:
            self.logger.error(f"Error caching data for {search_key}: {e}")
            self.db.session.rollback()
            return False

    def get_image_url(self, search_key):
        cache_entry = self.cache_model.query.filter_by(search_key=search_key).first()

        if cache_entry and (time.time() - cache_entry.created_at) < self.ttl:
            try:
                data = json.loads(cache_entry.json_data)
                return data.get('img')
            except json.JSONDecodeError:
                return None

        return None

    def clean_expired(self):
        deleted = self.cache_model.query.filter(
            self.cache_model.created_at < time.time() - Config.CACHE_CLEANUP_AGE
        ).delete()
        self.db.session.commit()
        return deleted