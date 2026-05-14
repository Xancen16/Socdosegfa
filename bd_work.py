import os
import shutil
import time
from models_of_bd import PriceCache, AppStat, User


def maintenance_task(db):
    try:
        deleted = PriceCache.query.filter(
            PriceCache.created_at < time.time() - 86400
        ).delete()
        db.session.commit()
        return deleted
    except Exception:
        db.session.rollback()
        return 0


def backup_db(db_path='skill_data.db'):
    if os.path.exists(db_path):
        backup_path = f'{db_path}.bak'
        shutil.copy(db_path, backup_path)
        return True
    return False


def check_db_health(db):
    try:
        db.session.execute(db.text('SELECT 1'))
        return True
    except Exception:
        return False


def get_stats_summary():
    user_count = User.query.count()
    cache_count = PriceCache.query.count()
    return f"Всего пользователей в системе {user_count}. Обработано уникальных запросов {cache_count}."


def init_metrics(db):
    stat = AppStat.query.filter_by(metric_name='starts').first()
    if not stat:
        db.session.add(AppStat(metric_name='starts', metric_value=1))
    else:
        stat.metric_value += 1
    db.session.commit()


def audit_log(app_logger, db):
    user_count = User.query.count()
    sales_count = db.session.query(db.Model).count()
    app_logger.info(f"Аудит: Пользователей - {user_count}")