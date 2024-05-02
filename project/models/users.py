import datetime

from sqlalchemy.orm import relationship

from project.extensions.extensions import db


# Users table containing user's authentication details
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    full_name = db.Column(db.String(400))
    email = db.Column(db.String(300), nullable=False)
    password = db.Column(db.String(300), default=None)
    user_type = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime(), nullable=False, default=datetime.datetime.now())
    status = db.Column(db.Boolean, default=False)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)
    recovery = db.Column(db.Integer)
    recovery_created_at = db.Column(db.DateTime())
    oauth_id = db.Column(db.Text(), default=None)
    login_type = db.Column(db.String(300))
    verification_token = db.Column(db.String(700))
    email_counter = db.Column(db.Integer, default=0)
    email_validation_date = db.Column(db.DateTime())
    login_through = db.Column(db.String(700))
    ratings = db.Column(db.Boolean, default=False)
    posts = db.relationship('Post', backref='user', lazy=True)
    feed = db.relationship('Feed', backref='user', lazy=True)
    about = db.Column(db.Text)
    followers = db.relationship('Follow', foreign_keys='Follow.followed_id', backref='followed', lazy='dynamic')
    followings = db.relationship('Follow', foreign_keys='Follow.follower_id', backref='follower', lazy='dynamic')
    likes = db.relationship('Like', backref='user', lazy=True)

class UserExperience(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    position = db.Column(db.String(300))
    company = db.Column(db.String(300))
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.String(300), default="Present")

class UserPortfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(300))
    link = db.Column(db.String(300))

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comments = db.relationship('Comment', backref='post', lazy=True)
    likes = db.relationship('Like', backref='post', lazy=True)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now(), nullable=False)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now(), nullable=False)

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now(), nullable=False)

class Follow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    followed_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now(), nullable=False)




class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.LargeBinary, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.String(255), nullable=False)
    condition = db.Column(db.String(255), nullable="")
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    seller = db.relationship('User', backref='products', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now(), nullable=False)

class Favourite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now(), nullable=False)

# Users Bio information details Table
# weight should be in lbs and height should be in feet and inches
class UsersAdditionalInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    followers = db.Column(db.Integer)
    following = db.Column(db.Integer)
    posts = db.Column(db.Integer, default=0)


# Business Module
class Feed(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    image = db.Column(db.LargeBinary, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now(), nullable=False)
    pinned = db.Column(db.Boolean, default=False)
    likes = relationship('Like_feed' , primaryjoin='Feed.id == Like_feed.feed_id')
    comments = relationship('Comment_feed', primaryjoin='Feed.id == Comment_feed.feed_id')


class Like_feed(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    feed_id = db.Column(db.Integer, db.ForeignKey('feed.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now(), nullable=False)

class Comment_feed(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    feed_id = db.Column(db.Integer, db.ForeignKey('feed.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now(), nullable=False)



# Job Module

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_title = db.Column(db.String(255), nullable=False)
    job_description = db.Column(db.Text, nullable=False)
    prefer_city = db.Column(db.String(100), nullable=False)
    job_type = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    likes = db.relationship('JobLike', backref='job', lazy=True)
    comments = db.relationship('JobComment', backref='job', lazy=True)
    applications = db.relationship('JobApplication', backref='job', lazy=True)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now(), nullable=False)

class JobLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now(), nullable=False)

class JobComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now(), nullable=False)

class JobApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    cover_letter = db.Column(db.Text, nullable=False)
    cv_path = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now(), nullable=False)

# Events

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(255), nullable=False)
    charges = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now(), nullable=False)
    comments = db.relationship('EventComment', backref='event', lazy=True)
    likes = db.relationship('EventLike', backref='event', lazy=True)

class EventComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now(), nullable=False)

class EventLike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now(), nullable=False)


# advertisement

class Ad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    media_link = db.Column(db.String(255), nullable=True)
    age_from = db.Column(db.Integer, nullable=False)
    age_to = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime)

class AdClick(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ad_id = db.Column(db.Integer, db.ForeignKey('ad.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now(), nullable=False)

class UserNotifications(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))

    breakfast_notifications = db.Column(db.String(500), default=None)
    breakfast_notification_status = db.Column(db.Boolean, default=False)

    lunch_notifications = db.Column(db.String(500), default=None)
    lunch_notification_status = db.Column(db.Boolean, default=False)

    dinner_notifications = db.Column(db.String(500), default=None)
    dinner_notification_status = db.Column(db.Boolean, default=False)

    noon_notifications = db.Column(db.String(500), default=None)
    noon_notification_status = db.Column(db.Boolean, default=False)

    afternoon_notifications = db.Column(db.String(500), default=None)
    afternoon_notification_status = db.Column(db.Boolean, default=False)

    evening_notifications = db.Column(db.String(500), default=None)
    evening_notification_status = db.Column(db.Boolean, default=False)

    device_token = db.Column(db.String(600), default=None)


# User's Custom Notifications Table
class UserCustomNotifications(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))

    custom_notification_name = db.Column(db.String(500), default=None)
    custom_notification_time = db.Column(db.String(500), default=None)
    custom_notification_status = db.Column(db.Boolean, default=False)

    device_token = db.Column(db.String(600), default=None)

class VersionChecker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    android_latest_version = db.Column(db.String(500), default=None)
    android_latest_priority = db.Column(db.Boolean, default=False)
    android_previous_version = db.Column(db.String(500), default=None)
    android_previous_priority = db.Column(db.Boolean, default=False)
    ios_latest_version = db.Column(db.String(500), default=None)
    ios_latest_priority = db.Column(db.Boolean, default=False)
    ios_previous_version = db.Column(db.String(500), default=None)
    ios_previous_priority = db.Column(db.Boolean, default=False)


