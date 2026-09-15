# screens/settings.py
"""
Экран настроек: тема, имя пользователя, очистка данных.
"""

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
    name: "settings"

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
    """Экран настроек."""

    db = ObjectProperty(None)
    app_ref = ObjectProperty(None)

    def __init__(self, db, app_ref, **kwargs):
        super().__init__(**kwargs)
        self.db = db
        self.app_ref = app_ref

    def on_enter(self, *args):
        """Заполняет настройки при входе."""
        self.ids.settings_container.clear_widgets()

        # Тема
        theme_item = OneLineListItem(
            text="🎨 Тёмная тема",
            on_release=self.toggle_theme
        )
        self.ids.settings_container.add_widget(theme_item)

        # Имя пользователя
        name_item = OneLineListItem(
            text="👤 Сменить имя",
            on_release=self.change_username
        )
        self.ids.settings_container.add_widget(name_item)

        # Экспорт
        export_item = OneLineListItem(
            text="📤 Экспорт чата в TXT",
            on_release=self.export_chat
        )
        self.ids.settings_container.add_widget(export_item)

        # Очистка
        clear_item = OneLineListItem(
            text="🗑 Очистить всё",
            on_release=self.confirm_clear
        )
        self.ids.settings_container.add_widget(clear_item)

        # Информация
        info_item = ThreeLineListItem(
            text="Локальный мессенджер",
            secondary_text="Версия 1.0",
            tertiary_text="Все данные хранятся только на устройстве"
        )
        self.ids.settings_container.add_widget(info_item)

    def toggle_theme(self, instance):
        """Переключает тёмную/светлую тему."""
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        if app.theme_cls.theme_style == "Dark":
            app.theme_cls.theme_style = "Light"
        else:
            app.theme_cls.theme_style = "Dark"

    def change_username(self, instance):
        """Диалог смены имени пользователя."""
        field = MDTextField(
            hint_text="Новое имя",
            text="Я",
            mode="rectangle"
        )
        dialog = MDDialog(
            title="Смена имени",
            type="custom",
            content_cls=field,
            buttons=[
                MDFlatButton(text="ОТМЕНА", on_release=lambda x: dialog.dismiss()),
                MDRaisedButton(
                    text="СОХРАНИТЬ",
                    on_release=lambda x: self._save_username(field.text, dialog)
                )
            ]
        )
        dialog.open()

    def _save_username(self, name, dialog):
        """Сохраняет новое имя."""
        if name.strip():
            self.app_ref.username = name.strip()
            self.app_ref.show_snackbar(f"Имя изменено на: {name.strip()}")
        dialog.dismiss()

    def export_chat(self, instance):
        """Экспортирует чат в TXT файл."""
        try:
            chats = self.db.get_all_chats()
            if not chats:
                self.app_ref.show_snackbar("Нет чатов для экспорта")
                return

            # Экспорт первого чата (можно доработать)
            chat_id = chats[0][0]
            chat_name = chats[0][1]
            messages = self.db.get_messages(chat_id)

            filename = f"export_{chat_name}_{chat_id}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"Чат: {chat_name}\n")
                f.write("=" * 40 + "\n")
                for msg in messages:
                    _, text, is_mine, ts = msg
                    who = "Я" if is_mine else chat_name
                    f.write(f"[{ts}] {who}: {text}\n")

            self.app_ref.show_snackbar(f"Экспортировано: {filename}")
        except Exception as e:
            print(f"Ошибка экспорта: {e}")
            self.app_ref.show_snackbar("Ошибка экспорта")

    def confirm_clear(self, instance):
        """Подтверждение полной очистки."""
        dialog = MDDialog(
            title="Очистить всё?",
            text="Все чаты и сообщения будут удалены безвозвратно.",
            buttons=[
                MDFlatButton(text="ОТМЕНА", on_release=lambda x: dialog.dismiss()),
                MDRaisedButton(
                    text="УДАЛИТЬ",
                    on_release=lambda x: self._do_clear(dialog)
                )
            ]
        )
        dialog.open()

    def _do_clear(self, dialog):
        """Выполняет очистку."""
        self.db.clear_all()
        self.app_ref.show_snackbar("Все данные удалены")
        dialog.dismiss()

    def go_back(self):
        """Возврат к списку чатов."""
        self.app_ref.go_to_chat_list()
