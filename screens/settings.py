# screens/settings.py
"""Экран настроек."""

from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import ObjectProperty
from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.list import OneLineListItem, ThreeLineListItem

KV = '''
<SettingsScreen>:
    MDBoxLayout:
        orientation: "vertical"

        MDTopAppBar:
            title: "Настройки"
            elevation: 4
            left_action_items: [["arrow-left", lambda x: root.go_back()]]

        ScrollView:
            MDList:
                id: settings_container
                padding: dp(8)
'''

Builder.load_string(KV)


class SettingsScreen(MDScreen):
    db = ObjectProperty(None)
    app_ref = ObjectProperty(None)

    def __init__(self, db, app_ref, **kwargs):
        super().__init__(**kwargs)
        self.db = db
        self.app_ref = app_ref

    def on_enter(self, *args):
        self.ids.settings_container.clear_widgets()
        self.ids.settings_container.add_widget(
            OneLineListItem(text="🎨 Тёмная тема", on_release=self.toggle_theme))
        self.ids.settings_container.add_widget(
            OneLineListItem(text="👤 Сменить имя", on_release=self.change_username))
        self.ids.settings_container.add_widget(
            OneLineListItem(text="📤 Экспорт чата в TXT", on_release=self.export_chat))
        self.ids.settings_container.add_widget(
            OneLineListItem(text="🗑 Очистить всё", on_release=self.confirm_clear))
        self.ids.settings_container.add_widget(
            ThreeLineListItem(text="Локальный мессенджер", secondary_text="Версия 1.0",
                              tertiary_text="Все данные хранятся только на устройстве"))

    def toggle_theme(self, instance):
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        if app.theme_cls.theme_style == "Dark":
            app.theme_cls.theme_style = "Light"
        else:
            app.theme_cls.theme_style = "Dark"

    def change_username(self, instance):
        field = MDTextField(hint_text="Новое имя", text="Я", mode="rectangle")
        dialog = MDDialog(
            title="Смена имени",
            type="custom",
            content_cls=field,
            buttons=[
                MDFlatButton(text="ОТМЕНА", on_release=lambda x: dialog.dismiss()),
                MDRaisedButton(text="СОХРАНИТЬ",
                               on_release=lambda x: self._save_username(field.text, dialog))
            ]
        )
        dialog.open()

    def _save_username(self, name, dialog):
        if name.strip():
            self.app_ref.username = name.strip()
            self.app_ref.show_snackbar(f"Имя изменено: {name.strip()}")
        dialog.dismiss()

    def export_chat(self, instance):
        try:
            chats = self.db.get_all_chats()
            if not chats:
                self.app_ref.show_snackbar("Нет чатов")
                return
            chat_id = chats[0][0]
            chat_name = chats[0][1]
            messages = self.db.get_messages(chat_id)
            filename = f"export_{chat_id}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"Чат: {chat_name}\n" + "=" * 40 + "\n")
                for msg in messages:
                    _, text, is_mine, ts = msg
                    who = "Я" if is_mine else chat_name
                    f.write(f"[{ts}] {who}: {text}\n")
            self.app_ref.show_snackbar(f"Сохранено: {filename}")
        except Exception as e:
            print(f"Ошибка экспорта: {e}")

    def confirm_clear(self, instance):
        dialog = MDDialog(
            title="Очистить всё?",
            text="Все чаты и сообщения будут удалены.",
            buttons=[
                MDFlatButton(text="ОТМЕНА", on_release=lambda x: dialog.dismiss()),
                MDRaisedButton(text="УДАЛИТЬ", on_release=lambda x: self._do_clear(dialog))
            ]
        )
        dialog.open()

    def _do_clear(self, dialog):
        self.db.clear_all()
        self.app_ref.show_snackbar("Все данные удалены")
        dialog.dismiss()

    def go_back(self):
        self.app_ref.go_to_chat_list()    msg_text = ""
    msg_time = ""
    is_mine = False
    msg_id = None

    def __init__(self, text, time_str, is_mine, msg_id, screen_ref, **kwargs):
        super().__init__(**kwargs)
        self.msg_time = time_str
        self.is_mine = is_mine
        self.msg_id = msg_id
        self.screen_ref = screen_ref

        if is_mine:
            self.md_bg_color = (0.26, 0.52, 0.96, 1)
            self.msg_text = f"[color=ffffff]{text}[/color]"
        else:
            self.md_bg_color = (0.88, 0.88, 0.88, 1)
            self.msg_text = f"[color=000000]{text}[/color]"


class ChatScreen(MDScreen):
    db = ObjectProperty(None)
    app_ref = ObjectProperty(None)
    chat_id = None
    chat_name = ""
    auto_reply_enabled = True

    def __init__(self, db, app_ref, **kwargs):
        super().__init__(**kwargs)
        self.db = db
        self.app_ref = app_ref

    def load_chat(self, chat_id, chat_name, chat_avatar):
        self.chat_id = chat_id
        self.chat_name = f"{chat_avatar} {chat_name}"
        self.auto_reply_enabled = (chat_name != "Избранное")
        self.refresh_messages()

    def refresh_messages(self):
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
            Clock.schedule_once(lambda dt: self._scroll_to_bottom(), 0.1)
        except Exception as e:
            print(f"Ошибка загрузки сообщений: {e}")

    def _scroll_to_bottom(self):
        try:
            self.ids.scroll_view.scroll_y = 0
        except Exception as e:
            print(f"Ошибка прокрутки: {e}")

    def send_message(self):
        text = self.ids.msg_input.text.strip()
        if not text:
            return
        try:
            self.db.add_message(self.chat_id, text, is_mine=True)
            self.ids.msg_input.text = ""
            self.refresh_messages()
            if self.auto_reply_enabled:
                Clock.schedule_once(lambda dt: self._auto_reply(text), 2.0)
        except Exception as e:
            print(f"Ошибка отправки: {e}")

    def _auto_reply(self, user_message):
        replies = ["Понятно, интересно!", "Расскажи подробнее", "Хорошо 👍",
                   "Согласен с тобой", "Да, точно!", "А что дальше?",
                   "Хм, надо подумать...", "Классная идея!"]
        reply = random.choice(replies)
        self.db.add_message(self.chat_id, reply, is_mine=False)
        self.refresh_messages()

    def clear_chat(self):
        try:
            self.db.clear_chat_messages(self.chat_id)
            self.refresh_messages()
            self.app_ref.show_snackbar("История очищена")
        except Exception as e:
            print(f"Ошибка очистки: {e}")

    def go_back(self):
        self.app_ref.go_to_chat_list()
        search_field = MDTextField(hint_text="Поиск по сообщениям...", mode="rectangle")

        self.dialog = MDDialog(
            title="Поиск",
            type="custom",
            content_cls=search_field,
            buttons=[
                MDFlatButton(text="ЗАКРЫТЬ", on_release=lambda x: self.dialog.dismiss()),
                MDRaisedButton(text="НАЙТИ", on_release=lambda x: self._do_search(search_field.text))
            ]
        )
        self.dialog.open()

    def _do_search(self, query):
        if not query.strip():
            return
        results = self.db.search_messages(query.strip())
        if self.dialog:
            self.dialog.dismiss()
        if not results:
            self.app_ref.show_snackbar("Ничего не найдено")
            return
        result_text = f"Найдено: {len(results)}\n\n"
        for r in results[:10]:
            result_text += f"{r[4]}: {r[1][:50]}\n"
        result_dialog = MDDialog(
            title="Результаты поиска",
            text=result_text,
            buttons=[MDFlatButton(text="ОК", on_release=lambda x: result_dialog.dismiss())]
        )
        result_dialog.open()
