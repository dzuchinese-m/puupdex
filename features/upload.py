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

            sm = self.screen_manager or self.manager
            print(f"UploadFeature: ScreenManager instance: {sm}") # Debug SM
            if sm:
                analyse_screen = sm.get_screen("analyse")
                print(f"UploadFeature: Analyse screen instance: {analyse_screen}") # Debug analyse_screen

                # Call a method on AnalyseFeature to set the file path and type
                if hasattr(analyse_screen, 'prepare_for_analysis'):
                    print(f"UploadFeature: Calling prepare_for_analysis for {self.selected_file_path}") # Debug call
                    analyse_screen.prepare_for_analysis(self.selected_file_path, is_video)
                    print(f"UploadFeature: prepare_for_analysis completed") # Debug call complete
                else:
                    print("Error: AnalyseFeature does not have prepare_for_analysis method.")
                
                print(f"UploadFeature: Attempting to switch to 'analyse' screen. Current before: {sm.current}") # Debug current screen
                sm.current = "analyse"
                # It's good practice to schedule the check for after the frame, to ensure Kivy has processed the change
                Clock.schedule_once(lambda dt: print(f"UploadFeature: Switched. Current screen after change: {sm.current}"), 0)
            else:
                print("UploadFeature: ScreenManager not found!") # Debug if SM is None

            self.select_button.disabled = False # Re-enable button
        else:
            # No file selected, re-enable the button
            self.select_button.disabled = False

    def open_camera_mbnv2(self, instance):
        """Open the camera using the integrated real-time breed detection."""
        # Disable the button to prevent multiple clicks
        self.capture_button.disabled = True
        mbnv2_script = os.path.join(os.path.dirname(__file__), "..", "dog_identification", "MBNv2test.py")
        mbnv2_script = os.path.abspath(mbnv2_script)
        try:
            subprocess.Popen([sys.executable, mbnv2_script]) 
        except Exception as e:
            print(f"Error opening camera with MobileNetV2: {e}")
        finally:
            # Re-enable the button after the operation attempts to complete
            self.capture_button.disabled = False

    def go_dashboard(self, instance):
        sm = self.screen_manager or self.manager
        if sm:
            sm.current = "dashboard"

# Example of how to integrate with ScreenManager in main.py (conceptual)
# class PuupDexApp(MDApp):
#     def build(self):

