import os
from datetime import datetime
from functools import wraps
from math import atan2, cos, radians, sin, sqrt

from flask import Flask, request, redirect, url_for, flash, session, jsonify, send_from_directory
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

app = Flask(__name__, static_folder="../client/build", static_url_path="")

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # Set up your SQLite DB
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'  # Replace with a strong secret key
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with a strong secret key
app.config['UPLOAD_FOLDER'] = 'static/uploads'  # Folder for storing profile pictures

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

### API ROUTES ###

# Home route to serve React app
@app.route('/')
def serve():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_file(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

# Feed page API (for all users)
@app.route('/api/feed', methods=['GET'])
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
                'event_id': event.id,
                'title': event.title,
                'description': event.description,
                'date': event.date.strftime('%Y-%m-%d'),
                'start_time': event.start_time.strftime('%H:%M'),
                'end_time': event.end_time.strftime('%H:%M'),
                'current_signups': current_signups,
                'max_capacity': max_capacity,
                'is_signed_up': is_signed_up
            })

        return jsonify({'events': event_data, 'user': {'username': user.username, 'id': user.id}})
    
    return jsonify({'error': 'Not logged in'}), 401

# Sign Up API
@app.route('/api/signup', methods=['POST'])
def signup():
    username = request.json['username']
    password = request.json['password']

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({'error': 'User already exists! Please log in.'}), 400

    new_user = User(username=username, password=password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'Account created successfully!'}), 201

# Sign In API
@app.route('/api/signin', methods=['POST'])
def signin():
    username = request.json['username']
    password = request.json['password']

    user = User.query.filter_by(username=username).first()

    if user and user.password == password:
        session['username'] = username
        return jsonify({'message': 'Logged in successfully!', 'username': username})
    else:
        return jsonify({'error': 'Incorrect username or password.'}), 401

# Logout API
@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    return jsonify({'message': 'You have been logged out.'}), 200

# Profile API
@app.route('/api/profile', methods=['POST'])
def profile():
    if 'username' not in session:
        return jsonify({'error': 'You must be logged in to view this page.'}), 401

    user = User.query.filter_by(username=session['username']).first()

    if 'profile_picture' in request.files:
        profile_picture = request.files['profile_picture']
        if profile_picture.filename != '':
            filename = secure_filename(profile_picture.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            profile_picture.save(filepath)
            user.profile_picture = filename

    # For text data in form (use request.form for regular fields)
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

    db.session.commit()
    return jsonify({'message': 'Profile updated successfully!'}), 200


# Discover API route
@app.route('/api/discover', methods=['GET'])
def discover():
    if 'username' not in session:
        return jsonify({'error': 'You must be logged in to view this page.'}), 401

    current_user = User.query.filter_by(username=session['username']).first()  
    current_user_lat, current_user_lng = get_coordinates(current_user.location_city, current_user.location_state)

    search_query = request.args.get('q', '')

    users = User.query.filter(
        User.username != session['username'], 
        User.name.isnot(None), 
        User.name != 'None'
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

    user_distances = []
    for user in users:
        lat, lng = get_coordinates(user.location_city, user.location_state)
        if lat is not None and lng is not None:
            distance = haversine(current_user_lat, current_user_lng, lat, lng)
            user_distances.append((user, distance))
        else:
            user_distances.append((user, float('inf')))  # Max distance if coordinates are unavailable

    sorted_users = sorted(user_distances, key=lambda x: x[1])
    sorted_users = [user[0] for user in sorted_users]

    return jsonify([{
        'id': user.id,
        'name': user.name,
        'bio': user.bio,
        'age': user.age,
        'sports': user.sports,
        'interests': user.interests,
        'location_city': user.location_city,
        'location_state': user.location_state,
        'languages': user.languages,
        'school_work': user.school_work
    } for user in sorted_users])

# More routes can be converted similarly ...

if __name__ == '__main__':
    app.run(debug=True)

@app.route('/api/create_event', methods=['POST'])
def create_event():
    if 'username' not in session:
        return jsonify({'error': 'You need to be logged in to create an event.'}), 401

    title = request.json['title']
    city = request.json['city']
    state = request.json['state']
    sport = request.json['sport']
    description = request.json['description']
    venue = request.json['venue']
    max_capacity = request.json['max_capacity']
    date_str = request.json['date']
    start_time_str = request.json['start_time']
    end_time_str = request.json['end_time']

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

    return jsonify({'message': 'Event created successfully!', 'event_id': new_event.id}), 201

@app.route('/api/signup_event/<int:event_id>', methods=['POST'])
def signup_event(event_id):
    if 'username' not in session:
        return jsonify({'error': 'You need to be logged in to sign up for an event.'}), 401

    event = Event.query.get(event_id)
    user = User.query.filter_by(username=session['username']).first()

    if event and user:
        existing_signup = EventSignup.query.filter_by(event_id=event.id, user_id=user.id).first()
        if existing_signup:
            return jsonify({'error': 'You are already signed up for this event.'}), 400

    current_signups_count = len(event.signups)

    if current_signups_count < event.max_capacity:
        signup = EventSignup(event_id=event.id, user_id=user.id)
        db.session.add(signup)
        db.session.commit()
        return jsonify({'message': 'You have successfully signed up for the event!'}), 200
    else:
        return jsonify({'error': 'Sorry, this event is full!'}), 400

@app.route('/api/unregister_event/<int:event_id>', methods=['POST'])
def unregister_event(event_id):
    if 'username' not in session:
        return jsonify({'error': 'You need to be logged in to unregister from an event.'}), 401

    event = Event.query.get(event_id)
    user = User.query.filter_by(username=session['username']).first()

    if event and user:
        signup = EventSignup.query.filter_by(event_id=event.id, user_id=user.id).first()
        if signup:
            db.session.delete(signup)
            db.session.commit()
            return jsonify({'message': 'You have successfully unregistered from the event!'}), 200
        else:
            return jsonify({'error': 'You are not signed up for this event.'}), 400

    return jsonify({'error': 'Event or user not found.'}), 404

@app.route('/api/my_events', methods=['GET'])
def my_events():
    if 'username' not in session:
        return jsonify({'error': 'You must be logged in to view your events.'}), 401

    user_events = Event.query.filter_by(organizer_id=session['username']).all()

    events_data = [{
        'event_id': event.id,
        'title': event.title,
        'description': event.description,
        'current_signups': len(event.signups),
        'max_capacity': event.max_capacity,
        'date': event.date.strftime('%Y-%m-%d'),
        'start_time': event.start_time.strftime('%H:%M'),
        'end_time': event.end_time.strftime('%H:%M')
    } for event in user_events]

    return jsonify({'events': events_data}), 200

@app.route('/api/delete_event/<int:event_id>', methods=['POST'])
def delete_event(event_id):
    if 'username' not in session:
        return jsonify({'error': 'You must be logged in to delete an event.'}), 401

    event = Event.query.get(event_id)
    if event and event.organizer_id == session['username']:
        db.session.delete(event)
        db.session.commit()
        return jsonify({'message': 'Event deleted successfully!'}), 200
    else:
        return jsonify({'error': 'You cannot delete this event.'}), 403

@app.route('/api/edit_event/<int:event_id>', methods=['POST'])
def edit_event(event_id):
    if 'username' not in session:
        return jsonify({'error': 'You must be logged in to edit an event.'}), 401

    event = Event.query.get(event_id)
    if not event or event.organizer_id != session['username']:
        return jsonify({'error': 'You cannot edit this event.'}), 403

    event.title = request.json['title']
    event.description = request.json['description']
    event.city = request.json['city']
    event.state = request.json['state']
    event.venue = request.json['venue']
    event.date = datetime.strptime(request.json['date'], '%Y-%m-%d').date()
    event.start_time = datetime.strptime(request.json['start_time'], '%H:%M').time()
    event.end_time = datetime.strptime(request.json['end_time'], '%H:%M').time()

    db.session.commit()
    return jsonify({'message': 'Event updated successfully!'}), 200

@app.route('/api/registered_events', methods=['GET'])
def registered_events():
    if 'username' not in session:
        return jsonify({'error': 'You must be logged in to view registered events.'}), 401

    username = session['username']
    user = User.query.filter_by(username=username).first()

    registered_events = Event.query.join(EventSignup).filter(EventSignup.user_id == user.id).all()

    events_data = [{
        'event_id': event.id,
        'title': event.title,
        'description': event.description,
        'current_signups': len(event.signups),
        'max_capacity': event.max_capacity,
        'date': event.date.strftime('%Y-%m-%d'),
        'start_time': event.start_time.strftime('%H:%M'),
        'end_time': event.end_time.strftime('%H:%M')
    } for event in registered_events]

    return jsonify({'events': events_data}), 200

@app.route('/api/send_request/<int:to_user_id>', methods=['POST'])
def send_request(to_user_id):
    if 'username' not in session:
        return jsonify({'error': 'You must be logged in to send a friend request.'}), 401

    from_user = User.query.filter_by(username=session['username']).first()
    to_user = User.query.get(to_user_id)

    if from_user.id == to_user_id:
        return jsonify({'error': "You can't send a friend request to yourself!"}), 400

    existing_request = Friendship.query.filter_by(user_id=from_user.id, friend_id=to_user.id).first()
    if existing_request:
        return jsonify({'error': 'Friend request already sent!'}), 400
    else:
        new_request = Friendship(user_id=from_user.id, friend_id=to_user.id, status='pending')
        db.session.add(new_request)
        db.session.commit()
        return jsonify({'message': 'Friend request sent!'}), 200

@app.route('/api/accept_request/<int:from_user_id>', methods=['POST'])
def accept_request(from_user_id):
    if 'username' not in session:
        return jsonify({'error': 'You must be logged in to accept a friend request.'}), 401

    to_user = User.query.filter_by(username=session['username']).first()
    friend_request = Friendship.query.filter_by(user_id=from_user_id, friend_id=to_user.id, status='pending').first()

    if friend_request:
        friend_request.status = 'accepted'
        db.session.commit()

        reverse_request = Friendship.query.filter_by(user_id=to_user.id, friend_id=from_user_id).first()
        if not reverse_request:
            new_friendship = Friendship(user_id=to_user.id, friend_id=from_user_id, status='accepted')
            db.session.add(new_friendship)
            db.session.commit()

        return jsonify({'message': 'Friend request accepted!'}), 200
    else:
        return jsonify({'error': 'No friend request found.'}), 404

@app.route('/api/friends', methods=['GET'])
def friends():
    if 'username' not in session:
        return jsonify({'error': 'You must be logged in to view friends.'}), 401

    current_user = User.query.filter_by(username=session['username']).first()

    friends_ids = [f.friend_id for f in current_user.sent_requests if f.status == 'accepted'] + \
                  [f.user_id for f in current_user.received_requests if f.status == 'accepted']

    friends = User.query.filter(User.id.in_(friends_ids)).all()

    friends_data = [{
        'id': friend.id,
        'name': friend.name,
        'phone': friend.phone,
        'email': friend.email,
        'bio': friend.bio,
        'sports': friend.sports,
        'interests': friend.interests,
        'location_city': friend.location_city,
        'location_state': friend.location_state,
        'languages': friend.languages
    } for friend in friends]

    return jsonify({'friends': friends_data}), 200

@app.route('/api/chat', methods=['GET', 'POST'])
def chat():
    if 'username' not in session:
        return jsonify({'error': 'You must be logged in to view this page.'}), 401

    current_user = User.query.filter_by(username=session['username']).first()

    friend_id = session.get('friend_id')
    if not friend_id:
        return jsonify({'error': 'No chat initiated. Please start a chat from the Friends page.'}), 400

    friend = User.query.get(friend_id)

    if request.method == 'POST':
        message_text = request.json.get('message')
        if message_text:
            new_message = ChatMessage(sender_id=current_user.id, recipient_id=friend_id, message=message_text)
            db.session.add(new_message)
            db.session.commit()
            return jsonify({'message': 'Message sent!'}), 201

    chat_history = ChatMessage.query.filter(
        ((ChatMessage.sender_id == current_user.id) & (ChatMessage.recipient_id == friend_id)) |
        ((ChatMessage.sender_id == friend_id) & (ChatMessage.recipient_id == current_user.id))
    ).order_by(ChatMessage.timestamp).all()

    history = [{
        'sender': msg.sender.username,
        'message': msg.message,
        'timestamp': msg.timestamp.isoformat()
    } for msg in chat_history]

    return jsonify({'chat_history': history}), 200

@app.route('/api/start_chat', methods=['POST'])
def start_chat():
    if 'username' not in session:
        return jsonify({'error': 'You must be logged in to start a chat.'}), 401

    friend_id = request.json.get('friend_id')

    if friend_id:
        session['friend_id'] = friend_id
        return jsonify({'message': 'Chat started!'}), 200

    return jsonify({'error': 'Could not start chat. Please try again.'}), 400

@app.route('/api/suggest_message', methods=['POST'])
def suggest_message():
    if 'username' not in session:
        return jsonify({'error': 'You must be logged in to get message suggestions.'}), 403

    current_user = User.query.filter_by(username=session['username']).first()
    friend_id = session.get('friend_id')

    if not friend_id:
        return jsonify({'error': 'No friend selected.'}), 400

    friend = User.query.get(friend_id)

    if not friend:
        return jsonify({'error': 'Friend not found.'}), 404

    chat_history = ChatMessage.query.filter(
        ((ChatMessage.sender_id == current_user.id) & (ChatMessage.recipient_id == friend_id)) |
        ((ChatMessage.sender_id == friend_id) & (ChatMessage.recipient_id == current_user.id))
    ).order_by(ChatMessage.timestamp.desc()).limit(10).all()

    chat_history_text = "\n".join([f"{msg.sender.username}: {msg.message}" for msg in chat_history[::-1]])

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
        result = generator(
            prompt,
            max_new_tokens=50,
            return_full_text=False,
            truncation=True
        )
        suggestion = result[0]['generated_text'].strip()

        return jsonify({"suggestion": suggestion}), 200

    except Exception as e:
        app.logger.error(f"Error generating message: {e}")
        return jsonify({"error": "Failed to generate a suggestion."}), 500
