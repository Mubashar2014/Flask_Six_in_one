from project import create_app
from project.extensions.extensions import socketio

app = create_app()

if __name__ == '__main__':
    socketio.run(app,host="0.0.0.0", debug=True)
