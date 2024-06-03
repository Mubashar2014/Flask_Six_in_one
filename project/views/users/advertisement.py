import os
from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, current_user
from werkzeug.utils import secure_filename

from project.config import CV_FOLDER, ad_FOLDER
from project.extensions.extensions import db
from project.models.users import Ad, AdClick


import boto3
from botocore.exceptions import NoCredentialsError
import os

from project.views.functions.global_functions import allowed_file

s3 = boto3.client('s3', aws_access_key_id='AKIAQ3EGSPOPKKCGD2HR',
                  aws_secret_access_key='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')

advertisement_bp = Blueprint('advertisement', __name__)

@advertisement_bp.route('/create_ad', methods=['POST'])
@jwt_required()
def create_ad():
    user_id = current_user.id

    title = request.form.get('title')
    description = request.form.get('description')
    media = request.files.get('media')
    age_from = int(request.form.get('age_from'))
    age_to = int(request.form.get('age_to'))
    gender = request.form.get('gender')
    city = request.form.get('city')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    timestamp = request.form.get('timestamp')

    if start_date:
        try:
            datetime.strptime(start_date, '%Y-%m-%d')
        except ValueError:
            return jsonify(message="Incorrect date format, should be YYYY-MM-DD", category="error", status=400)

    if end_date:
        try:
            datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            return jsonify(message="Incorrect date format, should be YYYY-MM-DD", category="error", status=400)

    if not title or not description or not media or not age_from or not age_to or not gender or not city:
        return jsonify({'error': 'All fields are required'}), 400


    try:
        if media and allowed_file(media.filename):
            s3.upload_fileobj(media, 'flask6in1', media.filename)
            image_url = f"https://flask6in1.s3.amazonaws.com/{media.filename}"
        else:
            return jsonify({'error': 'Invalid media file'}), 400

        new_ad = Ad(
            title=title,
            description=description,
            media_link=image_url,
            age_from=age_from,
            age_to=age_to,
            gender=gender,
            city=city,
            start_date=start_date,
            end_date=end_date,
            user_id=user_id,
            timestamp=timestamp
        )

        db.session.add(new_ad)
        db.session.commit()

        return jsonify({'message': 'Ad created successfully'})

    except Exception as e:
        return jsonify({'message': str(e)}), 500


@advertisement_bp.route('/click_ad', methods=['POST'])
@jwt_required()
def click_ad():
    ad_id = int(request.form.get('ad_id'))

    new_click = AdClick(ad_id=ad_id, user_id=current_user.id)
    db.session.add(new_click)
    db.session.commit()

    return jsonify({'message': 'Ad clicked successfully'})

@advertisement_bp.route('/get_ads', methods=['GET'])
@jwt_required()
def get_ads():
    ads = Ad.query.filter_by(user_id=current_user.id).all()
    ads_data = []

    for ad in ads:
        ad_data = {
            'id': ad.id,
            'title': ad.title,
            'description': ad.description,
            'media_link': ad.media_link,
            'age_from': ad.age_from,
            'age_to': ad.age_to,
            'gender': ad.gender,
            'city': ad.city,
            'start_date': ad.start_date,
            'end_date': ad.end_date,
            'user_id': ad.user_id,
            'timestamp': ad.timestamp
        }

        ads_data.append(ad_data)

    return jsonify({'ads': ads_data})