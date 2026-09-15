# screens/chat_list.py
"""
Экран со списком всех чатов.
"""

from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import ObjectProperty
from kivymd.uix.screen import MDScreen
from kivymd.uix.list import TwoLineAvatarIconListItem, IconLeftWidget
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.textfield import MDTextField

KV = '''
<ChatListScreen>:
    name: "chat_list"

    MDBoxLayout:
        orientation: "vertical"

        MDTopAppBar:
            title: "Локальный мессенджер"
            elevation: 4
            right_action_items: [["plus", lambda x: root.show_create_dialog()], ["magnify", lambda x: root.show_search_dialog()], ["cog", lambda x: root.go_to_settings()]]

        ScrollView:
            MDList:
                id: chat_list_container
                padding: dp(8)
'''

Builder.load_string(KV)


class ChatListItem(TwoLineAvatarIconListItem):
    """Элемент списка чатов."""

    def __init__(self, chat_data, db, screen, **kwargs):
        super().__init__(**kwargs)
        self.chat_id = chat_data[0]
        self.db = db
        self.screen = screen

        # Текст
        self.text = f"{chat_data[2]} {chat_data[1]}"
        if chat_data[5] > 0:
            self.text += f"  [{chat_data[5]}]"

        # Превью последнего сообщения
        preview = chat_data[3] if chat_data[3] else "Нет сообщений"
        time_str = chat_data[4] if chat_data[4] else ""
        self.secondary_text = f"{preview}  {time_str}"

        # Обработка нажатия
        self.bind(on_release=self.on_click)

    def on_click(self, instance):
        """Открывает чат."""
        self.screen.open_chat(self.chat_id)


class ChatListScreen(MDScreen):
    """Экран списка чатов."""

    db = ObjectProperty(None)
    app_ref = ObjectProperty(None)

    def __init__(self, db, app_ref, **kwargs):
        super().__init__(**kwargs)
        self.db = db
        self.app_ref = app_ref
        self.dialog = None

    def on_enter(self, *args):
        """Обновляет список при входе на экран."""
        self.refresh_list()

    def refresh_list(self):
        """Перезагружает список чатов."""
        try:
            self.ids.chat_list_container.clear_widgets()
            chats = self.db.get_all_chats()

            for chat in chats:
                item = ChatListItem(chat_data=chat, db=self.db, screen=self)
                self.ids.chat_list_container.add_widget(item)
        except Exception as e:
            print(f"Ошибка обновления списка: {e}")

    def open_chat(self, chat_id):
        """Открывает экран переписки."""
        self.db.reset_unread(chat_id)
        self.app_ref.open_chat(chat_id)

    def go_to_settings(self):
        """Переход в настройки."""
        self.app_ref.go_to_settings()

    def show_create_dialog(self):
        """Диалог создания нового чата."""
        if self.dialog:
            self.dialog.dismiss()

        name_field = MDTextField(
            hint_text="Имя контакта",
            mode="rectangle"
        )

        self.dialog = MDDialog(
            title="Новый чат",
            type="custom",
            content_cls=name_field,
            buttons=[
                MDFlatButton(
                    text="ОТМЕНА",
                    on_release=lambda x: self.dialog.dismiss()
                ),
                MDRaisedButton(
                    text="СОЗДАТЬ",
                    on_release=lambda x: self._create_chat(name_field.text)
                )
            ]
        )
        self.dialog.open()

    def _create_chat(self, name):
        """Создаёт новый чат."""
        if name.strip():
            self.db.create_chat(name.strip())
            self.refresh_list()
        if self.dialog:
            self.dialog.dismiss()

    def show_search_dialog(self):
        """Диалог поиска по сообщениям."""
        if self.dialog:
            self.dialog.dismiss()

        search_field = MDTextField(
            hint_text="Поиск по сообщениям...",
            mode="rectangle"
        )

        self.dialog = MDDialog(
            title="Поиск",
            type="custom",
            content_cls=search_field,
            buttons=[
                MDFlatButton(
                    text="ЗАКРЫТЬ",
                    on_release=lambda x: self.dialog.dismiss()
                ),
                MDRaisedButton(
                    text="НАЙТИ",
                    on_release=lambda x: self._do_search(search_field.text)
                )
            ]
        )
        self.dialog.open()

    def _do_search(self, query):
        """Выполняет поиск и показывает результат."""
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
            buttons=[
                MDFlatButton(
                    text="ОК",
                    on_release=lambda x: result_dialog.dismiss()
                )
            ]
        )
        result_dialog.open()
