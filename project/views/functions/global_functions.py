import random
import jwt
import requests

from flask import jsonify
from flask_mail import Message
from passlib.apps import custom_app_context as pwd_context

from project.extensions.extensions import mail
from project import config


# Function to encrypt user's password
def encrypt_password(password):
    return pwd_context.encrypt(password)


# Function to check user's encrypted password
def check_encrypted_password(password, hashed):
    return pwd_context.verify(password, hashed)


# Function to send email to User
def send_email(to, otp):
    msg = Message(
        subject="Password Recovery Email",
        body="Your OTP for Reset Password is " + str(otp),
        recipients=[to],
        sender=config.MAIL_USERNAME
    )
    mail.send(msg)


def send_verification_email(to, token):
    auth_url = "http://127.0.0.1:5000/verifyUser?token={}&email={}".format(token, to)
    msg = Message(
        subject="Project Email Verification",
        body=token,
        recipients=[to],
        sender=config.MAIL_USERNAME,
        html=""" <html lang="en">
​
<head>
    <meta charset="UTF-8" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Document</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@100;200;300;400;500;600;700;800;900&display=swap"
        rel="stylesheet" />
    <style>
        html,
        body {
            padding: 0px;
            margin: 0px;
        }
    </style>
</head>
​
<body>
    <div style=" width: 500px;
    padding-right: 1.5rem;
    padding-left: 1.5rem;
    margin-right: auto;
    margin-left: auto;">
        <div style="background-color: #191a30; position: relative; padding-top: 1rem; padding-bottom: 1rem;">
            <div style="margin-left: auto; margin-right: auto; width: fit-content;">
                <img src="https://myfitnesscoach.fit/assets/images/fitness-logo-mail.png"
                    style="width: auto; height: 3rem;" alt="" />
                <!-- <span style="font-family: 'Avenir LT Std'; font-style: normal; font-weight: 400; font-size: 1.375rem; line-height: 1.5rem; color: #ffffff; position: absolute;
                    top: 50%ds;
                    transform: translateY(-50%);">My
                    Fitness Coach</span> -->
            </div>
        </div>
        <div
            style="background: linear-gradient(90deg, #6f73bc 0%, #3e3c93 100%); padding-top: 1rem; padding-bottom: 1rem;">
            <div style="width: fit-content; margin-left: auto; margin-right: auto; padding-bottom: 1rem;">
                <span
                    style="height: 1px; width: 120px; background-color: white; vertical-align: text-top; display: inline-block;"></span>
                <img src="https://myfitnesscoach.fit/assets/images/Vector.png"
                    style="margin-left: 1rem; margin-right: 1rem; display: inline-block;" alt="" />
                <span
                    style="height: 1px; width: 120px; background-color: white; vertical-align: text-top; display: inline-block;"></span>
            </div>
            <span
                style="font-family: 'Inter', sans-serif; font-style: normal; font-weight: 300; font-size: 16px; line-height: 100%; letter-spacing: 0.1em; text-transform: uppercase; color: rgba(255, 255, 255, 0.9); margin-top: 0.65rem; display: block; text-align: center;">
                thanks for signing up
            </span>
            <span
                style="font-family: 'Inter', sans-serif; font-style: normal; font-weight: 600; font-size: 28px; line-height: 100%; color: #ffffff; margin-top: 1.25rem; margin-bottom: 0.65rem; display: block; text-align: center;">Verify
                Your Email Address</span>
        </div>
        <div>
            <p
                style="font-family: 'Inter', sans-serif; font-style: normal; font-weight: 500; font-size: 20px; text-align: center; line-height: 160%; color: #121212;">
                Hi,<br />
                In order to complete the registration process click the link below to verify your email address and get
                started on your fitness journey.
            </p>
            <a href=""" + auth_url + """
                style="display: block;
            padding: 1rem 1.75rem;
            text-transform: uppercase;
            font-size: 14px;
            font-weight: 400;
            line-height: 16px;
            color: #ffffff;
            text-align: center;
            text-decoration: none;
            vertical-align: middle;
            cursor: pointer;
            -webkit-user-select: none;
            -moz-user-select: none;
            user-select: none;
            border: 0;
            border-radius: 24px;
            background-color: #37395d;
            font-family: 'Helvetica';
            margin-left: auto;
            margin-right: auto;
            margin-top: 2rem;
            margin-bottom: 2rem;
            width: 30%;
            transition: color 0.15s ease-in-out, background-color 0.15s ease-in-out, border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;">
                Verify Login
            </a>
        </div>
        <div style="background: #CAD6F6; padding: 1rem;">
            <p style="
        font-family: 'Inter', sans-serif;
        font-style: normal;
        font-weight: 500;
        font-size: 24px;
        line-height: 100%;
        text-transform: uppercase;
        color: #37395d;
        text-align: center;
        margin-top: 1rem;
        ">Get in touch</p>
            <a href="mailto:info@myfitnesscoach.fit" style="font-family: 'Inter', sans-serif;
            font-style: normal;
            font-weight: 500;
            font-size: 20px;
            line-height: 100%;
            text-align: center;
            display: block;
            margin-top: 3rem;
            text-decoration: none;
            color: #373D3F;">info@myfitnesscoach.fit</a>
            <div
                style="background: #556EE6; width: 366px; height: 1px; margin-top: 1rem; margin-bottom: 1rem; margin-left: auto; margin-right: auto">
            </div>
            <div
                style="display: flex; align-items: center; column-gap: 1.5rem; margin-top: 1.65rem; margin-bottom: 0.65rem; margin-left: auto; margin-right: auto; width: fit-content;">
                <img src="https://myfitnesscoach.fit/assets/images/linkedin.png" style="width: 35px; height: 35px;"
                    alt="">
                <img src="https://myfitnesscoach.fit/assets/images/facebook.png" style="width: 35px; height: 35px;"
                    alt="">
                <img src="https://myfitnesscoach.fit/assets/images/insta.png" style="width: 35px; height: 35px;" alt="">
                <img src="https://myfitnesscoach.fit/assets/images/twitter.png" style="width: 35px; height: 35px;"
                    alt="">
            </div>
        </div>
        <div style="background: #191A30; padding-top: 1rem; padding-bottom: 1rem;">
            <span style="font-family: 'Inter', sans-serif;
        font-style: normal;
        font-weight: 300;
        font-size: 16px;
        line-height: 100%;
        text-align: center;
        display: block;
        color: #FFFFFF;">MyFitnessCoach All Rights Reserved</span>
        </div>
    </div>
</body>
​
</html> """.format(auth_url)
    )
    mail.send(msg)


# Function to generate random PIN for user.
def random_pin():
    number = random.randint(100000, 999999)
    return number


""" 
Following Function to get User Bio Information 
and calculates the required calories of user according to their gender.
"""


def user_info(age, gender, weight, height):
    if gender == 'male':
        # weight in kg, Height in cm, Age in Year
        bmr = (10 * (weight * 0.454)) + (6.25 * height) - (5 * age) + 5

    elif gender == 'female':

        bmr = (10 * (weight * 0.454)) + (6.25 * height) - (5 * age) - 161

    else:
        return jsonify(message="invalid gender input", category="error", status=400)

    return int(bmr)



# def fatloss_calcount(goal, calories, weekly_goal):
#     if goal == "fat_loss":
#         if weekly_goal <= 0.55:
#             cal_count = calories - 300
#         elif weekly_goal == 1.1:
#             cal_count = calories - 500
#         elif weekly_goal == 1.5:
#             cal_count = calories - 700
#         elif weekly_goal >= 2.0:
#             cal_count = calories - 825
#         else:
#             return jsonify(message="invalid weekly goal input", category="error", status=400)
#
#     elif goal == "extreme_fatloss":
#         if weekly_goal <= 0.55:
#             cal_count = calories - 500
#         elif weekly_goal == 1.1:
#             cal_count = calories - 700
#         elif weekly_goal == 1.5:
#             cal_count = calories - 900
#         elif weekly_goal >= 2.0:
#             cal_count = calories - 1100
#         else:
#             return jsonify(message="invalid weekly goal input", category="error", status=400)
#     else:
#         return jsonify(message="invalid activity goal input", category="error", status=400)
#     return int(cal_count)


# Following function to check the file format of user's profile picture.
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS


def verify_apple_user(identity_token):
    response = requests.get('https://appleid.apple.com/auth/keys')
    if response.status_code == 200:
        keys = response.json()
        public_key = keys['keys'][0]['kty']

    try:
        # Use the jwt library to decode the token
        decoded = jwt.decode(identity_token, options={"verify_signature": False})
        # Verify the token's signature using the Apple public key
        data = jwt.decode(identity_token, public_key, options={"verify_signature": False})
        # If the token is valid, return a success message
        if data["email_verified"] == "true":
            return str(data['email'])
        else:
            return str("invalid")
    except jwt.exceptions.InvalidSignatureError:
        # If the signature is invalid, return an error message
        return str("failed")





