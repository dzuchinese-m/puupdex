from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivymd.font_definitions import theme_font_styles
from kivy.event import EventDispatcher
import os

parent_dir = os.path.dirname(__file__)  # puupdex folder

# Pages!
from pages.login import LoginScreen
from pages.registration import RegistrationScreen
from pages.recovery import RecoveryScreen
from pages.dashboard import DashboardScreen
# Features!
from features.upload import UploadFeature
from features.analyse import AnalyseFeature

# Load AI model at startup
from features.artificial_intelligence import load_model
from kivy.config import Config
Config.set('input', 'mouse', 'mouse,disable_multitouch')

class DemoApp(MDApp, EventDispatcher):
    __events__ = ('on_new_analysis',) # Register the event

    def build(self):
        self.theme_cls.primary_palette = "LightBlue"
        self.theme_cls.theme_style = "Dark"
        Window.size = (768, 1024) # Tablet's
        Window.orientation = 'portrait'

        LabelBase.register(name="JetBrainsMono", fn_regular="assets/fonts/JetBrainsMono-Regular.ttf")
        if "JetBrainsMono" not in theme_font_styles:
            theme_font_styles.append("JetBrainsMono")

        font_styles = {
            "H1": ["JetBrainsMono", 96, False, -1.5], "H2": ["JetBrainsMono", 60, False, -0.5],
            "H3": ["JetBrainsMono", 48, False, 0], "H4": ["JetBrainsMono", 34, False, 0.25],
            "H5": ["JetBrainsMono", 24, False, 0], "H6": ["JetBrainsMono", 20, False, 0.15],
            "Subtitle1": ["JetBrainsMono", 16, False, 0.15], "Subtitle2": ["JetBrainsMono", 14, False, 0.1],
            "Body1": ["JetBrainsMono", 16, False, 0.5], "Body2": ["JetBrainsMono", 14, False, 0.25],
            "Button": ["JetBrainsMono", 14, True, 1.25], "Caption": ["JetBrainsMono", 12, False, 0.4],
            "Overline": ["JetBrainsMono", 10, True, 1.5],
        }
        self.theme_cls.font_styles.update(font_styles)

        self.root = ScreenManager()

        # Instantiate screens only once and reuse them
        self.dashboard_screen = DashboardScreen(name='dashboard')
        self.root.add_widget(self.dashboard_screen)
        self.login_screen = LoginScreen(name='login')
        self.root.add_widget(self.login_screen)
        self.registration_screen = RegistrationScreen(name='registration')
        self.root.add_widget(self.registration_screen)
        self.recovery_screen = RecoveryScreen(name='recovery')
        self.root.add_widget(self.recovery_screen)
        self.upload_screen = UploadFeature(name='upload')
        self.root.add_widget(self.upload_screen)
        self.analyse_screen = AnalyseFeature(name='analyse')
        self.root.add_widget(self.analyse_screen)

        self.root.current = 'login'  # Set the initial screen

        return self.root

    def on_start(self):
        pass

    def on_new_analysis(self, *args): # Add the default handler
        """
        Default handler for the on_new_analysis event.
        This event is dispatched when a new analysis is saved.
        """
        pass

if __name__ == "__main__":
    load_model() # Load the model once at startup
    print("AI model loaded successfully!")
    DemoApp().run()