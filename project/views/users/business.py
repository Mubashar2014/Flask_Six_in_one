import base64
import os
from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, current_user
from sqlalchemy import func, desc
from werkzeug.utils import secure_filename
from flask_socketio import emit
from project.config import CV_FOLDER
from project.extensions.extensions import db, socketio
from project.models.users import Feed, Like_feed, Comment_feed, Job, JobLike, JobComment, JobApplication, Event, \
    EventLike, EventComment, UserExperience, UserPortfolio, User

import boto3
from botocore.exceptions import NoCredentialsError
import os

from project.views.functions.global_functions import allowed_file

s3 = boto3.client('s3', aws_access_key_id='AKIAQ3EGSPOPKKCGD2HR', aws_secret_access_key='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')


# Initialize blueprint
business_bp = Blueprint('business', __name__)

# Route to create a new feed
@business_bp.route('/create_feed', methods=['POST'])
@jwt_required()
def create_feed():
    content = request.form.get('content')
    image_file = request.files.get('image')

    if not content:
        return jsonify({'error': 'Content is required'}), 400

    if image_file and allowed_file(image_file.filename):
        try:
            s3.upload_fileobj(image_file, 'flask6in1', image_file.filename)
            image_url = f"https://flask6in1.s3.amazonaws.com/{image_file.filename}"

            new_feed = Feed(content=content, image=image_url, user=current_user)
            db.session.add(new_feed)
            db.session.commit()

            socketio.emit('new_feed', {'event': 'new_feed', 'id': new_feed.id, 'content': new_feed.content,
                                       'user_id': new_feed.user_id}, namespace='/business')

            return jsonify({'message': 'Feed created successfully'}), 200
        except NoCredentialsError:
            return jsonify({'error': 'Credentials not available', 'category': 'error', 'status': 400})



# Route to get feed details
@business_bp.route('/feed_details', methods=['GET'])
@jwt_required()
def get_feed_details():
    feed_id = request.args.get('feed_id')
    feed = Feed.query.get(id=feed_id)

    if not feed:
        return jsonify({'error': 'Feed not found'}), 404

    like_count = db.session.query(func.count(Like_feed.id)).filter_by(feed_id=feed.id).scalar()
    comment_count = db.session.query(func.count(Comment_feed.id)).filter_by(feed_id=feed.id).scalar()

    return jsonify({'like_count': like_count, 'comment_count': comment_count}), 200

# Route to like a feed
@business_bp.route('/like_feed', methods=['POST'])
@jwt_required()
def like_feed():
    feed_id = request.form.get('feed_id')
    feed = Feed.query.get(feed_id)

    if not feed:
        return jsonify({'error': 'Feed not found'}), 404

    existing_like = Like_feed.query.filter_by(user_id=current_user.id, feed_id=feed.id).first()

    if existing_like:
        return jsonify({'error': 'You have already liked this feed'}), 400

    new_like = Like_feed(user_id=current_user.id, feed_id=feed_id)
    db.session.add(new_like)
    db.session.commit()

    # Emit a Socket.IO event to notify clients
    emit('feed_liked', {'feed_id': feed_id, 'user_id': current_user.id},namespace='/business')

    return jsonify({'message': 'Feed liked successfully'})

# Route to comment on a feed
@business_bp.route('/comment_feed', methods=['POST'])
@jwt_required()
def comment_feed():
    feed_id = request.form.get('feed_id')
    feed = Feed.query.get(feed_id)

    if not feed:
        return jsonify({'error': 'Feed not found'}), 404

    text = request.form.get('text')

    if not text:
        return jsonify({'error': 'Comment text is required'}), 400

    new_comment = Comment_feed(text=text, user_id=current_user.id, feed_id=feed_id)
    db.session.add(new_comment)
    db.session.commit()

    # Emit a Socket.IO event to notify clients
    emit('feed_commented', {'feed_id': feed_id, 'user_id': current_user.id, 'text': text}, broadcast=True,namespace='/business')

    return jsonify({'message': 'Comment added successfully'})


# Get Feed Comments
@business_bp.route('/feed_comments', methods=['GET'])
@jwt_required()
def get_feed_comments():
    feed_id = request.args.get('feed_id')
    feed = Feed.query.get(feed_id)

    if not feed:
        return jsonify({'error': 'Feed not found'}), 404

    comments = Comment_feed.query.filter_by(feed_id=feed.id).all()
    comments_data = [{'id': comment.id, 'text': comment.text, 'user_id': comment.user_id, 'timestamp': comment.timestamp} for comment in comments]

    return jsonify({'comments': comments_data})

# Pin Feed
@business_bp.route('/pin_feed', methods=['PUT'])
@jwt_required()
def pin_feed():
    feed_id = request.form.get('feed_id')
    feed = Feed.query.get(feed_id)

    if not feed:
        return jsonify({'error': 'Feed not found'}), 404

    if feed.user_id != current_user.id:
        return jsonify({'error': 'You are not authorized to pin this feed'}), 403

    feed.pinned = True
    db.session.commit()

    return jsonify({'message': 'Feed pinned successfully'})

# Delete Feed
@business_bp.route('/delete_feed', methods=['DELETE'])
@jwt_required()
def delete_feed():
    feed_id = request.form.get('feed_id')
    feed = Feed.query.get(feed_id)

    if not feed:
        return jsonify({'error': 'Feed not found'}), 404

    if feed.user_id != current_user.id:
        return jsonify({'error': 'You are not authorized to delete this feed'}), 403

    db.session.delete(feed)
    db.session.commit()

    return jsonify({'message': 'Feed deleted successfully'})


@business_bp.route('/feeds', methods=['GET'])
def get_feeds():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))

    feeds = Feed.query.order_by(desc(Feed.timestamp)).paginate(page=page, per_page=per_page, error_out=False)

    feeds_data = [
        {
            'feed_object':{
            'id': feed.id,
            'content': feed.content,
            'user_id': feed.user_id,
            'timestamp': feed.timestamp,
            'likes_count': len(feed.likes),
            'comments_count': len(feed.comments),
            'image': feed.image
            },
            'user_object':{
                
            }
        } for feed in feeds.items
    ]

    return jsonify({'feeds': feeds_data})

# Close Feed

# Jobs

@business_bp.route('/create_job', methods=['POST'])
@jwt_required()
def create_job():

    job_title = request.form.get('job_title')
    job_description = request.form.get('job_description')
    prefer_city = request.form.get('prefer_city')
    job_type = request.form.get('job_type')

    if not job_title or not job_description or not prefer_city or not job_type:
        return jsonify({'error': 'All fields are required'}), 400

    new_job = Job(
        job_title=job_title,
        job_description=job_description,
        prefer_city=prefer_city,
        job_type=job_type,
        user_id=current_user.id
    )

    db.session.add(new_job)
    db.session.commit()

    return jsonify({'message': 'Job created successfully'}), 201

@business_bp.route('/jobs', methods=['GET'])
def get_jobs():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))

    jobs = Job.query.order_by(desc(Job.timestamp)).paginate(page=page, per_page=per_page, error_out=False)

    jobs_data = [
        {
            'id': job.id,
            'title': job.job_title,
            'description': job.job_description,
            'prefer_city': job.prefer_city,
            'job_type': job.job_type,
            'user_id': job.user_id,
            'timestamp': job.timestamp,
            'likes_count': len(job.likes),
            'comments_count': len(job.comments),
        } for job in jobs.items
    ]

    return jsonify({'jobs': jobs_data})

@business_bp.route('/like_job', methods=['POST'])
@jwt_required()
def like_job():
    job_id = request.form.get('job_id')
    job = Job.query.get(job_id)

    if not job:
        return jsonify({'error': 'Job not found'}), 404

    like = JobLike.query.filter_by(user_id=current_user.id, job_id=job_id).first()

    if like:
        db.session.delete(like)
        db.session.commit()
        return jsonify({'message': 'Job unliked successfully'})

    new_like = JobLike(user_id=current_user.id, job_id=job_id)
    db.session.add(new_like)
    db.session.commit()

    return jsonify({'message': 'Job liked successfully'})

@business_bp.route('/comment_job', methods=['POST'])
@jwt_required()
def comment_job():
    job_id = request.form.get('job_id')
    text = request.form.get('text')

    if not text:
        return jsonify({'error': 'Comment text is required'}), 400

    job = Job.query.get(job_id)

    if not job:
        return jsonify({'error': 'Job not found'}), 404

    new_comment = JobComment(text=text, user_id=current_user.id, job_id=job_id)
    db.session.add(new_comment)
    db.session.commit()

    return jsonify({'message': 'Comment added successfully'}), 201

@business_bp.route('/job_details', methods=['GET'])
@jwt_required()
def get_job_details():
    job_id = request.args.get('job_id')
    job = Job.query.get(job_id)

    if not job:
        return jsonify({'error': 'Job not found'}), 404

    like_count = db.session.query(func.count(JobLike.id)).filter_by(job_id=job.id).scalar()
    comment_count = db.session.query(func.count(JobComment.id)).filter_by(job_id=job.id).scalar()

    return jsonify({'like_count': like_count, 'comment_count': comment_count}), 200


@business_bp.route('/job_comments', methods=['GET'])
@jwt_required()
def get_job_comments():
    job_id= request.args.get('job_id')
    job= Job.query.get(job_id)

    if not job:
        return jsonify({'error': 'Job not found'}), 404

    comments = JobComment.query.filter_by(job_id=job.id).all()
    comments_data = [{'id': comment.id, 'text': comment.text, 'user_id': comment.user_id, 'timestamp': comment.timestamp} for comment in comments]

    return jsonify({'comments': comments_data})


@business_bp.route('/apply_job', methods=['POST'])
@jwt_required()
def apply_job():
    job_id = request.form.get('job_id')
    cover_letter = request.form.get('cover_letter')
    cv_file = request.files.get('cv_file')

    if not cover_letter or not cv_file:
        return jsonify({'error': 'Cover letter and CV file are required'}), 400

    job = Job.query.get(job_id)

    if not job:
        return jsonify({'error': 'Job not found'}), 404


    cv_filename = str(current_user.id)+'_'+secure_filename(cv_file.filename)
    cv_path = os.path.join(CV_FOLDER, cv_filename)
    cv_file.save(cv_path)

    new_application = JobApplication(
        user_id=current_user.id,
        job_id=job_id,
        cover_letter=cover_letter,
        cv_path=cv_path,
    )

    db.session.add(new_application)
    db.session.commit()

    return jsonify({'message': 'Job application submitted successfully'}), 201

@business_bp.route('/search_jobs', methods=['GET'])
def search_jobs():
    job_title = request.args.get('job_title')
    prefer_city = request.args.get('prefer_city')
    job_type = request.args.get('job_type')

    jobs_query = Job.query

    if job_title:
        jobs_query = jobs_query.filter(Job.job_title.ilike(f"%{job_title}%"))

    if prefer_city:
        jobs_query = jobs_query.filter(Job.prefer_city.ilike(f"%{prefer_city}%"))

    if job_type:
        jobs_query = jobs_query.filter(Job.job_type.ilike(f"%{job_type}%"))

    jobs = jobs_query.all()
    jobs_data = [
        {
            'id': job.id,
            'job_title': job.job_title,
            'job_description': job.job_description,
            'prefer_city': job.prefer_city,
            'job_type': job.job_type,
            'timestamp': job.timestamp
        }
        for job in jobs
    ]

    return jsonify({'jobs': jobs_data})

# Events

@business_bp.route('/create_event', methods=['POST'])
@jwt_required()
def create_event():

    title = request.form.get('title')
    description = request.form.get('description')
    location = request.form.get('location')
    charges = request.form.get('charges')


    if not title or not description or not location or charges is None:
        return jsonify({'error': 'All fields are required'}), 400

    new_event = Event(
        title=title,
        description=description,
        location=location,
        charges=charges,
        user_id=current_user.id,
    )

    db.session.add(new_event)
    db.session.commit()

    return jsonify({'message': 'Event created successfully'}), 201


@business_bp.route('/get_events', methods=['GET'])
def get_events():
    events = Event.query.all()
    events_data = [
        {
            'id': event.id,
            'title': event.title,
            'description': event.description,
            'location': event.location,
            'charges': event.charges,
            'user_id': event.user_id,
            'timestamp': event.timestamp,
            'likes_count': len(event.likes),
            'comments_count': len(event.comments)
        } for event in events
    ]

    return jsonify({'events': events_data})


@business_bp.route('/like_event', methods=['POST'])
@jwt_required()
def like_event():
    event_id = request.form.get('event_id')
    event = Event.query.get(event_id)

    if not event:
        return jsonify({'error': 'Event not found'}), 404

    user = current_user

    # Check if the user has already liked the event
    if any(like.user_id == user.id for like in event.likes):
        return jsonify({'error': 'You have already liked this event'}), 400

    new_like = EventLike(user_id=current_user.id, event_id=event_id)

    db.session.add(new_like)
    db.session.commit()

    return jsonify({'message': 'Event liked successfully'}), 201


@business_bp.route('/comment_event', methods=['POST'])
@jwt_required()
def comment_event():
    event_id = request.form.get('event_id')
    text = request.form.get('text')

    if not text:
        return jsonify({'error': 'Comment text is required'}), 400

    event = Event.query.get(event_id)

    if not event:
        return jsonify({'error': 'Event not found'}), 404

    new_comment = EventComment(text=text, user_id=current_user.id, event_id=event_id)
    db.session.add(new_comment)
    db.session.commit()

    return jsonify({'message': 'Comment added successfully'}), 201

@business_bp.route('/event_details', methods=['GET'])
@jwt_required()
def get_event_details():
    event_id = request.args.get('event_id')
    event = Event.query.get(event_id)

    if not event:
        return jsonify({'error': 'Job not found'}), 404

    like_count = db.session.query(func.count(EventLike.id)).filter_by(event_id=event.id).scalar()
    comment_count = db.session.query(func.count(EventComment.id)).filter_by(event_id=event.id).scalar()

    return jsonify({'like_count': like_count, 'comment_count': comment_count}), 200


@business_bp.route('/event_comments', methods=['GET'])
@jwt_required()
def get_event_comments():
    event_id= request.args.get('event_id')
    event= Event.query.get(event_id)

    if not event:
        return jsonify({'error': 'Job not found'}), 404

    comments = EventComment.query.filter_by(event_id=event.id).all()
    comments_data = [{'id': comment.id, 'text': comment.text, 'user_id': comment.user_id, 'timestamp': comment.timestamp} for comment in comments]

    return jsonify({'comments': comments_data})

@business_bp.route('/search_events', methods=['GET'])
@jwt_required()
def search_events():
    title = request.args.get('event_title')
    location = request.args.get('location')

    event_query = Event.query

    if title:
        event_query = event_query.filter(Event.title.ilike(f"%{title}%"))

    if location:
        event_query = event_query.filter(Event.location.ilike(f"%{location}%"))

    events = event_query.all()

    events_data = [
        {
            'id': event.id,
            'event_title': event.title,
            'event_description': event.description,
            'prefer_city': event.location,
            'timestamp': event.timestamp
        }
        for event in events
    ]

    return jsonify({'jobs': events_data})

@business_bp.route('/events', methods=['GET'])
@jwt_required()
def get_all_events():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))

    events = Event.query.order_by(desc(Event.timestamp)).paginate(page=page, per_page=per_page, error_out=False)

    events_data = [
        {
            'id': event.id,
            'title': event.title,
            'description': event.description,
            'location': event.location,
            'charges': event.charges,
            'user_id': event.user_id,
            'timestamp': event.timestamp,
            'likes_count': len(event.likes),
            'comments_count': len(event.comments),
        }
        for event in events.items
    ]

    return jsonify({'events': events_data})


@business_bp.route('/add_experience', methods=['POST'])
@jwt_required()
def add_experience():
    position = request.form.get('position')
    company = request.form.get('company')
    description = request.form.get('description')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')

    if start_date:
        try:
            datetime.strptime(start_date, '%Y-%m-%d')
        except ValueError:
            return jsonify(message="Incorrect date format, should be YYYY-MM-DD", category="error", status=400)

    if not position or not company or not description or not start_date or not end_date:
        return jsonify({'error': 'All fields are required'}), 400

    new_experience = UserExperience(
        user_id=current_user.id,
        position=position,
        company=company,
        description=description,
        start_date=start_date,
        end_date=end_date
    )

    db.session.add(new_experience)
    db.session.commit()

    return jsonify({'message': 'Experience added successfully'})

@business_bp.route('/get_experience', methods=['GET'])
@jwt_required()
def get_experience():
    experience = UserExperience.query.filter_by(user_id=current_user.id).all()

    if not experience:
        return jsonify({'error': 'No experience found'}), 404

    experience_data = []
    for exp in experience:
        exp_data = {
            'id': exp.id,
            'position': exp.position,
            'company': exp.company,
            'description': exp.description,
            'start_date': exp.start_date,
            'end_date': exp.end_date
        }

        experience_data.append(exp_data)

    return jsonify({'experience': experience_data}), 200


@business_bp.route('/edit_experience', methods=['POST'])
@jwt_required()
def edit_experience():
    position = request.form.get('position')
    company = request.form.get('company')
    description = request.form.get('description')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    experience_id = request.form.get('experience_id')

    if not position or not company or not description or not start_date or not end_date or not experience_id:
        return jsonify({'error': 'All fields are required'}), 400

    user_experience = UserExperience.query.filter_by(user_id=current_user.id, id=experience_id).first()

    if not user_experience:
        return jsonify({'error': 'Experience not found'}), 404

    user_experience.position = position
    user_experience.company = company
    user_experience.description = description
    user_experience.start_date = start_date
    user_experience.end_date = end_date

    db.session.commit()

    return jsonify({'message': 'Experience updated successfully'})

@business_bp.route('/delete_experience', methods=['DELETE'])
@jwt_required()
def delete_experience():
    experience_id = request.form.get('experience_id')
    if not experience_id:
        return jsonify({'error': 'Experience ID is required'}), 400

    user_experience = UserExperience.query.filter_by(user_id=current_user.id,id=experience_id).first()

    if not user_experience:
        return jsonify({'error': 'Experience not found'}), 404

    db.session.delete(user_experience)
    db.session.commit()

    return jsonify({'message': 'Experience deleted successfully'})

@business_bp.route('/add_portfolio', methods=['POST'])
@jwt_required()
def add_portfolio():

    title = request.form.get('title')
    link = request.form.get('link')

    if not title or not link:
        return jsonify({'error': 'All fields are required'}), 400

    new_portfolio = UserPortfolio(
        user_id=current_user.id,
        title=title,
        link=link
    )

    db.session.add(new_portfolio)
    db.session.commit()

    return jsonify({'message': 'Portfolio added successfully'})

@business_bp.route('/get_experience', methods=['GET'])
@jwt_required()
def get_portfolio():
    portfolio = UserPortfolio.query.filter_by(user_id=current_user.id).all()

    if not portfolio:
        return jsonify({'error': 'No portfolio found'}), 404

    experience_data = []
    for exp in portfolio:
        exp_data = {
            'id': exp.id,
            'title': exp.title,
            'link': exp.link,

        }

        experience_data.append(exp_data)

    return jsonify({'portfolio': experience_data}), 200

@business_bp.route('/edit_portfolio', methods=['POST'])
@jwt_required()
def edit_portfolio():
    title = request.form.get('title')
    link = request.form.get('link')
    portfolio_id = request.form.get('portfolio_id')

    user_portfolio = UserPortfolio.query.filter_by(user_id=current_user.id, id=portfolio_id).first()

    if not user_portfolio:
        return jsonify({'error': 'Portfolio not found'}), 404

    user_portfolio.title = title
    user_portfolio.link = link

    db.session.commit()

    return jsonify({'message': 'Portfolio updated successfully'})

@business_bp.route('/delete_portfolio', methods=['DELETE'])
@jwt_required()
def delete_portfolio():
    portfolio_id = request.form.get('portfolio_id')
    user_portfolio = UserPortfolio.query.filter_by(user_id=current_user.id, id=portfolio_id).first()

    if not user_portfolio:
        return jsonify({'error': 'Portfolio not found'}), 404

    db.session.delete(user_portfolio)
    db.session.commit()

    return jsonify({'message': 'Portfolio deleted successfully'})

@business_bp.route('/edit_about', methods=['POST'])
@jwt_required()
def edit_about():
    about = request.form.get('about')
    if not about:
        return jsonify({'error': 'All fields are required'}), 400
    user_about = User.query.filter_by(id=current_user.id).first()
    user_about.about = about
    db.session.commit()
    return jsonify({'message': 'About updated successfully'})

@business_bp.route('/get_about', methods=['GET'])
@jwt_required()
def get_about():
    user_about = User.query.filter_by(id=current_user.id).first()
    return jsonify({'about': user_about.about})
