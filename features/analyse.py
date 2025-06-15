import os
import json
from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.dialog import MDDialog
from kivy.uix.floatlayout import FloatLayout
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
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
from kivy.clock import Clock
import subprocess
import sys
import threading # Added
from kivy.clock import Clock # Added
from .artificial_intelligence import predict_top_breeds, analyze_video_for_breeds
import cv2 # Added for video frame extraction
import firebase_admin
from firebase_admin import db


class AnalyseFeature(Screen):
    dialog = None,
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_file_path = None
        self._cropped_tempfile = None # For image center cropping
        self._video_representative_frame_tempfile = None # For video representative frame
        self._video_preview_frame_tempfile = None # For video first frame preview
        self.is_video_file = False # Flag to indicate if the selected file is a video
        self.analysis_in_progress = False # Flag to prevent concurrent analyses
        # It's better to initialize UI elements that are directly part of the class structure here
        # or ensure they are created before on_enter might try to access them if not built by kv.
        # For now, setup_ui() is called in __init__, which is fine.
        self.setup_ui()

    def on_enter(self, *args):
        """Called when the screen is entered."""
        print("AnalyseFeature: on_enter called")
        app = MDApp.get_running_app()
        file_path = getattr(app, 'current_analysis_file_path', None)
        is_video = getattr(app, 'current_analysis_is_video', False)

        if file_path:
            print(f"AnalyseFeature: File path from app: {file_path}, is_video: {is_video}")
            # Call prepare_for_analysis which should handle UI updates
            self.prepare_for_analysis(file_path, is_video)
            # Clear the attributes on the app instance after use to prevent reuse on accidental re-entry
            # without going through the upload flow again.
            delattr(app, 'current_analysis_file_path')
            delattr(app, 'current_analysis_is_video')
        else:
            print("AnalyseFeature: No file path found in app instance on_enter. UI might not update with new file.")
            # If there's no new file, we might want to ensure the UI reflects the current state
            # (e.g., if a file was already loaded from a previous session on this screen).
            # For now, prepare_for_analysis(None, False) or similar could be called if we want to clear.
            # However, if self.selected_file_path is already set, update_ui_for_file_type might be enough.
            if not self.selected_file_path: # If no file is selected at all
                 self.update_ui_for_file_type() # Ensure UI is in a default state

    def prepare_for_analysis(self, file_path, is_video):
        """Called by UploadFeature to set the file and prepare the UI before switching to this screen."""
        print(f"AnalyseFeature: Preparing for analysis of {file_path}, is_video: {is_video}")
        self.selected_file_path = file_path
        self.is_video_file = is_video
        self._cleanup_temp_files() # Clean up any previous temp files
        self.update_ui_for_file_type()
        # Reset analysis state
        self.analysis_in_progress = False
        self.breed_label.text = "Breed: Undetermined"
        # Ensure the analyze button is enabled if a file is selected
        self.analyze_button.disabled = not bool(self.selected_file_path)

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

        # Analyze button - text will be updated based on file type
        self.analyze_button = MDRaisedButton(
            text="Analyse Breed",
            icon="magnify",
            size_hint=(1, None),
            height=dp(50),
            disabled=True,
            on_release=self.start_analysis # Changed from self.analyze_image
        )
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

        label_y = (170 - 65) / 780  # normalized y for pos_hint
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
        # When "Change Image/Video" is clicked on this screen directly
        # Disable button to prevent multiple clicks
        instance.disabled = True # Disable the button that was clicked
        try:
            filechooser.open_file(
                on_selection=lambda sel: self._handle_direct_file_selection(sel, instance),
                filters=[
                    ("Supported Media Files", "*.jpg;*.jpeg;*.png;*.bmp;*.gif;*.mp4;*.avi;*.mov;*.mkv"),
                    ("All files", "*.*")
                ],
                title="Select a dog image or video"
            )
        except Exception as e:
            print(f"Error opening file explorer: {e}")
            instance.disabled = False # Re-enable on error
        
    def _handle_direct_file_selection(self, selection, button_instance):
        """Callback for filechooser when initiated from AnalyseFeature itself."""
        if self.analysis_in_progress:
            print("Analysis already in progress, ignoring new file selection for now.")
            button_instance.disabled = False # Re-enable button
            return

        self._cleanup_temp_files() # Clean up previous temp files

        if selection:
            new_file_path = selection[0]
            file_extension = os.path.splitext(new_file_path)[1].lower()
            is_video = file_extension in [".mp4", ".avi", ".mov", ".mkv"]
            
            # Call prepare_for_analysis to update UI and state correctly
            self.prepare_for_analysis(new_file_path, is_video)
            print(f"File changed directly in AnalyseFeature: {self.selected_file_path}, is_video: {self.is_video_file}")
        else:
            print("No file selected in AnalyseFeature after 'Change' button.")
            # Optionally, clear the selection or revert to a default state
            # self.prepare_for_analysis(None, False) # This would clear the UI
        button_instance.disabled = False # Re-enable button after selection (or no selection)

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

    def _cleanup_temp_files(self):
        # This is called at the beginning of a new file analysis or when the screen is left.
        # It should clean up all potentially lingering temp files from a *previous* operation.
        print("AnalyseFeature: Running _cleanup_temp_files")
        files_to_clean_attrs = [
            "_cropped_tempfile",
            "_video_representative_frame_tempfile",
            "_video_preview_frame_tempfile"
        ]
        for attr_name in files_to_clean_attrs:
            file_path = getattr(self, attr_name, None)
            if file_path:
                try:
                    if os.path.exists(file_path): # Check if file exists before trying to remove
                        os.remove(file_path)
                        print(f"Cleaned up temp file ({attr_name}): {file_path}")
                    else:
                        print(f"Temp file ({attr_name}) not found for cleanup (already removed or never created): {file_path}")
                except Exception as e:
                    print(f"Error removing temp file ({attr_name}) {file_path}: {e}")
                setattr(self, attr_name, None) # Set to None even if removal failed or file not found

    def _set_image_preview(self, image_path_to_preview):
        print(f"AnalyseFeature: _set_image_preview called with: {image_path_to_preview}")
        # 1. Clean up the *previous* self._cropped_tempfile, as we are about to create a new one.
        if self._cropped_tempfile:
            try:
                if os.path.exists(self._cropped_tempfile):
                    os.remove(self._cropped_tempfile)
                    print(f"Cleaned up old _cropped_tempfile: {self._cropped_tempfile}")
                self._cropped_tempfile = None
            except Exception as e:
                print(f"Error removing old _cropped_tempfile: {e}")
                self._cropped_tempfile = None # Ensure it's None

        # 2. If a new image path is provided, process it.
        if image_path_to_preview:
            if not os.path.exists(image_path_to_preview):
                print(f"Error: Input for _center_crop_image does not exist: {image_path_to_preview}")
                self.image_preview.source = 'assets/video_placeholder.png' # More generic placeholder
                self.image_preview.reload()
                # If the problematic path was _video_preview_frame_tempfile, nullify it
                if hasattr(self, '_video_preview_frame_tempfile') and self._video_preview_frame_tempfile == image_path_to_preview:
                    self._video_preview_frame_tempfile = None
                return

            new_cropped_path = self._center_crop_image(image_path_to_preview)
            if new_cropped_path:
                self._cropped_tempfile = new_cropped_path # Store the path of the NEWLY cropped image
                self.image_preview.source = new_cropped_path
                print(f"Set image_preview.source to new _cropped_tempfile: {new_cropped_path}")
                self.image_preview.reload()

                # 3. If the image_path_to_preview was the raw video frame (self._video_preview_frame_tempfile),
                #    it has now been processed into self._cropped_tempfile, so the raw frame can be deleted.
                if hasattr(self, '_video_preview_frame_tempfile') and \
                   self._video_preview_frame_tempfile and \
                   image_path_to_preview == self._video_preview_frame_tempfile:
                    try:
                        if os.path.exists(self._video_preview_frame_tempfile):
                            os.remove(self._video_preview_frame_tempfile)
                            print(f"Cleaned up raw video preview frame: {self._video_preview_frame_tempfile}")
                        self._video_preview_frame_tempfile = None
                    except Exception as e:
                        print(f"Error removing video preview temp file after cropping: {e}")
                        self._video_preview_frame_tempfile = None # Ensure it's None
            else:
                print(f"Error: _center_crop_image returned None for {image_path_to_preview}")
                self.image_preview.source = 'assets/video_placeholder.png' # More generic placeholder
                self.image_preview.reload()
        else:
            print("AnalyseFeature: _set_image_preview called with None/empty path. Clearing preview.")
            self.image_preview.source = 'assets/video_placeholder.png' # Default placeholder or empty
            self.image_preview.reload()
            # If image_path_to_preview is None, ensure any lingering _video_preview_frame_tempfile is also cleared
            if hasattr(self, '_video_preview_frame_tempfile') and self._video_preview_frame_tempfile:
                 try:
                     if os.path.exists(self._video_preview_frame_tempfile):
                         os.remove(self._video_preview_frame_tempfile)
                         print(f"Cleaned up lingering _video_preview_frame_tempfile in _set_image_preview (else branch): {self._video_preview_frame_tempfile}")
                     self._video_preview_frame_tempfile = None
                 except Exception as e:
                     print(f"Error cleaning lingering _video_preview_frame_tempfile (else branch): {e}")
                     self._video_preview_frame_tempfile = None

    def on_file_selected(self, selection): # This method is now effectively replaced by _handle_direct_file_selection for UI initiated selections
        """Handle file selection when \'Change Image/Video\' is clicked on this screen."""
        # This method might still be useful if called programmatically, but for UI, _handle_direct_file_selection is used.
        # For clarity, we can consolidate or ensure this isn't accidentally used by UI.
        # For now, let's assume it's not directly tied to the "Change Image" button's on_release anymore.
        if self.analysis_in_progress:
            print("Analysis already in progress, ignoring new file selection for now.")
            return

        self._cleanup_temp_files() # Clean up previous temp files

        if selection:
            new_file_path = selection[0]
            file_extension = os.path.splitext(new_file_path)[1].lower()
            is_video = file_extension in [".mp4", ".avi", ".mov", ".mkv"]
            
            self.prepare_for_analysis(new_file_path, is_video)
            print(f"File changed (on_file_selected): {self.selected_file_path}, is_video: {self.is_video_file}")
        else:
            print("No file selected (on_file_selected).")

    def update_ui_for_file_type(self):
        """Update UI elements based on whether an image or video is selected."""
        if not self.selected_file_path:
            self.file_label.text = "No file selected"
            self.image_preview.source = '' # Placeholder or empty
            self.image_preview.reload()
            self.analyze_button.text = "Analyse Breed"
            self.analyze_button.disabled = True
            self.select_button.text = "Select File"
            self.breed_label.text = "Breed: Undetermined"
            return

        filename = os.path.basename(self.selected_file_path)
        self.file_label.text = f"Selected: {filename}"
        self.analyze_button.disabled = False

        if self.is_video_file:
            self.analyze_button.text = "Analyse Video"
            self.select_button.text = "Change Video"
            # Extract first frame for preview
            preview_frame_path = self._extract_first_frame_for_preview(self.selected_file_path)
            if preview_frame_path:
                self._set_image_preview(preview_frame_path) # This will also handle cropping
                # No need to store preview_frame_path in self._video_preview_frame_tempfile if _set_image_preview uses _cropped_tempfile
            else:
                self.image_preview.source = 'assets/video_placeholder.png' # Fallback placeholder
                self.image_preview.reload()
        else:
            self.analyze_button.text = "Analyse Image"
            self.select_button.text = "Change Image"
            self._set_image_preview(self.selected_file_path)
        
        self.breed_label.text = "Breed: Undetermined" # Reset breed label

    def _extract_first_frame_for_preview(self, video_path):
        """Extracts the first frame of a video and saves it as a temporary image file."""
        try:
            # Clean up old preview frame if it exists
            if self._video_preview_frame_tempfile and os.path.exists(self._video_preview_frame_tempfile): # Added exists check
                try:
                    os.remove(self._video_preview_frame_tempfile)
                    print(f"Cleaned up old _video_preview_frame_tempfile: {self._video_preview_frame_tempfile}")
                except Exception as e:
                    print(f"Error removing old video preview temp file: {e}")
                self._video_preview_frame_tempfile = None # Set to None regardless

            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                print(f"Error: Could not open video file for preview: {video_path}")
                return None
            ret, frame = cap.read()
            cap.release()
            if ret:
                temp_preview_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                cv2.imwrite(temp_preview_file.name, frame)
                temp_preview_file.close()
                self._video_preview_frame_tempfile = temp_preview_file.name # Store for cleanup
                return temp_preview_file.name
            else:
                print(f"Error: Could not read first frame from video: {video_path}")
                return None
        except Exception as e:
            print(f"Exception extracting first frame for preview: {e}")
            return None

    def start_analysis(self, instance):
        """Starts the analysis based on whether an image or video is selected."""
        if not self.selected_file_path or self.analysis_in_progress:
            return

        self.analysis_in_progress = True
        self.analyze_button.disabled = True
        
        if self.is_video_file:
            self.breed_label.text = "Analyzing video... please wait.\nThis may take a few moments."
            self._start_video_analysis_thread()
        else:
            self.breed_label.text = "Analyzing image..."
            # Image analysis is quick, can run on main thread or be threaded similarly if it ever gets slow
            self._do_image_analysis()
            self.analysis_in_progress = False # Reset for image as it's synchronous for now
            self.analyze_button.disabled = False


    def _do_image_analysis(self):
        """Handles the logic for analyzing a static image."""
        if not self.selected_file_path:
            self.analysis_in_progress = False
            self.analyze_button.disabled = False
            return

        print(f"Analysing image: {self.selected_file_path}")
        # self._cropped_tempfile should be set by _set_image_preview or update_ui_for_file_type
        # The model expects the original uncropped path for its own preprocessing if it differs.
        # However, our current DogBreedPredictor.preprocess_image takes a path and does PIL open.
        # For consistency, we use self.selected_file_path for analysis.
        # The _cropped_tempfile is purely for the square preview.

        top_5_predictions = predict_top_breeds(self.selected_file_path, k=5)

        if top_5_predictions:
            main_breed, main_confidence = top_5_predictions[0]
            main_breed_formatted = main_breed.replace('_', ' ').title()
            main_confidence_str = f"{main_confidence:.1f}"
            
            if main_breed.lower() == "undetermined":
                self.breed_label.text = "Breed: Undetermined"
                self.save_analysis_history(self.selected_file_path, "Undetermined", "N/A", is_video=False)
            else:
                self.breed_label.text = f"Breed: {main_breed_formatted} ({main_confidence_str}%)"
                self.save_analysis_history(self.selected_file_path, main_breed_formatted, main_confidence_str, is_video=False)
            
            self._display_results_dialog(top_5_predictions, title_prefix="Image Prediction")
        else:
            self.breed_label.text = "Analysis failed or no breeds found."
        
        # Reset flags as image analysis is currently synchronous
        self.analysis_in_progress = False
        self.analyze_button.disabled = False


    def _start_video_analysis_thread(self):
        """Initiates video analysis in a separate thread."""
        if not self.selected_file_path:
            self.analysis_in_progress = False
            self.analyze_button.disabled = False
            return
        
        # Clear previous video representative frame if any
        if self._video_representative_frame_tempfile:
            try:
                os.remove(self._video_representative_frame_tempfile)
                self._video_representative_frame_tempfile = None
            except Exception as e:
                print(f"Error removing old video temp file: {e}")

        print(f"Starting video analysis thread for: {self.selected_file_path}")
        self.analyze_button.disabled = True # Ensure it's disabled
        self.breed_label.text = "Video analysis in progress..."
        
        thread = threading.Thread(target=self._video_analysis_worker, args=(self.selected_file_path,), daemon=True)
        thread.start()

    def _video_analysis_worker(self, video_path):
        """Worker function that runs in a separate thread for video analysis."""
        try:
            # analyze_video_for_breeds returns: representative_frame_path, best_frame_predictions, error_message_from_ai
            print(f"AnalyseFeature: Calling analyze_video_for_breeds with video_path: {video_path}")
            representative_frame_path, best_frame_predictions, error_message_from_ai = analyze_video_for_breeds(video_path)
            
            print(f"AnalyseFeature: analyze_video_for_breeds returned: path='{representative_frame_path}', preds='{best_frame_predictions}', ai_error='{error_message_from_ai}'")
            
            # Pass to completion handler in the correct order: best_frame_predictions, representative_frame_path, error
            Clock.schedule_once(lambda dt: self._on_video_analysis_complete(best_frame_predictions, representative_frame_path, error=error_message_from_ai))
        except Exception as e:
            # This catches errors from calling analyze_video_for_breeds if its signature is wrong,
            # or other unexpected errors within this worker function itself.
            print(f"CRITICAL Error during _video_analysis_worker (e.g., calling AI function or other setup): {e}")
            import traceback
            traceback.print_exc() # Print full traceback for debugging
            # Pass a generic error to the completion handler
            Clock.schedule_once(lambda dt, error_val=str(e): self._on_video_analysis_complete(None, None, error=f"Worker exception: {error_val}"))

    def _on_video_analysis_complete(self, best_frame_predictions, representative_frame_path, error=None):
        """Callback executed on the main Kivy thread after video analysis is done."""
        print(f"AnalyseFeature: _on_video_analysis_complete received: representative_frame_path='{representative_frame_path}', error='{error}'")
        print(f"AnalyseFeature: best_frame_predictions: {best_frame_predictions}")

        self.analysis_in_progress = False
        self.analyze_button.disabled = False

        if error:
            self.breed_label.text = f"Video analysis error: {error}"
            # Reset preview to the first frame (or placeholder if that failed)
            if self._video_preview_frame_tempfile and os.path.exists(self._video_preview_frame_tempfile):
                self._set_image_preview(self._video_preview_frame_tempfile)
            else:
                self.image_preview.source = "assets/video_placeholder.png"
                self.image_preview.reload()
            self._show_error_dialog(f"Video Analysis Error: {error}")
            return

        # Cleanup old _video_representative_frame_tempfile if it exists and is different from the new one
        if self._video_representative_frame_tempfile and self._video_representative_frame_tempfile != representative_frame_path:
            try: 
                os.remove(self._video_representative_frame_tempfile)
                print(f"Cleaned up old representative frame: {self._video_representative_frame_tempfile}")
            except Exception as e:
                print(f"Error cleaning old rep frame: {e}")
        self._video_representative_frame_tempfile = representative_frame_path # Store new one (can be None)

        if representative_frame_path and best_frame_predictions:
            print(f"AnalyseFeature: Valid result. Attempting to set preview with: {representative_frame_path}")
            self._set_image_preview(representative_frame_path)
            print(f"AnalyseFeature: _set_image_preview call completed for representative frame.")
            
            # --- FIX: Use dict keys instead of tuple unpacking ---
            main_breed = best_frame_predictions[0]["breed"]
            main_confidence = best_frame_predictions[0]["confidence"]
            main_breed_formatted = main_breed.replace('_', ' ').title()
            main_confidence_str = f"{float(main_confidence):.1f}"

            if main_breed.lower() == "undetermined":
                self.breed_label.text = "Video: Breed Undetermined"
                self.save_analysis_history(self.selected_file_path, "Undetermined", "N/A", is_video=True, representative_frame=representative_frame_path)
            else:
                self.breed_label.text = f"Video: {main_breed_formatted} ({main_confidence_str}%)"
                self.save_analysis_history(self.selected_file_path, main_breed_formatted, main_confidence_str, is_video=True, representative_frame=representative_frame_path)
            
            self._display_results_dialog(best_frame_predictions, title_prefix="Video Analysis Result")
        
        else: # No distinct breed found or no representative frame
            print(f"AnalyseFeature: No distinct breed/frame. Error: {error}. Rep_path: {representative_frame_path}")
            self.breed_label.text = "Video: No distinct breed found."
            # Reset preview to the first frame (or placeholder if that failed)
            print("AnalyseFeature: Reverting to initial video preview or placeholder.")
            if self._video_preview_frame_tempfile and os.path.exists(self._video_preview_frame_tempfile):
                print(f"AnalyseFeature: Reverting to _video_preview_frame_tempfile: {self._video_preview_frame_tempfile}")
                self._set_image_preview(self._video_preview_frame_tempfile)
            else:
                print("AnalyseFeature: Reverting to static video_placeholder.png using os.path.join")
                # Construct path relative to this file's directory, then up to project, then to assets
                placeholder_path = os.path.join(os.path.dirname(__file__), "..", "assets", "video_placeholder.png")
                placeholder_path = os.path.abspath(placeholder_path) # Get absolute path
                print(f"AnalyseFeature: Absolute placeholder path: {placeholder_path}")
                if os.path.exists(placeholder_path):
                    self.image_preview.source = placeholder_path
                else:
                    print(f"ERROR: Placeholder image not found at {placeholder_path}")
                    # Fallback or decide how to handle missing placeholder in history
                    self.image_preview.source = "" # Fallback to empty if still not found
                self.image_preview.reload()
            # Save a generic history entry indicating no result
            self.save_analysis_history(self.selected_file_path, "No distinct breed found", "N/A", is_video=True, representative_frame=None)
            self._show_error_dialog("Video Analysis Complete: No distinct dog breed could be identified with sufficient confidence.")


    def _display_results_dialog(self, predictions, title_prefix="Prediction Result"):
        """Displays the pie chart and breed list in a dialog."""
        # --- Robustly handle empty or N/A predictions ---
        show_undetermined = False
        # If predictions is empty or None, treat as undetermined
        if not predictions or len(predictions) == 0:
            show_undetermined = True
        else:
            # Check for N/A or all "Undetermined"
            if isinstance(predictions[0], dict):
                main_conf = predictions[0].get("confidence", None)
                main_breed = predictions[0].get("breed", "").lower()
                if (isinstance(main_conf, str) and main_conf.upper() == "N/A") or main_breed == "undetermined":
                    show_undetermined = True
            else:
                main_conf = predictions[0][1] if len(predictions[0]) > 1 else None
                main_breed = predictions[0][0].lower() if len(predictions[0]) > 0 else ""
                if (isinstance(main_conf, str) and main_conf.upper() == "N/A") or main_breed == "undetermined":
                    show_undetermined = True

        if show_undetermined:
            labels = ["Undetermined"]
            sizes = [100.0]
            pie_colors = ["#888888"]
        else:
            labels = []
            sizes = []
            if isinstance(predictions[0], dict):
                for pred in predictions:
                    # Only add if not undetermined and confidence is not N/A
                    if pred.get("breed", "").lower() != "undetermined" and not (isinstance(pred.get("confidence", None), str) and pred["confidence"].upper() == "N/A"):
                        labels.append(pred["breed"].replace('_', ' ').title())
                        sizes.append(float(pred["confidence"]))
            else:
                for breed, confidence in predictions:
                    if breed.lower() != "undetermined" and not (isinstance(confidence, str) and confidence.upper() == "N/A"):
                        labels.append(breed.replace('_', ' ').title())
                        sizes.append(confidence)
            # If after filtering, nothing remains, fallback to undetermined
            if not sizes:
                labels = ["Undetermined"]
                sizes = [100.0]
                pie_colors = ["#888888"]
            else:
                sum_top_k = sum(sizes)
                if sum_top_k < 99.9 and sum_top_k > 0:
                    others_percentage = 100.0 - sum_top_k
                    if others_percentage > 0.1:
                        labels.append("Others")
                        sizes.append(others_percentage)
                elif sum_top_k > 100.0:
                    scale_factor = 100.0 / sum_top_k
                    sizes = [s * scale_factor for s in sizes]
                all_colors = list(plt.cm.Paired.colors)
                pie_colors = all_colors[:len(sizes)] if len(sizes) <= len(all_colors) else (all_colors * ((len(sizes) // len(all_colors)) + 1))[:len(sizes)]

        legend_labels = [f"{label}: {size:.1f}%" for label, size in zip(labels, sizes)]

        import matplotlib.gridspec as gridspec
        fig = plt.figure(figsize=(5.5, 6), dpi=120)
        gs = gridspec.GridSpec(2, 1, height_ratios=[4, 1.2])
 
        ax_pie = fig.add_subplot(gs[0])
        wedges, _ = ax_pie.pie(
            sizes,
            labels=None,
            startangle=140,
            colors=pie_colors
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

        chart_image = KivyImage(source=pie_temp.name, size_hint_y=None, height=dp(340))
        pie_layout = MDBoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10), size_hint_y=None)
        pie_layout.add_widget(chart_image)
        pie_layout.height = chart_image.height + dp(20)

        scroll = ScrollView(size_hint=(1, None), size=(dp(320), min(pie_layout.height + dp(20), dp(400))))
        scroll.add_widget(pie_layout)

        self.dialog = MDDialog(
            title="Prediction Result", # Using fixed title as per provided code
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

        # Schedule cleanup of the pie chart temp file after dialog is dismissed or some time
        Clock.schedule_once(lambda dt, path=pie_temp.name: self._cleanup_single_temp_file(path), 2)


    def _cleanup_single_temp_file(self, path):
        if path and os.path.exists(path):
            try:
                os.remove(path)
                print(f"Cleaned up temp file: {path}")
            except Exception as e:
                print(f"Error cleaning up temp file {path}: {e}")


    def _show_error_dialog(self, message):
        if not hasattr(self, 'error_dialog') or not self.error_dialog:
            self.error_dialog = MDDialog(
                title="Error",
                text=message,
                buttons=[MDRaisedButton(text="OK", on_release=lambda x: self.error_dialog.dismiss())],
            )
        else:
            self.error_dialog.text = message
        self.error_dialog.open()


    def save_analysis_history(self, file_path, breed, confidence, is_video=False, representative_frame=None):
        """Save the analysis result, differentiating between image and video, and upload to Firebase."""
        from datetime import datetime
        # Correctly determine the project root to make asset paths more robust if needed
        # current_dir = os.path.dirname(__file__) # puupdex/features
        # project_root = os.path.dirname(current_dir) # puupdex
        # history_file = os.path.join(project_root, "analysis_history.json")
        # placeholder_path = os.path.join(project_root, "assets", "video_placeholder.png")
        # Using relative path for history file as before, assuming execution from project root
        history_file = os.path.join(os.path.dirname(__file__), "..", "analysis_history.json")

        history = []
        if os.path.exists(history_file):
            try:
                with open(history_file, "r") as file:
                    history = json.load(file)
                    if not isinstance(history, list): history = []
            except json.JSONDecodeError:
                history = []

        breed_info = self.generate_breed_info(breed.split('(')[0].strip()) # Get breed name before any annotation
        
        entry_type = "video" if is_video else "image"
        
        if is_video:
            if representative_frame and os.path.exists(representative_frame): # Ensure rep frame exists
                display_image_path = representative_frame
            else:
                # Use a relative path to the placeholder, assuming Kivy can resolve it from app root
                # display_image_path = "assets/video_placeholder.png" 
                # Construct path relative to this file's directory, then up to project, then to assets
                placeholder_path = os.path.join(os.path.dirname(__file__), "..", "assets", "video_placeholder.png")
                display_image_path = os.path.abspath(placeholder_path)
                if not os.path.exists(display_image_path):
                    print(f"ERROR in save_analysis_history: Placeholder image not found at {display_image_path}")
                    # Fallback or decide how to handle missing placeholder in history
                    display_image_path = "path/to/default/missing_image.png" # A generic placeholder if assets/video_placeholder.png is missing
        else: # It's an image
            display_image_path = file_path

        new_entry = {
            "original_file": file_path, 
            "display_image": display_image_path, 
            "breed": breed,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat(),
            "breed_info": breed_info,
            "type": entry_type
        }

        entry_updated = False
        # For videos, we might always append, or update based on original_file if re-analyzed.
        # For images, current logic updates if 'image' (now 'display_image') matches.
        # Let's update if 'original_file' matches to handle re-analysis of same file.
        for i, entry in enumerate(history):
            if entry.get("original_file") == file_path:
                history[i] = new_entry
                entry_updated = True
                break
        
        if not entry_updated:
            history.append(new_entry)
        
        history.sort(key=lambda x: x.get("timestamp", ""), reverse=True) # Show newest first

        with open(history_file, "w") as file:
            json.dump(history, file, indent=4)
        
        # --- Firebase upload ---
        try:
            # Assumes firebase_admin is already initialized elsewhere in your app
            ref = db.reference("history")
            # Use timestamp as key for uniqueness
            ref.child(new_entry["timestamp"]).set(new_entry)
            print("Uploaded history entry to Firebase.")
        except Exception as e:
            print(f"Error uploading history entry to Firebase: {e}")

        app = MDApp.get_running_app()
        if app:
            if not hasattr(app, 'on_new_analysis'):
                app.register_event_type('on_new_analysis')
            app.dispatch('on_new_analysis')
            print("Dispatched on_new_analysis event from save_analysis_history")

    def generate_breed_info(self, breed):
        """Generate some basic information about the dog breed."""
        # This is a simple mapping of some common breeds to their characteristics
        breed_lower = breed.lower()
        
        breed_info_map = {
            "undetermined": "It's difficult to determine the breed of this dog. It may be a mixed breed, an uncommon one or not a dog.",
            "golden retriever": "Friendly, intelligent and devoted. Excellent family dogs with a gentle temperament.",
            "labrador": "Outgoing, even-tempered, and gentle. Popular family pets and service dogs.",
            "german shepherd": "Confident, courageous and smart. Often used as working dogs in police and military.",
            "bulldog": "Docile, willful, and friendly. Known for their loose-jointed, shuffling gait and massive head.",
            "beagle": "Merry, friendly and curious. Excellent scent hounds originally bred for hunting.",
            "poodle": "Active, intelligent and elegant. One of the most intelligent dog breeds.",
            "rottweiler": "Loyal, loving and confident guardian. Good-natured with a calm, confident demeanor.",
            "yorkshire terrier": "Affectionate, sprightly and tomboyish. Small but feisty and loving.",
            "boxer": "Fun-loving, bright and active. Known for being playful and good with children.",
            "dachshund": "Clever, courageous and lively. Bred to hunt badgers, their name means 'badger dog'.",
            "shiba": "Alert, active and attentive. An ancient Japanese breed known for its spirited personality.",
            "husky": "Outgoing, gentle and friendly. Built for endurance and able to carry light loads over long distances.",
            "corgi": "Affectionate, smart and alert. Originally bred to herd cattle, sheep, and horses.",
            "chihuahua": "Graceful, charming and sassy. The smallest breed of dog, named for the Mexican state.",
            "pug": "Charming, mischievous and loving. Known for their wrinkled face and curled tail."
        }
        
        # Check if we have specific info for this breed
        for key, info in breed_info_map.items():
            if key in breed_lower:
                return info
                
        # Generic info if breed is not in our map
        return "A wonderful dog breed with unique characteristics. Each dog has its own personality and traits."


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
        # self.manager.current = "dashboard" # Old way
        MDApp.get_running_app().switch_to_screen("dashboard")

    def on_leave(self, *args):
        """Called when the screen is left."""
        print("AnalyseFeature: on_leave called. Cleaning up temp files.")
        self._cleanup_temp_files()
        # Reset analysis state if needed, or clear sensitive data
        # self.selected_file_path = None # Optional: clear selected file when leaving
        # self.is_video_file = False
        # self.update_ui_for_file_type() # Reset UI to default
        # self.analysis_in_progress = False
        # self.analyze_button.disabled = True
        # self.breed_label.text = "Breed: Undetermined"
