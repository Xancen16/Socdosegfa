import random


class RecommendationsHandler:
    def __init__(self, cheapshark_service, currency_service, stores_handler, logger):
        self.cheapshark_service = cheapshark_service
        self.currency_service = currency_service
        self.stores_handler = stores_handler
        self.logger = logger

    def get_random_recommendation(self, filter_query=None):
        try:
            deals = self.cheapshark_service.get_best_deal(min_savings=50 if not filter_query else 30)

            if not deals:
                return "Не удалось подобрать игру. Попробуйте позже или загляните в раздел Магазины."

            if filter_query:
                filtered = [d for d in deals if filter_query.lower() in d.get('title', '').lower()]
                if filtered:
                    deals = filtered

            if not deals:
                return f"По запросу '{filter_query}' ничего не найдено. Попробуйте другой жанр."

            pick = random.choice(deals)
            title = pick.get('title', 'Интересная игра')
            price_rub = self.currency_service.convert_usd_to_rub(pick.get('salePrice', 0), self.logger)
            discount = round(float(pick.get('savings', 0)))
            store = self.stores_handler.get_store_name(pick.get('storeID'))
            rating = pick.get('metacriticScore', 'высокий')

            prefix = f"В категории '{filter_query}' рекомендую: " if filter_query else "Случайный выбор для вас: "

            return (f"{prefix}{title}. "
                    f"Рейтинг: {rating}/100. Сейчас скидка {discount}%. "
                    f"В {store} цена составляет {price_rub} руб.")

        except Exception as e:
            self.logger.error(f"Recommendation error: {e}")
            return "Произошла ошибка при подборе рекомендации."

    def get_game_of_the_day(self):
        try:
            game = self.cheapshark_service.get_game_of_the_day()

            if not game:
                return "Не удалось определить игру дня. Попробуйте чуть позже."

            title = game.get('title')
            sale_price_rub = self.currency_service.convert_usd_to_rub(game.get('salePrice', 0), self.logger)
            normal_price_rub = self.currency_service.convert_usd_to_rub(game.get('normalPrice', 0), self.logger)
            savings = round(float(game.get('savings', 0)))
            store = self.stores_handler.get_store_name(game.get('storeID'))

            return (f"Игра дня: {title}!\n"
                    f"Скидка целых {savings}% в магазине {store}.\n"
                    f"Старая цена: {normal_price_rub} руб. Сейчас всего: {sale_price_rub} руб!")

        except Exception as e:
            self.logger.error(f"Game of the day error: {e}")
            return "Ошибка при поиске лучшего предложения."

    def get_games_by_budget(self, budget_rub):
        try:
            usd_rate = self.currency_service.get_usd_rate(self.logger)
            max_usd = float(budget_rub) / usd_rate

            deals = self.cheapshark_service.get_deals_by_budget(max_usd)

            if not deals:
                return f"На {budget_rub} руб. сейчас сложно найти что-то стоящее с высоким рейтингом. Попробуй чуть позже!"

            random.shuffle(deals)
            selection = deals[:3]

            message_lines = [f"Вот что можно взять на {budget_rub} рублей:"]
            for deal in selection:
                price_rub = self.currency_service.convert_usd_to_rub(deal['salePrice'], self.logger)
                store = self.stores_handler.get_store_name(deal['storeID'])
                message_lines.append(f"• {deal['title']} за {price_rub} руб. в {store}")

            return "\n".join(message_lines)

        except Exception as e:
            self.logger.error(f"Budget search error: {e}")
            return "Я запуталась в цифрах... Напиши сумму просто числом, например: 500."

    def get_free_games(self):
        try:
            freebies = self.cheapshark_service.get_free_games()

            if not freebies:
                return "На данный момент 100% скидок не найдено. Но можно заглянуть в раздел 'Дешево'!"

            message_lines = ["Актуальная халява:"]
            for game in freebies:
                store = self.stores_handler.get_store_name(game['storeID'])
                message_lines.append(f"• {game['title']} в магазине {store}")

            message_lines.append("\nУспей забрать, пока акция не закончилась!")
            return "\n".join(message_lines)

        except Exception as e:
            self.logger.error(f"Free games error: {e}")
            return "Ошибка при поиске халявы. Попробуй позже."

    def get_random_tip(self):
        tips = [
            "Цены на игры часто меняются по вторникам.",
            "Летняя распродажа Стим обычно начинается в конце июня.",
            "Эпик Геймс регулярно раздает игры бесплатно.",
            "В магазине ГОГ все игры продаются без защиты ДРМ.",
            "Следите за скидками в праздничные дни - они самые большие!",
            "Добавляйте игры в вишлист - так вы не пропустите скидку."
        ]
        return random.choice(tips)