"""
Following file is used to start the application
"""

from project import create_app, config

application = create_app()


if __name__ == '__main__':
    application.run(host="0.0.0.0", port=80, debug=True, load_dotenv=config)
