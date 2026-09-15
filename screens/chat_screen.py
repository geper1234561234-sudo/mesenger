# screens/chat_screen.py
"""
Экран переписки внутри чата.
"""

from kivy.lang import Builder
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import ObjectProperty
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel

KV = '''
<MessageBubble>:
    orientation: "vertical"
    size_hint_y: None
    height: self.minimum_height
    padding: dp(8)
    spacing: dp(2)

    MDLabel:
        text: root.msg_text
        halign: "right" if root.is_mine else "left"
        markup: True
        size_hint_y: None
        height: self.texture_size[1]
        text_size: self.width - dp(16), None
        padding_x: dp(8)

    MDLabel:
        text: root.msg_time
        halign: "right" if root.is_mine else "left"
        font_style: "Caption"
        theme_text_color: "Hint"
        size_hint_y: None
        height: dp(16)

<ChatScreen>:
    name: "chat_screen"

    MDBoxLayout:
        orientation: "vertical"

        MDTopAppBar:
            title: root.chat_name
            elevation: 4
            left_action_items: [["arrow-left", lambda x: root.go_back()]]
            right_action_items: [["delete-sweep", lambda x: root.clear_chat()], ["dots-vertical", lambda x: root.show_menu()]]

        ScrollView:
            id: scroll_view
            MDBoxLayout:
                id: messages_container
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                padding: dp(8)
                spacing: dp(4)

        MDBoxLayout:
            size_hint_y: None
            height: dp(60)
            padding: dp(8)
            spacing: dp(8)

            MDTextField:
                id: msg_input
                hint_text: "Сообщение..."
                mode: "rectangle"
                multiline: False
                on_text_validate: root.send_message()

            MDIconButton:
                icon: "send"
                theme_icon_color: "Custom"
                icon_color: app.theme_cls.primary_color
                on_release: root.send_message()
'''

Builder.load_string(KV)


class MessageBubble(MDBoxLayout):
    """Пузырь сообщения. Синий — мой, серый — собеседника."""

    msg_text = ""
    msg_time = ""
    is_mine = False
    msg_id = None

    def __init__(self, text, time_str, is_mine, msg_id, screen_ref, **kwargs):
        super().__init__(**kwargs)
        self.msg_text = text
        self.msg_time = time_str
        self.is_mine = is_mine
        self.msg_id = msg_id
        self.screen_ref = screen_ref

        # Цвет фона пузыря
        if is_mine:
            self.md_bg_color = (0.26, 0.52, 0.96, 1)  # Синий
            self.msg_text = f"[color=ffffff]{text}[/color]"
        else:
            self.md_bg_color = (0.88, 0.88, 0.88, 1)  # Серый
            self.msg_text = f"[color=000000]{text}[/color]"

        # Долгое нажатие — удаление
        self.bind(on_touch_down=self.on_long_press)

    def on_long_press(self, instance, touch):
        """Долгое нажатие — удалить сообщение."""
        if not self.collide_point(*touch.pos):
            return False

        if touch.is_double_tap:
            return False

        # Простая эмуляция долгого нажатия через таймер
        if not hasattr(self, '_long_press_event'):
            self._long_press_event = Clock.schedule_once(
                lambda dt: self.screen_ref.delete_message(self.msg_id),
                1.0
            )
            touch.bind(on_touch_up=lambda t, x: self._cancel_long_press())
        return True

    def _cancel_long_press(self):
        """Отменяет долгое нажатие при отпускании."""
        if hasattr(self, '_long_press_event'):
            self._long_press_event.cancel()
            del self._long_press_event


class ChatScreen(MDScreen):
    """Экран переписки."""

    db = ObjectProperty(None)
    app_ref = ObjectProperty(None)
    chat_id = None
    chat_name = ""
    chat_avatar = ""
    auto_reply_enabled = True

    def __init__(self, db, app_ref, **kwargs):
        super().__init__(**kwargs)
        self.db = db
        self.app_ref = app_ref

    def load_chat(self, chat_id, chat_name, chat_avatar):
        """Загружает чат."""
        self.chat_id = chat_id
        self.chat_name = f"{chat_avatar} {chat_name}"
        self.chat_avatar = chat_avatar
        self.auto_reply_enabled = (chat_name != "Избранное")
        self.refresh_messages()

    def refresh_messages(self):
        """Перезагружает сообщения в чате."""
        try:
            self.ids.messages_container.clear_widgets()
            messages = self.db.get_messages(self.chat_id)

            for msg in messages:
                msg_id, text, is_mine, timestamp = msg
                bubble = MessageBubble(
                    text=text,
                    time_str=timestamp,
                    is_mine=bool(is_mine),
                    msg_id=msg_id,
                    screen_ref=self
                )
                self.ids.messages_container.add_widget(bubble)

            # Прокрутка вниз
            Clock.schedule_once(lambda dt: self._scroll_to_bottom(), 0.1)
        except Exception as e:
            print(f"Ошибка загрузки сообщений: {e}")

    def _scroll_to_bottom(self):
        """Прокручивает список сообщений вниз."""
        try:
            self.ids.scroll_view.scroll_y = 0
        except Exception as e:
            print(f"Ошибка прокрутки: {e}")

    def send_message(self):
        """Отправляет сообщение."""
        text = self.ids.msg_input.text.strip()
        if not text:
            return

        try:
            self.db.add_message(self.chat_id, text, is_mine=True)
            self.ids.msg_input.text = ""
            self.refresh_messages()

            # Автоответ (если не "Избранное")
            if self.auto_reply_enabled:
                Clock.schedule_once(lambda dt: self._auto_reply(text), 2.0)
        except Exception as e:
            print(f"Ошибка отправки: {e}")

    def _auto_reply(self, user_message):
        """Бот отвечает через 2 секунды."""
        replies = [
            "Понятно, интересно!",
            "Расскажи подробнее",
            "Хорошо 👍",
            "Согласен с тобой",
            "Да, точно!",
            "А что дальше?",
            "Хм, надо подумать...",
            "Классная идея!",
        ]
        import random
        reply = random.choice(replies)
        self.db.add_message(self.chat_id, reply, is_mine=False)
        self.refresh_messages()

    def delete_message(self, msg_id):
        """Удаляет сообщение по долгому нажатию."""
        try:
            self.db.delete_message(msg_id)
            self.refresh_messages()
            self.app_ref.show_snackbar("Сообщение удалено")
        except Exception as e:
            print(f"Ошибка удаления: {e}")

    def clear_chat(self):
        """Очищает все сообщения в чате."""
        try:
            self.db.clear_chat_messages(self.chat_id)
            self.refresh_messages()
            self.app_ref.show_snackbar("История очищена")
        except Exception as e:
            print(f"Ошибка очистки: {e}")

    def show_menu(self):
        """Показывает меню (в разработке)."""
        self.app_ref.show_snackbar("Меню в разработке")

    def go_back(self):
        """Возврат к списку чатов."""
        self.app_ref.go_to_chat_list()
