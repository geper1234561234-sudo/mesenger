[app]

# Название приложения
title = Local Messenger

# Имя пакета (уникальное)
package.name = localmessenger

# Домен (заглушка)
package.domain = org.local

# Директория с исходниками
source.dir = .

# Расширения файлов, которые нужно включить
source.include_exts = py,png,jpg,kv,atlas,json,ttf

# Версия
version = 1.0

# Требования (БИБЛИОТЕКИ)
# ВАЖНО: KivyMD можно указать как "kivymd", Buildozer установит последнюю версию.
# Если возникнут проблемы — используй конкретную версию: kivymd==1.1.1
requirements = python3,kivy==2.3.0,kivymd==1.1.1

# Разрешения (нам не нужны внешние — всё локально)
android.permissions = 

# Ориентация
orientation = portrait

# Полноэкранный режим (0 = видны системные бары)
fullscreen = 0

# Архитектура (arm64-v8a покрывает большинство современных телефонов)
android.archs = arm64-v8a

# Версия API Android
android.api = 33
android.minapi = 21

# NDK версия
android.ndk = 28c

# NDK API
android.ndk_api = 21

# Python версия (КРИТИЧНО важно указать точно!)
p4a.python_version = 3.11

# Ветка python-for-android (develop стабильнее для новых API)
p4a.branch = master

# Разрешить бэкап
android.allow_backup = True

# Логирование
log_level = 2

# Не сжимать байт-код (для отладки)
android.no-byte-compile-python = False
