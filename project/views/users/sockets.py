from flask_restful import Api, Resource

from flask import Blueprint, request, jsonify, render_template

from project.extensions.extensions import socketio, api

sockets_blueprint = Blueprint('sockets', __name__)


class MessageResource(Resource):
    def post(self):
        data = request.json
        message = data.get('message')
        socketio.emit('message', message)
        return {'status': 'success', 'message': 'Message sent successfully'}

api.add_resource(MessageResource, '/message')