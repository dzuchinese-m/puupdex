import os
from kivy.uix.screenmanager import Screen
from kivymd.uix.button import MDRectangleFlatIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from plyer import filechooser
from kivy.metrics import dp

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
                filters=[("Image files", "*.jpg", "*.jpeg", "*.png", "*.bmp", "*.gif"),
                         ("All files", "*.*")],
                title="Select an image"
            )
        except Exception as e:
            print(f"Error opening file explorer: {e}")
            self.select_button.disabled = False

    def on_file_selected(self, selection):
        """Handle file selection"""
        if selection:
            self.selected_file_path = selection[0]
            print(f"File selected: {self.selected_file_path}")
            # Pass file path to analyse screen and redirect
            sm = self.screen_manager or self.manager
            if sm:
                analyse_screen = sm.get_screen("analyse")
                analyse_screen.selected_file_path = self.selected_file_path
                # Optionally update UI on analyse screen
                filename = os.path.basename(self.selected_file_path)
                analyse_screen.file_label.text = f"Selected: {filename}"
                analyse_screen.image_preview.source = self.selected_file_path
                analyse_screen.analyze_button.disabled = False
                sm.current = "analyse"
        else:
            print("No file selected.")

        # Re-enable the select button
        self.select_button.disabled = False

