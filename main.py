import requests
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# --- БАЗА ДАННЫХ (ORM) ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///game_analyzer.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class UserActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100))
    last_store = db.Column(db.String(50))  # Контекст: какой магазин смотрел последним
    query_time = db.Column(db.DateTime, default=datetime.utcnow)


class SaleCalendar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    store = db.Column(db.String(50))
    event_name = db.Column(db.String(100))
    start_date = db.Column(db.Date)


with app.app_context():
    db.create_all()
    if not SaleCalendar.query.first():
        event = SaleCalendar(store="Steam", event_name="Летняя распродажа",
                             start_date=datetime(2026, 6, 25).date())
        db.session.add(event)
        db.session.commit()


def fetch_games(store_id, min_savings=50):
    try:
        url = f"https://www.cheapshark.com/api/1.0/deals?storeID={store_id}&onSale=1&pageSize=3"
        data = requests.get(url, timeout=3).json()
        if not data: return "Скидок пока нет."
        return "\n".join([f"• {g['title']}: ${g['salePrice']} (-{round(float(g['savings']))}%)" for g in data])
    except:
        return "Сервис цен временно недоступен."


# --- ОБРАБОТКА ЗАПРОСОВ АЛИСЫ ---

@app.route('/post', methods=['POST'])
def main():
    req = request.json
    user_id = req['session']['user_id']
    command = req['request']['command'].lower()

    res_text = ""
    buttons = [
        {"title": "Цены в Steam", "hide": True},
        {"title": "Цены в Epic Games", "hide": True},
        {"title": "Когда распродажа?", "hide": True}
    ]
    user_record = UserActivity.query.filter_by(user_id=user_id).order_by(UserActivity.query_time.desc()).first()

    if req['session']['new']:
        if user_record:
            res_text = f"С возвращением! В прошлый раз ты проверял {user_record.last_store}. Посмотрим снова или выберем другой?"
        else:
            res_text = "Привет! Я проанализирую цены в Steam и Epic Games. Где ищем скидки?"

    elif "стим" in command or "steam" in command:
        res_text = f"Анализирую Steam... Вот лучшие предложения:\n{fetch_games(1)}"
        save_activity(user_id, "Steam")

    elif "эпик" in command or "epic" in command:
        res_text = f"В Epic Games Store сейчас выгодно:\n{fetch_games(25)}"
        save_activity(user_id, "Epic Games")

    elif "когда" in command or "расписание" in command:
        event = SaleCalendar.query.first()  # Берем ближайшее из БД
        res_text = f"Ближайший крупный ивент: {event.event_name} в {event.store}. Начнется {event.start_date}."

    else:
        res_text = "Я могу сравнить цены в Steam и Epic Games. Просто нажми на кнопку!"

    return jsonify({
        "session": req["session"],
        "version": req["version"],
        "response": {
            "text": res_text,
            "buttons": buttons,
            "end_session": False
        }
    })


def save_activity(uid, store):
    new_act = UserActivity(user_id=uid, last_store=store)
    db.session.add(new_act)
    db.session.commit()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
