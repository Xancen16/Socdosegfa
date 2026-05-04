# импорты
import requests
import logging
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from logging.handlers import RotatingFileHandler

# приложение 0_0
app = Flask(__name__)

# траблы ngrok-а
@app.after_request
def add_header(response):
    response.headers['ngrok-skip-browser-warning'] = 'true'
    return response

# логи
logging.basicConfig(level=logging.INFO)
handler = RotatingFileHandler('skill.log', maxBytes=10000, backupCount=1)
handler.setFormatter(logging.Formatter(
    '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
)) #формат записи если что
app.logger.addHandler(handler)

# БД-шка =UwU=
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///game_analyzer.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#Что то страшное 0_0 (
class UserActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), index=True)
    last_store = db.Column(db.String(50))
    last_query = db.Column(db.String(100))
    query_time = db.Column(db.DateTime, default=datetime.utcnow)

# распродажи мб
class SaleCalendar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    store = db.Column(db.String(50))
    event_name = db.Column(db.String(100))
    start_date = db.Column(db.Date)
    is_confirmed = db.Column(db.Boolean, default=False)

# создание таблиц (у Ярика SQLite нет.....)
with app.app_context():
    db.create_all()
    if not SaleCalendar.query.first():
        events = [
            SaleCalendar(store="Steam", event_name="Летняя распродажа",
                         start_date=date(2026, 6, 25), is_confirmed=True),
            SaleCalendar(store="Epic Games", event_name="Мегараспродажа",
                         start_date=date(2026, 5, 14), is_confirmed=False)
        ]
        db.session.bulk_save_objects(events)
        db.session.commit()

# функции (не математические)

# цифры.... ааааа (б), это коды магазинов с сайта

def get_store_name(store_id):
    stores = {
        "1": "Steam",
        "25": "Epic Games Store",
        "2": "GOG",
        "3": "Humble Store",
        "7": "GOG (Direct)"
    }
    return stores.get(str(store_id), "Unknown Store") # ты кто 0_-

def fetch_top_deals(store_id):
    try:
        url = f"https://www.cheapshark.com/api/1.0/deals?storeID={store_id}&onSale=1&pageSize=5"
        response = requests.get(url, timeout=5) # запросек
        if response.status_code != 200:
            return "Не удалось связаться с сервером цен." # печалька(

        data = response.json()
        if not data:
            return "Скидок в этом магазине сейчас нет." # печалька(

        lines = [f"Топ скидок в {get_store_name(store_id)}:"] # а это тема!
        for g in data:
            title = g.get('title', 'Unknown')
            price = g.get('salePrice', '0')
            savings = round(float(g.get('savings', 0)))
            lines.append(f"• {title}: ${price} (-{savings}%)")
        return "\n".join(lines)
    except Exception as e:
        app.logger.error(f"API Error: {e}")
        return "Ошибка при получении данных." # -_-

def search_game_price(game_name):
    try:
        url = f"https://www.cheapshark.com/api/1.0/games?title={game_name}&limit=1"
        search_res = requests.get(url, timeout=5).json() # запросек
        if not search_res:
            return f"К сожалению, я не нашла игру '{game_name}'." # (

        game_id = search_res[0]['gameID']
        detail_url = f"https://www.cheapshark.com/api/1.0/games?id={game_id}" # еще запрос...
        details = requests.get(detail_url, timeout=5).json()

        best_deal = details['deals'][0]
        store = get_store_name(best_deal['storeID'])
        price = best_deal['price']

        return f"Самое выгодное предложение на {game_name}: в {store} за ${price}." # о, это нада
    except Exception as e:
        app.logger.error(f"Search Error: {e}")
        return "Произошла ошибка при поиске игры."


# сохраним что он искал)
def save_user_action(uid, store=None, query=None):
    try:
        new_act = UserActivity(user_id=uid, last_store=store, last_query=query)
        db.session.add(new_act)
        db.session.commit()
    except Exception as e:
        app.logger.error(f"DB Error: {e}")
        db.session.rollback()

# Алиса (help)
@app.route('/post', methods=['POST'])
def main():
    req = request.json
    app.logger.info(f"Request: {req}") # каждый запрос в логи

    session = req.get('session', {})
    request_data = req.get('request', {})

    # Хаваем ID юзера >:)
    user_id = session.get('user', {}).get('user_id') or \
              session.get('application', {}).get('application_id', 'anonymous')
    # че он там просил.....
    command = request_data.get('command', '').lower().strip()
# кнопочкеееееееее
    buttons = [
        {"title": "Steam", "hide": True},
        {"title": "Epic Games", "hide": True},
        {"title": "Распродажи", "hide": True},
        {"title": "Помощь", "hide": True}
    ]

    res_text = ""

    if session.get('new'):
        last_visit = UserActivity.query.filter_by(user_id=user_id).order_by(UserActivity.query_time.desc()).first()
        if last_visit:
            # Какой магаз посещал в последний раз
            context = last_visit.last_store or last_visit.last_query or "поиском игр"
            res_text = f"С возвращением! Снова ищем скидки? В прошлый раз ты интересовался: {context}."
        else:
            res_text = "Привет! Я Анализатор Цен. Могу показать скидки в Steam, Epic Games или найти цену на конкретную игру. С чего начнем?"

    elif not command:
        res_text = "Я тебя слушаю! Можно выбрать магазин на кнопках или просто сказать название игры."
    # тут все понятно
    elif any(word in command for word in ["стим", "steam"]):
        res_text = fetch_top_deals(1)
        save_user_action(user_id, store="Steam")

    elif any(word in command for word in ["эпик", "epic", "егс", "egs"]):
        res_text = fetch_top_deals(25)
        save_user_action(user_id, store="Epic Games Store")

    elif any(word in command for word in ["когда", "распродажа", "календарь", "скидки будут"]):
        events = SaleCalendar.query.order_by(SaleCalendar.start_date).all()
        event_list = []
        for e in events:
            status = "(подтверждено)" if e.is_confirmed else "(прогноз)"
            event_list.append(f"• {e.store}: {e.event_name} — {e.start_date.strftime('%d.%m')} {status}")
        res_text = "Расписание ближайших распродаж:\n" + "\n".join(event_list)

    elif "помощь" in command or "что ты умеешь" in command:
        res_text = ("Я умею:\n"
                    "1. Показывать топ скидок в Steam и Epic Games.\n"
                    "2. Искать минимальную цену на игру.\n"
                    "3. Подсказывать даты крупных распродаж.")

    elif "найди" in command or "поиск" in command or len(command.split()) <= 3:
        search_term = command.replace("найди", "").replace("поиск", "").strip()
        if not search_term:
            res_text = "Какую игру мне найти?"
        else:
            res_text = search_game_price(search_term)
            save_user_action(user_id, query=search_term)

    else:
        res_text = "Пока я не знаю такой команды. Попробуй выбрать магазин или назови игру."

    return jsonify({
        "version": req.get("version", "1.0"),
        "session": {
            "session_id": session.get("session_id"),
            "message_id": session.get("message_id"),
            "user_id": session.get("user_id")
        },
        "response": {
            "text": res_text,
            "buttons": buttons,
            "end_session": False
        }
    })

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "version": "1.0",
        "response": {
            "text": "Произошла внутренняя ошибка сервера. Попробуйте позже.",
            "end_session": False
        }
    }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)