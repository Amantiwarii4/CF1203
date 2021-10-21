import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
DATABASES = { 
    'default': {
        'ENGINE': 'django.db.backends.mysql', 
        'NAME': 'CF1203',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': 'localhost',   # Or an IP Address that your DB is hosted on
        'PORT': '3306',
    }
}
 