[app]
title           = TG Secret Chat
package.name    = tgsecret
package.domain  = org.tgsecret
source.dir      = .
source.include_exts = py,png,jpg,kv,atlas
version         = 1.0

# УПРОЩЁННЫЕ зависимости — без telethon для теста
requirements = python3,kivy==2.3.0

android.permissions  = INTERNET
android.api          = 33
android.minapi       = 21
android.ndk          = 25b
android.ndk_api      = 21
android.archs        = arm64-v8a
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
