from kivy.lang import *
from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import *
from kivymd.uix.button import *
from kivy.metrics import *
from kivy.uix.textinput import TextInput
from kivymd.toast import toast

from pyrebaseConfig import auth

class RegistrationScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = FloatLayout()

        label = MDLabel(
            text='Please, tell us about yourself.',
            font_style='Button',  
            pos_hint= {'center_x': 0.5,'center_y': 0.8},
            halign='center',
            )
        
        layout.add_widget(label)

        # Use MDTextField directly so you can access .text
        self.name_field = MDTextField(
            hint_text='Name',
            size_hint=(0.8, None),
            height='20dp',
            pos_hint={'center_x': 0.5, 'center_y': 0.7}
        )
        layout.add_widget(self.name_field)

        self.username_field = MDTextField(
            hint_text='Username',
            size_hint=(0.8, None),
            height='20dp',
            pos_hint={'center_x': 0.5, 'center_y': 0.6}
        )
        layout.add_widget(self.username_field)

        self.email_field = MDTextField(
            hint_text='E-mail',
            size_hint=(0.8, None),
            height='20dp',
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        layout.add_widget(self.email_field)

        self.password_field = MDTextField(
            hint_text='Password',
            size_hint=(0.8, None),
            height='20dp',
            pos_hint={'center_x': 0.5, 'center_y': 0.4},
            password=True
        )
        layout.add_widget(self.password_field)

        btn_icon = MDFloatingActionButton(
            icon="arrow-left",
            icon_size="25sp",
            pos_hint={'x': 0, 'top': 1},
            on_release=self.go_login,
            size_hint= (None, None),
            size=(dp(20),dp(20)),
            )
        layout.add_widget(btn_icon)

        btn_flat = MDRaisedButton(
            text="Sign Up",
            size_hint=(None, None),
            pos_hint={'center_x': 0.5, 'center_y': 0.3},
            on_release=self.register_with_firebase
        )
        layout.add_widget(btn_flat)

        self.add_widget(layout)

    def register_with_firebase(self, instance):
        # Now you can safely access .text
        email = self.email_field.text
        password = self.password_field.text
        try:
            user = auth.create_user_with_email_and_password(email, password)
            print("Registration successful:", user['email'] if 'email' in user else user)
            toast("Registration successful!")
            # self.manager.current = 'login'  # Uncomment to redirect after registration
        except Exception as e:
            print("Registration failed:", e)
            toast("Registration failed. Check your input.")

    def go_login(self, *args):
        self.manager.current = 'login'
