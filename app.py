from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_migrate import Migrate, migrate
from flask_socketio import SocketIO, join_room, leave_room, send, emit
import random

app = Flask(__name__)

# configuration of mail 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///employee.db'
app.secret_key = 'my_secret_key'
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'dataset.api2023@gmail.com'
app.config['MAIL_PASSWORD'] = 'nhvp ytoa obnd aswy'
app.config['MAIL_USE_TLS'] = True
# app.config['MAIL_USE_SSL'] = False

# initialize the database connection
db = SQLAlchemy(app)
migrate = Migrate(app,db)
mail = Mail(app)
socketio = SocketIO(app)

# Secret key for session management
correct_otp = str(random.randint(100000, 999999))

# create db model
class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

class Meeting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    host_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    room_name = db.Column(db.String(120), unique=True, nullable=False)
    scheduled_time = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=False)
    host = db.relationship('Employee', backref=db.backref('hosted_meetings', lazy=True))


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
    return render_template('dashboard.html', name=session.get('name'))
    


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
        # data = {
        # 'app_name' : "virtual_meeting",
        # 'title' : "msg_title",
        # 'body' : "msg_body",
        # }

        try:
            mail.send(msg)
            return render_template('otp.html')
        except Exception as e:
            print(e)
            return f"Email not sent, {e}"
    
    else:
         flash('Account doesnt exist or username/password incorrect')
         return render_template('Login.html')
    
    
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
    

@app.route('/create', methods=['GET', 'POST'])
def create_meeting():
    if request.method == 'POST':
        room_name = request.form['room_name']
        name = request.form['username']
        scheduled_time = request.form.get('scheduled_time')

        # Check if a meeting with the same room_name already exists
        existing_meeting = Meeting.query.filter_by(room_name=room_name).first()
        if existing_meeting:
            flash("Room name already exists. Please choose a different room name.")
            return render_template('create_meeting.html')

        user = Employee.query.filter_by(name=name).first()
        if not user:
            flash("User does not exist. Please sign up first.")
            return redirect(url_for('signup'))

        meeting = Meeting(room_name=room_name, host=user)
        if scheduled_time:
            # Replace 'T' with a space to match the format
            scheduled_time = scheduled_time.replace('T', ' ')
            meeting.scheduled_time = datetime.strptime(scheduled_time, '%Y-%m-%d %H:%M')

        db.session.add(meeting)
        db.session.commit()

        return redirect(url_for('room', room_name=room_name))
    return render_template('create_meeting.html')




@app.route('/room/<room_name>')
def room(room_name):
    meeting = Meeting.query.filter_by(room_name=room_name).first()
    if not meeting or not meeting.is_active:
        return "Meeting is not active or does not exist."

    session['room'] = room_name
    session['is_host'] = meeting.host.name == session.get('name')
    return render_template('room.html', room_name=room_name)

@app.route('/schedule')
def schedule():
    meetings = Meeting.query.filter(Meeting.scheduled_time.isnot(None)).all()
    meeting_list = ''.join([f'<li>{meeting.room_name} - Scheduled at {meeting.scheduled_time}</li>' for meeting in meetings])
    return render_template('schedule.html', meetings=meetings)

# SocketIO event handlers
@socketio.on('join')
def handle_join(data):
    room = session.get('room')
    join_room(room)
    if session.get('is_host'):
        send(f"{data['name']} has joined the room.", to=room)

@socketio.on('leave')
def handle_leave(data):
    room = session.get('room')
    leave_room(room)
    if session.get('is_host'):
        send(f"{data['name']} has left the room.", to=room)

@socketio.on('message')
def handle_message(data):
    room = session.get('room')
    send(data['message'], to=room)

@socketio.on('mute_participants')
def handle_mute(data):
    if session.get('is_host'):
        emit('mute', broadcast=True)

@socketio.on('turn_off_video')
def handle_turn_off_video(data):
    if session.get('is_host'):
        emit('turn_off_video', broadcast=True)

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
    socketio.run(app, debug=True)
