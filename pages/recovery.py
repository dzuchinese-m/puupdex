from kivy.lang import *
from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import *
from kivymd.uix.button import *
from kivy.metrics import *
from kivymd.toast import toast
from pyrebaseConfig import auth
from kivymd.uix.dialog import MDDialog

class RecoveryScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.layout = FloatLayout()
        self.state = "email"  # can be "email", "reset"

        self.label_up = MDLabel(
            text='Please enter your e-mail to',
            halign='center',
            font_style='Button',  
            text_size='50px',
            font_size='40sp',
            pos_hint= {'center_x': 0.5,'center_y': 0.6}
        )
        self.layout.add_widget(self.label_up)

        self.label_down = MDLabel(
            text='get the recovery link.',
            halign='center',
            font_style='Button',  
            text_size='50px',
            font_size='40sp',
            pos_hint= {'center_x': 0.5,'center_y': 0.575}
        )
        self.layout.add_widget(self.label_down)

        self.email_field = MDTextField(
            hint_text='E-mail',
            size_hint=(0.8, None),
            height='20dp',
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        self.layout.add_widget(self.email_field)

        self.confirm_button = MDRaisedButton(
            text="Confirm",
            size_hint=(None, None),
            pos_hint={'center_x': 0.5, 'center_y': 0.4},
            on_release=self.handle_confirm
        )
        self.layout.add_widget(self.confirm_button)

        self.btn_icon = MDFloatingActionButton(
            icon="arrow-left",
            icon_size="25sp",
            pos_hint={'x': 0, 'top': 1},
            on_release=self.go_login,
            size_hint= (None, None),
            size=(dp(20),dp(20)),
        )
        self.layout.add_widget(self.btn_icon)

        self.add_widget(self.layout)
        self.dialog = None

    def handle_confirm(self, instance):
        if self.state == "email":
            email = self.email_field.text
            if not email:
                toast("Please enter your email.")
                return
            try:
                # Send password reset email
                auth.send_password_reset_email(email)
                self.show_popup()
                self.state = "reset"
            except Exception as e:
                print("Failed to send recovery email:", e)
                toast("Failed to send recovery email.")

    def show_popup(self):
        if self.dialog:
            self.dialog.dismiss()
        self.dialog = MDDialog(
            title="Recovery Link Sent",
            text="A password reset link has been sent to your email. Please check your inbox and follow the instructions.",
            buttons=[
                MDRaisedButton(
                    text="Okay!",
                    on_release=lambda x: self.dialog.dismiss()
                )
            ]
        )
        self.dialog.open()

    def go_login(self, *args):
        self.manager.current = 'login'