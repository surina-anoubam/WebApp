from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import secrets

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///short_links.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    links = db.relationship('ShortLink', backref='user', lazy=True)


class ShortLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.String(200), nullable=False)
    short_code = db.Column(db.String(10), unique=True, nullable=False)
    creation_date = db.Column(db.DateTime, default=datetime.utcnow)
    expiration_date = db.Column(db.DateTime, default=datetime.utcnow() + timedelta(days=2))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


@app.route('/')
def home():
    return 'Welcome to the Short Link Web App!'


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()

        if user:
            session['user_id'] = user.id
            flash('Login successful', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logout successful', 'success')
    return redirect(url_for('home'))


@app.route('/dashboard')
def dashboard():
    user_id = session.get('user_id')

    if user_id:
        user = User.query.get(user_id)
        user_links = ShortLink.query.filter_by(user=user).all()
        return render_template('dashboard.html', user_links=user_links)
    else:
        flash('Please login to access the dashboard', 'error')
        return redirect(url_for('login'))


@app.route('/create', methods=['POST'])
def create_short_link():
    user_id = session.get('user_id')

    if user_id:
        user = User.query.get(user_id)
        original_url = request.form['original_url']
        short_code = secrets.token_urlsafe(5)[:5]
        short_link = ShortLink(original_url=original_url, short_code=short_code, user=user)
        db.session.add(short_link)
        db.session.commit()
        flash(f'Short link created: {request.url_root}{short_code}', 'success')
        return redirect(url_for('dashboard'))
    else:
        flash('Please login to create short links', 'error')
        return redirect(url_for('login'))


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
