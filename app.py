from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_migrate import Migrate, migrate
import random

app = Flask(__name__)
mail = Mail(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///employee.db'
# initialize the database connection
db = SQLAlchemy(app)
migrate = Migrate(app,db)

# create db model
class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Name %r>' % self.id

# configuration of mail 
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'dataset.api2023@gmail.com'
app.config['MAIL_PASSWORD'] = 'nhvp ytoa obnd aswy'
app.config['MAIL_USE_TLS'] = True
# app.config['MAIL_USE_SSL'] = False
mail = Mail(app) 

# Secret key for session management
app.secret_key = 'my_secret_key'
correct_otp = str(random.randint(100000, 999999))



# Routes
@app.route('/')
def login():
    return render_template('Login.html')


@app.route('/logout')
def logout():
    session.pop('name', None)
    return redirect(url_for('login'))

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', name=session['name'])
    

# # @app.route('/otp')
# def otp():
#     return render_template('otp.html')

# Forms
@app.route('/submit', methods=['POST'])
def submit():
    email = request.form.get('email')
    name = request.form.get('name') 
    password = request.form.get('password')
    employee = Employee.query.filter_by(email=email, password=password).first()
    if employee:
        session['name'] = employee.name
        session['email'] = employee.email
        session['password'] = employee.password
        # Redirect to home page
        # return 'Logged in successfully!'
        msg_title = "OTP Verification"
        sender ='noreply@app.com'

        msg = Message(msg_title,sender=sender, recipients = [email] ) 
        msg.body = f'Hello {name}! Your OTP is {correct_otp}'
        data = {
        'app_name' : "virtual_meeting",
        'title' : "msg_title",
        'body' : "msg_body",
        }

        try:
            mail.send(msg)
            return render_template('otp.html')
        except Exception as e:
            print(e)
            return f"Email not sent, {e}"
    
        # msg.html = render_template('otp.html', data=data)
    else:
         flash('Account doesnt exist or username/password incorrect')
         return render_template('Login.html')
    
            # Account doesnt exist or username/password incorrect
    
    
@app.route('/profiles')
def index():
    profiles = Employee.query.all()
    return render_template('profiles.html', profiles=profiles)

@app.route('/signup2', methods=['POST'])
def signup2():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')

    existing_employee = Employee.query.filter_by(email=email, password=password).first()
    if existing_employee:
        flash('Email already exists. Please login.')
        return render_template('signup.html')

    # store data into database
    profile = Employee(name=name, email=email,password=password)
    db.session.add(profile)
    db.session.commit()

    #  Send OTP to the user
    msg_title = "OTP Verification"
    sender ='noreply@app.com'

    msg = Message(msg_title,sender=sender, recipients = [email] 
               ) 
    msg.body = f'Hello {name}! Your OTP is {correct_otp}'
    data = {
        'app_name' : "virtual_meeting",
        'title' : "msg_title",
        'body' : "msg_body",
        }
    
    # msg.html = render_template('otp.html', data=data)
    
    try:
        mail.send(msg)
        return render_template('otp.html')
    except Exception as e:
        print(e)
        return f"Email not sent, {e}"

@app.route('/verify', methods=['POST'])
def verify():
    # Simulate OTP verification logic
    entered_otp = request.form.get('otp')
     # This should be dynamically generated and sent to the user

    if entered_otp == correct_otp:
        return redirect(url_for('dashboard'))
    else:
        flash('Invalid OTP. Please try again.')
        return render_template('otp.html')
    

@app.route('/meeting')
def meeting():
    if 'name' in session:
        return render_template('meeting.html', name=session['name'])
    else:
        return redirect(url_for('login'))


@app.route('/join', methods=['GET', 'POST'])
def join():
    if request.method=="POST":
        room_id=request.form.get('room_ID')
        return redirect(url_for('meeting', roomID=room_id))
    return render_template('join.html')


# def reset_database():
#     with app.app_context():
#         db.drop_all()  # Delete all tables
#         db.create_all()  # Recreate the tables

if __name__ == '__main__':
    app.run(debug=True)
