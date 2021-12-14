import os
import firebase_admin
from decouple import config

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config('GOOGLE_APPLICATION_CREDENTIALS')
firebase_app = firebase_admin.initialize_app()
