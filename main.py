"""
Telegram Secret Chat — Android App
Фреймворк: Kivy (Python → APK)
API: Telethon (MTProto)
"""

import asyncio
import threading
import os

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.utils import get_color_from_hex

from telethon import TelegramClient, events
from telethon.tl.functions.messages import RequestEncryptionRequest
from telethon.tl.functions.contacts import GetContactsRequest, ResolveUsernameRequest
from telethon.tl.types import InputUser
from telethon.errors import SessionPasswordNeededError

# ── Цветовая схема (тёмная, как Telegram) ─────────────────────────────────────
BG        = get_color_from_hex("#0F1923")
BG2       = get_color_from_hex("#1A2633")
ACCENT    = get_color_from_hex("#2AABEE")
GREEN     = get_color_from_hex("#4CAF50")
RED_C     = get_color_from_hex("#F44336")
TEXT      = get_color_from_hex("#FFFFFF")
SUBTEXT   = get_color_from_hex("#8899AA")
LOCK_ICON = "🔐"

Window.clearcolor = BG

# ── Глобальный asyncio-loop в отдельном потоке ────────────────────────────────
_loop   = asyncio.new_event_loop()
_client: TelegramClient = None

def run_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

_thread = threading.Thread(target=run_loop, args=(_loop,), daemon=True)
_thread.start()

def run_async(coro):
    """Запустить корутину в фоновом потоке, вернуть Future."""
    return asyncio.run_coroutine_threadsafe(coro, _loop)


# ══════════════════════════════════════════════════════════════════════════════
#  ВИДЖЕТЫ-ХЕЛПЕРЫ
# ══════════════════════════════════════════════════════════════════════════════

def styled_btn(text, color=ACCENT, height=dp(48)):
    btn = Button(
        text=text,
        size_hint_y=None,
        height=height,
        background_normal="",
        background_color=color,
        color=TEXT,
        font_size=dp(16),
        bold=True,
    )
    return btn

def styled_input(hint, password=False):
    return TextInput(
        hint_text=hint,
        size_hint_y=None,
        height=dp(48),
        background_color=BG2,
        foreground_color=TEXT,
        hint_text_color=SUBTEXT,
        cursor_color=ACCENT,
        multiline=False,
        password=password,
        padding=[dp(12), dp(12)],
        font_size=dp(15),
    )

def show_popup(title, msg, color=TEXT):
    content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
    content.add_widget(Label(text=msg, color=color, halign="center"))
    btn = styled_btn("OK", height=dp(40))
    content.add_widget(btn)
    popup = Popup(
        title=title,
        content=content,
        size_hint=(0.85, 0.4),
        background_color=BG2,
        title_color=ACCENT,
    )
    btn.bind(on_press=popup.dismiss)
    popup.open()


# ══════════════════════════════════════════════════════════════════════════════
#  ЭКРАН 1 — НАСТРОЙКА API
# ══════════════════════════════════════════════════════════════════════════════

class ApiScreen(Screen):
    """Ввод api_id и api_hash от my.telegram.org"""

    def __init__(self, **kw):
        super().__init__(**kw)
        root = BoxLayout(orientation="vertical", padding=dp(24), spacing=dp(16))
        root.add_widget(Label(
            text=f"{LOCK_ICON}  Telegram Secret Chat",
            font_size=dp(22), bold=True, color=ACCENT,
            size_hint_y=None, height=dp(60),
        ))
        root.add_widget(Label(
            text="Получите ключи на\nmy.telegram.org → API Development Tools",
            color=SUBTEXT, halign="center", font_size=dp(13),
            size_hint_y=None, height=dp(50),
        ))

        self.api_id    = styled_input("api_id  (число, например 12345678)")
        self.api_hash  = styled_input("api_hash  (строка 32 символа)")
        root.add_widget(self.api_id)
        root.add_widget(self.api_hash)

        btn = styled_btn("Продолжить →")
        btn.bind(on_press=self.on_next)
        root.add_widget(btn)
        root.add_widget(Label())  # spacer
        self.add_widget(root)

    def on_next(self, *_):
        api_id   = self.api_id.text.strip()
        api_hash = self.api_hash.text.strip()

        if not api_id.isdigit() or not api_hash:
            show_popup("Ошибка", "Введите корректные api_id и api_hash", RED_C)
            return

        app = App.get_running_app()
        app.api_id   = int(api_id)
        app.api_hash = api_hash
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = "login"


# ══════════════════════════════════════════════════════════════════════════════
#  ЭКРАН 2 — АВТОРИЗАЦИЯ
# ══════════════════════════════════════════════════════════════════════════════

class LoginScreen(Screen):

    def __init__(self, **kw):
        super().__init__(**kw)
        self._phone  = None
        self._awaiting_code = False

        root = BoxLayout(orientation="vertical", padding=dp(24), spacing=dp(16))
        root.add_widget(Label(
            text="📱  Вход в аккаунт",
            font_size=dp(20), bold=True, color=TEXT,
            size_hint_y=None, height=dp(50),
        ))

        self.phone_input = styled_input("+79001234567  (номер телефона)")
        self.code_input  = styled_input("Код из Telegram")
        self.pass_input  = styled_input("Пароль 2FA (если есть)", password=True)
        self.code_input.opacity  = 0
        self.pass_input.opacity  = 0

        self.status = Label(text="", color=SUBTEXT, size_hint_y=None, height=dp(30))
        self.btn    = styled_btn("Отправить код")
        self.btn.bind(on_press=self.on_action)

        for w in [self.phone_input, self.code_input, self.pass_input,
                  self.status, self.btn]:
            root.add_widget(w)
        root.add_widget(Label())
        self.add_widget(root)

    def set_status(self, text, color=SUBTEXT):
        def _set(*_): self.status.text = text; self.status.color = color
        Clock.schedule_once(_set, 0)

    def on_action(self, *_):
        if not self._awaiting_code:
            self._send_code()
        else:
            self._sign_in()

    def _send_code(self):
        self._phone = self.phone_input.text.strip()
        if not self._phone:
            show_popup("Ошибка", "Введите номер телефона", RED_C)
            return

        app = App.get_running_app()
        global _client
        _client = TelegramClient("tg_secret", app.api_id, app.api_hash)

        self.set_status("Отправляем код…")

        def _task():
            async def _do():
                await _client.connect()
                await _client.send_code_request(self._phone)
            fut = run_async(_do())
            try:
                fut.result(timeout=20)
                self._awaiting_code = True
                Clock.schedule_once(lambda *_: self._show_code_step(), 0)
            except Exception as e:
                self.set_status(f"Ошибка: {e}", RED_C)

        threading.Thread(target=_task, daemon=True).start()

    def _show_code_step(self):
        self.code_input.opacity = 1
        self.pass_input.opacity = 1
        self.btn.text = "Войти ✓"
        self.set_status("Код отправлен в Telegram", GREEN)

    def _sign_in(self):
        code = self.code_input.text.strip()
        if not code:
            show_popup("Ошибка", "Введите код из Telegram", RED_C)
            return

        self.set_status("Авторизация…")

        def _task():
            async def _do():
                try:
                    await _client.sign_in(self._phone, code)
                except SessionPasswordNeededError:
                    pw = self.pass_input.text.strip()
                    await _client.sign_in(password=pw)
                me = await _client.get_me()
                return me
            fut = run_async(_do())
            try:
                me = fut.result(timeout=20)
                Clock.schedule_once(
                    lambda *_: self._on_logged_in(me), 0)
            except Exception as e:
                self.set_status(f"Ошибка: {e}", RED_C)

        threading.Thread(target=_task, daemon=True).start()

    def _on_logged_in(self, me):
        self.set_status(
            f"Добро пожаловать, {me.first_name}!", GREEN)
        self.manager.transition = SlideTransition(direction="left")
        self.manager.current = "home"


# ══════════════════════════════════════════════════════════════════════════════
#  ЭКРАН 3 — ГЛАВНЫЙ ЭКРАН (КОНТАКТЫ + ДЕЙСТВИЯ)
# ══════════════════════════════════════════════════════════════════════════════

class HomeScreen(Screen):

    def __init__(self, **kw):
        super().__init__(**kw)
        root = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))

        root.add_widget(Label(
            text=f"{LOCK_ICON}  Секретные чаты",
            font_size=dp(20), bold=True, color=ACCENT,
            size_hint_y=None, height=dp(50),
        ))

        # Поиск
        search_row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        self.search_input = styled_input("@username собеседника")
        find_btn = styled_btn("Найти", height=dp(48), color=BG2)
        find_btn.bind(on_press=self.find_user)
        search_row.add_widget(self.search_input)
        search_row.add_widget(find_btn)
        root.add_widget(search_row)

        # Кнопки действий
        btn_secret = styled_btn(f"{LOCK_ICON}  Создать секретный чат")
        btn_secret.bind(on_press=self.create_secret)
        btn_contacts = styled_btn("👥  Мои контакты", color=BG2)
        btn_contacts.bind(on_press=self.load_contacts)
        root.add_widget(btn_secret)
        root.add_widget(btn_contacts)

        # Лог / список контактов
        scroll = ScrollView()
        self.log = Label(
            text="← Введите @username и нажмите «Найти»\nили загрузите контакты",
            color=SUBTEXT, halign="left", valign="top",
            size_hint_y=None, markup=True,
        )
        self.log.bind(texture_size=self.log.setter("size"))
        scroll.add_widget(self.log)
        root.add_widget(scroll)

        self.add_widget(root)
        self._found_user = None

    def append_log(self, text, color="#AABBCC"):
        def _do(*_):
            self.log.text += f"\n[color={color}]{text}[/color]"
        Clock.schedule_once(_do, 0)

    def set_log(self, text):
        def _do(*_): self.log.text = text
        Clock.schedule_once(_do, 0)

    # ── Поиск пользователя ───────────────────────────────────────────────────
    def find_user(self, *_):
        username = self.search_input.text.strip().lstrip("@")
        if not username:
            show_popup("Ошибка", "Введите @username", RED_C)
            return

        self.set_log("🔍 Ищем пользователя…")

        def _task():
            async def _do():
                result = await _client(ResolveUsernameRequest(username))
                return result.users[0]
            fut = run_async(_do())
            try:
                user = fut.result(timeout=15)
                self._found_user = user
                name = f"{user.first_name} {user.last_name or ''}".strip()
                self.set_log(
                    f"[color=#2AABEE]✔ Найден:[/color] {name}\n"
                    f"[color=#8899AA]ID: {user.id}  @{user.username or '—'}[/color]\n\n"
                    f"Теперь нажмите «{LOCK_ICON} Создать секретный чат»"
                )
            except Exception as e:
                self.set_log(f"[color=#F44336]✖ Не найден: {e}[/color]")

        threading.Thread(target=_task, daemon=True).start()

    # ── Создание секретного чата ─────────────────────────────────────────────
    def create_secret(self, *_):
        if not self._found_user:
            show_popup("Внимание",
                       "Сначала найдите пользователя через поиск", get_color_from_hex("#FFCC00"))
            return

        user = self._found_user
        self.append_log(f"\n{LOCK_ICON} Отправляем запрос секретного чата…", "#2AABEE")

        def _task():
            async def _do():
                input_user = InputUser(
                    user_id=user.id,
                    access_hash=user.access_hash,
                )
                result = await _client(RequestEncryptionRequest(user_id=input_user))
                return result
            fut = run_async(_do())
            try:
                chat = fut.result(timeout=20)
                self.append_log(
                    f"✔ Запрос отправлен! ID чата: {chat.id}", "#4CAF50")
                self.append_log(
                    "⚠ Попросите собеседника принять запрос\n   в официальном Telegram-клиенте", "#FFCC00")
            except Exception as e:
                self.append_log(f"✖ Ошибка: {e}", "#F44336")

        threading.Thread(target=_task, daemon=True).start()

    # ── Загрузка контактов ───────────────────────────────────────────────────
    def load_contacts(self, *_):
        self.set_log("⏳ Загружаем контакты…")

        def _task():
            async def _do():
                result = await _client(GetContactsRequest(hash=0))
                return result.users
            fut = run_async(_do())
            try:
                users = fut.result(timeout=15)
                if not users:
                    self.set_log("[color=#FFCC00]Контакты не найдены[/color]")
                    return
                lines = ["[color=#2AABEE][b]👥 Ваши контакты:[/b][/color]\n"]
                for u in users:
                    name = f"{u.first_name} {u.last_name or ''}".strip()
                    uname = f"@{u.username}" if u.username else "—"
                    lines.append(f"• {name}  [color=#8899AA]{uname}[/color]")
                self.set_log("\n".join(lines))
            except Exception as e:
                self.set_log(f"[color=#F44336]Ошибка: {e}[/color]")

        threading.Thread(target=_task, daemon=True).start()


# ══════════════════════════════════════════════════════════════════════════════
#  ПРИЛОЖЕНИЕ
# ══════════════════════════════════════════════════════════════════════════════

class TelegramSecretApp(App):
    api_id   = 0
    api_hash = ""

    def build(self):
        sm = ScreenManager()
        sm.add_widget(ApiScreen(name="api"))
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(HomeScreen(name="home"))
        return sm


if __name__ == "__main__":
    TelegramSecretApp().run()
