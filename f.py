import base64
import uuid
from PIL import Image
import io
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
import jwt
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Jennicson1@localhost/abi'  # Update with your PostgreSQL database URI
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Change this to a secure random key
app.config['JWT_EXPIRATION_DELTA'] = timedelta(seconds=3600)  # Token expires in 1 hour
db = SQLAlchemy(app)
def convert_image_to_jpeg_base64(image_data):
    # Load image from binary data
    image = Image.open(io.BytesIO(image_data))

    # Create a BytesIO object to store the JPEG image data
    jpeg_buffer = io.BytesIO()

    # Convert the image to JPEG format and save it to the BytesIO object
    image.convert("RGB").save(jpeg_buffer, format="JPEG")

    # Get the JPEG image data as bytes
    jpeg_data = jpeg_buffer.getvalue()

    # Encode the JPEG data as base64
    jpeg_base64 = base64.b64encode(jpeg_data).decode('utf-8')

    return jpeg_base64


class Userdatas(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String, nullable=False)
    mobile = db.Column(db.String, unique=True, nullable=False)
    address = db.Column(db.String, nullable=False)

    def __repr__(self):
        return '<User %r>' % self.email

    @classmethod
    def find_by_email(cls, email):
        return cls.query.filter_by(email=email).first()

@app.route('/signup', methods=['POST'])
def signup():
    if request.method == 'POST':
        data = request.json
        email = data.get('email')
        password = data.get('password')
        first_name = data.get('firstName')
        last_name = data.get('lastName')
        mobile = data.get('mobile')
        address = data.get('address')
        user = Userdatas(email=email, password=generate_password_hash(password), first_name=first_name, last_name=last_name, mobile=mobile, address=address)
        db.session.add(user)
        db.session.commit()
        return jsonify({'message': 'User created successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        data = request.json
        email = data.get('email')
        password = data.get('password')

        user = Userdatas.find_by_email(email)
        if user and check_password_hash(user.password, password):
            token = jwt.encode({'email': email, 'exp': datetime.utcnow() + timedelta(seconds=3600)}, app.config['SECRET_KEY'])
            return jsonify({'token':token,'id':user.id})
        else:
            return jsonify({'message': 'Invalid email or password'}), 401

class Restaurantdatas(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    mobile = db.Column(db.String, unique=True, nullable=False)
    address = db.Column(db.String, nullable=False)

    def __repr__(self):
        return '<Restaurant %r>' % self.name

    @classmethod
    def find_by_email(cls, email):
        return cls.query.filter_by(email=email).first()

    @classmethod
    def find_by_name(cls, name):
        return cls.query.filter_by(name=name).first()

@app.route('/restaurant/signup', methods=['POST'])
def restaurant_signup():
    if request.method == 'POST':
        data = request.json
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        mobile = data.get('mobile')
        address = data.get('address')
        # Add more attributes as needed
        restaurant = Restaurantdatas(name=name, email=email, password=generate_password_hash(password), mobile=mobile, address=address)
        db.session.add(restaurant)
        db.session.commit()
        return jsonify({'message': 'Restaurant created successfully'}), 201

@app.route('/restaurant/login', methods=['POST'])
def restaurant_login():
    if request.method == 'POST':
        data = request.json
        email = data.get('email')
        password = data.get('password')

        restaurant = Restaurantdatas.find_by_email(email)
        if restaurant and check_password_hash(restaurant.password, password):
            token = jwt.encode({'email': email, 'exp': datetime.utcnow() + timedelta(seconds=3600)}, app.config['SECRET_KEY'])
            return jsonify({'token': token, 'id': restaurant.id})
        else:
            return jsonify({'message': 'Invalid email or password'}), 401

# Add more routes and functionalities for restaurant authentication and management as needed
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String, nullable=False)
    restaurant_name = db.Column(db.String, nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurantdatas.id'), nullable=False)
    ratingid = db.Column(db.String, unique=True, nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String, nullable=False)

    # Define relationship with Restaurantdatas
    restaurant = db.relationship('Restaurantdatas', backref=db.backref('products', lazy=True))
    def __repr__(self):
        return '<Product %r>' % self.product_name

@event.listens_for(Product, 'before_insert')
def generate_ratingid(mapper, connection, target):
    target.ratingid = str(uuid.uuid4())  # Generate a UUID for rating ID
  # Generate a UUID for rating ID
@app.route('/product/add', methods=['POST'])
def add_product():
    if request.method == 'POST':
        data = request.form
        product_name = data.get('productName')
        restaurant_name = data.get('restaurantName')
        restaurant_id = data.get('restaurantId')
        ratingid = data.get('ratingid')
        price = data.get('price')
        image_file = request.files.get('image')
        print(image_file.name)
        # Add more attributes as needed

        # Check if the restaurant ID exists
        restaurant = Restaurantdatas.query.get(restaurant_id)
        if not restaurant:
            return jsonify({'message': 'Restaurant not found'}), 404

        if image_file:
            # Read the image file as binary data
            image_data = image_file.read()
            # Convert binary data to base64
            image_base64 = convert_image_to_jpeg_base64(image_data)
        else:
            image_base64 = None
        product = Product(product_name=product_name, restaurant_name=restaurant_name, restaurant_id=restaurant_id, ratingid=ratingid, price=price, image=image_base64)
        db.session.add(product)
        db.session.commit()
        return jsonify({'message': 'Product added successfully'}), 201

# Add more routes and functionalities for product management as needed
@app.route('/product/all', methods=['GET'])
def get_all_products():
    products = Product.query.all()
    if products:
        products_data = []
        for product in products:
            product_data = {
                'id': product.id,
                'productName': product.product_name,
                'restaurantName': product.restaurant_name,
                'restaurantId': product.restaurant_id,
                'ratingid': product.ratingid,
                'price': product.price,
                'image': product.image
            }
            products_data.append(product_data)
        return jsonify({'products': products_data}), 200
    else:
        return jsonify({'message': 'No products found'}), 404


class Orders(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    product_name = db.Column(db.String, nullable=False)
    restaurant_name = db.Column(db.String, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String, nullable=False)

    def __repr__(self):
        return '<Order %r>' % self.id

    @classmethod
    def add_order(cls, customer_id, product_id, price, quantity, product_name, restaurant_name, status='pending'):
        order = cls(customer_id=customer_id, product_id=product_id, price=price, quantity=quantity,
                    product_name=product_name, restaurant_name=restaurant_name, status=status)
        db.session.add(order)
        db.session.commit()
        return order.id

    @classmethod
    def get_all_orders(cls):
        orders = cls.query.all()
        orders_data = []
        for order in orders:
            order_data = {
                'id': order.id,
                'customerId': order.customer_id,
                'productId': order.product_id,
                'price': order.price,
                'quantity': order.quantity,
                'productName': order.product_name,
                'restaurantName': order.restaurant_name,
                'timestamp': order.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'status': order.status
            }
            orders_data.append(order_data)
        return orders_data

    @classmethod
    def remove_order(cls, order_id):
        order = cls.query.get(order_id)
        if order:
            db.session.delete(order)
            db.session.commit()
            return True
        else:
            return False

# Flask app route methods
@app.route('/order/add', methods=['POST'])
def add_order_route():
    if request.method == 'POST':
        data = request.json
        customer_id = data.get('customerId')
        product_id = data.get('productId')
        price = data.get('price')
        quantity = data.get('quantity')
        product_name = data.get('productName')
        restaurant_name = data.get('restaurantName')
        status = data.get('status', 'pending')  # Default status is pending

        order_id = Orders.add_order(customer_id, product_id, price, quantity, product_name, restaurant_name, status)
        return jsonify({'message': 'Order added successfully', 'orderId': order_id}), 201

@app.route('/order/all', methods=['GET'])
def get_all_orders_route():
    orders_data = Orders.get_all_orders()
    if orders_data:
        return jsonify({'orders': orders_data}), 200
    else:
        return jsonify({'message': 'No orders found'}), 404

@app.route('/order/remove/<int:order_id>', methods=['DELETE'])
def remove_order_route(order_id):
    if Orders.remove_order(order_id):
        return jsonify({'message': 'Order removed successfully'}), 200
    else:
        return jsonify({'message': 'Order not found'}), 404

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({'message': 'Token is missing'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user = Userdatas.find_by_email(data['email'])
        except:
            return jsonify({'message': 'Token is invalid'}), 401

        return f(current_user, *args, **kwargs)

    return decorated

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, nullable=False)
    restaurant_id = db.Column(db.Integer, nullable=False)  # New column for restaurant ID
    product_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return '<CartItem %r>' % self.id

    @classmethod
    def add_to_cart(cls, customer_id, restaurant_id, product_id, quantity):  # Updated method signature
        existing_item = cls.query.filter_by(customer_id=customer_id, product_id=product_id, restaurant_id=restaurant_id).first()
        if existing_item:
            existing_item.quantity += quantity
            db.session.commit()
            return existing_item.id
        else:
            cart_item = cls(customer_id=customer_id, restaurant_id=restaurant_id, product_id=product_id, quantity=quantity)
            db.session.add(cart_item)
            db.session.commit()
            return cart_item.id

    @classmethod
    def get_all_items(cls, customer_id):
        items = cls.query.filter_by(customer_id=customer_id).all()
        items_data = []
        for item in items:
            item_data = {
                'id': item.id,
                'customerId': item.customer_id,
                'restaurantId': item.restaurant_id,  # Include restaurant ID in response
                'productId': item.product_id,
                'quantity': item.quantity,
                'timestamp': item.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            }
            items_data.append(item_data)
        return items_data

# Flask app route methods for Cart
@app.route('/cart/add', methods=['POST'])
def add_to_cart_route():
    if request.method == 'POST':
        data = request.json
        customer_id = data.get('customerId')
        restaurant_id = data.get('restaurantId')  # Retrieve restaurant ID from request data
        product_id = data.get('productId')
        quantity = data.get('quantity')

        cart_item_id = Cart.add_to_cart(customer_id, restaurant_id, product_id, quantity)  # Pass restaurant ID to method
        return jsonify({'message': 'Item added to cart successfully', 'cartItemId': cart_item_id}), 201

@app.route('/cart/all/<int:customer_id>', methods=['GET'])
def get_all_items_in_cart_route(customer_id):
    items_data = Cart.get_all_items(customer_id)
    if items_data:
        return jsonify({'items': items_data}), 200
    else:
        return jsonify({'message': 'No items found in the cart'}), 404

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    review = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return '<Rating %r>' % self.id

    @classmethod
    def add_rating(cls, product_id, rating, review=None):
        rating = cls(product_id=product_id, rating=rating, review=review)
        db.session.add(rating)
        db.session.commit()
        return rating.id

    @classmethod
    def get_ratings_for_product(cls, product_id):
        ratings = cls.query.filter_by(product_id=product_id).all()
        ratings_data = []
        for rating in ratings:
            rating_data = {
                'id': rating.id,
                'productId': rating.product_id,
                'rating': rating.rating,
                'review': rating.review,
                'timestamp': rating.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            }
            ratings_data.append(rating_data)
        return ratings_data

    @classmethod
    def remove_rating(cls, rating_id):
        rating = cls.query.get(rating_id)
        if rating:
            db.session.delete(rating)
            db.session.commit()
            return True
        else:
            return False

# Flask app route methods for Rating
@app.route('/rating/add', methods=['POST'])
def add_rating_route():
    if request.method == 'POST':
        data = request.json
        product_id = data.get('productId')
        rating = data.get('rating')
        review = data.get('review')

        rating_id = Rating.add_rating(product_id, rating, review)
        return jsonify({'message': 'Rating added successfully', 'ratingId': rating_id}), 201

@app.route('/rating/all/<int:product_id>', methods=['GET'])
def get_ratings_for_product_route(product_id):
    ratings_data = Rating.get_ratings_for_product(product_id)
    if ratings_data:
        return jsonify({'ratings': ratings_data}), 200
    else:
        return jsonify({'message': 'No ratings found for the product'}), 404

@app.route('/rating/remove/<int:rating_id>', methods=['DELETE'])
def remove_rating_route(rating_id):
    if Rating.remove_rating(rating_id):
        return jsonify({'message': 'Rating removed successfully'}), 200
    else:
        return jsonify({'message': 'Rating not found'}), 404


# Add database creation within app context
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
