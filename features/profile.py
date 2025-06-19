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
from pyrebaseConfig import storage, db, auth

class ClickableImage(ButtonBehavior, KivyImage):
    pass

class ProfileFeature(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._cropped_tempfile = None
        self.edit_mode = False
        self.profile_ui()
        self.load_profile_info()

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
            height=dp(400),
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
            source='assets/pfp/easter_egg.png',
            size_hint=(None, None),
            width=dp(120),
            height=dp(120),
            allow_stretch=True,
            keep_ratio=False,
            pos_hint={'center_x': 0.5}
        )
        self.pfp_image.bind(on_release=self.open_file_explorer)
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
            pos_hint={'center_x': 0.5},
            disabled=True
        )
        upload_card.add_widget(self.name_field)

        # Birth date field
        self.birth_field = MDTextField(
            hint_text='Birth Date (DD/MM/YYYY)',
            text='1/1/1970',
            size_hint=(1, None),
            height=dp(40),
            pos_hint={'center_x': 0.5},
            disabled=True
        )
        upload_card.add_widget(self.birth_field)

        # Sex field
        self.sex_field = MDTextField(
            hint_text='Sex',
            size_hint=(1, None),
            height=dp(40),
            pos_hint={'center_x': 0.5},
            disabled=True
        )
        upload_card.add_widget(self.sex_field)

        # Edit and Save buttons
        self.edit_button = MDRectangleFlatIconButton(
            text="Edit",
            icon="pencil",
            halign="center",
            size_hint=(1, None),
            height=dp(50),
            on_release=self.enable_edit_mode
        )
        upload_card.add_widget(self.edit_button)

        self.save_button = MDRectangleFlatIconButton(
            text="Save",
            icon="content-save",
            halign="center",
            size_hint=(1, None),
            height=dp(50),
            on_release=self.save_profile_info,
            disabled=True
        )
        upload_card.add_widget(self.save_button)

        main_layout.add_widget(upload_card)
        self.add_widget(main_layout)

    def enable_edit_mode(self, instance):
        self.edit_mode = True
        self.name_field.disabled = False
        self.birth_field.disabled = False
        self.sex_field.disabled = False
        self.save_button.disabled = False
        self.edit_button.disabled = True

    def disable_edit_mode(self):
        self.edit_mode = False
        self.name_field.disabled = True
        self.birth_field.disabled = True
        self.sex_field.disabled = True
        self.save_button.disabled = True
        self.edit_button.disabled = False

    def load_profile_info(self):
        try:
            user = getattr(auth, "current_user", None)
            id_token = None
            user_id = None
            # Try to get the latest user info from auth
            if user and "idToken" in user:
                id_token = user["idToken"]
                user_id = user.get("localId")
            elif hasattr(auth, 'current_user') and auth.current_user and "idToken" in auth.current_user:
                id_token = auth.current_user["idToken"]
                user_id = auth.current_user.get("localId")
            # If not found, try to refresh from local storage/session
            if not id_token or not user_id:
                print("No user token found, cannot load profile info.")
                self.name_field.text = ""
                self.birth_field.text = "1/1/1970"
                self.sex_field.text = ""
                self.disable_edit_mode()
                return
            # Try to fetch from /users/{user_id}/info first, fallback to /users/{user_id}
            info = None
            try:
                data = db.child("users").child(user_id).child("info").get(token=id_token)
                info = data.val()
                print(f"Loaded info from /users/{user_id}/info: {info}")
            except Exception as e:
                print(f"Could not load from /users/{user_id}/info: {e}")
            if not info:
                try:
                    data = db.child("users").child(user_id).get(token=id_token)
                    info = data.val()
                    print(f"Loaded info from /users/{user_id}: {info}")
                except Exception as e:
                    print(f"Could not load from /users/{user_id}: {e}")
            from kivy.clock import Clock
            def set_fields(*_):
                self.name_field.text = info.get("name", "") if info else ""
                self.birth_field.text = info.get("birth", "1/1/1970") if info else "1/1/1970"
                self.sex_field.text = info.get("sex", "") if info else ""
            Clock.schedule_once(set_fields, 0)
            self.disable_edit_mode()
        except Exception as e:
            print(f"Failed to load profile info: {e}")
            self.name_field.text = ""
            self.birth_field.text = "1/1/1970"
            self.sex_field.text = ""
            self.disable_edit_mode()

    def open_file_explorer(self, instance):
        if not self.edit_mode:
            return  # Only allow changing pfp in edit mode
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
        if not self.edit_mode:
            return
        if selection:
            image_path = selection[0]
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
            try:
                # Save to Firebase Storage under user id if available
                user = getattr(auth, "current_user", None)
                user_id = None
                if user and "localId" in user:
                    user_id = user["localId"]
                elif hasattr(auth, 'current_user') and auth.current_user and "localId" in auth.current_user:
                    user_id = auth.current_user["localId"]
                if user_id:
                    storage.child(f"profile_pictures/{user_id}.png").put(cropped_path)
                    toast("Profile picture uploaded to Firebase!")
                else:
                    storage.child("profile_pictures/user_pfp.png").put(cropped_path)
                    toast("Profile picture uploaded to Firebase (no user id)!");
            except Exception as e:
                print(f"Failed to upload profile picture: {e}")
                toast("Failed to upload profile picture.")

    def save_profile_info(self, instance):
        name = self.name_field.text
        birth = self.birth_field.text
        sex = self.sex_field.text
        print(f"Saved profile: Name={name}, Birth={birth}, Sex={sex}")
        try:
            user = getattr(auth, "current_user", None)
            id_token = None
            user_id = None
            if user and "idToken" in user:
                id_token = user["idToken"]
                user_id = user.get("localId")
            elif hasattr(auth, 'current_user') and auth.current_user and "idToken" in auth.current_user:
                id_token = auth.current_user["idToken"]
                user_id = auth.current_user.get("localId")
            if not id_token or not user_id:
                toast("No user logged in. Please log in again.")
                return
            db.child("users").child(user_id).set({
                "name": name,
                "birth": birth,
                "sex": sex
            }, id_token)
            toast("Profile info uploaded to Firebase!")
            self.disable_edit_mode()
        except Exception as e:
            print(f"Failed to upload profile info: {e}")
            toast("Failed to upload profile info.")

    def upload_profile_info_and_picture(user_id, info_dict, local_image_path=None):
        """
        Upload user profile info and profile picture to Firebase using pyrebase only.
        info_dict: dict of profile fields (e.g., name, email, bio, etc.)
        local_image_path: path to local image file (optional)
        """
        profile_pic_url = None
        if local_image_path:
            try:
                # Upload image to pyrebase storage
                storage.child(f"profile_pictures/{user_id}.png").put(local_image_path)
                # Get the download URL
                profile_pic_url = storage.child(f"profile_pictures/{user_id}.png").get_url(None)
                db.child("users").child(user_id).child("profile_picture").set(profile_pic_url)
                print(f"Profile picture uploaded and URL saved: {profile_pic_url}")
            except Exception as e:
                print(f"Error uploading profile picture: {e}")

        try:
            # Optionally add the profile_pic_url to info_dict for convenience
            if profile_pic_url:
                info_dict["profile_picture"] = profile_pic_url
            db.child("users").child(user_id).child("info").set(info_dict)
            print(f"Profile info uploaded for user {user_id}.")
        except Exception as e:
            print(f"Error uploading profile info: {e}")

    def fetch_profile_info_and_picture(user_id):
        """
        Fetch user profile info and profile picture URL from Firebase using pyrebase only.
        Returns a tuple: (info_dict, profile_pic_url)
        """
        info = None
        profile_pic_url = None
        try:
            info = db.child("users").child(user_id).child("info").get().val()
        except Exception as e:
            print(f"Error fetching profile info: {e}")
        try:
            profile_pic_url = db.child("users").child(user_id).child("profile_picture").get().val()
        except Exception as e:
            print(f"Error fetching profile picture URL: {e}")
        # Optionally, if info contains 'profile_picture', prefer that
        if info and "profile_picture" in info:
            profile_pic_url = info["profile_picture"]
        return info, profile_pic_url
