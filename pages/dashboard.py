from kivy.lang import *
from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivymd.uix.label import *
from kivymd.uix.textfield import *
from kivymd.uix.button import *
from kivy.metrics import *
from kivy.uix.behaviors import ButtonBehavior
from kivymd.uix.bottomnavigation import *
from kivymd.app import MDApp

# Features!
from features.upload import UploadFeature
from features.profile import ProfileFeature
from features.settings import SettingsFeature

class DashboardScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = FloatLayout()
        bottom_nav = MDBottomNavigation()

        # Get the main ScreenManager from the app
        from kivymd.app import MDApp
        app = MDApp.get_running_app() if MDApp.get_running_app() else None
        screen_manager = app.root if app else None

        tab1 = MDBottomNavigationItem(
            name='analyse',
            text='Analyse',
            icon='image-search'
        )
        # Place UploadFeature directly in the tab, passing the main ScreenManager
        tab1.add_widget(UploadFeature(screen_manager=screen_manager))
        bottom_nav.add_widget(tab1)

        tab2 = MDBottomNavigationItem(
            name='history',
            text='History',
            icon='history'
        )
        #tab2.add_widget()
        bottom_nav.add_widget(tab2)

        tab3 = MDBottomNavigationItem(
            name='profile',
            text='Profile',
            icon='account'
        )
        tab3.add_widget(ProfileFeature())
        bottom_nav.add_widget(tab3)

        tab4 = MDBottomNavigationItem(
            name='settings',
            text='Settings',
            icon='cog'
        )
        tab4.add_widget(SettingsFeature())
        bottom_nav.add_widget(tab4)

        layout.add_widget(bottom_nav)

        self.add_widget(layout)