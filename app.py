import os
from datetime import datetime
from functools import wraps
import numpy as np
from sklearn.neighbors import KNeighborsRegressor
from math import atan2, cos, radians, sin, sqrt

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity
)
from flask_migrate import Migrate
from werkzeug.utils import secure_filename

from models import ChatMessage, db, User, Event, EventSignup, Friendship

import requests
from dotenv import load_dotenv
from transformers import pipeline

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key' 
app.config['SECRET_KEY'] = 'your_secret_key' 
app.config['UPLOAD_FOLDER'] = 'static/uploads' 

# Ensure upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db.init_app(app)
migrate = Migrate(app, db)
CORS(app, supports_credentials=True)
jwt = JWTManager(app)

# Initialize the database tables
with app.app_context():
    db.create_all()

HUGGINGFACE_API_TOKEN = os.getenv('HUGGINGFACE_API_TOKEN')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

generator = pipeline(
    'text-generation',
    model='gpt2',
    framework='pt',
    pad_token_id=50256  # GPT-2's eos_token_id
)

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

### HELPER FUNCTIONS ###

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

# Function to compute the sport similarity score (fraction of matching sports)
def sport_similarity(user_sports, event_sports):
    user_sports_set = set(user_sports.split(','))  # Split user sports by comma and create a set
    event_sports_set = set(event_sports.split(','))  # Split event sports by comma and create a set
    
    # Find the intersection of sports between the user and the event
    common_sports = user_sports_set.intersection(event_sports_set)
    
    # Calculate the similarity score as the fraction of common sports over total unique sports
    total_sports = len(user_sports_set.union(event_sports_set))
    similarity_score = len(common_sports) / total_sports if total_sports > 0 else 0
    
    return similarity_score

# Function to check if the event organizer is a friend of the user
def is_friend(user, organizer_id):
    friend_relationship = Friendship.query.filter(
        (Friendship.user_id == user.id) & (Friendship.friend_id == organizer_id) & (Friendship.status == 'accepted')
    ).first()

    reverse_relationship = Friendship.query.filter(
        (Friendship.friend_id == user.id) & (Friendship.user_id == organizer_id) & (Friendship.status == 'accepted')
    ).first()

    # Return True if either relationship exists (mutual friendship)
    return friend_relationship is not None or reverse_relationship is not None

# Prepare the feature vector for each event
def prepare_features(user, event, today):
    # 1. Date proximity: days between today and event date
    date_proximity = abs((event.date - today).days)

    # 2. Location proximity: Haversine distance between user and event location
    user_lat, user_lon = get_coordinates(user.location_city, user.location_state)
    event_lat, event_lon = get_coordinates(event.city, event.state)
    location_proximity = haversine(user_lat, user_lon, event_lat, event_lon)

    # 3. Sports similarity (fraction of matching sports)
    sport_match = sport_similarity(user.sports or '', event.sport or '')

    # 4. Interest matching: binary (1 if there's any match, otherwise 0)
    interest_match = 1 if any(interest in (event.description or '') for interest in (user.interests or '').split(',')) else 0

    # 5. Friend event: binary (1 if the event is created by a friend, 0 otherwise)
    friend_match = 1 if is_friend(user, event.organizer_id) else 0

    # Return feature vector as a list
    return [date_proximity, location_proximity, sport_match, interest_match, friend_match]

# Fit the KNN model to rank the events
def rank_events_knn(user, events):
    today = datetime.today().date()

    # Prepare feature vectors for all events
    X = []
    for event in events:
        X.append(prepare_features(user, event, today))

    # Convert feature vectors to numpy array
    X = np.array(X)

    # Fit a KNN model (n_neighbors should be the number of events since we want to rank all)
    knn = KNeighborsRegressor(n_neighbors=len(events), metric='euclidean')

    # Fit the KNN model using the feature vectors
    knn.fit(X, np.arange(len(events)))  # We fit to indices since we don't have explicit labels

    # Compute distances to each event (closeness) from the model
    distances, indices = knn.kneighbors(X)

    # The indices array provides the order in which events are ranked by closeness
    # Sort events based on their ranking and return the ordered list
    ranked_events = [events[i] for i in indices[0]]

    return ranked_events


### ROUTES ###

# Home route
@app.route('/')
def home():
    return render_template('index.html')

## Authentication Routes ##

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

# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)  # Remove username from session
    flash('You have been logged out.')
    return redirect(url_for('signin'))

@app.route('/feed', methods=['GET', 'POST'])
def feed():
    if 'username' in session:
        username = session['username']
        user = User.query.filter_by(username=username).first()

        # Fetch all events that are not created by the current user
        events = Event.query.filter(Event.organizer_id != username).all()

        if len(events) > 3:
            # Rank the events using the KNN model
            ranked_events = rank_events_knn(user, events)
        else:
            # If there are 3 or fewer events, no need to run KNN
            ranked_events = events

        # Prepare the event data with additional information like signups and capacity
        event_data = []
        for event in ranked_events:
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

@app.route('/friends')
def friends():
    if 'username' not in session:
        flash('You must be logged in to view this page.')
        return redirect(url_for('signin'))

    current_user = User.query.filter_by(username=session['username']).first()

    # Query accepted friendships
    friends_ids = [f.friend_id for f in current_user.sent_requests if f.status == 'accepted'] + \
                  [f.user_id for f in current_user.received_requests if f.status == 'accepted']
    
    friends = User.query.filter(User.id.in_(friends_ids)).all()

    return render_template('friends.html', friends=friends)


@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'username' not in session:
        flash('You must be logged in to view this page.')
        return redirect(url_for('signin'))

    current_user = User.query.filter_by(username=session['username']).first()
    
    # Get the friend ID from the session
    friend_id = session.get('friend_id')
    if not friend_id:
        flash('No chat initiated. Please start a chat from the Friends page.')
        return redirect(url_for('friends'))

    friend = User.query.get(friend_id)

    if request.method == 'POST':
        message_text = request.form.get('message')
        if message_text:
            new_message = ChatMessage(sender_id=current_user.id, recipient_id=friend_id, message=message_text)
            db.session.add(new_message)
            db.session.commit()
            flash(f'Message sent to {friend.name}')
    
    # Retrieve the chat history between the current user and the friend
    chat_history = ChatMessage.query.filter(
        ((ChatMessage.sender_id == current_user.id) & (ChatMessage.recipient_id == friend_id)) |
        ((ChatMessage.sender_id == friend_id) & (ChatMessage.recipient_id == current_user.id))
    ).order_by(ChatMessage.timestamp).all()

    return render_template('chat.html', friend=friend, chat_history=chat_history, current_user=current_user)


@app.route('/start_chat', methods=['POST'])
def start_chat():
    if 'username' not in session:
        flash('You must be logged in to start a chat.')
        return redirect(url_for('signin'))

    friend_id = request.form.get('friend_id')
    
    if friend_id:
        session['friend_id'] = friend_id  # Store the friend's ID in the session
        return redirect(url_for('chat'))  # Redirect to the /chat route
    
    flash('Could not start chat. Please try again.')
    return redirect(url_for('friends'))

@app.route('/suggest_message', methods=['POST'])
def suggest_message():
    if 'username' not in session:
        return jsonify({"error": "You must be logged in to get message suggestions."}), 403

    # Get the current logged-in user and the friend they are chatting with
    current_user = User.query.filter_by(username=session['username']).first()
    friend_id = session.get('friend_id')
    if not friend_id:
        return jsonify({"error": "No friend selected."}), 400

    friend = User.query.get(friend_id)

    if not friend:
        return jsonify({"error": "Friend not found."}), 404

    # Fetch the last 10 messages between the two users
    chat_history = ChatMessage.query.filter(
        ((ChatMessage.sender_id == current_user.id) & (ChatMessage.recipient_id == friend_id)) |
        ((ChatMessage.sender_id == friend_id) & (ChatMessage.recipient_id == current_user.id))
    ).order_by(ChatMessage.timestamp.desc()).limit(10).all()

    # Reverse chat history to have the oldest message first
    chat_history = chat_history[::-1]

    # Format the chat history for the prompt
    chat_history_text = "\n".join(
        [f"{msg.sender.name}: {msg.message}" for msg in chat_history]
    )

    # Construct the prompt with user profiles and chat history
    prompt = f"""
    The following is a conversation between {current_user.name} and {friend.name}.
    {current_user.name}'s Profile:
    - Sports: {current_user.sports or 'N/A'}
    - Bio: {current_user.bio or 'N/A'}
    - Interests: {current_user.interests or 'N/A'}
    - Location: {current_user.location_city}, {current_user.location_state or 'N/A'}
    - Languages: {current_user.languages or 'N/A'}
    - School/Work: {current_user.school_work or 'N/A'}

    {friend.name}'s Profile:
    - Sports: {friend.sports or 'N/A'}
    - Bio: {friend.bio or 'N/A'}
    - Interests: {friend.interests or 'N/A'}
    - Location: {friend.location_city}, {friend.location_state or 'N/A'}
    - Languages: {friend.languages or 'N/A'}
    - School/Work: {friend.school_work or 'N/A'}

    Based on the above profiles and the chat history below, generate a relevant and engaging message for {current_user.name} to send to {friend.name} about meeting up to play some sports.

    Chat History:
    {chat_history_text}

    {current_user.name}:
    """

    try:
        # Generate a message using GPT-2 with max_new_tokens and return only the generated text
        result = generator(
            prompt,
            max_new_tokens=50,       # Number of tokens to generate
            return_full_text=False,  # Return only the generated text
            truncation=True
        )
        suggestion = result[0]['generated_text'].strip()

        return jsonify({"suggestion": suggestion}), 200

    except Exception as e:
        # Log the exception (optional)
        app.logger.error(f"Error generating message: {e}")
        return jsonify({"error": "Failed to generate a suggestion."}), 500



@app.route('/my_events')
def my_events():
    if 'username' not in session:
        flash('You must be logged in to view your events.')
        return redirect(url_for('signin'))

    user_events = Event.query.filter_by(organizer_id=session['username']).all()
    
    events_data = []
    for event in user_events:
        current_signups_count = len(event.signups)
        events_data.append({
            'event': event,
            'current_signups': current_signups_count
        })

    return render_template('my_events.html', events=events_data)

@app.route('/delete_event/<int:event_id>', methods=['POST'])
def delete_event(event_id):
    if 'username' not in session:
        flash('You must be logged in to view this page.')
        return redirect(url_for('signin'))
    
    event = Event.query.get(event_id)
    if event and event.organizer_id == session['username']:
        db.session.delete(event)
        db.session.commit()
        flash('Event deleted successfully!')
    else:
        flash('You cannot delete this event.')

    return redirect(url_for('my_events'))

@app.route('/edit_event/<int:event_id>', methods=['GET', 'POST'])
def edit_event(event_id):
    if 'username' not in session:
        flash('You must be logged in to edit an event.')
        return redirect(url_for('signin'))

    event = Event.query.get(event_id)
    if not event or event.organizer_id != session['username']:
        flash('You cannot edit this event.')
        return redirect(url_for('my_events'))

    if request.method == 'POST':
        # Update event fields based on form input
        event.title = request.form['title']
        event.description = request.form['description']
        event.city = request.form['city']
        event.state = request.form['state']
        event.venue = request.form['venue']
        event.date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()

        start_time = datetime.strptime(request.form['start_time'], '%H:%M').time()
        end_time = datetime.strptime(request.form['end_time'], '%H:%M').time()
        event.start_time = start_time
        event.end_time = end_time
        
        db.session.commit()
        flash('Event updated successfully!')
        return redirect(url_for('my_events'))

    return render_template('edit_event.html', event=event)

@app.route('/registered_events')
def registered_events():
    if 'username' not in session:
        flash('You must be logged in to view your registered events.')
        return redirect(url_for('signin'))

    username = session['username']
    user = User.query.filter_by(username=username).first()

    registered_events = Event.query.join(EventSignup).filter(EventSignup.user_id == user.id).all()

    events_data = []
    for event in registered_events:
        current_signups_count = len(event.signups)
        events_data.append({
            'event': event,
            'current_signups': current_signups_count
        })
    return render_template('registered_events.html', events=events_data, user=user)

from flask import render_template

@app.route('/find-events')
def find_events():
    return render_template('find_events.html', api_key=GOOGLE_API_KEY)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
