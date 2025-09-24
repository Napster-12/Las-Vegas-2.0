from flask import Flask, render_template, request, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
import os, json

app = Flask(__name__)

# Database setup
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
if not os.path.exists(INSTANCE_DIR):
    os.makedirs(INSTANCE_DIR)

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(INSTANCE_DIR, "shop.db")}'
app.config['SECRET_KEY'] = 'change-me'
db = SQLAlchemy(app)

# Mail setup
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'codnellsmall@gmail.com'
app.config['MAIL_PASSWORD'] = 'mrmxmmomvhvfqoee'  # Gmail App Password
app.config['MAIL_DEFAULT_SENDER'] = ("Las Vegas Store", 'codnellsmall@gmail.com')
mail = Mail(app)

# Models
class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=100)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    items_json = db.Column(db.Text, nullable=False)
    total = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    customer_json = db.Column(db.Text)

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/menu')
def menu():
    items = MenuItem.query.all()
    return render_template('menu.html', items=items)

@app.route('/cart')
def cart():
    return render_template('cart.html')

@app.route('/customise')
def customise():
    return render_template('customise.html')

@app.route('/checkout', methods=['GET','POST'])
def checkout():
    success_msg = None
    if request.method == 'POST':
        try:
            items = request.form.get('cart_data')
            total = request.form.get('total')
            client_name = request.form.get('client_name')
            client_email = request.form.get('client_email')
            client_phone = request.form.get('client_phone')
            client_address = request.form.get('client_address')

            if not items or not total or not client_name or not client_email or not client_address:
                flash('Please fill all required fields!')
            else:
                items_json = json.loads(items)
                client_info = {
                    "name": client_name,
                    "email": client_email,
                    "phone": client_phone,
                    "address": client_address
                }

                # Save order
                order = Order(
                    items_json=json.dumps(items_json),
                    total=float(total),
                    customer_json=json.dumps(client_info)
                )
                db.session.add(order)
                db.session.commit()

                # Send confirmation emails
                rows = ""
                for i in items_json:
                    size = i.get('size','M')
                    rows += f"""
                    <tr style="border-bottom:1px solid #ddd;text-align:center;">
                        <td style="padding:8px;">{i['name']}</td>
                        <td style="padding:8px;">{size}</td>
                        <td style="padding:8px;">{i['quantity']}</td>
                        <td style="padding:8px;">R{i['price']*i['quantity']}</td>
                    </tr>"""

                html_content = f"""
                <div style="font-family:Arial,sans-serif;color:#333;">
                    <div style="max-width:600px;margin:auto;border:1px solid #eee;border-radius:10px;padding:20px;background:#f9f9f9;">
                        <h2 style="text-align:center;color:#28a745;">🛒 Order Confirmation</h2>
                        <p style="text-align:center;font-size:14px;color:#666;">Thank you for your order! Below are the details:</p>
                        <hr>
                        <p><strong>Order ID:</strong> {order.id}</p>
                        <p><strong>Status:</strong> {order.status}</p>
                        <h3 style="color:#555;">Client Information</h3>
                        <ul>
                            <li><strong>Name:</strong> {client_name}</li>
                            <li><strong>Email:</strong> {client_email}</li>
                            <li><strong>Phone:</strong> {client_phone}</li>
                            <li><strong>Address:</strong> {client_address}</li>
                        </ul>
                        <h3>Order Details</h3>
                        <table style="width:100%;border-collapse:collapse;">
                            <thead style="background:#28a745;color:#fff;">
                                <tr>
                                    <th>Item</th><th>Size</th><th>Quantity</th><th>Subtotal</th>
                                </tr>
                            </thead>
                            <tbody>{rows}</tbody>
                        </table>
                        <h3 style="text-align:right;color:#28a745;">Total: R{total}</h3>
                    </div>
                </div>
                """

                msg_admin = Message(
                    subject=f"🛒 New Order Received (ID: {order.id})",
                    recipients=["codnellsmall@gmail.com"],
                    html=html_content
                )
                mail.send(msg_admin)

                msg_client = Message(
                    subject=f"✅ Your Order Confirmation (ID: {order.id})",
                    recipients=[client_email],
                    html=html_content
                )
                mail.send(msg_client)

                flash('Order placed successfully! Confirmation email sent.')

        except Exception as e:
            db.session.rollback()
            flash(f'Error placing order: {str(e)}')

    return render_template('checkout.html', success_msg=success_msg)

# API routes
@app.route('/api/menu')
def api_menu():
    items = MenuItem.query.all()
    return json.dumps([{
        'id': i.id, 'name': i.name, 'description': i.description, 'price': i.price, 'stock': i.stock
    } for i in items])

@app.route('/api/orders', methods=['POST'])
def api_create_order():
    data = request.json
    order = Order(
        items_json=json.dumps(data.get('items', [])),
        total=data.get('total', 0),
        customer_json=json.dumps(data.get('customer', {}))
    )
    db.session.add(order)
    db.session.commit()
    return json.dumps({'id': order.id, 'status': 'created'})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
