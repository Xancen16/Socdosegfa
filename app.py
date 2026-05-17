from flask import Flask, jsonify
from config import Config
from models_of_bd import db, Sales, StoreCache, PriceCache, User, Favorite, AppStat
from ngrokfix import fix_ngrok_headers
from utils.logging_custom import setup_logger
from utils. bd_work import init_metrics, backup_db, maintenance_task, check_db_health
from services.d_r_mod import CurrencyService
from services.shops import CheapSharkService
from services.dialogsY import YandexService
from services.cache import CacheService
from handlers.commands import UserHandler
from handlers.commands2 import StoresHandler
from handlers.commands3 import GamesHandler
from handlers.commands4 import SalesHandler
from handlers.recomm import RecommendationsHandler
from handlers.alice import MainHandler


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    logger = setup_logger(app)
    app.after_request(fix_ngrok_headers)
    return app, logger


def init_database(app, logger):
    with app.app_context():
        db.create_all()
        if not Sales.query.first():
            from config import InitialDataConfig
            for sale_data in InitialDataConfig.SALES:
                sale = Sales(**sale_data)
                db.session.add(sale)
            db.session.commit()
            logger.info("Initial sales data added")


def register_routes(app, main_handler):

    @app.route('/post', methods=['POST'])
    def entry_point():
        return main_handler.handle_request()

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"status": "error", "msg": "not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"status": "error", "msg": "method not allowed"}), 405

    @app.errorhandler(500)
    def server_crash(e):
        app.logger.critical(f"Critical error: {e}")
        return jsonify({
            "version": "1.0",
            "response": {
                "text": "В работе приложения возникла внутренняя ошибка. Инженеры уже уведомлены. Пожалуйста, повторите запрос позже.",
                "end_session": False
            }
        }), 500


def run_startup_tasks(app, logger):
    with app.app_context():
        init_metrics(db)
        currency_service = CurrencyService()
        cheapshark_service = CheapSharkService(currency_service, logger)
        cheapshark_service.sync_stores(StoreCache, db)
        sales_handler = SalesHandler(db, logger)
        sales_handler.update_priority_sales()
        backup_db()
        cache_service = CacheService(PriceCache, db, logger)
        cache_service.clean_expired()
        if not check_db_health(db):
            logger.critical("Database health check failed!")
        logger.info("Application started successfully")


def main():
    app, logger = create_app()
    init_database(app, logger)
    currency_service = CurrencyService()
    cheapshark_service = CheapSharkService(currency_service, logger)
    yandex_service = YandexService(logger)
    cache_service = CacheService(PriceCache, db, logger)
    user_handler = UserHandler(db, logger)
    stores_handler = StoresHandler(cheapshark_service, currency_service, db, logger)
    games_handler = GamesHandler(
        cheapshark_service, cache_service, yandex_service,
        currency_service, stores_handler, logger
    )
    sales_handler = SalesHandler(db, logger)
    recommendations_handler = RecommendationsHandler(
        cheapshark_service, currency_service, stores_handler, logger
    )
    main_handler = MainHandler(
        user_handler, stores_handler, games_handler,
        sales_handler, recommendations_handler, logger
    )
    register_routes(app, main_handler)
    run_startup_tasks(app, logger)
    app.run(host='0.0.0.0', port=5000, debug=False)


if __name__ == '__main__':
    main()