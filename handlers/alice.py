from flask import request, jsonify
from config import InitialDataConfig
from utils.cleaner import extract_budget
from utils.datatest import validate_input_encoding
from utils.bd_work import get_stats_summary


class MainHandler:
    def __init__(self, user_handler, stores_handler, games_handler,
                 sales_handler, recommendations_handler, logger):
        self.user_handler = user_handler
        self.stores_handler = stores_handler
        self.games_handler = games_handler
        self.sales_handler = sales_handler
        self.recommendations_handler = recommendations_handler
        self.logger = logger

    def build_response(self, request_data, text, buttons=None, end_session=False, card_data=None):
        if buttons is None:
            buttons = InitialDataConfig.MAIN_MENU_BUTTONS

        formatted_buttons = [{"title": btn, "hide": True} for btn in buttons]

        response = {
            "version": request_data.get('version', '1.0'),
            "session": request_data.get('session'),
            "response": {
                "text": text,
                "buttons": formatted_buttons,
                "end_session": end_session
            }
        }

        if card_data:
            response["response"]["card"] = {
                "type": "BigImage",
                "image_id": card_data['image'],
                "title": card_data['title'],
                "description": text
            }

        return jsonify(response)

    def handle_welcome(self, request_data, user_id, is_new_session):
        if not is_new_session:
            return None

        user_info = self.user_handler.get_user_info(user_id)

        if user_info['total_requests'] > 0:
            current_rank, _, _ = self.user_handler.get_user_rank(user_info['total_requests'])
            welcome = (f"Здравствуйте! Рады вашему возвращению.\n"
                       f"Ваш текущий статус: {current_rank}.\n"
                       f"Какую игру или магазин проверим сегодня?")
        else:
            welcome = "Здравствуйте! Это сервис мониторинга цен на видеоигры. Какую информацию найти хотите сегодня?"

        return self.build_response(request_data, welcome)

    def process_command(self, request_data, user_id, command):
        cmd_lower = command.lower().strip()

        if cmd_lower == "магазины":
            stores = self.stores_handler.get_active_stores()
            buttons = [s['name'] for s in stores] + ["Назад"]
            return self.build_response(request_data, "Выберите магазин из списка ниже:", buttons=buttons)

        if any(word in cmd_lower for word in ["уровень", "мой лвл", "статус"]):
            message = self.user_handler.build_rank_message(user_id)
            return self.build_response(request_data, message)

        if "во что поиграть" in cmd_lower:
            rec_text = self.recommendations_handler.get_random_recommendation()
            return self.build_response(request_data, rec_text)

        if cmd_lower == "избранное":
            favorites = self.user_handler.get_favorites(user_id)
            if not favorites:
                return self.build_response(
                    request_data,
                    "Ваш список избранного пока пуст. Чтобы добавить игру, скажите 'Добавь [название] в избранное'."
                )
            fav_list = [f"{i + 1}. {game}" for i, game in enumerate(favorites)]
            return self.build_response(request_data, "Ваши игры:\n" + "\n".join(fav_list))

        if "добавь" in cmd_lower and "избранное" in cmd_lower:
            game_name = command.replace("добавь", "").replace("в избранное", "").strip()
            if game_name:
                if self.user_handler.add_to_favorites(user_id, game_name):
                    return self.build_response(request_data, f"Игра {game_name} добавлена в ваш список.")
                return self.build_response(request_data, "Эта игра уже есть в вашем списке.")

        if "игра дня" in cmd_lower:
            report = self.recommendations_handler.get_game_of_the_day()
            return self.build_response(request_data, report)

        budget = extract_budget(cmd_lower)
        if ("купить на" in cmd_lower or "до" in cmd_lower) and budget:
            result = self.recommendations_handler.get_games_by_budget(budget)
            return self.build_response(request_data, result)

        if any(word in cmd_lower for word in ["экономия", "бесплатн", "халява"]):
            result = self.recommendations_handler.get_free_games()
            return self.build_response(request_data, result)

        store_id = self.stores_handler.validate_store_request(cmd_lower)
        if store_id:
            deals_message = self.stores_handler.get_store_deals_message(store_id)
            store_name = self.stores_handler.get_store_name(store_id)
            self.user_handler.update_user_stats(user_id, store=store_name)
            return self.build_response(request_data, deals_message)

        if any(word in cmd_lower for word in ["когда", "распродаж", "календарь", "сейл"]):
            message = self.sales_handler.build_sales_calendar_message()
            return self.build_response(request_data, message)

        if any(word in cmd_lower for word in ["помощь", "че умеешь", "умеешь"]):
            help_text = (
                "Инструкция по использованию сервиса:\n"
                "1. Нажмите 'Магазины', чтобы выбрать площадку.\n"
                "2. Введите название игры для поиска цены.\n"
                "3. Скажите 'Добавь [игра] в избранное' для сохранения.\n"
                "4. Спросите про распродажи для календаря акций.\n"
                "Какое действие выполнить?"
            )
            return self.build_response(request_data, help_text)

        if "статистика" in cmd_lower:
            return self.build_response(request_data, get_stats_summary())

        if "совет" in cmd_lower:
            tip = self.recommendations_handler.get_random_tip()
            return self.build_response(request_data, tip)

        if cmd_lower == "категории":
            cat_buttons = ["Шутеры", "РПГ", "Хорроры", "Для слабых ПК", "Назад"]
            return self.build_response(request_data, "Выберите жанр для подбора отличных игр со скидками:",
                                       buttons=cat_buttons)

        if "шутеры" in cmd_lower:
            result = self.recommendations_handler.get_random_recommendation("shooter")
            return self.build_response(request_data, result)

        if "рпг" in cmd_lower or "rpg" in cmd_lower:
            result = self.recommendations_handler.get_random_recommendation("rpg")
            return self.build_response(request_data, result)

        if "хорроры" in cmd_lower or "horror" in cmd_lower:
            result = self.recommendations_handler.get_random_recommendation("horror")
            return self.build_response(request_data, result)

        if "слабых пк" in cmd_lower:
            result = self.recommendations_handler.get_random_recommendation("edition")
            return self.build_response(request_data, result)

        if any(word in cmd_lower for word in ["67", "six seven", "сикс севен", "шесть семь"]):
            return self.build_response(request_data, "Да какой сикс севен!?")

        if len(cmd_lower) > 1:
            self.user_handler.update_user_stats(user_id, query=cmd_lower)

            result_text, card_data = self.games_handler.get_game_with_card(cmd_lower)
            return self.build_response(request_data, result_text, card_data=card_data)

        return self.build_response(
            request_data,
            "Ожидаю вашу команду. Выберите один из предложенных магазинов или введите название игры."
        )

    def handle_request(self):
        data = request.json

        if not validate_input_encoding(data):
            return jsonify({"status": "error", "message": "Bad request"}), 400

        session = data.get('session', {})
        user_id = session.get('user', {}).get('user_id', 'anon_user')
        request_obj = data.get('request', {})
        command = request_obj.get('command', '')
        is_new_session = session.get('new', False)

        welcome_response = self.handle_welcome(data, user_id, is_new_session)
        if welcome_response:
            return welcome_response

        return self.process_command(data, user_id, command)