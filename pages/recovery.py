from kivy.lang import *
from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import *
from kivymd.uix.button import *
from kivy.metrics import *

email_helper = '''
MDTextField:
    hint_text: 'E-mail'
    size_hint: 0.8, None
    height: '20dp'
    pos_hint: {'center_x': 0.5, 'center_y': 0.5}
'''

class RecoveryScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = FloatLayout()

        label_up = MDLabel(
            text='Please enter your e-mail to',
            halign='center',
            font_style='Button',  
            text_size='50px',
            font_size='40sp',
            pos_hint= {'center_x': 0.5,'center_y': 0.7}
            )
        
        layout.add_widget(label_up)

        label_down = MDLabel(
            text='get the recovery link.',
            halign='center',
            font_style='Button',  
            text_size='50px',
            font_size='40sp',
            pos_hint= {'center_x': 0.5,'center_y': 0.675}
            )

        layout.add_widget(label_down)

        email = Builder.load_string(email_helper) 
        layout.add_widget(email)

        btn_flat = MDRaisedButton(
            text="Confirm",
            size_hint=(None, None),
            pos_hint={'center_x': 0.5, 'center_y': 0.4},
        )

        btn_icon = MDFloatingActionButton(
            icon="arrow-left",
            icon_size="25sp",
            pos_hint={'x': 0, 'top': 1},
            on_release=self.go_login,
            size_hint= (None, None),
            size=(dp(20),dp(20)),
            )
        layout.add_widget(btn_icon)

        layout.add_widget(btn_flat)
        self.add_widget(layout)

    def go_login(self, *args):
        self.manager.current = 'login'