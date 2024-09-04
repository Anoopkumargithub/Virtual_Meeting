from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_migrate import Migrate, migrate
from flask_socketio import SocketIO, join_room, leave_room, send, emit
import random
import string

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

meetings = {}

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
    meeting_id = db.Column(db.String(120), unique=True, nullable=False) 
    host_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    room_name = db.Column(db.String(120), nullable=False)  
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
    
def generate_meeting_id(size=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=size))

@app.route('/create')
def create():
    return render_template('create_meeting.html')



@app.route('/create_meeting', methods=['POST'])
def create_meeting():
    try:
        data = request.get_json()
        meeting_name = data.get('name')
        password = data.get('password')
        meeting_id = generate_meeting_id()
        host_id = 1  # Replace with actual session user ID if applicable

        meeting = Meeting(meeting_id=meeting_id, host_id=host_id, room_name=meeting_name, is_active=True)
        db.session.add(meeting)
        db.session.commit()

        return jsonify({'meeting_id': meeting_id})
    except Exception as e:
        return jsonify({'message': 'Failed to create meeting', 'error': str(e)}), 500

@app.route('/room/<meeting_id>')
def room(meeting_id):
    try:
        meeting = Meeting.query.filter_by(meeting_id=meeting_id).first_or_404()
        return render_template('room.html', room_name=meeting.room_name)
    except Exception as e:
        return jsonify({'message': 'Failed to load room', 'error': str(e)}), 500

@app.route('/join')
def join():
    return render_template('join.html')

@app.route('/schedule_meeting')
def schedule_meeting():
    try:
        meetings = Meeting.query.filter(Meeting.scheduled_time.isnot(None)).all()
        return render_template('schedule_meeting.html', meetings=meetings)
    except Exception as e:
        return jsonify({'message': 'Failed to load scheduled meetings', 'error': str(e)}), 500

@socketio.on('join')
def handle_join(data):
    try:
        name = data['name']
        emit('new-participant', {'participant_id': request.sid}, broadcast=True)
        emit('ready', {'participant_id': request.sid}, room=request.sid)
    except Exception as e:
        print(f"Error in handle_join: {str(e)}")

@socketio.on('chat-message')
def handle_chat_message(data):
    try:
        emit('chat-message', data, broadcast=True)
    except Exception as e:
        print(f"Error in handle_chat_message: {str(e)}")

@socketio.on('draw')
def handle_draw(data):
    try:
        emit('draw', data, broadcast=True)
    except Exception as e:
        print(f"Error in handle_draw: {str(e)}")

@socketio.on('share-screen')
def handle_share_screen(stream):
    try:
        emit('share-screen', {'stream': stream}, broadcast=True)
    except Exception as e:
        print(f"Error in handle_share_screen: {str(e)}")

@socketio.on('screen-share-ended')
def handle_screen_share_ended():
    try:
        emit('screen-share-ended', broadcast=True)
    except Exception as e:
        print(f"Error in handle_screen_share_ended: {str(e)}")

@socketio.on('offer')
def handle_offer(data):
    try:
        emit('offer', data, room=data['target'])
    except Exception as e:
        print(f"Error in handle_offer: {str(e)}")

@socketio.on('answer')
def handle_answer(data):
    try:
        emit('answer', data, room=data['target'])
    except Exception as e:
        print(f"Error in handle_answer: {str(e)}")

@socketio.on('ice-candidate')
def handle_ice_candidate(data):
    try:
        emit('ice-candidate', data, room=data['target'])
    except Exception as e:
        print(f"Error in handle_ice_candidate: {str(e)}")

@socketio.on('mute-participants')
def handle_mute_participants():
    try:
        emit('mute-participants', broadcast=True)
    except Exception as e:
        print(f"Error in handle_mute_participants: {str(e)}")

@socketio.on('turn-off-video')
def handle_turn_off_video():
    try:
        emit('turn-off-video', broadcast=True)
    except Exception as e:
        print(f"Error in handle_turn_off_video: {str(e)}")

@socketio.on('disconnect')
def handle_disconnect():
    try:
        emit('participant-left', {'participant_id': request.sid}, broadcast=True)
    except Exception as e:
        print(f"Error in handle_disconnect: {str(e)}")





@socketio.on('leave')
def handle_leave():
    try:
        emit('participant-left', {'participant_id': request.sid}, broadcast=True)
    except Exception as e:
        print(f"Error in handle_leave: {str(e)}")

# if __name__ == '__main__':
#     socketio.run(app, debug=True, host='0.0.0.0', port=8000)
if __name__ == '__main__':
    socketio.run(app, debug=True,port=8000)
    
# def generate_meeting_id():
#     """Generate a unique meeting ID."""
#     return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))  # Change: Function to generate unique meeting ID


# @app.route('/create', methods=['GET', 'POST'])
# def create_meeting():
#     if request.method == 'POST':
#         room_name = request.form['room_name']
#         user = request.form['username']
#         schedule_meeting = 'schedule_meeting' in request.form
#         scheduled_time = request.form.get('scheduled_time')

#         # user = Employee.query.filter_by(name=name).first()
#         # if not user:
#         #     flash("User does not exist. Please sign up first.")
#         #     return redirect(url_for('signup'))

#         # Generate a unique meeting ID
#         meeting_id = str(random.randint(100000, 999999))

#         meeting = Meeting(meeting_id=meeting_id, room_name=room_name, host=user, is_active=not schedule_meeting)

#         if schedule_meeting and scheduled_time:
#             scheduled_time = scheduled_time.replace('T', ' ')
#             meeting.scheduled_time = datetime.strptime(scheduled_time, '%Y-%m-%d %H:%M')
#             meeting.is_active = False  
#             # Set the meeting as inactive until the scheduled time

#         db.session.add(meeting)
#         db.session.commit()

#         meeting_link = url_for('room', meeting_id=meeting_id, _external=True)
#         flash(f"Meeting created successfully! Share this link with participants: {meeting_link}")

#         if schedule_meeting:
#             return redirect(url_for('schedule'))
#         else:
#             return redirect(url_for('room', meeting_id=meeting_id))
#     return render_template('create_meeting.html')



# @app.route('/room/<meeting_id>')
# def room(meeting_id):
#     meeting = Meeting.query.filter_by(meeting_id=meeting_id).first()
#     if not meeting or not meeting.is_active:
#         return "Meeting is not active or does not exist."

#     session['room'] = meeting.room_name
#     session['meeting_id'] = meeting_id
#     session['is_host'] = meeting.host.name == session.get('name')

#     # Additional setup for screen sharing and media management
#     screen_sharing = session.get('screen_sharing', False)
#     media_streams = session.get('media_streams', {})

#     return render_template('room.html', room_name=meeting.room_name, screen_sharing=screen_sharing, media_streams=media_streams)

# @app.route('/schedule')
# def schedule():
#     meetings = Meeting.query.filter(Meeting.scheduled_time.isnot(None)).all()
#     return render_template('schedule.html', meetings=meetings)


# # SocketIO event handlers
# @socketio.on('join')
# def handle_join(data):
#     room = session.get('room')
#     join_room(room)
#     if session.get('is_host'):
#         send(f"{data['name']} has joined the room.", to=room)

# @socketio.on('leave')
# def handle_leave(data):
#     room = session.get('room')
#     leave_room(room)
#     if session.get('is_host'):
#         send(f"{data['name']} has left the room.", to=room)

# @socketio.on('message')
# def handle_message(data):
#     room = session.get('room')
#     send(data['message'], to=room)

# @socketio.on('mute_participants')
# def handle_mute(data):
#     if session.get('is_host'):
#         emit('mute', broadcast=True)

# @socketio.on('turn_off_video')
# def handle_turn_off_video(data):
#     if session.get('is_host'):
#         emit('turn_off_video', broadcast=True)

# @socketio.on('draw')  # NEW: Handle drawing events
# def handle_draw(data):
#     room = session.get('room')
#     emit('draw', data, room=room)

# @socketio.on('start_screen_share')
# def handle_start_screen_share(data):
#     room = session.get('room')
#     if session.get('is_host'):
#         emit('start_screen_share', data, to=room, broadcast=True)

# @socketio.on('stop_screen_share')
# def handle_stop_screen_share(data):
#     room = session.get('room')
#     if session.get('is_host'):
#         emit('stop_screen_share', data, to=room, broadcast=True)




# @app.route('/join', methods=['GET', 'POST'])
# def join():
#     if request.method == "POST":
#         meeting_id = request.form.get('meeting_ID')
#         return redirect(url_for('room', meeting_id=meeting_id))
#     return render_template('join.html')

# @socketio.on('offer')
# def handle_offer(data):
#     emit('offer', data, broadcast=True)

# @socketio.on('answer')
# def handle_answer(data):
#     emit('answer', data, broadcast=True)

# @socketio.on('ice-candidate')
# def handle_ice_candidate(data):
#     emit('ice-candidate', data, broadcast=True)


# def reset_database():
#     with app.app_context():
#         db.drop_all()  # Delete all tables
#         db.create_all()  # Recreate the tables

# if __name__ == '__main__':
#     socketio.run(app, debug=True, host='0.0.0.0', port=8000)
