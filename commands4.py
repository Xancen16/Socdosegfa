from datetime import date
from models_of_bd import Sales


class SalesHandler:
    def __init__(self, db, logger):
        self.db = db
        self.logger = logger

    def get_upcoming_sales(self):
        today = date.today()
        sales = Sales.query.filter(Sales.start_at >= today).order_by(Sales.start_at).all()
        return sales

    def build_sales_calendar_message(self):
        upcoming = self.get_upcoming_sales()

        if not upcoming:
            return "На текущий момент информация о будущих распродажах не поступала."

        message_lines = ["График ближайших распродаж в магазинах:"]

        for sale in upcoming:
            date_str = sale.start_at.strftime('%d.%m')
            confidence = "прогноз подтвержден" if sale.prob > 90 else "дата ориентировочная"
            message_lines.append(f"- {sale.provider}: {sale.event_title} ({date_str}, {confidence})")

        return "\n".join(message_lines)

    def update_priority_sales(self):
        try:
            Sales.query.filter(Sales.prob > 90).update({Sales.priority: 1})
            self.db.session.commit()
            self.logger.info("Priority sales updated")
        except Exception as e:
            self.logger.error(f"Error updating priority sales: {e}")
            self.db.session.rollback()