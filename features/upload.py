import os
import subprocess
import sys
from kivy.uix.screenmanager import Screen
from kivymd.uix.button import MDRectangleFlatIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from plyer import filechooser
from kivy.metrics import dp
from kivy.clock import Clock # Added for scheduling
from kivymd.app import MDApp # Added import

class UploadFeature(Screen):
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

        upload_card = MDCard(
            orientation='vertical',
            padding=dp(20),
            spacing=dp(15),
            size_hint=(0.9, None),
            height=dp(130),
            pos_hint={'center_x': 0.5},
            elevation=2
        )

        title = MDLabel(
            text="Choose a method:",
            font_style="H5",
            halign="center",
            size_hint_y=None,
            height=dp(50)
        )
        main_layout.add_widget(title)

        self.capture_button = MDRectangleFlatIconButton(
            text="Open Camera",
            icon="camera",
            halign="center",
            size_hint=(1, None),
            height=dp(50),
            on_release=self.open_camera_mbnv2
        )
        upload_card.add_widget(self.capture_button)

        self.select_button = MDRectangleFlatIconButton(
            text="Open File Explorer",
            icon="folder-open",
            halign="center",
            size_hint=(1, None),
            height=dp(50),
            on_release=self.open_file_explorer
        )
        upload_card.add_widget(self.select_button)

        main_layout.add_widget(upload_card)
        self.add_widget(main_layout)

    def open_file_explorer(self, instance):
        # Disable the button to prevent multiple clicks
        self.select_button.disabled = True
        try:
            filechooser.open_file(
                on_selection=self.on_file_selected,
                filters=[
                    ("Supported Media Files", "*.jpg;*.jpeg;*.png;*.bmp;*.gif;*.mp4;*.avi;*.mov;*.mkv"),
                    ("All files", "*.*")
                ],
                title="Select an image or video file"
            )
        except Exception as e:
            print(f"Error opening file explorer: {e}")
            self.select_button.disabled = False

    def on_file_selected(self, selection):
        """Handle file selection"""
        if selection:
            self.selected_file_path = selection[0]
            print(f"File selected: {self.selected_file_path}")
            
            file_extension = os.path.splitext(self.selected_file_path)[1].lower()
            is_video = file_extension in [".mp4", ".avi", ".mov", ".mkv"]

            # Get the running app instance
            app = MDApp.get_running_app()
            
            # It's better to pass data to the screen *after* ensuring it's loaded
            # and switched. We can store it in the app instance temporarily if needed,
            # or call a method on the screen instance after switching.

            # For now, let's assume AnalyseFeature will retrieve this path or
            # it will be passed via a method called after screen switch.
            # We can store it in the app instance for AnalyseFeature to pick up.
            app.current_analysis_file_path = self.selected_file_path
            app.current_analysis_is_video = is_video
            
            print(f"UploadFeature: Attempting to switch to 'analyse' screen.")
            app.switch_to_screen("analyse")
            # The prepare_for_analysis logic should ideally be in AnalyseFeature's on_enter or similar,
            # or called explicitly after the switch by whatever manages the flow.

            self.select_button.disabled = False # Re-enable button
        else:
            # No file selected, re-enable the button
            self.select_button.disabled = False

    def open_camera_mbnv2(self, instance):
        """Open the camera using the integrated real-time breed detection."""
        # Disable the button to prevent multiple clicks
        self.capture_button.disabled = True
        mbnv2_script = os.path.join(os.path.dirname(__file__), "..", "dog_identification", "YOLOnew.py")
        mbnv2_script = os.path.abspath(mbnv2_script)
        try:
            subprocess.Popen([sys.executable, mbnv2_script]) 
        except Exception as e:
            print(f"Error opening camera with MobileNetV2: {e}")
        finally:
            # Re-enable the button after the operation attempts to complete
            self.capture_button.disabled = False

    def go_dashboard(self, instance):
        # sm = self.screen_manager or self.manager # Not needed if using app instance
        # if sm: # Not needed
        MDApp.get_running_app().switch_to_screen("dashboard")

# Example of how to integrate with ScreenManager in main.py (conceptual)
# class PuupDexApp(MDApp):
#     def build(self):

