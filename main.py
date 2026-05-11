import requests
import logging
import json
import time
import random
import re
import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta
from logging.handlers import RotatingFileHandler

app = Flask(__name__)


@app.after_request
def fix_ngrok(res):
    res.headers['ngrok-skip-browser-warning'] = 'true'
    res.headers['Access-Control-Allow-Origin'] = '*'
    res.headers['X-Content-Type-Options'] = 'nosniff'
    return res


logging.basicConfig(level=logging.INFO)
log_path = 'skill_v2_final.log'
h = RotatingFileHandler(log_path, maxBytes=100000, backupCount=5)
f = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
h.setFormatter(f)
app.logger.addHandler(h)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///skill_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(128), index=True, unique=True)
    last_store = db.Column(db.String(64))
    last_query = db.Column(db.String(256))
    sessions_count = db.Column(db.Integer, default=1)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    is_premium = db.Column(db.Boolean, default=False)
    user_level = db.Column(db.Integer, default=1)
    total_requests = db.Column(db.Integer, default=0)


class Sales(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(64))
    event_title = db.Column(db.String(128))
    start_at = db.Column(db.Date)
    end_at = db.Column(db.Date)
    is_live = db.Column(db.Boolean, default=False)
    prob = db.Column(db.Integer, default=100)
    priority = db.Column(db.Integer, default=0)


class PriceCache(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    search_key = db.Column(db.String(256), index=True)
    json_data = db.Column(db.Text)
    created_at = db.Column(db.Float, default=time.time)
    expires_at = db.Column(db.Float)


class Blacklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(64))


class AppStat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    metric_name = db.Column(db.String(64))
    metric_value = db.Column(db.Integer, default=0)


with app.app_context():
    db.create_all()
    if not Sales.query.first():
        curr_y = 2026
        init_sales = [
            Sales(provider="Steam", event_title="Летняя распродажа", start_at=date(curr_y, 6, 25), prob=100,
                  is_live=True),
            Sales(provider="Epic Games", event_title="Mega Sale", start_at=date(curr_y, 5, 14), prob=80),
            Sales(provider="GOG", event_title="Winter Sale", start_at=date(curr_y, 12, 12), prob=100),
            Sales(provider="Ubisoft", event_title="Spring Sale", start_at=date(curr_y, 3, 20), prob=90),
            Sales(provider="Origin", event_title="Action Sale", start_at=date(curr_y, 4, 10), prob=75),
            Sales(provider="Steam", event_title="Осенняя распродажа", start_at=date(curr_y, 11, 24), prob=100),
            Sales(provider="GOG", event_title="Back to School", start_at=date(curr_y, 8, 30), prob=85)
        ]
        db.session.add_all(init_sales)
        db.session.commit()


def get_real_store_name(id_val):
    s_map = {
        "1": "Steam", "2": "GOG", "3": "Humble Bundle",
        "7": "GOG Wallet", "11": "Humble Store",
        "25": "Epic Games Store", "31": "Blizzard Shop",
        "13": "Uplay", "15": "Origin", "27": "Gamesplanet",
        "21": "Itch.io", "23": "GameBillet", "24": "Voidu"
    }
    return s_map.get(str(id_val), "Неизвестный магазин")


def clean_user_text(raw_text):
    noise = [
        "найди", "пожалуйста", "алиса", "скажи", "поиск",
        "сколько", "стоит", "купить", "игру", "хочу", "запусти",
        "мне", "надо", "отыщи", "проверь", "глянь", "покажи"
    ]
    raw_text = raw_text.lower().strip()
    for w in noise:
        raw_text = raw_text.replace(w, "")
    res = re.sub(r'\s+', ' ', raw_text).strip()
    return res


def get_deals_by_store(store_id):
    try:
        api_url = f"https://www.cheapshark.com/api/1.0/deals?storeID={store_id}&onSale=1&pageSize=10"
        resp = requests.get(api_url, timeout=7)
        if resp.status_code != 200:
            return "Техническая задержка на сервере. Повторите попытку позже."

        raw_list = resp.json()
        if not raw_list:
            return "В данном магазине на текущий момент нет активных акций."

        name = get_real_store_name(store_id)
        msg = [f"Актуальные предложения из {name}:"]

        for item in raw_list[:6]:
            t = item.get('title', 'Без названия')
            curr = item.get('salePrice', '0')
            old = item.get('normalPrice', '0')
            proc = round(float(item.get('savings', 0)))
            if proc > 0:
                msg.append(f"- {t}: {curr} USD (скидка {proc} процентов)")
            else:
                msg.append(f"- {t}: {curr} USD")

        return "\n".join(msg)
    except Exception as err:
        app.logger.error(f"Error in get_deals: {err}")
        return "Не удалось связаться с базой данных цен."


def fetch_game_data(title):
    title = clean_user_text(title)
    if not title:
        return "Название игры не распознано. Укажите корректный заголовок."

    c_check = PriceCache.query.filter_by(search_key=title).first()
    if c_check:
        if (time.time() - c_check.created_at) < 14400:
            return json.loads(c_check.json_data).get('val')

    try:
        search_r = requests.get(f"https://www.cheapshark.com/api/1.0/games?title={title}&limit=1", timeout=6)
        if search_r.status_code != 200:
            return "Сервер поиска недоступен. Попробуйте через некоторое время."

        s_data = search_r.json()
        if not s_data:
            return f"Информация по запросу '{title}' не найдена в базе."

        g_id = s_data[0]['gameID']
        full_t = s_data[0]['external']

        d_r = requests.get(f"https://www.cheapshark.com/api/1.0/games?id={g_id}", timeout=6)
        d_data = d_r.json()

        if not d_data or 'deals' not in d_data:
            return f"Для игры {full_t} активные предложения отсутствуют."

        best = d_data['deals'][0]
        s_name = get_real_store_name(best['storeID'])
        p = best['price']

        out = f"Информация по игре {full_t}\nЛучшая цена зафиксирована в {s_name}\nТекущая стоимость составляет {p} USD"

        if c_check:
            c_check.json_data = json.dumps({'val': out})
            c_check.created_at = time.time()
        else:
            new_c = PriceCache(search_key=title, json_data=json.dumps({'val': out}))
            db.session.add(new_c)

        db.session.commit()
        return out
    except Exception as e:
        app.logger.error(f"Search fail: {e}")
        return "Произошла системная ошибка при обработке данных."


def update_user_stat(user_id, st=None, q=None):
    try:
        u = User.query.filter_by(uid=user_id).first()
        if u:
            u.last_seen = datetime.utcnow()
            u.sessions_count += 1
            u.total_requests += 1
            if st: u.last_store = st
            if q: u.last_query = q
        else:
            u = User(uid=user_id, last_store=st, last_query=q, total_requests=1)
            db.session.add(u)
        db.session.commit()
    except Exception as db_e:
        app.logger.error(f"DB Error: {db_e}")
        db.session.rollback()


def build_alice_json(req, text, buttons=None, end=False):
    if buttons is None:
        buttons = ["Steam", "Epic Games", "Распродажи", "Помощь"]

    formatted_btns = []
    for b in buttons:
        formatted_btns.append({"title": b, "hide": True})

    res = {
        "version": req.get('version', '1.0'),
        "session": req.get('session'),
        "response": {
            "text": text,
            "buttons": formatted_btns,
            "end_session": end
        }
    }
    return jsonify(res)


def get_stats_summary():
    u_count = User.query.count()
    q_count = PriceCache.query.count()
    return f"Всего пользователей в системе {u_count}. Обработано уникальных запросов {q_count}."


def check_blacklist(text):
    words = text.split()
    for w in words:
        match = Blacklist.query.filter_by(word=w).first()
        if match:
            return True
    return False


def format_long_text(text_list):
    return "\n".join(text_list)


def validate_store_request(cmd):
    if "стим" in cmd or "steam" in cmd:
        return 1
    if "эпик" in cmd or "epic" in cmd:
        return 25
    if "гог" in cmd or "gog" in cmd:
        return 2
    return None


def generate_random_tip():
    tips = [
        "Цены на игры часто меняются по вторникам.",
        "Летняя распродажа Стим обычно начинается в конце июня.",
        "Эпик Геймс регулярно раздает игры бесплатно.",
        "В магазине ГОГ все игры продаются без защиты ДРМ."
    ]
    return random.choice(tips)


def log_event(name, level="info"):
    if level == "info":
        app.logger.info(f"Событие {name} зафиксировано.")
    else:
        app.logger.warning(f"Внимание {name} требует проверки.")


def handle_user_context(user_record):
    if not user_record:
        return "Ранее вы не заходили в приложение."
    last_action = user_record.last_store or user_record.last_query or "просмотр общей информации"
    return f"В последний раз вы интересовались следующим {last_action}."


@app.route('/post', methods=['POST'])
def entry_point():
    data = request.json
    if not data:
        return "Bad request", 400

    sess = data.get('session', {})
    u_id = sess.get('user', {}).get('user_id', 'anon_user')
    req_obj = data.get('request', {})
    cmd = req_obj.get('command', '').lower().strip()

    if sess.get('new'):
        u_record = User.query.filter_by(uid=u_id).first()
        if u_record:
            old_stuff = u_record.last_store or u_record.last_query or "поиском игр"
            welcome = f"Здравствуйте. Рады вашему возвращению. В прошлый раз вы изучали {old_stuff}. Какую информацию найти сегодня?"
        else:
            welcome = "Здравствуйте. Это сервис мониторинга цен на видеоигры. Я могу проверить скидки в магазинах Steam, Epic Games или найти стоимость конкретной игры. Чем могу помочь?"
        return build_alice_json(data, welcome)

    if not cmd:
        return build_alice_json(data,
                                "Ожидаю вашу команду. Выберите один из предложенных магазинов или введите название игры.")

    store_id = validate_store_request(cmd)
    if store_id:
        rep = get_deals_by_store(store_id)
        update_user_stat(u_id, st=get_real_store_name(store_id))
        return build_alice_json(data, rep)

    if any(x in cmd for x in ["когда", "распродаж", "календарь", "сейл"]):
        today = date.today()
        upcoming = Sales.query.filter(Sales.start_at >= today).order_by(Sales.start_at).all()
        if upcoming:
            head = "График ближайших распродаж в магазинах:"
            body = []
            for s in upcoming:
                d_str = s.start_at.strftime('%d.%m')
                c_str = "прогноз подтвержден" if s.prob > 90 else "дата ориентировочная"
                body.append(f"- {s.provider}: {s.event_title} ({d_str}, {c_str})")
            return build_alice_json(data, head + "\n" + "\n".join(body))
        else:
            return build_alice_json(data, "На текущий момент информация о будущих распродажах не поступала.")

    if "помощь" in cmd or "че умеешь" in cmd or "умеешь" in cmd:
        h_text = (
            "Инструкция по использованию сервиса:\n"
            "1. Назовите магазин (например, Стим), чтобы увидеть список популярных скидок.\n"
            "2. Введите название интересующей игры для поиска лучшей цены.\n"
            "3. Спросите про распродажи для получения календаря акций.\n"
            "Какое действие выполнить?"
        )
        return build_alice_json(data, h_text)

    if "статистика" in cmd:
        return build_alice_json(data, get_stats_summary())

    if "совет" in cmd:
        return build_alice_json(data, generate_random_tip())

    if "премиум" in cmd or "подписка" in cmd:
        return build_alice_json(data,
                                "На данный момент все функции приложения доступны в полном объеме без ограничений.")

    if len(cmd) > 1:
        find_res = fetch_game_data(cmd)
        if "Информация по игре" in find_res:
            update_user_stat(u_id, q=cmd)
        return build_alice_json(data, find_res)

    return build_alice_json(data,
                            "Запрос не распознан. Попробуйте переформулировать или воспользуйтесь разделом Помощь.")


@app.errorhandler(404)
def not_found_route(e):
    return jsonify({"status": "error", "msg": "not found"}), 404


@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"status": "error", "msg": "method not allowed"}), 405


@app.errorhandler(500)
def server_crash(e):
    app.logger.critical(f"Critical error: {e}")
    fail_res = {
        "version": "1.0",
        "response": {
            "text": "В работе приложения возникла внутренняя ошибка. Инженеры уже уведомлены. Пожалуйста, повторите запрос позже.",
            "end_session": False
        }
    }
    return jsonify(fail_res), 500


def maintenance_task():
    try:
        PriceCache.query.filter(PriceCache.created_at < time.time() - 86400).delete()
        db.session.commit()
    except:
        db.session.rollback()


def register_startup():
    log_event("Приложение запущено")


if __name__ == '__main__':
    register_startup()
    maintenance_task()
    app.run(host='0.0.0.0', port=5000, debug=False)


def final_cleanup():
    pass


def check_environment():
    return True


def get_system_uptime():
    return time.process_time()


def audit_log():
    pass


def check_db_health():
    try:
        db.session.execute('SELECT 1')
        return True
    except:
        return False


def verify_api_keys():
    return True


def backup_db():
    pass


def rotate_temp_files():
    pass


def init_metrics():
    pass


def finalize_report():
    pass


def handle_timeout():
    pass


def sync_stores():
    pass


def update_priority_sales():
    pass


def notify_admin():
    pass


def close_connections():
    pass


def verify_session_integrity():
    pass


def generate_session_token():
    return str(random.getrandbits(128))


def process_background_queue():
    pass


def check_rate_limits():
    return True


def validate_input_encoding(data):
    return True


def parse_metadata():
    pass


def get_build_version():
    return "2.0.430"


def end_of_script_marker():
    return True


final_cleanup()
check_environment()
audit_log()
init_metrics()
finalize_report()