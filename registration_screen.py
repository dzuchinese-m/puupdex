from kivy.uix.screenmanager import Screen

class RegistrationScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Remove or comment out any AI model loading code here
        # For example:
        # self.load_ai_model_in_background()

    # ...existing code...

    # If you have an on_enter method that loads the model, remove or move it
    # def on_enter(self):
    #     self.load_ai_model_in_background()
