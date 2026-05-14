from config import InitialDataConfig
from models_of_bd import User, Favorite
from datetime import datetime


class UserHandler:
    def __init__(self, db, logger):
        self.db = db
        self.logger = logger

    def get_user_rank(self, request_count):
        ranks = InitialDataConfig.RANKS

        for i, rank in enumerate(ranks):
            if request_count < rank['threshold']:
                prev_rank = ranks[i - 1] if i > 0 else None
                next_rank = rank
                needed = rank['threshold'] - request_count
                return prev_rank['name'] if prev_rank else "Новичок", next_rank['name'], needed

        return ranks[-1]['name'], None, 0

    def update_user_stats(self, user_id, store=None, query=None):
        try:
            user = User.query.filter_by(uid=user_id).first()

            if user:
                user.last_seen = datetime.utcnow()
                user.total_requests += 1
                if store:
                    user.last_store = store
                if query:
                    user.last_query = query
            else:
                user = User(
                    uid=user_id,
                    last_store=store,
                    last_query=query,
                    total_requests=1
                )
                self.db.session.add(user)

            self.db.session.commit()

        except Exception as e:
            self.logger.error(f"Error updating user stats: {e}")
            self.db.session.rollback()

    def get_user_info(self, user_id):
        user = User.query.filter_by(uid=user_id).first()

        if not user:
            return {
                'total_requests': 0,
                'last_seen': None,
                'last_query': None,
                'last_store': None
            }

        return {
            'total_requests': user.total_requests,
            'last_seen': user.last_seen,
            'last_query': user.last_query,
            'last_store': user.last_store
        }

    def add_to_favorites(self, user_id, game_name):
        try:
            existing = Favorite.query.filter_by(
                user_id=user_id,
                game_name=game_name
            ).first()

            if existing:
                return False

            favorite = Favorite(user_id=user_id, game_name=game_name)
            self.db.session.add(favorite)
            self.db.session.commit()
            return True

        except Exception as e:
            self.logger.error(f"Error adding to favorites: {e}")
            self.db.session.rollback()
            return False

    def get_favorites(self, user_id):
        favorites = Favorite.query.filter_by(user_id=user_id).all()
        return [fav.game_name for fav in favorites]

    def build_rank_message(self, user_id):
        user_info = self.get_user_info(user_id)
        request_count = user_info['total_requests']

        current_rank, next_rank, needed = self.get_user_rank(request_count)

        message = f"Ваш текущий ранг: {current_rank}.\nВсего запросов выполнено: {request_count}."

        if next_rank and needed > 0:
            message += f"\nДо статуса '{next_rank}' осталось запросов: {needed}."
        elif not next_rank:
            message += "\nВы достигли высшего звания! Поздравляем!"

        return message