"""
Following file to deal with all kinda notifications of a user.
"""

import json
from datetime import datetime, timedelta

import requests

from flask import Blueprint, request, jsonify
from flask_jwt_extended import current_user, jwt_required

from project.extensions.extensions import db
from project.models.users import UserNotifications, UsersAdditionalInfo, UserCustomNotifications

notifications_blueprint = Blueprint('notifications', __name__)



# Following functions to add user custom Notifications
@notifications_blueprint.route('/addCustomNotifications', methods=['POST'])
@jwt_required()
def add_custom_notifications():
    try:
        custom_notification_name = request.form.get("custom_notification_name")
        custom_notification_time = request.form.get("custom_notification_time")
        device_token = request.form.get("device_token")
        if not (custom_notification_time and custom_notification_name and device_token):
            return jsonify(message="custom notification required", category="error", status=400)

        custom_noti = UserCustomNotifications.query.filter_by(user_id=current_user.id).all()
        if custom_noti:
            for items in custom_noti:
                if UserCustomNotifications.query.filter_by(user_id=items.user_id).update(
                        dict(device_token=device_token)):
                    db.session.commit()
                else:
                    pass
            return jsonify(message="custom notification updated successfully",
                           category="success", status=200)
        else:
            add_custom = UserCustomNotifications(custom_notification_name=custom_notification_name,
                                                 custom_notification_time=custom_notification_time,
                                                 custom_notification_status=True,
                                                 device_token=device_token, user_id=current_user.id)
            db.session.add(add_custom)
            db.session.commit()
            try:
                # Parse the UTC time string into a datetime object
                utc_time = datetime.strptime(custom_notification_time, "%H:%M")

                # Add 12 hours to the datetime object
                utc_time += timedelta(hours=12)

                # Format the resulting datetime object back to the desired string format
                result_time_string = utc_time.strftime("%H:%M")

            except ValueError:
                return "Invalid time format. Please use 'HH:MM'."

            add_custom = UserCustomNotifications(custom_notification_name="evening",
                                                 custom_notification_time=result_time_string,
                                                 custom_notification_status=True,
                                                 device_token=device_token, user_id=current_user.id)
            db.session.add(add_custom)
            db.session.commit()
            custom_notification_id = add_custom.id
            return jsonify(custom_notification_id=custom_notification_id,
                           message="custom notification added successfully",
                           category="success", status=200)
    except Exception as err:
        return jsonify(message="something went wrong", error=str(err), status=400)


