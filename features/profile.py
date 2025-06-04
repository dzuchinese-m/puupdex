import os
from kivy.uix.floatlayout import FloatLayout
from kivymd.uix.button import MDRectangleFlatIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivy.metrics import dp
from kivy.uix.image import Image as KivyImage
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.scrollview import ScrollView
from plyer import filechooser
from PIL import Image as PILImage
import tempfile
from kivymd.toast import toast
from pyrebaseConfig import storage

class ClickableImage(ButtonBehavior, KivyImage):
    pass

class ProfileFeature(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._cropped_tempfile = None
        self.profile_ui()

    def profile_ui(self):
        main_layout = MDBoxLayout(
            orientation='vertical',
            spacing=dp(20),
            adaptive_height=True,
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            size_hint_y=None,
            height=dp(540)
        )

        upload_card = MDCard(
            orientation='vertical',
            padding=dp(20),
            spacing=dp(15),
            size_hint=(0.9, None),
            height=dp(340),
            pos_hint={'center_x': 0.5},
            elevation=2
        )

        title = MDLabel(
            text="Profile",
            font_style="H5",
            halign="center",
            size_hint_y=None,
            height=dp(50)
        )
        main_layout.add_widget(title)

        # Profile picture area
        self.pfp_image = ClickableImage(
            source='assets/pfp/easter_egg.png',  # Set default pfp
            size_hint=(None, None),
            width=dp(120),
            height=dp(120),
            allow_stretch=True,
            keep_ratio=False,
            pos_hint={'center_x': 0.5}
        )
        self.pfp_image.bind(on_release=self.open_file_explorer)
        # Add a border around the image
        bordered_pfp = MDBoxLayout(
            size_hint=(None, None),
            width=dp(124),
            height=dp(124),
            padding=dp(2),
            pos_hint={'center_x': 0.5}
        )
        bordered_pfp.add_widget(self.pfp_image)
        upload_card.add_widget(bordered_pfp)

        # Name field
        self.name_field = MDTextField(
            hint_text='Name',
            size_hint=(1, None),
            height=dp(40),
            pos_hint={'center_x': 0.5}
        )
        upload_card.add_widget(self.name_field)

        # Birth date field
        self.birth_field = MDTextField(
            hint_text='Birth Date (DD/MM/YYYY)',
            text='1/1/1970',
            size_hint=(1, None),
            height=dp(40),
            pos_hint={'center_x': 0.5}
        )
        upload_card.add_widget(self.birth_field)

        # Sex field
        self.sex_field = MDTextField(
            hint_text='Sex',
            size_hint=(1, None),
            height=dp(40),
            pos_hint={'center_x': 0.5}
        )
        upload_card.add_widget(self.sex_field)

        # Save button
        self.save_button = MDRectangleFlatIconButton(
            text="Save",
            icon="content-save",
            halign="center",
            size_hint=(1, None),
            height=dp(50),
            on_release=self.save_profile_info
        )
        upload_card.add_widget(self.save_button)

        main_layout.add_widget(upload_card)
        self.add_widget(main_layout)

    def open_file_explorer(self, instance):
        try:
            filechooser.open_file(
                on_selection=self.on_file_selected,
                filters=[
                    ("Image files", "*.jpg", "*.jpeg", "*.png", "*.bmp", "*.gif"),
                    ("All files", "*.*")
                ],
                title="Select a profile picture"
            )
        except Exception as e:
            print(f"Error opening file explorer: {e}")

    def _center_crop_image(self, image_path):
        """Crop the image to a 1:1 aspect ratio centered, resize to 120x120, and save to a temp file."""
        img = PILImage.open(image_path).convert("RGB")
        width, height = img.size
        min_dim = min(width, height)
        left = (width - min_dim) // 2
        top = (height - min_dim) // 2
        right = left + min_dim
        bottom = top + min_dim
        img_cropped = img.crop((left, top, right, bottom)).resize((120, 120), PILImage.LANCZOS)
        temp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        img_cropped.save(temp.name)
        temp.close()
        return temp.name

    def on_file_selected(self, selection):
        if selection:
            image_path = selection[0]
            # Remove previous temp file if exists
            if self._cropped_tempfile:
                try:
                    os.remove(self._cropped_tempfile)
                except Exception:
                    pass
                self._cropped_tempfile = None
            cropped_path = self._center_crop_image(image_path)
            self._cropped_tempfile = cropped_path
            self.pfp_image.source = cropped_path
            self.pfp_image.reload()
            print(f"Profile picture set: {cropped_path}")
            # Upload to Firebase Storage
            try:
                # You can change the path as needed, e.g., use user id or name
                storage.child("profile_pictures/user_pfp.png").put(cropped_path)
                toast("Profile picture uploaded to Firebase!")
            except Exception as e:
                print(f"Failed to upload profile picture: {e}")
                toast("Failed to upload profile picture.")

    def save_profile_info(self, instance):
        name = self.name_field.text
        birth = self.birth_field.text
        sex = self.sex_field.text
        print(f"Saved profile: Name={name}, Birth={birth}, Sex={sex}")