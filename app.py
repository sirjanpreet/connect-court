from math import atan2, cos, radians, sin, sqrt
from flask import Flask, render_template, request, redirect, url_for, flash, session
import requests
from werkzeug.utils import secure_filename
import os
from flask_migrate import Migrate
from models import db, User, Friendship

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
@app.route('/feed')
def feed():
    if 'username' in session:
        username = session['username']
        return render_template('feed.html', username=username)
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

# Function to get latitude and longitude from city and state using Nominatim
def get_coordinates(city, state):
    url = f'https://nominatim.openstreetmap.org/search?city={city}&state={state}&format=json'
    response = requests.get(url, headers={'User-Agent': 'YourApp'}).json()
    if response:
        location = response[0]
        return float(location['lat']), float(location['lon'])
    return None, None

# Function to calculate distance using the Haversine formula
def haversine(lat1, lon1, lat2, lon2):
    # Radius of the Earth in kilometers
    R = 6371.0

    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)

    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c  # Distance in kilometers
    return distance

@app.route('/discover')
def discover():
    if 'username' not in session:
        flash('You must be logged in to view this page.')
        return redirect(url_for('signin'))

    current_user = User.query.filter_by(username=session['username']).first()  # same
    current_user_lat, current_user_lng = get_coordinates(current_user.location_city, current_user.location_state)

    friendships = {
        'sent': [f.friend_id for f in current_user.sent_requests if f.status == 'pending'],
        'received': [f.user_id for f in current_user.received_requests if f.status == 'pending'],
        'accepted': [f.friend_id for f in current_user.sent_requests if f.status == 'accepted'] + 
                    [f.user_id for f in current_user.received_requests if f.status == 'accepted']
    }

    search_query = request.args.get('q', '')

    # Get all users except the logged-in user and those with name "None"
    users = User.query.filter(
        User.username != session['username'], 
        User.name.isnot(None), 
        User.name != 'None',
        ~User.id.in_(friendships['accepted'])  # Exclude accepted friends
    )

    if search_query:
        search_query = f"%{search_query}%"
        users = users.filter(
            (User.name.ilike(search_query)) |
            (User.bio.ilike(search_query)) |
            (User.sports.ilike(search_query)) |
            (User.interests.ilike(search_query)) |
            (User.location_city.ilike(search_query)) |
            (User.location_state.ilike(search_query)) |
            (User.languages.ilike(search_query)) |
            (User.school_work.ilike(search_query))
        )

    users = users.all()

    # Calculate the distance for each user and sort by distance
    user_distances = []
    for user in users:
        lat, lng = get_coordinates(user.location_city, user.location_state)
        if lat is not None and lng is not None:
            distance = haversine(current_user_lat, current_user_lng, lat, lng)
            user_distances.append((user, distance))
        else:
            user_distances.append((user, float('inf')))  # Max distance if coordinates are unavailable

    # Sort users by distance (closest first)
    sorted_users = sorted(user_distances, key=lambda x: x[1])

    # Extract just the user objects for rendering
    sorted_users = [user[0] for user in sorted_users]

    # add friendships here

    return render_template('discover.html', users=sorted_users, friendships=friendships)

@app.route('/send_request/<int:to_user_id>', methods=['POST'])
def send_request(to_user_id):
    if 'username' not in session:
        flash('You must be logged in to send a friend request.')
        return redirect(url_for('discover'))

    from_user = User.query.filter_by(username=session['username']).first()
    to_user = User.query.get(to_user_id)

    if from_user.id == to_user_id:
        flash("You can't send a friend request to yourself!")
        return redirect(url_for('discover'))

    # Check if a request already exists
    existing_request = Friendship.query.filter_by(user_id=from_user.id, friend_id=to_user.id).first()
    if existing_request:
        flash('Friend request already sent!')
    else:
        new_request = Friendship(user_id=from_user.id, friend_id=to_user.id, status='pending')
        db.session.add(new_request)
        db.session.commit()
        flash('Friend request sent!')

    return redirect(url_for('discover'))

# Route to accept a friend request
@app.route('/accept_request/<int:from_user_id>', methods=['POST'])
def accept_request(from_user_id):
    if 'username' not in session:
        flash('You must be logged in to accept a friend request.')
        return redirect(url_for('discover'))

    to_user = User.query.filter_by(username=session['username']).first()
    friend_request = Friendship.query.filter_by(user_id=from_user_id, friend_id=to_user.id, status='pending').first()

    if friend_request:
        # Update the existing request status to 'accepted'
        friend_request.status = 'accepted'
        db.session.commit()

        # Also, create a mutual relationship if it doesn't exist
        reverse_request = Friendship.query.filter_by(user_id=to_user.id, friend_id=from_user_id).first()
        if not reverse_request:
            new_friendship = Friendship(user_id=to_user.id, friend_id=from_user_id, status='accepted')
            db.session.add(new_friendship)
            db.session.commit()

        flash('Friend request accepted!')
    else:
        flash('No friend request found.')

    return redirect(url_for('discover'))

if __name__ == '__main__':
    app.run(debug=True)