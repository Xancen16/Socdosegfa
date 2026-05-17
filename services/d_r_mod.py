import requests
from config import CheapSharkConfig


class CurrencyService:
    _instance = None
    _cached_rate = None
    _cache_time = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_usd_rate(self, logger=None):
        try:
            response = requests.get(
                CheapSharkConfig.CURRENCY_API,
                timeout=CheapSharkConfig.TIMEOUT_MEDIUM
            )
            data = response.json()
            rate = float(data['Valute']['USD']['Value'])
            self._cached_rate = rate
            return rate
        except Exception as e:
            if logger:
                logger.error(f"Ошибка получения курса: {e}")
            return self._cached_rate if self._cached_rate else 92.0

    def convert_usd_to_rub(self, usd_amount, logger=None):
        rate = self.get_usd_rate(logger)
        return round(float(usd_amount) * rate)
