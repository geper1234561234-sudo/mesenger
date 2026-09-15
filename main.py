# main.py
"""
Локальный мессенджер — точка входа.
Всё работает офлайн. Данные хранятся в SQLite на устройстве.
"""

from kivy.lang import Builder
from kivy.metrics import dp
from kivy.uix.screenmanager import ScreenManager, SlideTransition
from kivymd.app import MDApp
from kivymd.uix.snackbar import Snackbar

from database import Database
from screens.chat_list import ChatListScreen
from screens.chat_screen import ChatScreen
from screens.settings import SettingsScreen

KV = '''
<MainRoot>:
    ScreenManager:
        id: sm
        transition: SlideTransition()
'''

Builder.load_string(KV)


class MainRoot(ScreenManager):
    """Корневой менеджер экранов."""
    pass


class MessengerApp(MDApp):
    """Главное приложение."""

    db = None
    username = "Я"
    sm = None

    # Ссылки на экраны
    chat_list_screen = None
    chat_screen = None
    settings_screen = None

    def build(self):
        """Строит UI."""
        # Настройки темы
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"
        self.theme_cls.material_style = "M3"

        # Инициализация БД
        self.db = Database()

        # Корневой ScreenManager
        self.sm = ScreenManager(transition=SlideTransition())

        # Создание экранов
        self.chat_list_screen = ChatListScreen(db=self.db, app_ref=self)
        self.chat_screen = ChatScreen(db=self.db, app_ref=self)
        self.settings_screen = SettingsScreen(db=self.db, app_ref=self)

        # Добавление экранов
        self.sm.add_widget(self.chat_list_screen)
        self.sm.add_widget(self.chat_screen)
        self.sm.add_widget(self.settings_screen)

        # Стартовый экран
        self.sm.current = "chat_list"

        return self.sm

    # ─────────────── НАВИГАЦИЯ ───────────────

    def open_chat(self, chat_id):
        """Открывает экран переписки."""
        # Получаем данные чата
        chats = self.db.get_all_chats()
        chat_data = None
        for c in chats:
            if c[0] == chat_id:
                chat_data = c
                break

        if chat_data:
            self.chat_screen.load_chat(chat_id, chat_data[1], chat_data[2])
            self.sm.current = "chat_screen"

    def go_to_chat_list(self):
        """Переход к списку чатов."""
        self.sm.current = "chat_list"
        self.chat_list_screen.refresh_list()

    def go_to_settings(self):
        """Переход в настройки."""
        self.sm.current = "settings"

    # ─────────────── УТИЛИТЫ ───────────────

    def show_snackbar(self, text):
        """Показывает всплывающее уведомление."""
        try:
            Snackbar(text=text, duration=2).open()
        except Exception as e:
            print(f"Snackbar error: {e}")

    def on_stop(self):
        """Закрывает БД при выходе."""
        if self.db:
            self.db.close()


if __name__ == "__main__":
    MessengerApp().run()
