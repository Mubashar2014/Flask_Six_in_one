"""
This file is used to create APP and register all the modules in the application
"""

from flask import Flask, g
from project import config
from flask_cors import CORS


def create_app(config_file='config.py'):
    app = Flask(__name__, static_url_path='/projectdia', static_folder='media')
    CORS(app)
    app.config.from_pyfile(config_file)

    with app.app_context():

        from project.views.users.users_auth import users_auth_blueprint
        app.register_blueprint(users_auth_blueprint)

        from project.views.users.sockets import sockets_blueprint
        app.register_blueprint(sockets_blueprint)

        from project.views.users.social_media import social_media_blueprint
        app.register_blueprint(social_media_blueprint)

        from project.views.users.e_commerece import e_commerce_bp
        app.register_blueprint(e_commerce_bp)

        from project.views.users.business import business_bp
        app.register_blueprint(business_bp)

        from project.views.users.advertisement import advertisement_bp
        app.register_blueprint(advertisement_bp)

        from project.extensions.extensions import db, jwt, mail, migrate, marsh, socketio, api, swagger
        db.init_app(app)
        migrate.init_app(app, db, compare_type=True)
        db.create_all()
        db.session.commit()
        jwt.init_app(app)
        mail.init_app(app)
        marsh.init_app(app)
        socketio.init_app(app)
        api.init_app(app)
        swagger.init_app(app)


        @app.teardown_appcontext
        def teardown_db(exception):
            db = g.pop('db', None)

            if db is not None:
                db.close()

        return app
