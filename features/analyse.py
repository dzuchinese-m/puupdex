import os
from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.dialog import MDDialog
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.widget import Widget
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.popup import Popup
from plyer import filechooser
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.uix.image import Image
from kivy.metrics import dp
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.uix.button import MDFloatingActionButton
from PIL import Image as PILImage
import tempfile
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from kivy.uix.image import Image as KivyImage
from kivy.uix.scrollview import ScrollView
import subprocess
import sys


class AnalyseFeature(Screen):
    dialog = None,
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_file_path = None
        # Store path to cropped temp image
        self._cropped_tempfile = None
        self.setup_ui()

    def setup_ui(self):
        # Main container
        main_layout = FloatLayout()

        # Card container for upload area
        upload_card = MDCard(
            orientation='vertical',
            padding=dp(20),
            spacing=dp(15),
            size_hint=(None, None),
            size=(dp(300), dp(468)),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
            elevation=2
        )

        # Remove self.file_label from inside the card

        # Add spacing above the image
        from kivy.uix.widget import Widget
        upload_card.add_widget(Widget(size_hint_y=None, height=dp(14)))

        # Image preview area with black border, centered
        from kivy.uix.boxlayout import BoxLayout
        from kivy.graphics import Color, Rectangle, PushMatrix, PopMatrix, Translate, Scale
        from kivy.core.image import Image as CoreImage

        class CenterCropImage(Widget):
            def __init__(self, source='', **kwargs):
                super().__init__(**kwargs)
                self.source = source
                self.size_hint = (None, None)
                self.width = dp(224)
                self.height = dp(224)
                self.pos_hint = {'center_x': 0.5}
                self._coreimage = None
                self.bind(pos=self._update_canvas, size=self._update_canvas)
                self.reload()

            def reload(self):
                if self.source:
                    self._coreimage = CoreImage(self.source)
                else:
                    self._coreimage = None
                self._update_canvas()

            def _update_canvas(self, *args):
                self.canvas.clear()
                if not self._coreimage:
                    return
                iw, ih = self._coreimage.size
                tw, th = self.size
                # Calculate crop: scale to fill, then crop center
                scale = max(tw / iw, th / ih)
                sw, sh = iw * scale, ih * scale
                x = (tw - sw) / 2
                y = (th - sh) / 2
                with self.canvas:
                    Rectangle(texture=self._coreimage.texture, pos=(self.x + x, self.y + y), size=(sw, sh))

            @property
            def source(self):
                return self._source

            @source.setter
            def source(self, value):
                self._source = value
                self.reload()

        class BorderedImage(BoxLayout):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.size_hint = (None, None)
                self.width = dp(228)  # 224 + 2*2px border
                self.height = dp(228)
                self.padding = dp(2)
                self.orientation = 'vertical'
                self.pos_hint = {'center_x': 0.5}  # Center horizontally
                with self.canvas.before:
                    Color(1, 1, 1, 1)  # White
                    self.border_rect = Rectangle(pos=self.pos, size=self.size)
                self.bind(pos=self.update_rect, size=self.update_rect)

            def update_rect(self, *args):
                self.border_rect.pos = self.pos
                self.border_rect.size = self.size

        self.image_preview = Image(
            source='',
            size_hint=(None, None),  # Fixed size
            width=dp(224),
            height=dp(224),
            pos_hint={'center_x': 0.5},
            allow_stretch=True,
            keep_ratio=False
        )
        bordered_image = BorderedImage()
        bordered_image.add_widget(self.image_preview)
        upload_card.add_widget(bordered_image)

        # Add breed result label below the image preview
        self.breed_label = MDLabel(
            text="Breed: Undetermined",
            font_style="Caption",
            halign="center",
            size_hint_y=None,
            height=dp(30)
        )
        upload_card.add_widget(self.breed_label)

        self.select_button = MDRaisedButton(
            text="Change Image",
            icon="folder-open",
            size_hint=(1, None),
            height=dp(50),
            on_release=self.open_file_explorer
        )
        upload_card.add_widget(self.select_button)

        # Analyze button
        self.analyze_button = MDRaisedButton(
            text="Analyse Breed",
            icon="magnify",
            size_hint=(1, None),
            height=dp(50),
            disabled=True,
            on_release=self.analyze_image        )
        upload_card.add_widget(self.analyze_button)

        main_layout.add_widget(upload_card)

        # Add file label below the card, centered horizontally, with a gap
        self.file_label = MDLabel(
            text="No file selected",
            font_style="Caption",
            halign="center",
            size_hint=(None, None),
            width=dp(300),
            height=dp(30),
        )
        # Calculate y-position for the label below the card

        label_y = (170 - 50) / 780  # normalized y for pos_hint
        self.file_label.pos_hint = {'center_x': 0.5, 'y': label_y}
        main_layout.add_widget(self.file_label)

        # Add floating back button to go to dashboard (on top of card)
        btn_icon = MDFloatingActionButton(
            icon="arrow-left",
            icon_size="25sp",
            pos_hint={'x': 0, 'top': 1},
            on_release=self.go_dashboard,
            size_hint=(None, None),
            size=(dp(40), dp(40)),
        )
        main_layout.add_widget(btn_icon)


        self.camera_button = MDRaisedButton(
            text="Open Camera",
            icon="camera",
            size_hint=(1, None),
            height=dp(50),
            on_release=self.open_camera_mbnv2
        )
        upload_card.add_widget(self.camera_button)

        self.add_widget(main_layout)

    def open_file_explorer(self, instance):

        try:
            filechooser.open_file(
                on_selection=self.on_file_selected,
                filters=[
                    ("Image files", "*.jpg", "*.jpeg", "*.png", "*.bmp", "*.gif"),
                    ("All files", "*.*")
                ],
                title="Select a dog image"
            )
        except Exception as e:
            print(f"Error opening file explorer: {e}")
            self.select_button.disabled = False
        
    def _center_crop_image(self, image_path):
        """Crop the image to a 1:1 aspect ratio centered, resize to 224x224, and save to a temp file."""
        img = PILImage.open(image_path).convert("RGB")
        width, height = img.size
        min_dim = min(width, height)
        left = (width - min_dim) // 2
        top = (height - min_dim) // 2
        right = left + min_dim
        bottom = top + min_dim
        img_cropped = img.crop((left, top, right, bottom)).resize((224, 224), PILImage.LANCZOS)
        temp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        img_cropped.save(temp.name)
        temp.close()
        return temp.name

    def _set_image_preview(self, image_path):
        # Remove previous temp file if exists
        if self._cropped_tempfile:
            try:
                os.remove(self._cropped_tempfile)
            except Exception:
                pass
            self._cropped_tempfile = None
        if image_path:
            cropped_path = self._center_crop_image(image_path)
            self._cropped_tempfile = cropped_path
            self.image_preview.source = cropped_path
            self.image_preview.reload()
        else:
            self.image_preview.source = ''
            self.image_preview.reload()

    def on_file_selected(self, selection):
        """Handle file selection"""
        if selection:
            self.selected_file_path = selection[0]
            filename = os.path.basename(self.selected_file_path)
            # Update UI
            self.file_label.text = f"Selected: {filename}"
            self._set_image_preview(self.selected_file_path)
            self.analyze_button.disabled = False
            self.breed_label.text = "Breed: Undetermined"
            print(f"File selected: {self.selected_file_path}")
        else:
            print("No file selected.")

    def on_pre_enter(self, *args):
        """Update UI with the selected file path when entering the screen."""
        if self.selected_file_path:
            filename = os.path.basename(self.selected_file_path)
            self.file_label.text = f"Selected: {filename}"
            self._set_image_preview(self.selected_file_path)
            self.analyze_button.disabled = False
            self.breed_label.text = "Breed: Undetermined"
        else:
            self.file_label.text = "No file selected"
            self._set_image_preview(None)
            self.analyze_button.disabled = True
            self.breed_label.text = "Breed: Undetermined"

    def analyze_image(self, instance):
        """Analyze the selected image for dog breed recognition"""
        if self.selected_file_path:
            print(f"Analysing image: {self.selected_file_path}")

        filename = os.path.basename(self.selected_file_path)
        filename_without_ext = os.path.splitext(filename)[0]
        self.file_label.text = f"Now analysing: {filename}"

        from .artificial_intelligence import predict_top_breeds
        top_5_predictions = predict_top_breeds(self.selected_file_path, k=5)

        if top_5_predictions:
            main_breed, main_confidence = top_5_predictions[0]
            main_breed_formatted = main_breed.replace('_', ' ').title()
            main_confidence_str = f"{main_confidence:.1f}"

            if main_breed.lower() == "undetermined":
                self.breed_label.text = "Breed: Undetermined"
            else:
                self.breed_label.text = f"Breed: {main_breed_formatted} ({main_confidence_str}%)"

        if top_5_predictions:
            labels = []
            sizes = []
            for breed, confidence in top_5_predictions:
                labels.append(breed.replace('_', ' ').title())
                sizes.append(confidence)
            sum_top5 = sum(sizes)
            if sum_top5 < 100:
                labels.append("Others")
                sizes.append(100 - sum_top5)
            else:
                sizes[-1] = 100 - sum(sizes[:-1])

            legend_labels = [f"{label}: {size:.1f}%" for label, size in zip(labels, sizes)]

            import matplotlib.gridspec as gridspec
            fig = plt.figure(figsize=(5.5, 6), dpi=120)
            gs = gridspec.GridSpec(2, 1, height_ratios=[4, 1.2])
     
            ax_pie = fig.add_subplot(gs[0])
            colors = plt.cm.Paired.colors
            wedges, _ = ax_pie.pie(
                sizes,
                labels=None,
                startangle=140,
                colors=colors
            )
            ax_pie.axis('equal')

            ax_legend = fig.add_subplot(gs[1])
            ax_legend.axis('off')
            legend_y_start = 1
            legend_y_step = 0.23 
            rect_height = 0.16
            for i, (legend_label, wedge) in enumerate(zip(legend_labels, wedges)):
                color = wedge.get_facecolor()
                y = legend_y_start - i * legend_y_step
                ax_legend.add_patch(
                    plt.Rectangle((0.18, y - rect_height), 0.07, rect_height, color=color, transform=ax_legend.transAxes, clip_on=False)
                )
                ax_legend.text(
                    0.28, y,
                    legend_label,
                    ha='left', va='top',
                    fontsize=14, color='white', fontweight='bold',
                    transform=ax_legend.transAxes
                )
            fig.patch.set_facecolor('black')
            ax_pie.set_facecolor('black')
            ax_legend.set_facecolor('black')

            pie_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            plt.savefig(pie_temp.name, bbox_inches='tight', transparent=True)
            plt.close(fig)
            pie_temp.close()

            chart_image = KivyImage(source=pie_temp.name, size_hint_y=None, height=dp(340))  # Increased chart height
            pie_layout = MDBoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10), size_hint_y=None)
            pie_layout.add_widget(chart_image)
            pie_layout.height = chart_image.height + dp(20)

            scroll = ScrollView(size_hint=(1, None), size=(dp(320), min(pie_layout.height + dp(20), dp(400))))
            scroll.add_widget(pie_layout)

            self.dialog = MDDialog(
                title="Prediction Result",
                type="custom",
                content_cls=scroll,
                buttons=[
                    MDRaisedButton(
                        text="Nice!",
                        on_release=lambda x: self.dialog.dismiss(),
                    )
                ],
            )

            self.dialog.open()

    def open_camera_yolo(self, instance):
        """Launch YOLOtest.py as a subprocess to open the camera."""
        yolo_script = os.path.join(os.path.dirname(__file__), "..", "dog_identification", "YOLOtest.py")
        yolo_script = os.path.abspath(yolo_script)
        try:
            subprocess.Popen([sys.executable, yolo_script])
        except Exception as e:
            print(f"Failed to launch YOLO camera: {e}")

    def open_camera_mbnv2(self, instance):
        """Launch MBNv2test.py as a subprocess to open the camera."""
        mbnv2_script = os.path.join(os.path.dirname(__file__), "..", "dog_identification", "MBNv2test.py")
        mbnv2_script = os.path.abspath(mbnv2_script)
        try:
            subprocess.Popen([sys.executable, mbnv2_script])
        except Exception as e:
            print(f"Failed to launch MBNv2 camera: {e}")

    def go_dashboard(self, instance):
        # Switch to dashboard screen
        app = MDApp.get_running_app()
        app.root.current = 'dashboard'
