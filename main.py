"""
TG Secret Chat - тестовая версия
(без telethon для проверки сборки)
"""
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.utils import get_color_from_hex

class TGSecretApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=20)
        layout.add_widget(Label(
            text='🔐 TG Secret Chat\nСборка работает!',
            color=get_color_from_hex('#2AABEE'),
            halign='center',
            font_size='24sp'
        ))
        return layout

if __name__ == '__main__':
    TGSecretApp().run()
