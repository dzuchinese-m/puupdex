from kivy.lang import *
from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivymd.uix.label import *
from kivymd.uix.textfield import *
from kivymd.uix.button import *
from kivy.metrics import *
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivymd.toast import toast
from kivymd.app import MDApp # Added import

from pyrebaseConfig import auth

class ClickableMDLabel(ButtonBehavior, MDLabel):
    pass

class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = FloatLayout()

        label = MDLabel(
            text='Tell us, who are you?',
            halign='center',
            font_style='Button',  
            font_size='60sp',
            size_hint=(0.8, None),
            pos_hint= {'center_x': 0.5,'center_y': 0.7}
        )
        layout.add_widget(label)

        # Use MDTextField directly so you can access .text
        self.email_field = MDTextField(
            hint_text='E-mail',
            size_hint=(0.8, None),
            height='20dp',
            pos_hint={'center_x': 0.5, 'center_y': 0.6}
        )
        layout.add_widget(self.email_field)

        self.password_field = MDTextField(
            hint_text='Password',
            size_hint=(0.8, None),
            height='20dp',
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            password=True
        )
        layout.add_widget(self.password_field)

        forgot_password = ClickableMDLabel(
            text='[u]Forgot your identity?[/u]',
            markup=True,
            halign='center',
            theme_text_color='Primary',
            font_style='Caption',
            size_hint=(None, None),
            height='20dp',
            width='200dp',
            pos_hint={'center_x': 0.5, 'center_y': 0.43},
        )
        forgot_password.bind(on_release=self.go_recovery)
        layout.add_widget(forgot_password)

        sign_up = ClickableMDLabel(
            text="[u]Don't know who you are?[/u]",
            markup=True,
            halign='center',
            theme_text_color="Primary",
            font_style='Caption',
            size_hint=(None, None),
            height='20dp',
            width='200dp',
            pos_hint={'center_x': 0.5, 'center_y': 0.4},
        )

        sign_up.bind(on_release=self.go_registeration)
        layout.add_widget(sign_up)

        btn_flat = MDRaisedButton(
            text="Login",
            size_hint=(None, None),
            pos_hint={'center_x': 0.5, 'center_y': 0.325},
            on_release=self.login_with_firebase
        )

        layout.add_widget(btn_flat)
        self.add_widget(layout)

    def login_with_firebase(self, instance):
        # Get email and password from the text fields
        email = self.email_field.text
        password = self.password_field.text
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            print("Login successful:", user['email'] if 'email' in user else user)
            toast("Login successful!")
            MDApp.get_running_app().switch_to_screen('dashboard') # Changed this line
        except Exception as e:
            print("Login failed:", e)
            toast("Login failed. Check your credentials.")

    def go_registeration(self, *args):
        MDApp.get_running_app().switch_to_screen('registration') # Changed this line

    def go_recovery(self, *args):
        MDApp.get_running_app().switch_to_screen('recovery') # Changed this line
