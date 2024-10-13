from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
import os
from flask_migrate import Migrate
from models import db, User

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
