import os
from kivy.uix.screenmanager import Screen
from kivymd.uix.button import MDRectangleFlatIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from plyer import filechooser
from kivy.metrics import dp
from pyrebaseConfig import auth
from kivymd.toast import toast
from kivymd.app import MDApp # Added import

class SettingsFeature(Screen):
    def __init__(self, screen_manager=None, **kwargs):
        super().__init__(**kwargs)
        self.selected_file_path = None
        self.screen_manager = screen_manager  # Reference to main ScreenManager
        self.setup_ui()

    def setup_ui(self):
        main_layout = MDBoxLayout(
            orientation='vertical',
            spacing=dp(20),
            adaptive_height=True,
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            size_hint_y=None,
            height=dp(400)
        )

        settings_card = MDCard(
            orientation='vertical',
            padding=dp(20),
            spacing=dp(15),
            size_hint=(0.9, None),
            height=dp(75),
            pos_hint={'center_x': 0.5},
            elevation=2
        )

        title = MDLabel(
            text="What do you want to do?",
            font_style="H5",
            halign="center",
            size_hint_y=None,
            height=dp(50)
        )
        main_layout.add_widget(title)

        self.select_button = MDRectangleFlatIconButton(
            text="Sign out",
            icon="logout",
            halign="center",
            size_hint=(1, None),
            height=dp(50),
            on_release=self.sign_out
        )
        settings_card.add_widget(self.select_button)

        main_layout.add_widget(settings_card)
        self.add_widget(main_layout)

    def sign_out(self, instance):
        try:
            # Clear pyrebase auth session
            auth.current_user = None
            # If you store user info or tokens elsewhere, clear them here as well
            # For example, if you have a global or app-level user variable:
            app = MDApp.get_running_app()
            if hasattr(app, "user"):
                app.user = None
            toast("Signed out successfully!")
        except Exception as e:
            print(f"Sign out error: {e}")
            toast("Error signing out.")
        # Return to login screen and optionally reset login fields
        app = MDApp.get_running_app()
        app.switch_to_screen('login')
        # Optionally reset login fields if needed:
        login_screen = app.root.get_screen('login')
        if hasattr(login_screen, "email_field"):
            login_screen.email_field.text = ""
        if hasattr(login_screen, "password_field"):
            login_screen.password_field.text = ""
