# database.py
"""
Модуль для работы с локальной базой данных SQLite.
Все данные хранятся ТОЛЬКО на устройстве. Никаких серверов.
"""

import sqlite3
import os
from datetime import datetime

DB_NAME = "messenger.db"


class Database:
    """Класс-обёртка для работы с SQLite."""

    def __init__(self):
        # check_same_thread=False — чтобы Kivy мог обращаться к БД из разных потоков
        # ВАЖНО: это компромисс. В реальном многопоточном приложении лучше
        # создавать отдельное соединение на каждый поток [citation:19][citation:30].
        self.conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._create_tables()
        self._create_default_chat()

    def _create_tables(self):
        """Создаёт таблицы, если их ещё нет."""
        try:
            # Таблица чатов (диалогов)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS chats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    avatar TEXT DEFAULT '👤',
                    last_message TEXT DEFAULT '',
                    last_time TEXT DEFAULT '',
                    unread_count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Таблица сообщений
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    is_mine INTEGER DEFAULT 0,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (chat_id) REFERENCES chats (id) ON DELETE CASCADE
                )
            """)

            self.conn.commit()
        except Exception as e:
            print(f"Ошибка создания таблиц: {e}")

    def _create_default_chat(self):
        """Создаёт чат 'Избранное' по умолчанию."""
        try:
            self.cursor.execute("SELECT COUNT(*) FROM chats")
            count = self.cursor.fetchone()[0]
            if count == 0:
                self.create_chat("Избранное", "⭐")
        except Exception as e:
            print(f"Ошибка создания стандартного чата: {e}")

    # ─────────────── РАБОТА С ЧАТАМИ ───────────────

    def create_chat(self, name, avatar="👤"):
        """Создаёт новый чат. Возвращает его ID."""
        try:
            self.cursor.execute(
                "INSERT INTO chats (name, avatar) VALUES (?, ?)",
                (name, avatar)
            )
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            print(f"Ошибка создания чата: {e}")
            return None

    def get_all_chats(self):
        """Возвращает все чаты, отсортированные по времени последнего сообщения."""
        try:
            self.cursor.execute("""
                SELECT id, name, avatar, last_message, last_time, unread_count
                FROM chats
                ORDER BY
                    CASE WHEN last_time = '' THEN 1 ELSE 0 END,
                    last_time DESC
            """)
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Ошибка получения чатов: {e}")
            return []

    def update_chat_preview(self, chat_id, last_message, last_time):
        """Обновляет превью чата (последнее сообщение и время)."""
        try:
            self.cursor.execute(
                "UPDATE chats SET last_message = ?, last_time = ? WHERE id = ?",
                (last_message, last_time, chat_id)
            )
            self.conn.commit()
        except Exception as e:
            print(f"Ошибка обновления превью: {e}")

    def increment_unread(self, chat_id):
        """Увеличивает счётчик непрочитанных."""
        try:
            self.cursor.execute(
                "UPDATE chats SET unread_count = unread_count + 1 WHERE id = ?",
                (chat_id,)
            )
            self.conn.commit()
        except Exception as e:
            print(f"Ошибка счётчика: {e}")

    def reset_unread(self, chat_id):
        """Сбрасывает счётчик непрочитанных."""
        try:
            self.cursor.execute(
                "UPDATE chats SET unread_count = 0 WHERE id = ?",
                (chat_id,)
            )
            self.conn.commit()
        except Exception as e:
            print(f"Ошибка сброса счётчика: {e}")

    def delete_chat(self, chat_id):
        """Удаляет чат и все его сообщения."""
        try:
            self.cursor.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
            self.cursor.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
            self.conn.commit()
        except Exception as e:
            print(f"Ошибка удаления чата: {e}")

    # ─────────────── РАБОТА С СООБЩЕНИЯМИ ───────────────

    def add_message(self, chat_id, text, is_mine=False):
        """Добавляет сообщение. Возвращает ID сообщения."""
        try:
            timestamp = datetime.now().strftime("%H:%M")
            self.cursor.execute(
                "INSERT INTO messages (chat_id, text, is_mine, timestamp) VALUES (?, ?, ?, ?)",
                (chat_id, text, 1 if is_mine else 0, timestamp)
            )
            msg_id = self.cursor.lastrowid
            self.conn.commit()

            # Обновляем превью чата
            self.update_chat_preview(chat_id, text, timestamp)

            return msg_id
        except Exception as e:
            print(f"Ошибка добавления сообщения: {e}")
            return None

    def get_messages(self, chat_id, limit=100):
        """Возвращает последние сообщения чата."""
        try:
            self.cursor.execute("""
                SELECT id, text, is_mine, timestamp
                FROM messages
                WHERE chat_id = ?
                ORDER BY id ASC
                LIMIT ?
            """, (chat_id, limit))
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Ошибка получения сообщений: {e}")
            return []

    def search_messages(self, query, chat_id=None):
        """Поиск сообщений по тексту."""
        try:
            if chat_id:
                self.cursor.execute("""
                    SELECT m.id, m.text, m.is_mine, m.timestamp, c.name, c.avatar
                    FROM messages m
                    JOIN chats c ON m.chat_id = c.id
                    WHERE m.text LIKE ? AND m.chat_id = ?
                    ORDER BY m.id DESC
                """, (f"%{query}%", chat_id))
            else:
                self.cursor.execute("""
                    SELECT m.id, m.text, m.is_mine, m.timestamp, c.name, c.avatar
                    FROM messages m
                    JOIN chats c ON m.chat_id = c.id
                    WHERE m.text LIKE ?
                    ORDER BY m.id DESC
                    LIMIT 50
                """, (f"%{query}%",))
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Ошибка поиска: {e}")
            return []

    def delete_message(self, msg_id):
        """Удаляет сообщение по ID."""
        try:
            self.cursor.execute("DELETE FROM messages WHERE id = ?", (msg_id,))
            self.conn.commit()
        except Exception as e:
            print(f"Ошибка удаления сообщения: {e}")

    def clear_chat_messages(self, chat_id):
        """Очищает все сообщения в чате."""
        try:
            self.cursor.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
            self.cursor.execute(
                "UPDATE chats SET last_message = '', last_time = '', unread_count = 0 WHERE id = ?",
                (chat_id,)
            )
            self.conn.commit()
        except Exception as e:
            print(f"Ошибка очистки чата: {e}")

    def clear_all(self):
        """Полная очистка всех данных."""
        try:
            self.cursor.execute("DELETE FROM messages")
            self.cursor.execute("DELETE FROM chats")
            self.conn.commit()
            self._create_default_chat()
        except Exception as e:
            print(f"Ошибка полной очистки: {e}")

    def close(self):
        """Закрывает соединение с БД."""
        try:
            self.conn.close()
        except Exception as e:
            print(f"Ошибка закрытия БД: {e}")
