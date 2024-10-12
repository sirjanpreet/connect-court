from flask import Flask, render_template, request, redirect, url_for, flash, session
from models import db, User

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'b1b2f5b74c3b5fdbcdde4f218f6d3e2ff3a1fcd0ad63de452391ef8c9bf4a9d1'
db.init_app(app)

# Create the database tables
with app.app_context():
    db.create_all()

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

# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)  # Remove username from session
    flash('You have been logged out.')
    return render_template('logout.html')  # Render a logout confirmation page

if __name__ == '__main__':
    app.run(debug=True)
