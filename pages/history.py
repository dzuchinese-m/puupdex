import os
import json
from datetime import datetime
from functools import partial # Added import
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.metrics import dp
from kivymd.uix.button import MDIconButton, MDRaisedButton, MDFlatButton # Ensure MDRaisedButton and MDFlatButton are imported
from kivymd.uix.dialog import MDDialog # Ensure MDDialog is imported
from kivy.core.window import Window # Import Window
from kivymd.app import MDApp
from kivy.event import EventDispatcher
import firebase_admin
from firebase_admin import db

# Load the KV file explicitly
Builder.load_file(os.path.join(os.path.dirname(__file__), 'history.kv'))

class HistoryPage(Screen, EventDispatcher): # Inherit from EventDispatcher
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_event_type('on_app_event_new_analysis') # Register custom event for clarity if needed, though direct binding to app event is fine
        Clock.schedule_once(self.load_history)
        Window.bind(on_resize=self.adjust_grid_cols)
        Clock.schedule_once(self.adjust_grid_cols, 0)
        
        # Bind to the app's global event
        app = MDApp.get_running_app()
        if app:
            app.bind(on_new_analysis=self.handle_new_analysis)

    def handle_new_analysis(self, *args):
        print("HistoryPage: Detected on_new_analysis event, reloading history.")
        self.load_history()

    def on_app_event_new_analysis(self, *args): # If using self.dispatch('on_app_event_new_analysis')
        pass # Placeholder for the registered event

    # It's good practice to unbind, though for a persistent screen it's less critical
    def on_leave(self, *args): # Or on_stop if it's when the app closes
        app = MDApp.get_running_app()
        if app:
            try:
                app.unbind(on_new_analysis=self.handle_new_analysis)
            except Exception as e:
                print(f"HistoryPage: Error unbinding on_new_analysis: {e}")
        super().on_leave(*args) # Call super if overriding a Kivy method

    def adjust_grid_cols(self, *args):
        history_container = self.ids.get('history_container')
        if history_container:
            width_dp = Window.width / dp(1) # Get window width in dp units
            if width_dp < 600:
                history_container.cols = 1
            elif width_dp < 1000: # Base
                history_container.cols = 2
            elif width_dp < 1400:
                history_container.cols = 3
            else:
                history_container.cols = 4
            
            if hasattr(history_container, 'do_layout'):
                history_container.do_layout() # Ensure layout updates

    def format_confidence(self, confidence):
        """Format confidence level for display with appropriate color."""
        try:
            conf_float = float(confidence)
            if conf_float > 90:
                return f"[color=00FF00]{conf_float:.1f}%[/color]"  # Green for high confidence
            elif conf_float > 70:
                return f"[color=FFFF00]{conf_float:.1f}%[/color]"  # Yellow for medium confidence
            else:
                return f"[color=FF0000]{conf_float:.1f}%[/color]"  # Red for low confidence
        except (ValueError, TypeError):
            return f"{confidence}%"
    
    def get_timestamp(self, entry):
        """Get formatted timestamp from entry or return current time if not available."""
        timestamp = entry.get('timestamp', None)
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp)
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                pass
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
    def load_history(self, *args):
        history_file = os.path.join(os.path.dirname(__file__), "..", "analysis_history.json")
        history_container = self.ids.get('history_container') # Directly access the container using its id

        if not history_container:
            print("Error: history_container not found in HistoryPage ids. Check history.kv.")
            # Optionally, create a fallback label to show the error in the UI
            error_label = MDLabel(
                text="Critical Error: UI element 'history_container' is missing.",
                halign="center",
                theme_text_color="Error"
            )
            self.add_widget(error_label) # Add to the screen itself if container is missing
            return

        history_container.clear_widgets()
        
        if os.path.exists(history_file):
            try:
                with open(history_file, "r") as file:
                    history = json.load(file)

                if not history:
                    no_history_label = MDLabel(
                        text="No analysis history available yet.",
                        halign="center",
                        theme_text_color="Secondary", # Use theme color
                        font_style="Subtitle1", # Make it a bit more prominent
                        size_hint_y=None,
                        height=dp(100)
                    )
                    history_container.add_widget(no_history_label)
                else:
                    # Sort history by timestamp if available, newest first
                    try:
                        history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
                    except:
                        pass  # If sorting fails, use the original order
                    
                    for entry in history:
                        # Create a card for each history entry
                        card = MDCard(
                            orientation="vertical",
                            size_hint_y=None,
                            height=dp(300), # Increased height for more content space
                            padding=dp(10), # Standardized padding
                            spacing=dp(10), # Standardized spacing
                            ripple_behavior=True,
                            elevation=2, # Slightly reduced elevation for a flatter design
                            radius=[12, 12, 12, 12], # Softer corners
                        )
                        card.md_bg_color = MDApp.get_running_app().theme_cls.bg_light

                        # Top row: Breed Name (larger) and Delete Button
                        header_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(48)) # Increased height
                        breed_label = MDLabel(
                            text=f"[b]{entry.get('breed', 'Unknown Breed')}[/b]",
                            markup=True,
                            font_style="H6", # Consistent font style
                            size_hint_x=0.85, # Adjusted size hint
                            halign='left',
                            valign='center', # Center vertically
                            shorten=True,
                            shorten_from='right',
                        )
                        # Bind text_size to label's width for wrapping, ensure width is not zero
                        breed_label.bind(width=lambda instance, width: setattr(instance, 'text_size', (width if width > 0 else dp(100), None)))


                        header_box.add_widget(breed_label)

                        delete_button = MDIconButton(
                            icon="delete-outline",
                            theme_text_color="Error",
                            icon_size="24sp", # Standard icon size
                            pos_hint={"center_y": 0.5}, # Center button vertically
                            # Pass the button instance explicitly if needed, or adjust confirm_delete_entry
                            on_release=partial(self.confirm_delete_entry, entry.get('timestamp'))
                        )
                        header_box.add_widget(delete_button)
                        card.add_widget(header_box)
                        
                        # Image widget
                        image_box = BoxLayout(size_hint_y=None, height=dp(130), padding=(0, dp(5))) # Adjusted height
                        # Corrected image source logic
                        image_path = entry.get("display_image", entry.get("image", "assets/placeholder.png"))
                        img = Image(
                            source=image_path,
                            allow_stretch=True,
                            keep_ratio=True,
                            size_hint=(1,1)
                        )
                        image_box.add_widget(img)
                        card.add_widget(image_box)
                        
                        # Info Box: Timestamp, Confidence, Breed Info
                        info_scroll = ScrollView(size_hint_y=None, height=dp(70), do_scroll_x=False, bar_width=dp(2)) # Slimmer scrollbar
                        info_box_content = BoxLayout(orientation="vertical", spacing=dp(8), size_hint_y=None, padding=(dp(5),0)) # Increased spacing, Added padding
                        info_box_content.bind(minimum_height=info_box_content.setter('height'))

                        timestamp_label = MDLabel(
                            text=f"Date: {self.get_timestamp(entry)}",
                            font_style="Caption",
                            theme_text_color="Secondary",
                            adaptive_height=True # Restored adaptive_height
                        )
                        timestamp_label.bind(width=lambda instance, width: setattr(instance, 'text_size', (width if width > 0 else dp(80), None))) # Re-enabled width binding for text_size
                        # timestamp_label.bind(texture_size=lambda instance, size: setattr(instance, 'height', size[1]))
                        info_box_content.add_widget(timestamp_label)
                        
                        confidence_label = MDLabel(
                            text=f"Confidence: {self.format_confidence(entry.get('confidence', 'N/A'))}",
                            markup=True,
                            font_style="Caption",
                            theme_text_color="Secondary", # Keep consistent
                            adaptive_height=True # Restored adaptive_height
                        )
                        confidence_label.bind(width=lambda instance, width: setattr(instance, 'text_size', (width if width > 0 else dp(80), None))) # Re-enabled width binding for text_size
                        # confidence_label.bind(texture_size=lambda instance, size: setattr(instance, 'height', size[1]))
                        info_box_content.add_widget(confidence_label)
                        
                        breed_info_text = entry.get('breed_info', 'No additional information.')
                        info_label = MDLabel(
                            text=breed_info_text,
                            font_style="Caption", # Consistent font style
                            theme_text_color="Secondary",
                            halign='left',
                            adaptive_height=True  # Added adaptive_height
                        )
                        # Bind text_size to label's width for wrapping
                        info_label.bind(width=lambda instance, width: setattr(instance, 'text_size', (width if width > 0 else dp(100), None)))
                        # Removed: info_label.bind(texture_size=lambda instance, size: setattr(instance, 'height', size[1]))


                        info_box_content.add_widget(info_label)
                        info_scroll.add_widget(info_box_content)
                        card.add_widget(info_scroll)
                        
                        history_container.add_widget(card)
                    history_container.do_layout() # Force layout update
            except Exception as e:
                print(f"Error loading history: {e}")
                no_history_label = MDLabel(text=f"Error loading history: {e}", halign="center")
                history_container.add_widget(no_history_label)
        else:
            no_history_label = MDLabel(
                text="No history file found.\nAnalyze some dog breeds to build history!",
                halign="center",
                size_hint_y=None,
                height=dp(100)
            )
            history_container.add_widget(no_history_label)

        # --- Firebase fetch and merge ---
        try:
            ref = db.reference("history")
            firebase_history = ref.get()
            if firebase_history:
                # Convert dict of dicts to list of dicts
                firebase_history_list = list(firebase_history.values())
                # Optionally, merge with local history or replace it
                history = firebase_history_list
        except Exception as e:
            print(f"Error loading history from Firebase: {e}")

    def confirm_delete_entry(self, entry_id, instance): # Corrected parameter order
        if not entry_id:
            print("Error: Cannot delete entry without a valid ID (timestamp).")
            return

        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton, MDRaisedButton

        self.dialog = MDDialog(
            title="Delete Entry?",
            text=f"Are you sure you want to delete this history entry?",
            buttons=[
                MDFlatButton(
                    text="CANCEL", 
                    on_release=lambda x: self.dialog.dismiss()
                ),
                MDRaisedButton(
                    text="DELETE",
                    # md_bg_color=MDApp.get_running_app().theme_cls.error_color,
                    on_release=lambda x, e_id=entry_id: self.do_delete_entry(e_id)
                ),
            ],
        )
        # Set button color after creation
        self.dialog.buttons[1].md_bg_color = MDApp.get_running_app().theme_cls.error_color
        self.dialog.open()

    def do_delete_entry(self, entry_id):
        if self.dialog:
            self.dialog.dismiss()
            self.dialog = None

        history_file = os.path.join(os.path.dirname(__file__), "..", "analysis_history.json")
        updated_history = []
        deleted = False
        if os.path.exists(history_file):
            try:
                with open(history_file, "r") as file:
                    history = json.load(file)
                for entry in history:
                    if entry.get('timestamp') == entry_id:
                        deleted = True
                        continue # Skip this entry
                    updated_history.append(entry)
            except Exception as e:
                print(f"Error reading history file for deletion: {e}")
                return # Avoid overwriting if read failed

        if deleted:
            try:
                with open(history_file, "w") as file:
                    json.dump(updated_history, file, indent=4)
                self.load_history() # Refresh the display
            except Exception as e:
                print(f"Error writing updated history file: {e}")
        else:
            print(f"Entry with ID {entry_id} not found for deletion.")

    def confirm_delete_all_entries(self):
        """Display a confirmation dialog before deleting all history entries."""
        if not hasattr(self, 'dialog_delete_all'):
            self.dialog_delete_all = MDDialog(
                title="Delete All History?",
                text="Are you sure you want to delete all analysis history entries? This action cannot be undone.",
                buttons=[
                    MDFlatButton(
                        text="CANCEL",
                        on_release=lambda x: self.dialog_delete_all.dismiss()
                    ),
                    MDRaisedButton(
                        text="DELETE ALL",
                        # md_bg_color=MDApp.get_running_app().theme_cls.error_color,
                        on_release=lambda x: self.do_delete_all_entries()
                    ),
                ],
            )
        # Set button color after creation
        self.dialog_delete_all.buttons[1].md_bg_color = MDApp.get_running_app().theme_cls.error_color
        self.dialog_delete_all.open()

    def do_delete_all_entries(self):
        """Delete all entries from the analysis_history.json file."""
        if hasattr(self, 'dialog_delete_all') and self.dialog_delete_all:
            self.dialog_delete_all.dismiss()

        history_file = os.path.join(os.path.dirname(__file__), "..", "analysis_history.json")
        try:
            # Overwrite the file with an empty list
            with open(history_file, "w") as file:
                json.dump([], file, indent=4)
            
            # Refresh the history display
            self.load_history()
            print("All history entries deleted.")
        except Exception as e:
            print(f"Error deleting all history entries: {e}")
