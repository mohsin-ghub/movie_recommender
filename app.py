import os
from flask import Flask, render_template, request, flash, redirect, url_for, session
from dotenv import load_dotenv
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from flask_caching import Cache
from markupsafe import escape
from utils import get_env_key, get_movie_poster, get_ai_recommendations, extract_title_and_year
from typing import Optional
import re
from flask_sqlalchemy import SQLAlchemy
import bcrypt

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev_secret_key')  # Required for CSRF and flash
csrf = CSRFProtect(app)

# Configure Flask-Caching
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

OPENROUTER_API_KEY = get_env_key("OPENROUTER_API_KEY")
OMDB_API_KEY = get_env_key("OMDB_API_KEY")

class MovieForm(FlaskForm):
    movie = StringField('Movie', validators=[DataRequired(), Length(max=100)])

class SignupForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8, max=64)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match.')])

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired()])

def is_strong_password(password: str) -> bool:
    # At least 8 chars, 1 uppercase, 1 lowercase, 1 digit, 1 special char
    import re
    return (
        len(password) >= 8 and
        re.search(r'[A-Z]', password) and
        re.search(r'[a-z]', password) and
        re.search(r'\d', password) and
        re.search(r'[^A-Za-z0-9]', password)
    )

def get_cached_movie_poster(title: str, year: Optional[str]) -> str:
    """
    Get movie poster URL with caching.
    """
    cache_key = f"poster:{title}:{year}"
    poster = cache.get(cache_key)
    if poster is None:
        poster = get_movie_poster(title, year, OMDB_API_KEY)
        cache.set(cache_key, poster, timeout=60*60*24)  # Cache for 24 hours
    return poster

@app.route("/", methods=["GET"])
def landing():
    """Landing page route."""
    return render_template("landing.html")

@app.route('/login-signup', methods=['GET'])
def login_signup():
    # Default to login form
    form = LoginForm()
    return render_template('login_signup.html', form=form, show_signup=False)

@app.route("/recommender", methods=["GET", "POST"])
def home():
    """Main recommender route."""
    form = MovieForm()
    query = ""
    results = []
    error = None
    generic_texts = []
    if form.validate_on_submit():
        query = escape(form.movie.data.strip())
        if query:
            movie_strings = get_ai_recommendations(query, OPENROUTER_API_KEY)
            title_years = [extract_title_and_year(line) for line in movie_strings]
            posters = []
            failed_count = 0
            for title, year in title_years:
                poster = get_cached_movie_poster(title, year)
                if poster.endswith("No+Image"):
                    failed_count += 1
                posters.append(poster)
            def split_title_desc(s):
                parts = re.split(r"\s*[\u2013\-:]\s+", s, maxsplit=1)
                if len(parts) == 2:
                    return parts[0].strip(), parts[1].strip()
                return s.strip(), ""
            results = []
            for movie_str, poster in zip(movie_strings, posters):
                title, desc = split_title_desc(movie_str)
                title = title.replace('*', '').strip()
                if (not desc and (len(title) > 60 or 'movie' in title.lower() or 'recommend' in title.lower() or 'like' in title.lower())) or (poster.endswith('No+Image') and not desc):
                    generic_texts.append(title)
                else:
                    results.append((title, desc, poster))
            if failed_count == len(title_years):
                flash("No posters found for any recommended movies. Check OMDB API key or title format.", "error")
    elif request.method == "POST":
        flash("Invalid input. Please enter a valid movie name.", "error")
    return render_template("index.html", query=query, results=results, error=error, generic_texts=generic_texts, form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        password = form.password.data
        if not is_strong_password(password):
            flash('Password must be at least 8 characters and include uppercase, lowercase, digit, and special character.', 'error')
            return render_template('login_signup.html', form=form, show_signup=True)
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('login_signup.html', form=form, show_signup=True)
        pw_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        user = User(email=email, password_hash=pw_hash.decode('utf-8'))
        db.session.add(user)
        db.session.commit()
        flash('Signup successful! Please log in.', 'success')
        return redirect(url_for('login_signup'))
    return render_template('login_signup.html', form=form, show_signup=True)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        password = form.password.data
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            session['user_id'] = user.id
            session['user_email'] = user.email
            flash('Logged in successfully!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password.', 'error')
    return render_template('login_signup.html', form=form, show_signup=False)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out.', 'success')
    return redirect(url_for('login_signup'))

if __name__ == "__main__":
    app.run(debug=True)
    
