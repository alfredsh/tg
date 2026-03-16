[app]
title           = TG Secret Chat
package.name    = tgsecret
package.domain  = org.tgsecret
source.dir      = .
source.include_exts = py,png,jpg,kv,atlas
version         = 1.0

# Зависимости — минимальный набор для Android
requirements = python3==3.10.14,kivy==2.3.0,telethon==1.34.0,pyaes==1.6.1,rsa==4.9

# Android
android.permissions  = INTERNET
android.api          = 33
android.minapi       = 21
android.ndk          = 25b
android.ndk_api      = 21
android.archs        = arm64-v8a

# Включаем интернет через cleartext для отладки
android.manifest.user_permissions = INTERNET
android.allow_backup = True

# Отключаем splash для простоты
#presplash.filename  = %(source.dir)s/data/presplash.png
#icon.filename       = %(source.dir)s/data/icon.png

[buildozer]
log_level = 2
warn_on_root = 1
