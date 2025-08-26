# max_bot.py
import json
import asyncio
from matrix_client.client import MatrixClient
import telebot
import requests
import os


class MaxBot:
    def __init__(self):
        self.config = self.load_config()

        self.matrix_client = MatrixClient(
            self.config.get('matrix_homeserver', 'https://matrix.example.com')
        )
        self.matrix_client.login(
            username=self.config.get('matrix_username'),
            password=self.config.get('matrix_password')
        )

        self.tg_bot = telebot.TeleBot(self.config.get('telegram_bot_token'))

        self.max_token = self.config.get('max_token')
        self.max_user_id = self.config.get('max_user_id')

    def load_config(self):
        config = {}

        if os.path.exists('max_config.json'):
            with open('max_config.json', 'r', encoding='utf-8') as f:
                max_config = json.load(f)
                config.update(max_config)

        config.update({
            'matrix_homeserver': os.getenv('MATRIX_HOMESERVER', 'https://matrix.example.com'),
            'matrix_username': os.getenv('MATRIX_USERNAME'),
            'matrix_password': os.getenv('MATRIX_PASSWORD'),
            'matrix_room_id': os.getenv('MATRIX_ROOM_ID'),
            'telegram_bot_token': os.getenv('TELEGRAM_BOT_TOKEN'),
            'telegram_chat_id': os.getenv('TELEGRAM_CHAT_ID'),
            'max_token': os.getenv('MAX_TOKEN') or config.get('token'),
            'max_user_id': os.getenv('MAX_USER_ID') or config.get('user_id')
        })

        return config

    def ensure_auth(self):
        if not self.max_token or not self.max_user_id:
            print("Не найдены данные для авторизации в Max.")
            print("Запускаю сервер авторизации...")
            from auth_server import run_auth_server
            run_auth_server()
            self.config = self.load_config()
            self.max_token = self.config.get('max_token')
            self.max_user_id = self.config.get('max_user_id')

            if not self.max_token or not self.max_user_id:
                raise Exception("Не удалось получить данные авторизации")

    async def get_max_messages(self):
        """Получение сообщений из Max"""
        self.ensure_auth()

        try:
            url = "https://api.max.ru/v1/messages"
            headers = {
                "Authorization": f"Bearer {self.max_token}",
                "User-Agent": "MaxBridge/1.0"
            }

            params = {"limit": 20, "user_id": self.max_user_id}

            response = requests.get(url, headers=headers, params=params)

            if response.status_code == 200:
                messages = response.json().get('items', [])
                new_messages = []

                for msg in messages:
                    if not hasattr(self, 'last_message_id') or msg['id'] > self.last_message_id:
                        new_messages.append({
                            'text': msg.get('text', ''),
                            'sender': msg.get('from', {}).get('name', 'Unknown'),
                            'timestamp': msg.get('timestamp')
                        })
                        self.last_message_id = msg['id']

                return new_messages

        except Exception as e:
            print(f"Error fetching Max messages: {e}")
            return []

    async def send_to_matrix(self, message):
        pass

    async def send_to_telegram(self, message):
        pass

    async def monitoring_loop(self, interval=10):
        pass


if __name__ == '__main__':
    bot = MaxBot()

    # Проверяем авторизацию при запуске
    try:
        bot.ensure_auth()
        print("Авторизация успешна, запускаем мониторинг...")
        asyncio.run(bot.monitoring_loop())
    except Exception as e:
        print(f"Ошибка: {e}")
        print("Пожалуйста, проверьте данные авторизации и попробуйте снова.")