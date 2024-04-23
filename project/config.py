"""
All the configurations of the applications are set in this file.
"""

DEBUG = True
HOST = '127.0.0.1'

SECRET_KEY = "Th1s1s111221"
MAIL_SERVER = "servername"
MAIL_PORT = 465
MAIL_USE_TLS = False
MAIL_USE_SSL = True
MAIL_USERNAME = "mubasharmalik2014@gmail.com"
MAIL_PASSWORD = "Hello@1122"


SQLALCHEMY_DATABASE_URI = "mysql://admin:tenken123@mydb.cvciuuc6mdwd.us-east-2.rds.amazonaws.com/project_db"
#SQLALCHEMY_DATABASE_URI = "mysql://username:password@127.0.0.1/db_name"
#SQLALCHEMY_DATABASE_URI = "mysql://root:Qwerty0.@127.0.0.1/fitness_app_db"

SQLALCHEMY_TRACK_MODIFICATIONS = False

JWT_ACCESS_TOKEN_EXPIRES = "ACCESS_EXPIRES"



UPLOAD_FOLDER = 'project/media/uploaded_photos/'
CV_FOLDER = 'project/media/cv_uploads/'
ad_FOLDER = 'project/media/ad_uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

SQLALCHEMY_MAX_CONNECTIONS = 100000
MAX_CONNECTIONS = 100000

