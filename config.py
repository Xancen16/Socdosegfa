import os
from datetime import date


class Config:
    SECRET_KEY = os.urandom(24)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///skill_data.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # логи
    LOG_PATH = 'skill_v2_final.log'
    LOG_MAX_BYTES = 100000
    LOG_BACKUP_COUNT = 5

    # кэш
    CACHE_TTL = 14400  # 4 часа
    CACHE_CLEANUP_AGE = 86400  # 24 часа


class YandexConfig:
    SKILL_ID = "498a9f1b-b89f-46ca-8ea0-5f68e7c24c10"
    OAUTH_TOKEN = "49636d3f79ea4b9399a44b7d9e59319e"

    @property
    def IMAGES_API_URL(self):
        return f"https://dialogs.yandex.net/api/v1/skills/{self.SKILL_ID}/images"


class CheapSharkConfig:
    DEALS_API = "https://www.cheapshark.com/api/1.0/deals"
    GAMES_API = "https://www.cheapshark.com/api/1.0/games"
    STORES_API = "https://www.cheapshark.com/api/1.0/stores"
    CURRENCY_API = "https://www.cbr-xml-daily.ru/daily_json.js"

    TIMEOUT_SHORT = 3
    TIMEOUT_MEDIUM = 5
    TIMEOUT_LONG = 7


class InitialDataConfig:
    CURRENT_YEAR = 2026
    SALES = [
        {"provider": "Steam", "event_title": "Летняя распродажа",
         "start_at": date(CURRENT_YEAR, 6, 25), "prob": 100, "is_live": True},
        {"provider": "Epic Games", "event_title": "Mega Sale",
         "start_at": date(CURRENT_YEAR, 5, 14), "prob": 80, "is_live": False},
        {"provider": "GOG", "event_title": "Winter Sale",
         "start_at": date(CURRENT_YEAR, 12, 12), "prob": 100, "is_live": False},
        {"provider": "Ubisoft", "event_title": "Spring Sale",
         "start_at": date(CURRENT_YEAR, 3, 20), "prob": 90, "is_live": False},
        {"provider": "Origin", "event_title": "Action Sale",
         "start_at": date(CURRENT_YEAR, 4, 10), "prob": 75, "is_live": False},
        {"provider": "Steam", "event_title": "Осенняя распродажа",
         "start_at": date(CURRENT_YEAR, 11, 24), "prob": 100, "is_live": False},
        {"provider": "GOG", "event_title": "Back to School",
         "start_at": date(CURRENT_YEAR, 8, 30), "prob": 85, "is_live": False}
    ]


    MAIN_MENU_BUTTONS = [
        "Во что поиграть?", "Мой уровень", "Магазины",
        "Игра дня", "До 500 рублей", "Распродажи", "Помощь", "Категории", "Избранное", "Совет"
    ]


    NOISE_WORDS = [
        "найди", "пожалуйста", "алиса", "скажи", "поиск",
        "сколько", "стоит", "купить", "игру", "хочу", "запусти",
        "мне", "надо", "отыщи", "проверь", "глянь", "покажи",
        "в избранное", "добавь"
    ]


    RANKS = [
        {"name": "Новичок 👶", "threshold": 0, "next": "Геймер"},
        {"name": "Геймер 🎮", "threshold": 5, "next": "Охотник за скидками"},
        {"name": "Охотник за скидками 🏹", "threshold": 15, "next": "Мастер экономии"},
        {"name": "Мастер экономии 💰", "threshold": 30, "next": "Легенда распродаж"},
        {"name": "Легенда распродаж 🏆", "threshold": 50, "next": None}
    ]