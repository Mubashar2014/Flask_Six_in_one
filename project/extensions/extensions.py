"""
File for creating objects of Libraries we are going to use
for prominent libraries in our projects. i-e sending emails,
user authentication through Tokens etc.
"""

from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow
from flask_restful import Api, Resource
from flask_socketio import SocketIO
from flasgger import Swagger

db = SQLAlchemy()  # SQL object creation
jwt = JWTManager()  # JWT Authentication Token Library object creation
mail = Mail()  # Mail sending from Flask
migrate = Migrate()  # Database Migrations
marsh = Marshmallow()  # Object Mapping/Parsing in ORM, Not implemented yet.
api = Api()  # REST API
socketio = SocketIO()
swagger = Swagger()
