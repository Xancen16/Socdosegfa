import requests
from config import CheapSharkConfig


class CheapSharkService:
    def __init__(self, currency_service, logger):
        self.currency_service = currency_service
        self.logger = logger

    def get_deals_by_store(self, store_id, limit=10):
        try:
            url = f"{CheapSharkConfig.DEALS_API}?storeID={store_id}&onSale=1&pageSize={limit}"
            response = requests.get(url, timeout=CheapSharkConfig.TIMEOUT_LONG)

            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            self.logger.error(f"Error getting deals for store {store_id}: {e}")
            return None

    def search_game(self, title):
        try:
            search_url = f"{CheapSharkConfig.GAMES_API}?title={title}&limit=1"
            search_resp = requests.get(search_url, timeout=CheapSharkConfig.TIMEOUT_MEDIUM)

            if search_resp.status_code != 200:
                return None

            games = search_resp.json()
            if not games:
                return None

            game_data = games[0]
            game_id = game_data['gameID']

            price_url = f"{CheapSharkConfig.GAMES_API}?id={game_id}"
            price_resp = requests.get(price_url, timeout=CheapSharkConfig.TIMEOUT_MEDIUM)

            if price_resp.status_code != 200:
                return None

            price_data = price_resp.json()

            return {
                'title': game_data['external'],
                'game_id': game_id,
                'thumb': game_data.get('thumb', ''),
                'deals': price_data.get('deals', [])
            }
        except Exception as e:
            self.logger.error(f"Error searching game {title}: {e}")
            return None

    def get_best_deal(self, min_savings=50, limit=30, metacritic=80):
        try:
            url = f"{CheapSharkConfig.DEALS_API}?metacritic={metacritic}&lowerPrice=0&onSale=1&pageSize={limit}"
            response = requests.get(url, timeout=CheapSharkConfig.TIMEOUT_LONG)

            if response.status_code == 200:
                deals = response.json()
                return [d for d in deals if float(d.get('savings', 0)) > min_savings]
            return []
        except Exception as e:
            self.logger.error(f"Error getting best deals: {e}")
            return []

    def get_deals_by_budget(self, max_price_usd, limit=10, metacritic=70):
        try:
            url = f"{CheapSharkConfig.DEALS_API}?upperPrice={max_price_usd}&metacritic={metacritic}&pageSize={limit}&onSale=1"
            response = requests.get(url, timeout=CheapSharkConfig.TIMEOUT_LONG)

            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            self.logger.error(f"Error getting deals by budget: {e}")
            return []

    def get_free_games(self, limit=5):
        try:
            url = f"{CheapSharkConfig.DEALS_API}?upperPrice=0&pageSize={limit}"
            response = requests.get(url, timeout=CheapSharkConfig.TIMEOUT_MEDIUM)

            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            self.logger.error(f"Error getting free games: {e}")
            return []

    def get_game_of_the_day(self):
        try:
            url = f"{CheapSharkConfig.DEALS_API}?sortBy=Savings&pageSize=1&onSale=1"
            response = requests.get(url, timeout=CheapSharkConfig.TIMEOUT_LONG)

            if response.status_code == 200:
                deals = response.json()
                return deals[0] if deals else None
            return None
        except Exception as e:
            self.logger.error(f"Error getting game of the day: {e}")
            return None

    def sync_stores(self, store_cache_model, db):
        try:
            response = requests.get(
                CheapSharkConfig.STORES_API,
                timeout=CheapSharkConfig.TIMEOUT_MEDIUM
            )

            if response.status_code == 200:
                stores = response.json()
                count = 0

                for store in stores:
                    existing = store_cache_model.query.filter_by(
                        store_id=str(store['storeID'])
                    ).first()

                    if not existing:
                        new_store = store_cache_model(
                            store_id=str(store['storeID']),
                            store_name=store['storeName'],
                            is_active=bool(store['isActive'])
                        )
                        db.session.add(new_store)
                        count += 1
                    else:
                        existing.store_name = store['storeName']
                        existing.is_active = bool(store['isActive'])

                db.session.commit()
                self.logger.info(f"Синхронизировано {count} новых магазинов")
                return count

            return 0
        except Exception as e:
            self.logger.error(f"Sync stores failed: {e}")
            return 0