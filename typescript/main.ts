import { MatrixClient } from "matrix-js-sdk";
import TelegramBot from "node-telegram-bot-api";
import axios from "axios";
import WebSocket from "ws";

interface MaxMessage {
  id: number;
  text: string;
  sender: {
    id: number;
    name: string;
  };
  timestamp: number;
}

class MaxBridge {
  private matrixClient: MatrixClient;
  private telegramBot: TelegramBot;
  private lastMessageId: number = 0;
  private maxAuthToken: string;
  private maxUserId: string;

  constructor() {
    this.matrixClient = MatrixClient.create({
      baseUrl: process.env.MATRIX_HOMESERVER || "https://matrix.example.com",
      userId: process.env.MATRIX_USER_ID || "@bot:example.com",
      accessToken: process.env.MATRIX_ACCESS_TOKEN || "your_access_token"
    });

    this.telegramBot = new TelegramBot(
      process.env.TELEGRAM_BOT_TOKEN || "your_telegram_bot_token",
      { polling: true }
    );

    this.maxAuthToken = process.env.MAX_AUTH_TOKEN || "your_max_token";
    this.maxUserId = process.env.MAX_USER_ID || "your_max_user_id";
  }

  async getMaxMessages(): Promise<MaxMessage[]> {
    try {
      const response = await axios.get("https://api.max.ru/v1/messages", {
        headers: {
          Authorization: `Bearer ${this.maxAuthToken}`,
          "User-Agent": "MaxBridge/1.0"
        },
        params: {
          limit: 20,
          user_id: this.maxUserId
        }
      });

      const messages: MaxMessage[] = response.data.items || [];
      const newMessages: MaxMessage[] = [];

      for (const message of messages) {
        if (message.id > this.lastMessageId) {
          newMessages.push(message);
          this.lastMessageId = message.id;
        }
      }

      return newMessages;
    } catch (error) {
      console.error("Ошибка при получении сообщений из Max:", error);
      return [];
    }
  }

  async sendToMatrix(message: MaxMessage): Promise<void> {
    try {
      const roomId = process.env.MATRIX_ROOM_ID || "!room_id:example.com";
      const content = {
        body: `${message.sender.name}: ${message.text}`,
        msgtype: "m.text"
      };

      await this.matrixClient.sendEvent(roomId, "m.room.message", content);
      console.log("Сообщение отправлено в Matrix");
    } catch (error) {
      console.error("Ошибка при отправке в Matrix:", error);
    }
  }

  async sendToTelegram(message: MaxMessage): Promise<void> {
    try {
      const chatId = process.env.TELEGRAM_CHAT_ID || "your_chat_id";
      const text = `📨 ${message.sender.name}:\n${message.text}`;

      await this.telegramBot.sendMessage(chatId, text);
      console.log("Сообщение отправлено в Telegram");
    } catch (error) {
      console.error("Ошибка при отправке в Telegram:", error);
    }
  }

  async startMonitoring(interval: number = 10000): Promise<void> {
    console.log("Запуск мониторинга Max...");

    while (true) {
      try {
        const newMessages = await this.getMaxMessages();

        for (const message of newMessages) {
          await this.sendToMatrix(message);
          await this.sendToTelegram(message);
        }

        await this.delay(interval);
      } catch (error) {
        console.error("Ошибка в основном цикле:", error);
        await this.delay(60000);
      }
    }
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  connectMaxWebSocket(): void {
    try {
      const ws = new WebSocket("wss://max.ru/ws", {
        headers: {
          Authorization: `Bearer ${this.maxAuthToken}`
        }
      });

      ws.on("open", () => {
        console.log("Подключение к WebSocket Max установлено");

        // Отправка авторизации (предполагаемый формат)
        ws.send(JSON.stringify({
          type: "auth",
          token: this.maxAuthToken
        }));
      });

      ws.on("message", async (data: WebSocket.Data) => {
        try {
          const message = JSON.parse(data.toString());

          if (message.type === "message") {
            const maxMessage: MaxMessage = {
              id: message.id,
              text: message.text,
              sender: message.from,
              timestamp: message.timestamp
            };

            await this.sendToMatrix(maxMessage);
            await this.sendToTelegram(maxMessage);
          }
        } catch (error) {
          console.error("Ошибка обработки WebSocket сообщения:", error);
        }
      });

      ws.on("error", (error) => {
        console.error("WebSocket ошибка:", error);
      });

      ws.on("close", () => {
        console.log("WebSocket соединение закрыто, переподключение через 10 секунд");
        setTimeout(() => this.connectMaxWebSocket(), 10000);
      });
    } catch (error) {
      console.error("Ошибка подключения к WebSocket:", error);
    }
  }
}

const bridge = new MaxBridge();

bridge.startMonitoring(10000);
