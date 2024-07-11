from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
# import random

app = Flask(__name__)

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'dataset.api2023@gmail.com'
app.config['MAIL_PASSWORD'] = 'anoopkumarmotog40'
app.config['MAIL_DEFAULT_SENDER'] = 'dataset.api2023@gmail.com'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

mail = Mail(app)

# Secret key for session management
app.secret_key = 'my_secret_key'
otp = 123456

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# OTP generation function
# def generate_otp():
#     return str(random.randint(100000, 999999))


# Routes
# Route for login page
@app.route('/')
def login():
    return render_template('Login.html')

db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    # otp = db.Column(db.String(6))

    def __repr__(self):
        return f'<User {self.email}>'

# Route for index page
@app.route('/index')
def index():
    return render_template('index.html')

# Route for submitting the login form
@app.route('/submit', methods=['POST'])
def submit():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')

     # Check if user already exists
    user = User.query.filter_by(email=email).first()
    if user:
        flash('Email already exists.')
        return redirect(url_for('login'))

    new_user = User(name=name, email=email, password='password')
    db.session.add(new_user)
    db.session.commit()

    # otp = generate_otp()
    # otp = 123456
    session['otp'] = otp
    session['email'] = email
    session['name'] = name

    msg = Message('Your OTP Code', sender='dataset.api2023@gmail.com', recipients=[email])
    msg.body = f'Welcome {name}, \nYour OTP code is {otp}'
    mail.send(msg)

    flash('OTP has been sent to your email.')
    return redirect(url_for('otp'))



# Route for OTP page
@app.route('/otp')
def otp():
    return render_template('otp.html')

# Route for verifying OTP
@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    otp_check = request.form.get('otp')

    if 'otp' in session and otp_check == str(session['otp']):
        flash('OTP verified successfully. You are now logged in.')
        return redirect(url_for('index'))
    else:
        flash('Invalid OTP. Please try again.')
        return redirect(url_for('otp_page'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)


# @app.route("/")
# def index():
#     return render_template("Login.html")

# @app.route("/signup", methods=["POST"])
# def signup():
#     return render_template("Login.html")

# @app.route("/submit", methods=["POST"])
# def submit():
#     return render_template("index.html")


# Route for OTP verification
# @app.route('/signup', methods=['POST'])
# def signup():
#     name = request.form.get('name')
#     email = request.form.get('email')
#     password = request.form.get('password')

#     otp = generate_otp()
#     session['otp'] = otp
#     session['email'] = email

#     msg = Message('Your OTP Code', sender='dataset.api2023@gmail.com', recipients=[email])
#     msg.body = f'Your OTP code is {otp}'
#     mail.send(msg)

#     flash('OTP has been sent to your email.')
#     return redirect(url_for('otp'))