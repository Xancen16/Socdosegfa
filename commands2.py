from models_of_bd import StoreCache


class StoresHandler:
    def __init__(self, cheapshark_service, currency_service, db, logger):
        self.cheapshark_service = cheapshark_service
        self.currency_service = currency_service
        self.db = db
        self.logger = logger

    def get_store_name(self, store_id):
        store = StoreCache.query.filter_by(store_id=str(store_id)).first()
        return store.store_name if store else "Неизвестный магазин"

    def get_active_stores(self, limit=12):
        stores = StoreCache.query.filter_by(is_active=True).limit(limit).all()
        return [{'id': s.store_id, 'name': s.store_name} for s in stores]

    def get_store_deals_message(self, store_id):
        try:
            # Получаем курс
            usd_rate = self.currency_service.get_usd_rate(self.logger)

            # Получаем скидки из API
            deals = self.cheapshark_service.get_deals_by_store(store_id)

            if deals is None:
                return "Техническая задержка на сервере. Повторите попытку позже."

            if not deals:
                return "В данном магазине на текущий момент нет активных акций."

            # Формируем сообщение
            store_name = self.get_store_name(store_id)
            message_lines = [f"Актуальные предложения из {store_name} (курс: {round(usd_rate, 2)} руб):"]

            for item in deals[:10]:
                title = item.get('title', 'Без названия')
                price_usd = float(item.get('salePrice', '0'))
                price_rub = round(price_usd * usd_rate)
                discount = round(float(item.get('savings', 0)))

                if discount > 0:
                    message_lines.append(f"- {title}: {price_rub} руб (скидка {discount}%)")
                else:
                    message_lines.append(f"- {title}: {price_rub} руб")

            return "\n".join(message_lines)

        except Exception as e:
            self.logger.error(f"Error getting store deals: {e}")
            return "Не удалось связаться с базой данных цен."

    def validate_store_request(self, command):
        stores = StoreCache.query.all()
        for store in stores:
            if store.store_name.lower() in command:
                return store.store_id
        return None

    def get_stores_buttons(self):
        stores = self.get_active_stores()
        return [store['name'] for store in stores]