import os

SPECIAL_CHARS = ["\ue600", "\ue601"]
MONGO_URI = os.environ.get('MONGODB', 'localhost:32777')