from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import webbrowser
import threading
import os


class AuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()

            with open('auth.html', 'r', encoding='utf-8') as f:
                html_content = f.read()
            self.wfile.write(html_content.encode('utf-8'))

        elif self.path.startswith('/save'):
            query = urlparse(self.path).query
            params = parse_qs(query)

            token = params.get('token', [''])[0]
            user_id = params.get('user_id', [''])[0]

            if token and user_id:
                with open('max_config.json', 'w', encoding='utf-8') as f:
                    json.dump({'token': token, 'user_id': user_id}, f)

                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()

                response_html = """
                <html>
                    <body>
                        <h1>Успех!</h1>
                        <p>Токен сохранен. Вы можете закрыть эту страницу и запустить бота.</p>
                    </body>
                </html>
                """
                self.wfile.write(response_html.encode('utf-8'))

                threading.Thread(target=self.server.shutdown).start()
            else:
                self.send_error(400, "Не указаны token или user_id")

    def log_message(self, format, *args):
        return


def run_auth_server():
    server = HTTPServer(('localhost', 8080), AuthHandler)
    print("Сервер авторизации запущен на http://localhost:8080")
    print("Откройте браузер для авторизации...")
    webbrowser.open('http://localhost:8080')
    server.serve_forever()


if __name__ == '__main__':
    run_auth_server()