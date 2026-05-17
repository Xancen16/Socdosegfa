from utils.cleaner import clean_user_text


class GamesHandler:
    def __init__(self, cheapshark_service, cache_service, yandex_service,
                 currency_service, stores_handler, logger):
        self.cheapshark_service = cheapshark_service
        self.cache_service = cache_service
        self.yandex_service = yandex_service
        self.currency_service = currency_service
        self.stores_handler = stores_handler
        self.logger = logger

    def search_game(self, query):
        cleaned_query = clean_user_text(query)

        if not cleaned_query:
            return "Название игры не распознано. Укажите корректный заголовок."

        cached_result = self.cache_service.get(cleaned_query)
        if cached_result:
            return cached_result

        game_data = self.cheapshark_service.search_game(cleaned_query)

        if not game_data:
            return f"Информация по запросу '{cleaned_query}' не найдена в базе."

        if not game_data.get('deals'):
            return f"Для игры {game_data['title']} активные предложения отсутствуют."

        best_deal = game_data['deals'][0]
        store_name = self.stores_handler.get_store_name(best_deal['storeID'])

        price_rub = self.currency_service.convert_usd_to_rub(best_deal['price'], self.logger)

        result_text = (
            f"Информация по игре {game_data['title']}\n"
            f"Лучшая цена зафиксирована в {store_name}\n"
            f"Текущая стоимость составляет {price_rub} руб"
        )

        image_url = game_data.get('thumb', '')

        self.cache_service.set(cleaned_query, result_text, image_url)

        return {
            'text': result_text,
            'image_url': image_url,
            'title': game_data['title']
        }

    def get_game_with_card(self, query):
        result = self.search_game(query)

        if isinstance(result, dict):
            yandex_image_id = self.yandex_service.upload_image(result['image_url'])

            card_data = None
            if yandex_image_id:
                card_data = {
                    'image': yandex_image_id,
                    'title': result['title']
                }

            return result['text'], card_data

        return result, None