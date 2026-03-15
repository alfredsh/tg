[app]

# ── Основные данные приложения ─────────────────────────────────────────────
title           = TG Secret Chat
package.name    = tgsecret
package.domain  = org.tgsecret
source.dir      = .
source.include_exts = py,png,jpg,kv,atlas
version         = 1.0

# ── Зависимости Python ────────────────────────────────────────────────────
requirements = python3,kivy==2.3.0,telethon,pyaes,rsa

# ── Android-специфика ─────────────────────────────────────────────────────
android.permissions = INTERNET, ACCESS_NETWORK_STATE
android.api         = 33
android.minapi      = 21
android.ndk         = 25b
android.archs       = arm64-v8a, armeabi-v7a

# Иконка и заставка (можно заменить своими)
# icon.filename       = %(source.dir)s/icon.png
# presplash.filename  = %(source.dir)s/presplash.png

android.allow_backup = True

# ── Buildozer ─────────────────────────────────────────────────────────────
[buildozer]
log_level = 2
warn_on_root = 1
