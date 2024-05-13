import os
import uuid
from datetime import datetime

from flasgger import swag_from
from flask import Blueprint, request, jsonify, render_template
from flask_jwt_extended import jwt_required, current_user
from werkzeug.utils import secure_filename

from project.extensions.extensions import socketio
from project.config import ALLOWED_EXTENSIONS
from project.extensions.extensions import db
from project.models.users import User, Post, Follow, Comment, Like
import boto3
from botocore.exceptions import NoCredentialsError
import os

social_media_blueprint = Blueprint('social_media', __name__)




s3 = boto3.client('s3', aws_access_key_id='AKIAQ3EGSPOPKKCGD2HR', aws_secret_access_key='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')

@social_media_blueprint.route('/create_post', methods=['POST'])
@jwt_required()
@swag_from('swagger/create_post.yml')  # Add this line to specify the Swagger YAML file
def create_post():
    try:
        image_file = request.files.get('image')
        description = request.form.get('description')
        timestamp = request.form.get('timestamp')

        if not image_file or not description or not timestamp:
            return jsonify({'error': 'Image, date, and description are required'}), 400

        timestamp = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%f')

        if image_file and allowed_file(image_file.filename):
            try:
                s3.upload_fileobj(image_file, 'flask6in1', image_file.filename)
                image_url = f"https://flask6in1.s3.amazonaws.com/{image_file.filename}"


                new_post = Post(image=image_url, description=description, user_id=current_user.id, timestamp=timestamp)

                db.session.add(new_post)
                db.session.commit()

                socketio.emit('New post', {'user_id': current_user.id}, namespace='/social_media')
                return jsonify({'message': 'Post created successfully', 'category': 'success', 'status': 200})
            except NoCredentialsError:
                return jsonify({'error': 'Credentials not available', 'category': 'error', 'status': 400})
        else:
            return jsonify(
                {'error': 'Invalid file type, allowed types are: png, jpg, jpeg, gif', 'category': 'error',
                 'status': 400})

    except Exception as e:
        return jsonify({'error': str(e), 'category': 'error', 'status': 400})



def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@social_media_blueprint.route('/get_all_posts', methods=['GET'])
@jwt_required()
def get_posts():
    try:
        posts = Post.query.all()

        if not posts:
            return jsonify({'error': 'No posts found'}), 404

        posts_data = []
        for post in posts:
            followers_query = Follow.query.filter_by(followed_id=post.user_id)
            followers_count = followers_query.count()
            followings_query = Follow.query.filter_by(follower_id=post.user_id)
            followings_count = followings_query.count()

            comment = Comment.query.filter_by(post_id=post.id).order_by(Comment.timestamp.desc()).first()

            like_count = Like.query.filter_by(post_id=post.id).count()
            comments_count = Comment.query.filter_by(post_id=post.id).count()

            if not comment:
                text = None
                comment_id = None
                timestamp = None
                user_id = None

                if text is None and comment_id and timestamp and user_id is None:
                    last_comment = None
                else:
                    last_comment = {
                        "comment_id": comment_id,
                        "comment": text,
                        "timestamp": timestamp,
                        "user_id": user_id
                    }
            else:
                text = comment.text
                comment_id = comment.id
                timestamp = comment.timestamp
                user_id = comment.user_id

                last_comment = {
                    "comment_id": comment_id,
                    "comment": text,
                    "timestamp": timestamp,
                    "user_id": user_id
                }

            post_data = {
                "post_object": {
                    'post_id': post.id,
                    'image': post.image,
                    'description': post.description,
                    'timestamp': post.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    "like_count": like_count,
                    "comments_count": comments_count,
                    "Latest_comment": last_comment,
                },

                'user_object': {
                    'user_id': post.user.id,
                    "followers_count": followers_count,
                    "followings_count": followings_count,
                    "username": post.user.full_name,
                    "profile_pic": post.user.photo,
                    "facebook_id": "",
                    "instagram_id": "",
                    "tiktok_id": "",
                    "youtube_id ": "",

                },

            }
            posts_data.append(post_data)

        socketio.emit('get_posts', {'user_id': current_user.id}, namespace='/social_media')
        return jsonify({'posts': posts_data}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 404


@social_media_blueprint.route('/get_post', methods=['GET'])
@jwt_required()
def get_post():
    post_id = request.args.get('post_id')
    post = Post.query.filter_by(id=post_id).first()
    if not post:
        return jsonify({'error': 'Post not found'}), 404

    followers_query = Follow.query.filter_by(followed_id=post.user_id)
    followers_count = followers_query.count()
    followings_query = Follow.query.filter_by(follower_id=post.user_id)
    followings_count = followings_query.count()

    comment = Comment.query.filter_by(post_id=post.id).order_by(Comment.timestamp.desc()).first()

    like_count = Like.query.filter_by(post_id=post.id).count()
    comments_count = Comment.query.filter_by(post_id=post.id).count()

    if not comment:
        text = None
        comment_id = None
        timestamp = None
        user_id = None
    else:
        text = comment.text
        comment_id = comment.id
        timestamp = comment.timestamp
        user_id = comment.user_id

    post_data = {
        "post_object": {
            'post_id': post.id,
            'image': post.image,
            'description': post.description,
            'timestamp': post.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            "like_count": like_count,
            "comments_count": comments_count,
            "Latest_comment": {
                "comment_id": comment_id,
                "comment": text,
                "timestamp": timestamp,
                "user_id": user_id
            },
        },

        'user_object': {
            'user_id': post.user.id,
            "followers_count": followers_count,
            "followings_count": followings_count,
            "username": post.user.full_name,
            "profile_pic": post.user.photo,
            "facebook_id": "",
            "instagram_id": "",
            "tiktok_id": "",
            "youtube_id ": "",

        },

    }

    return jsonify({'post': post_data}), 200


@social_media_blueprint.route('/delete_post', methods=['DELETE'])
@jwt_required()
def delete_post():
    post_id = request.form.get('post_id')
    post = Post.query.filter_by(id=post_id, user_id=current_user.id).first()

    if not post:
        return jsonify({'error': 'Post not found or you do not have permission to delete it'}), 404

    try:
        db.session.delete(post)
        db.session.commit()
        socketio.emit('Post Deleted', {'user_id': current_user.id}, namespace='/social_media')
        return jsonify({'message': 'Post deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@social_media_blueprint.route('/edit_post', methods=['PUT'])
@jwt_required()
def edit_post():
    post_id = request.form.get('post_id')
    new_description = request.form.get('description')
    image_file = request.files.get('image')

    post = Post.query.filter_by(id=post_id, user_id=current_user.id).first()

    if not post:
        return jsonify({'error': 'Post not found or you do not have permission to edit it'}), 404

        # Get new data from the request

    if not new_description and not image_file:
        return jsonify({'error': 'Description or image is required for editing'}), 400

    if new_description:
        post.description = new_description

    if image_file and allowed_file(image_file.filename):
        filename = secure_filename(image_file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower()
        unique_filename = str(uuid.uuid4()) + '.' + file_ext
        filepath = os.path.join('project/media/posts', unique_filename)
        image_file.save(filepath)
        image_data = filepath
        post.image = image_data

    post.timestamp = datetime.now()
    db.session.commit()
    socketio.emit('Post Edited', {'user_id': current_user.id}, namespace='/social_media')
    return jsonify({'message': 'Post edited successfully'})


@social_media_blueprint.route('/follow', methods=['POST'])
@jwt_required()
def follow_user():
    user_id = request.form.get('user_id')

    if current_user.id == user_id:
        return jsonify({'error': 'Cannot follow yourself'}), 400

    user_to_follow = User.query.get(user_id)

    if not user_to_follow:
        return jsonify({'error': 'User not found'}), 404

    existing_follow = Follow.query.filter_by(follower_id=current_user.id, followed_id=user_id).first()

    if existing_follow:
        db.session.delete(existing_follow)
        db.session.commit()
        socketio.emit('follow_count_updated', {'user_id': current_user.id}, namespace='/social_media')
        return jsonify({'message': f'You have unfollowed {user_to_follow.full_name}'}), 200

    new_follow = Follow(follower_id=current_user.id, followed_id=user_id, timestamp=datetime.now())
    db.session.add(new_follow)
    db.session.commit()
    socketio.emit('follow_count_updated', {'user_id': current_user.id}, namespace='/social_media')
    return jsonify({'message': f'You are now following {user_to_follow.full_name}'}), 200


@social_media_blueprint.route('/unfollow', methods=['POST'])
@jwt_required()
def unfollow_user():
    user_id = request.args.get('user_id')

    if current_user.id == user_id:
        return jsonify({'error': 'Cannot unfollow yourself'}), 400

    user_to_unfollow = User.query.get(user_id)

    if not user_to_unfollow:
        return jsonify({'error': 'User not found'}), 404

    follow = Follow.query.filter_by(follower_id=current_user.id, followed_id=user_id).first()

    if not follow:
        return jsonify({'error': 'You are not following this user'}), 400

    db.session.delete(follow)
    db.session.commit()

    return jsonify({'message': f'You have unfollowed {user_to_unfollow.full_name}'})


@social_media_blueprint.route('/followers', methods=['GET'])
@jwt_required()
def get_followers():
    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400

    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    followers_query = Follow.query.filter_by(followed_id=user_id)
    followers_count = followers_query.count()

    followers = followers_query.all()
    followers_data = [{'id': follower.follower.id, 'full_name': follower.follower.full_name} for follower in followers]

    socketio.emit('followers_count_updated', {'user_id': user_id, 'followers_count': followers_count},
                  namespace='/social_media')

    return jsonify({'followers': followers_data, 'followers_count': followers_count})


@social_media_blueprint.route('/followings', methods=['GET'])
@jwt_required()
def get_followings():
    user_id = request.args.get('user_id')
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    followings_query = Follow.query.filter_by(follower_id=user_id)
    followings_count = followings_query.count()

    followings = followings_query.all()
    followings_data = [{'id': following.followed.id, 'full_name': following.followed.full_name} for following in
                       followings]
    socketio.emit('followings_count_updated', {'user_id': user_id, 'followings_count': followings_count},
                  namespace='/social_media')
    return jsonify({'followings': followings_data, 'followings_count': followings_count})


@social_media_blueprint.route('/create_comment', methods=['POST'])
@jwt_required()
def create_comment():
    post_id = request.form.get('post_id')
    post = Post.query.get(post_id)
    timestamp = request.form.get('timestamp')

    if not timestamp:
        return jsonify({'error': 'Timestamp is required'}), 400

    timestamp = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%f')

    if not post:
        return jsonify({'error': 'Post not found'}), 404

    text = request.form.get('text')

    if not text:
        return jsonify({'error': 'Comment text is required'}), 400

    new_comment = Comment(text=text, user_id=current_user.id, post_id=post_id, timestamp=timestamp)
    db.session.add(new_comment)
    db.session.commit()

    return jsonify({'message': 'Comment created successfully'})


@social_media_blueprint.route('/get_comments', methods=['GET'])
@jwt_required()
def get_comments():
    post_id = request.args.get('post_id')
    post = Post.query.get(post_id)

    if not post:
        return jsonify({'error': 'Post not found'}), 404

    comments_query = Comment.query.filter_by(post_id=post_id)
    comments_count = comments_query.count()

    comments = comments_query.all()

    comments_data = []

    for comment in comments:
        followers_query = Follow.query.filter_by(followed_id=post.user_id)
        followers_count = followers_query.count()
        followings_query = Follow.query.filter_by(follower_id=post.user_id)
        followings_count = followings_query.count()

        comment_data = {
            'comment_object': {
                'comment_id': comment.id,
                'username': post.user.full_name,
                'photo': post.user.photo,
                'text': comment.text,
                'user_id': comment.user_id,
                'timestamp': comment.timestamp
            },
            'user_object': {
                'user_id': comment.user_id,
                "followers_count": followers_count,
                "followings_count": followings_count,
                "username": post.user.full_name,
                "profile_pic": post.user.photo,
                "facebook_id": "",
                "instagram_id": "",
                "tiktok_id": "",
                "youtube_id ": "",

            },
        }
        comments_data.append(comment_data)

    socketio.emit('comment_count_updated', {'user_id': current_user.id, 'comments_count': comments_count},
                  namespace='/social_media')
    return jsonify({'comments': comments_data, 'comments_count': comments_count})


@social_media_blueprint.route('/update_comment', methods=['PUT'])
@jwt_required()
def update_comment():
    comment_id = request.args.get('comment_id')
    comment = Comment.query.get(comment_id)

    if not comment:
        return jsonify({'error': 'Comment not found'}), 404

    if comment.user_id != current_user.id:
        return jsonify({'error': 'You do not have permission to update this comment'}), 403

    new_text = request.form.get('text')

    if not new_text:
        return jsonify({'error': 'Comment text is required'}), 400

    comment.text = new_text
    db.session.commit()

    return jsonify({'message': 'Comment updated successfully'})


@social_media_blueprint.route('/delete_comment', methods=['DELETE'])
@jwt_required()
def delete_comment():
    comment_id = request.args.get('comment_id')
    comment = Comment.query.get(comment_id)

    if not comment:
        return jsonify({'error': 'Comment not found'}), 404

    if comment.user_id != current_user.id:
        return jsonify({'error': 'You do not have permission to delete this comment'}), 403

    db.session.delete(comment)
    db.session.commit()

    return jsonify({'message': 'Comment deleted successfully'})


@social_media_blueprint.route('/like_post', methods=['POST'])
@jwt_required()
def like_post():
    post_id = request.form.get('post_id')

    post = Post.query.get(post_id)

    if not post:
        return jsonify({'error': 'Post not found'}), 404

    existing_like = Like.query.filter_by(user_id=current_user.id, post_id=post_id).first()

    if existing_like:
        db.session.delete(existing_like)
        db.session.commit()
        socketio.emit('like_count_updated', {'user_id': current_user.id}, namespace='/social_media')
        return jsonify({'message': 'Post unliked successfully'})

    new_like = Like(user_id=current_user.id, post_id=post_id, timestamp=datetime.now())
    db.session.add(new_like)
    db.session.commit()
    socketio.emit('like_count_updated', {'user_id': current_user.id}, namespace='/social_media')
    return jsonify({'message': 'Post liked successfully'})


@social_media_blueprint.route('/unlike_post', methods=['POST'])
@jwt_required()
def unlike_post():
    post_id = request.form.get('post_id')
    post = Post.query.get(post_id)

    if not post:
        return jsonify({'error': 'Post not found'}), 404

    like = Like.query.filter_by(user_id=current_user.id, post_id=post_id).first()

    if not like:
        return jsonify({'error': 'You have not liked this post'}), 400

    db.session.delete(like)
    db.session.commit()

    return jsonify({'message': 'Post unliked successfully'})


@social_media_blueprint.route('/get_likes', methods=['GET'])
def get_likes():
    post_id = request.args.get('post_id')
    post = Post.query.get(post_id)

    if not post:
        return jsonify({'error': 'Post not found'}), 404

    likes_count = Like.query.filter_by(post_id=post_id).count()
    socketio.emit('likes_count_updated', {'post_id': post_id, 'likes_count': likes_count}, namespace='/social_media')
    return jsonify({'likes_count': likes_count})


@social_media_blueprint.route('/otherUserPosts', methods=['GET'])
@jwt_required()
def otherUserPosts():
    user_id = request.args.get('user_id')
    posts = Post.query.filter_by(user_id=user_id).all()

    if not posts:
        return jsonify({'error': 'No posts found'}), 404

    posts_data = []
    for post in posts:
        followers_query = Follow.query.filter_by(followed_id=post.user_id)
        followers_count = followers_query.count()
        followings_query = Follow.query.filter_by(follower_id=post.user_id)
        followings_count = followings_query.count()

        comment = Comment.query.filter_by(post_id=post.id).order_by(Comment.timestamp.desc()).first()

        like_count = Like.query.filter_by(post_id=post.id).count()
        comments_count = Comment.query.filter_by(post_id=post.id).count()

        if not comment:
            text = None
            comment_id = None
            timestamp = None
            user_id = None

            if text is None and comment_id and timestamp and user_id is None:
                last_comment = None
            else:
                last_comment = {
                    "comment_id": comment_id,
                    "comment": text,
                    "timestamp": timestamp,
                    "user_id": user_id
                }
        else:
            text = comment.text
            comment_id = comment.id
            timestamp = comment.timestamp
            user_id = comment.user_id

            last_comment = {
                "comment_id": comment_id,
                "comment": text,
                "timestamp": timestamp,
                "user_id": user_id
            }

        post_data = {
            "post_object": {
                'post_id': post.id,
                'image': post.image,
                'description': post.description,
                'timestamp': post.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                "like_count": like_count,
                "comments_count": comments_count,
                "Latest_comment": last_comment,
            },

            'user_object': {
                'user_id': post.user.id,
                "followers_count": followers_count,
                "followings_count": followings_count,
                "username": post.user.full_name,
                "profile_pic": post.user.photo,
                "facebook_id": "",
                "instagram_id": "",
                "tiktok_id": "",
                "youtube_id ": "",

            },

        }
        posts_data.append(post_data)

    socketio.emit('get_other_user_posts', {'user_id': current_user.id}, namespace='/social_media')
    return jsonify({'posts': posts_data}), 200



