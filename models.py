from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    name = db.Column(db.String(150), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(150), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    age = db.Column(db.Integer, nullable=True)
    sports = db.Column(db.String(200), nullable=True)
    interests = db.Column(db.String(200), nullable=True)
    location_city = db.Column(db.String(100), nullable=True)
    location_state = db.Column(db.String(50), nullable=True)
    languages = db.Column(db.String(200), nullable=True)
    gender = db.Column(db.String(50), nullable=True)
    pronouns = db.Column(db.String(50), nullable=True)
    school_work = db.Column(db.String(150), nullable=True)
    profile_picture = db.Column(db.String(250), nullable=True)

class Friendship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')  # 'pending' or 'accepted'

    user = db.relationship('User', foreign_keys=[user_id], backref='sent_requests')
    friend = db.relationship('User', foreign_keys=[friend_id], backref='received_requests')

    def __repr__(self):
        return f'<User {self.username}>'

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    sport = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    venue = db.Column(db.String(150), nullable=False)
    max_capacity = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False) 
    organizer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    signups = db.relationship('EventSignup', backref='event', lazy=True)

    def get_signups_usernames(self):
        return [signup.user_id for signup in self.signups]

    def __repr__(self):
        return f'<Event {self.title} by {self.organizer_id}>'

class EventSignup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)

    def __repr__(self):
        return f'<Signup {self.user.username} for {self.event.title}>'
