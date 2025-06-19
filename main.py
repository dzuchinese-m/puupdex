from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivymd.font_definitions import theme_font_styles
from kivy.event import EventDispatcher
import os
import threading
import importlib # Added for dynamic imports

parent_dir = os.path.dirname(__file__)  # puupdex folder

# AI model import is also deferred to where it's used, or can remain if load_model is a simple function definition
# from features.artificial_intelligence import load_model 
from kivy.config import Config
Config.set('input', 'mouse', 'mouse,disable_multitouch')

class DemoApp(MDApp, EventDispatcher):
    __events__ = ('on_new_analysis',) # Register the event

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set theme before any widget is created
        self.theme_cls.primary_palette = "LightBlue"
        self.theme_cls.theme_style = "Dark"
        # Register font before any widget is created
        try:
            LabelBase.register(name="JetBrainsMono", fn_regular="assets/fonts/JetBrainsMono-Regular.ttf")
        except Exception as e:
            print(f"Font registration failed: {e}")
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

    _screen_instances = {} # Cache for instantiated screen instances
    _screen_module_paths = { # Maps screen names to their module path and class name
        'login': ('pages.login', 'LoginScreen'),
        'registration': ('pages.registration', 'RegistrationScreen'),
        'recovery': ('pages.recovery', 'RecoveryScreen'),
        'dashboard': ('pages.dashboard', 'DashboardScreen'),
        'upload': ('features.upload', 'UploadFeature'), # Assuming UploadFeature is a Kivy Screen
        'analyse': ('features.analyse', 'AnalyseFeature'), # Assuming AnalyseFeature is a Kivy Screen
    }

    def build(self):
        Window.size = (768, 1024) # Tablet's
        Window.orientation = 'portrait'
        self.root = ScreenManager()

        # Load the initial screen
        self.ensure_screen_loaded('login')
        self.root.current = 'login'  # Set the initial screen

        return self.root

    def ensure_screen_loaded(self, screen_name):
        """Dynamically imports and instantiates a screen if not already loaded."""
        if screen_name not in self._screen_instances:
            if screen_name not in self._screen_module_paths:
                print(f"Error: Screen '{screen_name}' is not defined in _screen_module_paths.")
                return False
            
            module_path, class_name = self._screen_module_paths[screen_name]
            try:
                module = importlib.import_module(module_path)
                ScreenClass = getattr(module, class_name)
                # Check if ScreenClass is a subclass of Screen
                if not issubclass(ScreenClass, Screen):
                    print(f"Error: {class_name} in {module_path} is not a subclass of kivy.uix.screenmanager.Screen.")
                    print(f"Type loaded: {type(ScreenClass)}")
                    return False
                instance = ScreenClass(name=screen_name)
                self.root.add_widget(instance)
                self._screen_instances[screen_name] = instance
                print(f"Successfully loaded and added screen: {screen_name}")
            except Exception as e:
                import traceback
                print(f"Error loading screen {screen_name} (from {module_path}.{class_name}): {e}")
                traceback.print_exc()
                return False
        return True

    def switch_to_screen(self, screen_name, *args): # *args for kv compatibility e.g. on_release
        """Switches to the specified screen, loading it if necessary."""
        if self.ensure_screen_loaded(screen_name):
            self.root.current = screen_name
        else:
            # Fallback or error handling if screen loading failed
            print(f"Critical: Could not switch to screen '{screen_name}' due to loading errors.")
            # Optionally, switch to a default error screen or stay on the current screen
            # For now, we'll just print the error. If current screen is invalid, Kivy might error.
            if not self.root.has_screen(self.root.current): # Ensure current screen is valid
                 if 'login' in self._screen_instances: # Try to go to login if current is bad
                    self.root.current = 'login'
                 else: # Absolute fallback, though ensure_screen_loaded('login') should run in build
                    pass # Or raise an exception

    def on_start(self):
        # Load the AI model in a background thread
        thread = threading.Thread(target=self.load_model_in_background)
        thread.daemon = True # Allow main program to exit even if thread is still running
        thread.start()

    def load_model_in_background(self):
        """Helper method to load the model, called in a separate thread."""
        try:
            from features.artificial_intelligence import load_model
            print("Starting AI model loading in background...")
            load_model()  # Ensure this does NOT touch any Kivy UI or properties!
            print("AI model loaded successfully in background!")
        except Exception as e:
            import traceback
            print("Exception occurred while loading AI model in background:")
            traceback.print_exc()

    def on_new_analysis(self, *args): # Add the default handler
        """
        Default handler for the on_new_analysis event.
        This event is dispatched when a new analysis is saved.
        """
        pass

if __name__ == "__main__":
    DemoApp().run()
