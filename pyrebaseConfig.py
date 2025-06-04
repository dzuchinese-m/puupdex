import pyrebase

config = {
  "apiKey": "AIzaSyCNO00Bk8tIsZW-OcPMAFbJF-ONvAvZb2o",
  "authDomain": "fir-f254b.firebaseapp.com",
  "databaseURL": "https://fir-f254b-default-rtdb.asia-southeast1.firebasedatabase.app",
  "storageBucket": "fir-f254b.appspot.com"
}

firebase = pyrebase.initialize_app(config)

auth = firebase.auth()
db = firebase.database()
storage = firebase.storage()
