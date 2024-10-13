from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
import os
from flask_migrate import Migrate
from models import db, User, Event, EventSignup
from datetime import datetime, time

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # Set up your SQLite DB
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with a strong secret key
app.config['UPLOAD_FOLDER'] = 'static/uploads'  # Folder for storing profile pictures
db.init_app(app)

migrate = Migrate(app, db)

# Ensure upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Initialize the database tables
with app.app_context():
    db.create_all()

# States list to populate the dropdown in the profile form
states = [
    ('AL', 'Alabama'), ('AK', 'Alaska'), ('AZ', 'Arizona'), ('AR', 'Arkansas'),
    ('CA', 'California'), ('CO', 'Colorado'), ('CT', 'Connecticut'), ('DE', 'Delaware'),
    ('FL', 'Florida'), ('GA', 'Georgia'), ('HI', 'Hawaii'), ('ID', 'Idaho'),
    ('IL', 'Illinois'), ('IN', 'Indiana'), ('IA', 'Iowa'), ('KS', 'Kansas'),
    ('KY', 'Kentucky'), ('LA', 'Louisiana'), ('ME', 'Maine'), ('MD', 'Maryland'),
    ('MA', 'Massachusetts'), ('MI', 'Michigan'), ('MN', 'Minnesota'), ('MS', 'Mississippi'),
    ('MO', 'Missouri'), ('MT', 'Montana'), ('NE', 'Nebraska'), ('NV', 'Nevada'),
    ('NH', 'New Hampshire'), ('NJ', 'New Jersey'), ('NM', 'New Mexico'), ('NY', 'New York'),
    ('NC', 'North Carolina'), ('ND', 'North Dakota'), ('OH', 'Ohio'), ('OK', 'Oklahoma'),
    ('OR', 'Oregon'), ('PA', 'Pennsylvania'), ('RI', 'Rhode Island'), ('SC', 'South Carolina'),
    ('SD', 'South Dakota'), ('TN', 'Tennessee'), ('TX', 'Texas'), ('UT', 'Utah'),
    ('VT', 'Vermont'), ('VA', 'Virginia'), ('WA', 'Washington'), ('WV', 'West Virginia'),
    ('WI', 'Wisconsin'), ('WY', 'Wyoming')
]

# Home route
@app.route('/')
def home():
    return render_template('index.html')

# Sign Up route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('User already exists! Please log in.')
            return redirect(url_for('signin'))

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully! Please log in.')
        return redirect(url_for('signin'))

    return render_template('signup.html')

# Sign In route
@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and user.password == password:
            # Store the username in the session
            session['username'] = username
            return redirect(url_for('feed'))
        else:
            flash('Incorrect username or password. Please try again.')
            return redirect(url_for('signin'))

    return render_template('signin.html')

# Feed page route (for all users)
@app.route('/feed', methods=['GET', 'POST'])
def feed():
    if 'username' in session:
        username = session['username']
        user = User.query.filter_by(username=username).first()

        events = Event.query.filter(Event.organizer_id != username).all()

        event_data = []
        for event in events:
            current_signups = len(event.signups)
            max_capacity = event.max_capacity
            # Check if the user is signed up for the event
            is_signed_up = any(signup.user_id == user.id for signup in event.signups)
            event_data.append({
                'event': event,
                'current_signups': current_signups,
                'max_capacity': max_capacity,
                'is_signed_up': is_signed_up
            })

        return render_template('feed.html', username=username, events=event_data, user=user)  # Pass user object

    else:
        flash('You are not logged in!')
        return redirect(url_for('signin'))


# Profile route (view/edit profile)
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'username' not in session:
        flash('You must be logged in to view this page.')
        return redirect(url_for('signin'))

    user = User.query.filter_by(username=session['username']).first()

    if request.method == 'POST':
        # Update profile information
        user.name = request.form.get('name')
        user.phone = request.form.get('phone')
        user.email = request.form.get('email')
        user.bio = request.form.get('bio')
        user.age = request.form.get('age')
        user.sports = request.form.get('sports')
        user.interests = request.form.get('interests')
        user.location_city = request.form.get('location_city')
        user.location_state = request.form.get('location_state')
        user.languages = request.form.get('languages')
        user.gender = request.form.get('gender')
        user.pronouns = request.form.get('pronouns')
        user.school_work = request.form.get('school_work')

        # Handle profile picture upload
    if 'profile_picture' in request.files:
        profile_picture = request.files['profile_picture']
        if profile_picture.filename != '':
            filename = secure_filename(profile_picture.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            profile_picture.save(filepath)
            # Save only the filename in the database (not the full path)
            user.profile_picture = filename


        db.session.commit()
        flash('Profile updated successfully!')
        return redirect(url_for('profile'))

    return render_template('profile.html', user=user, states=states)

# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)  # Remove username from session
    flash('You have been logged out.')
    return redirect(url_for('signin'))

@app.route('/create_event', methods=['GET', 'POST'])
def create_event():
    if 'username' not in session:
        flash('You need to be logged in to create an event.')
        return redirect(url_for('signin'))
        
    if request.method == 'POST':
        title = request.form['title']
        city = request.form['city']  # Get city from form
        state = request.form['state']  # Get state from form
        sport = request.form['sport']
        description = request.form['description']
        venue = request.form['venue']
        max_capacity = request.form['max_capacity']
        date_str = request.form['date']
        start_time_str = request.form['start_time']
        end_time_str = request.form['end_time']

        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        start_time = datetime.strptime(start_time_str, '%H:%M').time()
        end_time = datetime.strptime(end_time_str, '%H:%M').time()
        
        new_event = Event(
            title=title,
            city=city,
            state=state,
            sport=sport,
            description=description,
            venue=venue,
            max_capacity=max_capacity,
            date=date,
            start_time=start_time,
            end_time=end_time,
            organizer_id=session['username']
        )

        
        db.session.add(new_event)
        db.session.commit()

        signup_event(event_id=new_event.id)

        flash('Event created successfully!')
        return redirect(url_for('feed'))

    return render_template('create_event.html')

@app.route('/signup_event/<int:event_id>', methods=['POST'])
def signup_event(event_id):
    if 'username' not in session:
        flash('You need to be logged in to sign up for an event.')
        return redirect(url_for('signin'))
    
    event = Event.query.get(event_id)
    user = User.query.filter_by(username=session['username']).first()
    
    if event and user:
        existing_signup = EventSignup.query.filter_by(event_id=event.id, user_id=user.id).first()
        if existing_signup:
            flash('You are already signed up for this event.')
            return redirect(url_for('feed'))

    current_signups_count = len(event.signups)

    if current_signups_count < event.max_capacity:
        signup = EventSignup(event_id=event.id, user_id=user.id)
        db.session.add(signup)
        db.session.commit()
        flash('You have successfully signed up for the event!')
    else:
        flash('Sorry, this event is full!')
    
    return redirect(url_for('feed'))

@app.route('/unregister_event/<int:event_id>', methods=['POST'])
def unregister_event(event_id):
    if 'username' not in session:
        flash('You need to be logged in to unregister from an event.')
        return redirect(url_for('signin'))
    
    event = Event.query.get(event_id)
    user = User.query.filter_by(username=session['username']).first()
    
    if event and user:
        signup = EventSignup.query.filter_by(event_id=event.id, user_id=user.id).first()
        if signup:
            db.session.delete(signup)
            db.session.commit()
            flash('You have successfully unregistered from the event!')
        else:
            flash('You are not signed up for this event.')
    
    return redirect(url_for('feed'))

@app.route('/discover')
def discover():
    if 'username' not in session:
        flash('You must be logged in to view this page.')
        return redirect(url_for('signin'))

    # Get all users from the database
    users = User.query.filter(User.username != session['username']).all()

    return render_template('discover.html', users=users)


if __name__ == '__main__':
    app.run(debug=True)
