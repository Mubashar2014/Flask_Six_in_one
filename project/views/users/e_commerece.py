import base64
from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, current_user

from project.extensions.extensions import db
from project.models.users import User, Product, Favourite

e_commerce_bp = Blueprint('e_commerce', __name__)


@e_commerce_bp.route('/add_product', methods=['POST'])
@jwt_required()
def add_product():
    seller = User.query.get(current_user.id)
    image = request.files.get('image')
    name = request.form.get('name')
    description = request.form.get('description')
    price = (request.form.get('price'))
    condition = request.form.get('condition')



    if not image or not name or not description or not price or not condition:
        return jsonify({'error': 'All fields are required'}), 400

    image_data = image.read()

    new_product = Product(image=image_data, name=name, description=description, price=price, seller=seller, condition=condition)
    db.session.add(new_product)
    db.session.commit()

    return jsonify({'message': 'Product added successfully'})



@e_commerce_bp.route('/get_products_by_seller', methods=['GET'])
@jwt_required()
def get_products_by_seller():

    products = Product.query.filter_by(seller_id=current_user.id).all()
    products_data = []

    for product in products:
        product_data = {
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': product.price,
            'seller_id': product.seller_id,
            'condition': product.condition
        }

        if product.image:
            product_data['image'] = base64.b64encode(product.image).decode('utf-8')

        products_data.append(product_data)

    return jsonify({'products': products_data})



@e_commerce_bp.route('/add_to_favourites', methods=['POST'])
@jwt_required()
def add_to_favourites():
    product_id = request.form.get('product_id')

    favourite = Favourite.query.filter_by(buyer_id=current_user.id, product_id=product_id).first()

    if favourite:
        return jsonify({'error': 'Product is already in favourites'}), 400

    new_favourite = Favourite(buyer_id=current_user.id, product_id=product_id)
    db.session.add(new_favourite)
    db.session.commit()

    return jsonify({'message': 'Product added to favourites'})


@e_commerce_bp.route('/get_favourites', methods=['GET'])
@jwt_required()
def get_favourites():


    favourites = Favourite.query.filter_by(buyer_id=current_user.id).all()
    favourites_data = []

    for favourite in favourites:
        product = Product.query.get(favourite.product_id)

        if product:
            product_data = {
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': product.price,
                'seller_id': product.seller_id,
                'condition': product.condition
            }

            if product.image:
                product_data['image'] = base64.b64encode(product.image).decode('utf-8')

            favourites_data.append({'id': favourite.id, 'product': product_data})

    return jsonify({'favourites': favourites_data})


@e_commerce_bp.route('/edit_product', methods=['PUT'])
@jwt_required()
def edit_product():

    product_id = request.form.get('product_id')
    product = Product.query.filter_by(id=product_id, seller_id=current_user.id).first()

    if not product:
        return jsonify({'error': 'Product not found or you do not have permission to edit it'}), 404

    image = request.files.get('image')
    name = request.form.get('name')
    description = request.form.get('description')
    price = request.form.get('price')
    condition = request.form.get('condition')

    if not name or not description or not price or not condition:
        return jsonify({'error': 'All fields are required'}), 400

    if image:
        image_data = image.read()
        product.image = image_data

    product.name = name
    product.description = description
    product.price = price
    product.condition = condition

    db.session.commit()

    return jsonify({'message': 'Product updated successfully'})


@e_commerce_bp.route('/delete_product', methods=['DELETE'])
@jwt_required()
def delete_product():
    product_id = request.form.get('product_id')
    product = Product.query.filter_by(id=product_id, seller_id=current_user.id).first()

    if not product:
        return jsonify({'error': 'Product not found or you do not have permission to delete it'}), 404

    db.session.delete(product)
    db.session.commit()

    return jsonify({'message': 'Product deleted successfully'})


@e_commerce_bp.route('/search_products', methods=['GET'])
def search_products():
    name_filter = request.args.get('name')
    condition_filter = request.args.get('condition')
    min_price = float(request.args.get('min_price', 0))
    max_price = float(request.args.get('max_price', float('inf')))
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        except ValueError:
            return jsonify(message="Incorrect data format, should be YYYY-MM-DD", category="error", status=400)

    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            return jsonify(message="Incorrect data format, should be YYYY-MM-DD", category="error", status=400)


    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))

    query = Product.query

    if name_filter:
        query = query.filter(Product.name.ilike(f'%{name_filter}%'))

    if condition_filter:
        query = query.filter_by(condition=condition_filter)

    if min_price is not None:
        query = query.filter(Product.price >= min_price)

    if max_price is not None and max_price != float('inf'):
        query = query.filter(Product.price <= max_price)

    if start_date:
        query = query.filter(Product.created_at >= start_date)

    if end_date:
        query = query.filter(Product.created_at <= end_date)

    products = query.paginate(page=page, per_page=per_page, error_out=False)

    products_data = [
        {
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': product.price,
            'seller_id': product.seller_id,
            'condition': product.condition,
            'timestamp': product.created_at.isoformat(),
            'image': base64.b64encode(product.image).decode('utf-8') if product.image else None
        }
        for product in products.items
    ]

    pagination_data = {
        'page': products.page,
        'per_page': products.per_page,
        'total_pages': products.pages,
        'total_items': products.total
    }

    return jsonify({'products': products_data, 'pagination': pagination_data})