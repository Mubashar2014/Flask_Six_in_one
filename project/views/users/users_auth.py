"""
All the user's authentications,
and user information details and upgrades handled in this file.
"""

import datetime
import os
import random
import string

from email_validator import validate_email, EmailNotValidError
from flask import Blueprint, request, jsonify, render_template, send_from_directory
from flask_jwt_extended import create_access_token, current_user, jwt_required, get_jwt
from werkzeug.utils import secure_filename

from project import config
from project.extensions.extensions import db, jwt as app_jwt
from project.models.users import  UsersAdditionalInfo, VersionChecker, User, Follow
from project.models.jwt import TokenBlocklist
from project.views.functions.global_functions import encrypt_password, check_encrypted_password, send_email, \
    random_pin, user_info, allowed_file, verify_apple_user, send_verification_email


users_auth_blueprint = Blueprint('users_auth', __name__)

global response


@users_auth_blueprint.route('/', methods=['GET'])
def home():
    return jsonify(message="running")


# Following function to register the user
@users_auth_blueprint.route('/register', methods=['POST'])
def user_registration():
    if request.method == "POST":
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        gender = request.form.get('gender')
        age = request.form.get('age')
        height = request.form.get('height')
        weight = request.form.get('weight')
        fitness_level = request.form.get('fitness_level')
        fitness_goal = request.form.get('fitness_goal')
        goal_weight = request.form.get('goal_weight')
        location = request.form.get('location')
        meals_per_day = request.form.get('meals_per_day')
        foods_you_dislike = request.form.get('foods_you_dislike')
        diet_type = request.form.get('diet_type')
        workout_per_week = request.form.get('workout_per_week')
        weekly_goal = request.form.get('weekly_goal')
        body_fat_percentage = request.form.get('body_fat_percentage')
        body_fat_value = request.form.get('body_fat_value')
        oauth_id = request.form.get('oauth_id')
        login_type = request.form.get('login_type')
        user_unit_preference = request.form.get('user_unit_preference')
        workout_place_preference = request.form.get('workout_place_preference')
        user_injury = request.form.get('user_injury')
        home_workout_instruments = request.form.get('home_workout_instruments')
        difficulty_level = request.form.get('workout_difficulty')
        login_through = request.form.get('login_through')
        error_messages = []

        if not full_name:
            error_messages.append("full name required")
        if not email:
            error_messages.append("email required")
        if not workout_place_preference:
            error_messages.append("workout place preference required")
        if not gender:
            error_messages.append("gender required")
        if not age:
            error_messages.append("age required")
        if not height:
            error_messages.append("height required")
        if not meals_per_day:
            error_messages.append("meals per day required")
        if not weight:
            error_messages.append("weight required")
        if not fitness_level:
            error_messages.append("fitness level required")
        if not fitness_goal:
            error_messages.append("fitness goal required")
        if not goal_weight:
            error_messages.append("goal weight required")
        if not weekly_goal:
            error_messages.append("weekly goal required")
        if not body_fat_percentage:
            error_messages.append("body fat percentage required")
        if not body_fat_value:
            error_messages.append("body fat value required")
        if not login_type:
            error_messages.append("login type required")
        if not user_unit_preference:
            error_messages.append("user unit preference required")
        if not difficulty_level:
            error_messages.append("difficulty level required")
        if workout_place_preference == "home":
            if not home_workout_instruments:
                error_messages.append("home workout instrument required")
        if len(error_messages):
            return jsonify(error_messages=error_messages, category="error", status=400)

        try:
            valid = validate_email(email)
            email = valid.email
        except EmailNotValidError:
            error_messages.append("invalid email")

        if login_type == "manual":
            user_email = User.query.filter_by(email=email).first()
            if user_email:
                return jsonify(message="email already exist, please login to continue", category="error", status=400)
            if not password:
                error_messages.append("password required")
            token = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            user_data = User(full_name=full_name, email=email, email_validation_date=datetime.datetime.now().date(),
                              password=encrypt_password(password), email_counter=1,
                              user_type="user", login_type=login_type, verification_token=token)

            db.session.add(user_data)
            db.session.commit()
            user_id = user_data.id

            send_verification_email(to=email, token=token)

            try:

                expires = datetime.timedelta(days=30)
                access_token = create_access_token(identity=user_id, expires_delta=expires)
                user_additional_data = UsersAdditionalInfo(user_id=user_id, gender=gender, age=age, height=height,
                                                           weight=weight, location=location,
                                                           fitness_level=fitness_level, fitness_goal=fitness_goal,
                                                           goal_weight=goal_weight, meals_per_day=int(meals_per_day),
                                                           foods_you_dislike=foods_you_dislike, diet_type=diet_type,
                                                           workout_per_week=int(workout_per_week),
                                                           body_fat_percentage=body_fat_percentage,
                                                           weekly_goal=weekly_goal,
                                                           body_fat_value=body_fat_value, user_injury=user_injury,
                                                           workout_place_preference=workout_place_preference,
                                                           user_unit_preference=user_unit_preference,
                                                           home_workout_instrument=home_workout_instruments,
                                                           difficulty_level=difficulty_level
                                                           )

                db.session.add(user_additional_data)
                db.session.commit()

                return jsonify(message="Registration Successful", access_token=str(access_token), category="success",
                               status=200)

            except Exception as err:
                User.query.filter_by(id=user_id).delete()
                return jsonify(message="try registering again", error=str(err), category="error", status=400)

        elif login_type == "oauth":
            user_email = User.query.filter_by(email=email).first()
            if user_email:
                user = User.query.filter_by(email=user_email.email).first()
                if not user:
                    return jsonify(message="email doesn't exist", category="error", status=400)
                if not user.oauth_id:
                    return jsonify(message="no auth id for this user", category="error", status=400)
                user_oauth_id = user_email.oauth_id.split("-")
                if not oauth_id == user_oauth_id[0]:
                    if user.login_through:
                        return jsonify(message="invalid oauth id", category="error", status=400,
                                       login_through=user.login_through)
                    else:
                        return jsonify(message="invalid oauth id", category="error", status=400)
                expires = datetime.timedelta(days=30)
                access_token = create_access_token(identity=user_email.id, expires_delta=expires)
                return jsonify(message="login successful", access_token=str(access_token),
                               category="success", status=200)
            if not oauth_id:
                error_messages.append("o auth id required")
            user_data = User(full_name=full_name, email=email, oauth_id=str(oauth_id) + "-beeaayy", user_type="user",
                              login_type=login_type, login_through=login_through)
            db.session.add(user_data)
            db.session.commit()
            user_id = user_data.id
        elif login_type == "apple_oauth":
            user_email = User.query.filter_by(email=email).first()
            if user_email:
                oauth_response = verify_apple_user(oauth_id)
                if oauth_response == user_email.email:
                    expires = datetime.timedelta(days=30)
                    access_token = create_access_token(identity=user_email.id, expires_delta=expires)
                    return jsonify(message="login successful", access_token=str(access_token),
                                   category="success", status=200)
            if not oauth_id:
                error_messages.append("identity token required")
            response_status = verify_apple_user(oauth_id)
            print(response_status, email)
            if response_status == email:
                user_data = User(full_name=full_name, email=email, oauth_id=str(oauth_id) + "-beeaayy",
                                  user_type="user",
                                  login_type=login_type)
                db.session.add(user_data)
                db.session.commit()
                user_id = user_data.id
            elif response_status == "invalid":
                return jsonify(message="email not verified", category="error", status=400)
            else:
                return jsonify(message="authentication failed", category="error", status=400)
        else:
            return jsonify(message="invalid login type", category="error", status=400)
        try:

            expires = datetime.timedelta(days=30)
            access_token = create_access_token(identity=user_id, expires_delta=expires)
            user_additional_data = UsersAdditionalInfo(user_id=user_id, gender=gender, age=age, height=height,
                                                       weight=weight, location=location,
                                                       fitness_level=fitness_level, fitness_goal=fitness_goal,
                                                       goal_weight=goal_weight, meals_per_day=int(meals_per_day),
                                                       foods_you_dislike=foods_you_dislike, diet_type=diet_type,
                                                       workout_per_week=int(workout_per_week),
                                                       body_fat_percentage=body_fat_percentage, weekly_goal=weekly_goal,
                                                       body_fat_value=body_fat_value, user_injury=user_injury,
                                                       workout_place_preference=workout_place_preference,
                                                       user_unit_preference=user_unit_preference,
                                                       home_workout_instrument=home_workout_instruments,
                                                       difficulty_level=difficulty_level
                                                       )

            db.session.add(user_additional_data)
            db.session.commit()
            return jsonify(message="user registered successfully", category="success", status=200,
                           access_token=access_token)
        except Exception as err:
            User.query.filter_by(id=user_id).delete()
            return jsonify(message="try registering again", error=str(err), category="error", status=400)
    else:
        return jsonify(message="method not allowed", category="error", status=400)


@users_auth_blueprint.route('/signup', methods=['POST'])
def signup():
    if request.method == "POST":
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        oauth_id = request.form.get('oauth_id')
        login_type = request.form.get('login_type')
        login_through = request.form.get('login_through')
        error_messages = []

        if not full_name:
            error_messages.append("full name required")
        if not email:
            error_messages.append("email required")

        if not login_type:
            error_messages.append("login type required")

        if len(error_messages):
            return jsonify(error_messages=error_messages, category="error", status=400)

        try:
            valid = validate_email(email)
            email = valid.email
        except EmailNotValidError:
            error_messages.append("invalid email")

        # user_data = User.query.filter_by(email=email).first()
        # user_id = user_data.id
        # user_additional_info = UsersAdditionalInfo.query.filter_by(user_id=user_id).first()
        #
        # if user_additional_info:
        #     user_additional_info_status = "true"
        # else:
        #     user_additional_info_status = "false"

        if login_type == "manual":
            password = request.form.get('password')
            user_email = User.query.filter_by(email=email).first()
            if user_email:
                return jsonify(message="email already exist, please login to continue", category="error", status=400)
            if not password:
                error_messages.append("password required")
            token = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            user_data = User(full_name=full_name, email=email, email_validation_date=datetime.datetime.now().date(),
                              password=encrypt_password(password), email_counter=1,
                              user_type="user", login_type=login_type, verification_token=token)

            db.session.add(user_data)
            db.session.commit()
            user_id = user_data.id
            try:

                expires = datetime.timedelta(days=30)
                access_token = create_access_token(identity=user_id, expires_delta=expires)
                return jsonify(message="Registration Successful", access_token=str(access_token), category="success",
                               status=200, user_additional_info_status=False)

            except Exception as err:
                User.query.filter_by(id=user_id).delete()
                db.session.commit()
                return jsonify(message="try registering again", error=str(err), category="error", status=400)

        elif login_type == "oauth":
            user_email = User.query.filter_by(email=email).first()
            if user_email:
                user = User.query.filter_by(email=user_email.email).first()
                if not user:
                    return jsonify(message="email doesn't exist", category="error", status=400)
                if not user.oauth_id:
                    return jsonify(message="no auth id for this user", category="error", status=400)
                user_oauth_id = user_email.oauth_id.split("-")
                if not oauth_id == user_oauth_id[0]:
                    if user.login_through:
                        return jsonify(message="invalid oauth id", category="error", status=400,
                                       login_through=user.login_through)
                    else:
                        return jsonify(message="invalid oauth id", category="error", status=400)
                expires = datetime.timedelta(days=30)
                access_token = create_access_token(identity=user_email.id, expires_delta=expires)

                user_additional_info = UsersAdditionalInfo.query.filter_by(user_id=user.id).first()

                if user_additional_info:
                    user_additional_info_status = True
                else:
                    user_additional_info_status = False
                return jsonify(message="login successful", access_token=str(access_token),
                               category="success", status=200, user_additional_info_status=user_additional_info_status)
            if not oauth_id:
                error_messages.append("o auth id required")
            user_data = User(full_name=full_name, email=email, oauth_id=str(oauth_id) + "-beeaayy", user_type="user",
                              login_type=login_type, login_through=login_through)
            db.session.add(user_data)
            db.session.commit()
            user_id = user_data.id
        elif login_type == "apple_oauth":
            user_email = User.query.filter_by(email=email).first()
            if user_email:
                oauth_response = verify_apple_user(oauth_id)
                if oauth_response == user_email.email:
                    user_additional_info = UsersAdditionalInfo.query.filter_by(user_id=user_email.id).first()

                    if user_additional_info:
                        user_additional_info_status = True
                    else:
                        user_additional_info_status = False
                    expires = datetime.timedelta(days=30)
                    access_token = create_access_token(identity=user_email.id, expires_delta=expires)
                    return jsonify(message="login successful", access_token=str(access_token),
                                   category="success", status=200,
                                   user_additional_info_status=user_additional_info_status)
            if not oauth_id:
                error_messages.append("identity token required")
            response_status = verify_apple_user(oauth_id)
            print(response_status, email)
            if response_status == email:
                user_data = User(full_name=full_name, email=email, oauth_id=str(oauth_id) + "-beeaayy",
                                  user_type="user",
                                  login_type=login_type)
                db.session.add(user_data)
                db.session.commit()
                user_id = user_data.id
            elif response_status == "invalid":
                return jsonify(message="email not verified", category="error", status=400)
            else:
                return jsonify(message="authentication failed", category="error", status=400)
        else:
            return jsonify(message="invalid login type", category="error", status=400)
        try:

            expires = datetime.timedelta(days=30)
            access_token = create_access_token(identity=user_id, expires_delta=expires)

            return jsonify(message="user registered successfully", category="success", status=200,
                           access_token=access_token)
        except Exception as err:
            User.query.filter_by(id=user_id).delete()
            return jsonify(message="try registering again", error=str(err), category="error", status=400)
    else:
        return jsonify(message="method not allowed", category="error", status=400)


# Following function to log in the user




@users_auth_blueprint.route('/login', methods=['POST'])
def user_login():
    if request.method == "POST":
        print("called")
        login_type = request.form.get('login_type')
        email = request.form.get('email')
        full_name = request.form.get('name')

        user_data = User.query.filter_by(email=email).first()
        if user_data:
           # followers_query = Follow.query.filter_by(followed_id=current_user.id)
           # followers_count = followers_query.count()
           # followings_query = Follow.query.filter_by(follower_id=current_user.id)
           # followings_count = followings_query.count()
            user_object = {
                "id": user_data.id,
                "full_name": user_data.full_name,
                "following_count": 0,
                "followers_count": 0,
                "profile_pic": user_data.photo,
                "facebook_id": "",
                "instagram_id": "",
                "tiktok_id": "",
                "youtube_id ": "",
            }
            user_id = user_data.id
            user_additional_info = UsersAdditionalInfo.query.filter_by(user_id=user_id).first()

            if user_additional_info:
                user_additional_info_status = True
            else:
                user_additional_info_status = False

        if login_type == 'manual':

            password = request.form.get('password')

            if not email:
                return jsonify(message="email required", category="error", status=400)
            if not password:
                return jsonify(message="password required", category="error", status=400)
            user = User.query.filter_by(email=email).first()
            if not user:
                return jsonify(message="email doesn't exist", category="error", status=400)
            if user.login_type == "oauth" or user.login_type == "apple_oauth":
                return jsonify(message="try logging in through auths", category="error", status=400)
            if user.status is False:
                return jsonify(message="Please, verify your email first", catgory="error", status=400)

            if not check_encrypted_password(password, user.password):
                return jsonify(message="invalid password", category="error", status=400)

            # user_additional_info = UsersAdditionalInfo.query.filter_by(user_id=user.id).first()
            expires = datetime.timedelta(days=30)
            access_token = create_access_token(identity=user.id, expires_delta=expires)
            # if UserDummyRecipes.query.filter_by(user_id=user.id).first() is not None:
            #     plan = "true"
            # else:
            #     plan = "false"
            # if not user_additional_info:
            #     return jsonify(message="no fitness goal found", category="error", status=400)


            return jsonify(message="user logged in successfully", access_token=str(access_token),
                           category="success", status=200, user_additional_info_status=user_additional_info_status, user_object=user_object)
        elif login_type == "oauth":

            oauth_id = request.form.get('oauth_id')

            if not email:
                return jsonify(message="email required", category="error", status=400)
            if not oauth_id:
                return jsonify(message="oauth id required", category="error", status=400)
            user = User.query.filter_by(email=email).first()
            if not user:
                user_data = User(full_name=full_name, email=email, oauth_id=str(oauth_id) + "-beeaayy",
                                  user_type="user",
                                  login_type=login_type, login_through="oauth")
                db.session.add(user_data)
                db.session.commit()


                expires = datetime.timedelta(days=30)
                access_token = create_access_token(identity=user_data.id, expires_delta=expires)

                return jsonify(message="login successful", access_token=str(access_token),
                               category="success", status=200, user_additional_info_status=False,user_object=user_object)
            if not user.oauth_id:
                return jsonify(message="no auth id for this user", category="error", status=400)
            user_oauth_id = user.oauth_id.split("-")
            if not oauth_id == user_oauth_id[0]:

                if user.login_through:
                    return jsonify(message="invalid oauth id", category="error", status=400,
                                   login_through=user.login_through)
                else:
                    return jsonify(message="invalid oauth id", category="error", status=400)

            print(user_oauth_id[0])

            expires = datetime.timedelta(days=30)
            access_token = create_access_token(identity=user.id, expires_delta=expires)
            return jsonify(message="login successful", access_token=str(access_token),
                           category="success", status=200, user_additional_info_status=user_additional_info_status, user_object=user_object)
        elif login_type == "apple_oauth":

            oauth_id = request.form.get('oauth_id')

            oauth_response = verify_apple_user(oauth_id)
            if oauth_response == email:
                user = User.query.filter_by(email=email).first()
                if not user:
                    return jsonify(message="email doesn't exist", category="error", status=400)
                expires = datetime.timedelta(days=30)
                access_token = create_access_token(identity=user.id, expires_delta=expires)
                return jsonify(message="login successful", access_token=str(access_token),
                               category="success", status=200, user_additional_info_status=False,user_object=user_object)
            elif oauth_response != email:
                user = User.query.filter_by(email=email).first()
                if not user:
                    return jsonify(message="email doesn't exist", category="error", status=400)
            elif oauth_response == "invalid":
                return jsonify(message="email not verified", category="error", status=400)
            else:
                return jsonify(message="authentication failed", category="error", status=400)
        else:
            return jsonify(message="login type invalid", category="error", status=400)
    else:
        return jsonify(message="method not allowed", category="error", status=400)


# Following function to upload photo of the user
@users_auth_blueprint.route('/photo', methods=['POST'])
@jwt_required()
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify(message="no file part", category="error", status=400)
        file = request.files['file']
        if file.filename == '':
            return jsonify(message="no selected file", category="error", status=400)
        if file and allowed_file(file.filename):
            ct = datetime.datetime.now()
            ts = ct.timestamp()
            filename = secure_filename(file.filename)
            file.save(os.path.join(config.UPLOAD_FOLDER, str(ts) + filename))
            photo_dump = config.UPLOAD_FOLDER + str(ts) + filename
            if User.query.filter_by(user_id=current_user.id).update(dict(photo=photo_dump)):
                db.session.commit()
            return jsonify(message="uploaded successfully", category="success", status=200)
    return jsonify(message="method not allowed", category="error", status=400)


# Following function to reset the password of the user.
@users_auth_blueprint.route('/forget-password', methods=['POST'])
def forget_password():
    if request.method == "POST":
        email = request.form.get('email')

        if not email:
            return jsonify(message="email required", category="error", status=400)

        if User.query.filter_by(email=email).first():
            user = User.query.filter_by(email=email).first()
            if user.login_type == "oauth":
                return jsonify(message="you were logged in using social logins", category="error", status=400)

            otp = random_pin()

            User.query.filter_by(email=email).update(dict(recovery=otp, recovery_created_at=datetime.datetime.now()))
            db.session.commit()
            send_email(email, otp)
            return jsonify(message="email sent successfully", category="success", status=200)
        else:
            return jsonify(message="email doesn't exist", category="error", status=400)

    else:
        return jsonify(message="method not allowed", category="error", status=400)


# Following function to reset the password of the user. - verify OTP
@users_auth_blueprint.route('/verify-otp', methods=['POST'])
def verify_otp():
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            return jsonify(message="email required", category="error", status=400)
        otp = request.form.get('otp')
        if not otp:
            return jsonify(message="otp required", category="error", status=400)

        users = User.query.filter_by(email=email).first()
        if User.recovery == int(otp):
            return jsonify(message="otp verified", category="success", status=200)
        else:
            return jsonify(message="invalid otp", category="error", status=400)

    else:
        return jsonify(message="method not allowed", category="error", status=400)


# Following function to reset the password of the user. - Set New Password
@users_auth_blueprint.route('/new-password', methods=['POST'])
def new_password():
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            return jsonify(message="email required", category="error", status=400)
        otp = request.form.get('otp')
        if not otp:
            return jsonify(message="otp required", category="error", status=400)

        new_pass = request.form.get('new_password')
        if not new_pass:
            return jsonify(message="new password required", category="error", status=400)

        user = User.query.filter_by(email=email, recovery=otp).first()
        if not user:
            return jsonify(message="invalid credentials", category="error", status=400)
        if check_encrypted_password(new_pass, user.password):
            return jsonify(message="password can't be same as current password", category="error", status=400)

        if User.query.filter_by(email=email, recovery=otp).update(dict(password=encrypt_password(new_pass))):
            db.session.commit()
            return jsonify(message="password changed successfully", category="success", status=200)
        else:
            return jsonify(message="invalid credentials", category="error", status=400)

    else:
        return jsonify(message="method not allowed", category="error", status=400)


# Following function to change the password of the user from within the application.
@users_auth_blueprint.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        n_password = request.form.get('new_password')
        confirm_password = request.form.get("confirm_password")
        if n_password != confirm_password:
            return jsonify(message="new passwords should be same", category="error", status=400)
        if not current_password:
            return jsonify(message="current password required", category="error", status=400)
        if not n_password:
            return jsonify(message="new password required", category="error", status=400)

        user = User.query.filter_by(id=current_user.id).first()
        if check_encrypted_password(current_password, user.password):
            if check_encrypted_password(n_password, user.password):
                return jsonify(message="password can't be same as current password", category="error", status=400)
            if User.query.filter_by(id=current_user.id).update(dict(password=encrypt_password(n_password))):
                db.session.commit()
                return jsonify(message="password updated successfully", category="success", status=200)
            else:
                return jsonify(message="invalid credentials", category="error", status=400)
        else:
            return jsonify(message="invalid current password", category="error", status=400)

    else:
        return jsonify(message="method not allowed", category="error", status=400)


# Following function to log out the user.
@users_auth_blueprint.route("/logout", methods=["DELETE"])
@jwt_required()
def modify_token():
    if request.method == "DELETE":
        jti = get_jwt()["jti"]
        now = datetime.datetime.now()
        db.session.add(TokenBlocklist(jti=jti, created_at=now))
        db.session.commit()
        return jsonify(message="JWT revoked", category="success", status=200)
    else:
        return jsonify(message="method not allowed", category
        ="error", status=400)


# Following function to check the user identity
@app_jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return User.query.filter_by(id=identity).one_or_none()


# Following function to check the user identity token is valid or not
@app_jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    token = db.session.query(TokenBlocklist.id).filter_by(jti=jti).scalar()
    return token is not None


# Following function to get all the info of any user.


# Following function to edit all the info of any user.
@users_auth_blueprint.route('/editUser', methods=['PATCH'])
@jwt_required()
def edit_user():
    if request.method == "PATCH":
        full_name = request.form.get('full_name')
        age = request.form.get('age')
        height = request.form.get('height')
        # weight = request.form.get('weight')
        fitness_level = request.form.get('fitness_level')
        fitness_goal = request.form.get('fitness_goal')
        goal_weight = request.form.get('goal_weight')
        location = request.form.get('location')
        meals_per_day = request.form.get('meals_per_day')
        foods_you_dislike = request.form.get('foods_you_dislike')
        diet_type = request.form.get('diet_type')
        workout_per_week = request.form.get('workout_per_week')
        weekly_goal = request.form.get('weekly_goal')
        user_unit_preference = request.form.get('user_unit_preference')

        body_fat_percentage = request.form.get('body_fat_percentage')
        body_fat_value = request.form.get('body_fat_value')
        workout_place_preference = request.form.get('workout_place_preference')
        user_injury = request.form.get('user_injury')
        home_workout_instruments = request.form.get('home_workout_instruments')
        difficulty_level = request.form.get('workout_difficulty')
        error_messages = []

        if not full_name:
            error_messages.append("full name required")
        if not workout_place_preference:
            error_messages.append("workout place preference required")
        if not age:
            error_messages.append("age required")
        if not height:
            error_messages.append("height required")
        if not meals_per_day:
            error_messages.append("meals per day required")
        if not fitness_level:
            error_messages.append("fitness level required")
        if not fitness_goal:
            error_messages.append("fitness goal required")
        if not goal_weight:
            error_messages.append("goal weight required")
        if not weekly_goal:
            error_messages.append("weekly goal required")
        if not body_fat_percentage:
            error_messages.append("body fat percentage required")
        if not body_fat_value:
            error_messages.append("body fat value required")
        if not user_unit_preference:
            error_messages.append("user unit preference required")
        if not difficulty_level:
            error_messages.append("workout difficulty required")
        if workout_place_preference == "home":
            if not home_workout_instruments:
                error_messages.append("home workout instrument required")
        if len(error_messages):
            return jsonify(error_messages=error_messages, category="error", status=400)

        try:
            if User.query.filter_by(id=current_user.id).update(dict(full_name=full_name)) and \
                    UsersAdditionalInfo.query.filter_by(user_id=current_user.id).update(dict(
                        age=age,
                        height=height,
                        fitness_level=fitness_level,
                        fitness_goal=fitness_goal,
                        goal_weight=goal_weight,
                        location=location,
                        meals_per_day=meals_per_day,
                        foods_you_dislike=foods_you_dislike,
                        diet_type=diet_type,
                        workout_per_week=workout_per_week,
                        weekly_goal=weekly_goal,
                        user_unit_preference=user_unit_preference,
                        body_fat_percentage=body_fat_percentage,
                        body_fat_value=body_fat_value,
                        workout_place_preference=workout_place_preference,
                        user_injury=user_injury,
                        home_workout_instrument=home_workout_instruments,
                        difficulty_level=difficulty_level
                    )):
                db.session.commit()
            return jsonify(message="user updated successfully", category="success", status=200)
        except Exception as err:
            return jsonify(message="error, try again", error=str(err), category="error", status=400)
    else:
        return jsonify(message="method not allowed", category="error", status=400)


@users_auth_blueprint.route('/verifyUser', methods=['GET'])
def verify_user():
    email = request.args.get("email")
    token = request.args.get("token")
    if not (email and token):
        return jsonify(message="email and token required to continue", category="error", status=400)

    user = User.query.filter_by(email=email).first()
    if user:
        if user.verification_token == token:
            if User.query.filter_by(email=user.email).update(dict(status=True)):
                db.session.commit()
                return render_template('response.html')
            else:
                return render_template('unverified.html')

        else:
            return render_template('unverified.html')
    else:
        return render_template('unverified.html')


@users_auth_blueprint.route('/verifyUserEmail', methods=['GET'])
def verify_user_email():
    user_email = request.args.get('email')
    if not user_email:
        return jsonify(message="email required")
    token = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    if User.query.filter_by(email=user_email).update(dict(verification_token=token)):
        db.session.commit()
    else:
        return jsonify(message="email doesn't exist", category="error", status=400)

    user_data = User.query.filter_by(email=user_email).first()
    if user_data:
        if user_data.email_validation_date != datetime.datetime.now().date():
            if User.query.filter_by(email=user_data.email).update(dict(email_counter=1)):
                db.session.commit()

        if user_data.email_counter > 3:
            return jsonify(message="daily email sending limit reached", category="error", status=400)

        counter = user_data.email_counter + 1
        if User.query.filter_by(email=user_data.email).update(dict(email_counter=counter)):
            db.session.commit()

    else:
        return jsonify(message="user record not found", category="error", status=400)
    send_verification_email(to=user_email, token=token)
    return jsonify(message="verification email sent", category="success", status=200)


@users_auth_blueprint.route('/versionCheck', methods=['GET'])
def version_checker():
    version_history = VersionChecker.query.filter_by(id=1).first()
    if version_history:
        data = {
            "android": {"android_latest_version": version_history.android_latest_version,
                        "android_latest_priority": version_history.android_latest_priority,
                        "android_previous_version": version_history.android_previous_version,
                        "android_previous_priority": version_history.android_previous_priority
                        },
            "ios": {"ios_latest_version": version_history.ios_latest_version,
                    "ios_latest_priority": version_history.ios_latest_priority,
                    "ios_previous_version": version_history.ios_previous_version,
                    "ios_previous_priority": version_history.ios_previous_priority
                    }
        }
        return jsonify(data=data, category="success", status=200)
    else:
        return jsonify(message="no record_found", category="error", status=400)


@users_auth_blueprint.route('/editUnit', methods=['PATCH'])
@jwt_required()
def edit_unit():
    if request.method == "PATCH":
        user_unit_preference = request.form.get('user_unit_preference')
        if not user_unit_preference:
            return jsonify(message="user unit preference required", category="error", status=400)
        try:
            if UsersAdditionalInfo.query.filter_by(user_id=current_user.id).update(dict(

                    user_unit_preference=user_unit_preference,

            )):
                db.session.commit()
            return jsonify(message="unit updated successfully", category="success", status=200)
        except Exception as err:
            return jsonify(message="error, try again", error=str(err), category="error", status=400)
    else:
        return jsonify(message="method not allowed", category="error", status=400)


@users_auth_blueprint.route('/deleteUser', methods=['POST'])
@jwt_required()
def delete_user():
    user_email = User.query.filter_by(id=current_user.id).first()
    if user_email:
        token = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        new_email = user_email.email + '-' + token
        if user_email.oauth_id:
            new_oauth_id = user_email.oauth_id + '-' + token
            if User.query.filter_by(id=current_user.id).update(dict(oauth_id=new_oauth_id)):
                db.session.commit()
        if User.query.filter_by(id=current_user.id).update(dict(email=new_email)):
            db.session.commit()
            return jsonify(message="user deleted successfully", category="success", status=200)
        else:
            return jsonify(message="invalid user", category="error", status=400)
    else:
        return jsonify(message="invalid user", category="error", status=400)


@users_auth_blueprint.route('/addRatings', methods=['POST'])
@jwt_required()
def add_ratings():
    if request.method == "POST":
        user_ratings = request.form.get('user_ratings')
        user_ratings = bool(user_ratings)
        print(user_ratings)
        if not user_ratings:
            return jsonify(message="user ratings required", category="error", status=400)
        try:
            if User.query.filter_by(id=current_user.id).update(dict(
                    ratings=user_ratings
            )):
                db.session.commit()
            return jsonify(message="ratings updated successfully", category="success", status=200)
        except Exception as err:
            return jsonify(message="error, try again", error=str(err), category="error", status=400)
    else:
        return jsonify(message="method not allowed", category="error", status=400)

@users_auth_blueprint.route('/UserInfo', methods=['GET'])
@jwt_required()
def user_info():

    try:
        email = current_user.email
        user_data = User.query.filter_by(email=email).first()
        if user_data:
            followers_query = Follow.query.filter_by(followed_id=current_user.id)
            followers_count = followers_query.count()
            followings_query = Follow.query.filter_by(follower_id=current_user.id)
            followings_count = followings_query.count()
            user_object = {
                "user_id": user_data.id,
                "username": user_data.full_name,
                "followings_count": followings_count,
                "followers_count": followers_count,
                "profile_pic": user_data.photo,
                "facebook_id": "",
                "instagram_id": "",
                "tiktok_id": "",
                "youtube_id ": "",
            }

            return jsonify(data=user_object, category="success", status=200)

    except Exception as err:
        return jsonify(message="error, try again", error=str(err), category="error", status=400)

    from flask import send_from_directory

@users_auth_blueprint.route('/media/<path:filename>')
def serve_media(filename):
    return send_from_directory('/home/ubuntu/mmmw/project/media/', filename)
