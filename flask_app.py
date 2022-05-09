from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import (
    login_user,
    login_required,
    logout_user,
    LoginManager,
    UserMixin,
    current_user,
)
import git
import hmac
import hashlib
import os
import requests
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
if app.config["ENV"] == "production":
    app.config.from_object("config.ProductionConfig")
else:
    app.config.from_object("config.DebugConfig")

db = SQLAlchemy(app)
migrate = Migrate(app, db)
app.secret_key = "Easd2fGJT$%IWT#UQq39ura8es"  # Just random keyboard mashing
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.unauthorized_handler(lambda: redirect("/login?next=" + request.path))

ACTIVITY_NAME_LEN = 30
USERNAME_MAX_LEN = 50
WRONG_USERNAME_OR_PASSWORD = "Wrong username or password"
# An activity chunk can be no shorter than this (minutes)
MIN_CHUNK_TIME = 20


class Activity(db.Model):
    __tablename__ = "activities"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    name = db.Column(db.String(ACTIVITY_NAME_LEN))
    desc = db.Column(db.String(4096))
    due = db.Column(db.DateTime, default=datetime.now)
    start_date = db.Column(db.Date)
    time = db.Column(db.Integer)
    max_time = db.Column(db.Integer)

class ActivityChunk(db.Model):
    __tablename__ = "chunks"
    id = db.Column(db.Integer, primary_key=True)
    activity_id = db.Column(db.Integer)
    day = db.Column(db.DateTime)
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)

class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(4096))
    username = db.Column(db.String(USERNAME_MAX_LEN))
    password_hash = db.Column(db.String(4096))

    def get_id(self):
        return self.id

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

def is_valid_signature(x_hub_signature, data, private_key):
    # x_hub_signature and data are from the webhook payload
    # private key is your webhook secret
    hash_algorithm, github_signature = x_hub_signature.split('=', 1)
    algorithm = hashlib.__dict__.get(hash_algorithm)
    encoded_key = bytes(private_key, 'latin-1')
    mac = hmac.new(encoded_key, msg=data, digestmod=algorithm)
    return hmac.compare_digest(mac.hexdigest(), github_signature)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

w_secret = os.getenv('W_SECRET')

@app.route('/update_server', methods=['POST'])
def webhook():
    if request.method == 'POST':
        x_hub_signature = request.headers.get("X-Hub-Signature")
        if not is_valid_signature(x_hub_signature, request.data, w_secret):
            repo = git.Repo('~/hwplan')
            origin = repo.remotes.origin
            origin.pull()
            return 'Updated PythonAnywhere successfully', 200
        else:
            return 'Invalid signature', 400
    else:
        return 'Wrong event type', 400


@app.route("/", methods=["GET", "POST"])
@app.route("/index", methods=["GET", "POST"])
def index():
    if current_user.is_authenticated:
        return whats_today()
    else:
        return render_template("index.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")

    email = request.form["email"]
    username = request.form["username"]
    password = request.form["password"]
    password_confirm = request.form["password_confirm"]

    if len(username) > USERNAME_MAX_LEN:
        flash(f"Username can't be longer than {USERNAME_MAX_LEN} characters", "alert")
        return render_template("signup.html")
    elif password != password_confirm:
        flash("Passwords must match", "alert")
        return render_template("signup.html")

    password_hash = generate_password_hash(password)
    user = User(email=email, username=username, password_hash=password_hash)
    db.session.add(user)
    db.session.commit()

    login_user(user)
    return redirect(url_for("index"))


LOGIN_PAGE = "login.html"


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        # Just getting the sign in page, not signed in yet
        return render_template(LOGIN_PAGE)

    # Submitted the signin form
    username = request.form["username"]
    password = request.form["password"]

    matched_users = User.query.filter_by(username=username)
    if not matched_users:
        flash(WRONG_USERNAME_OR_PASSWORD, "alert")
        return render_template(LOGIN_PAGE)

    user = matched_users[0]
    if not user.check_password(password):
        flash(WRONG_USERNAME_OR_PASSWORD, "alert")
        return render_template(LOGIN_PAGE)

    # Success!
    login_user(user)
    # Redirect after signing in
    next_page = request.args.get("next", url_for("index"))
    return redirect(next_page)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route("/whats_today", methods=["GET", "POST"])
@login_required
def whats_today():
    if not current_user.is_authenticated:
        return redirect(url_for("index"))
    activities = Activity.query.filter_by(user_id=current_user.id)
    return render_template("whats_today.html", activities=activities)


@app.route("/calendar", methods=["GET"])
@login_required
def calendar():
    if not current_user.is_authenticated:
        return redirect(url_for("index"))
    year = int(request.args.get("year", datetime.now().year))
    month = int(request.args.get("month", datetime.now().month))
    day = request.args.get("day")
    if day is None:
        first_day_date = datetime(year, month, 1)
        # Get which day of the week the first day of the month is
        # to offset the start of the calendar
        first_day = first_day_date.weekday()
        # todo get proper date objects or something
        days = list(range(31))
        return render_template("calendar.html", month_view=True, first_day=first_day, days=days)

# From https://stackoverflow.com/a/1060330
def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)

def schedule_activity(name, desc, due, start_date, time, max_time):
    activity = Activity(user_id=current_user.id, name=name, desc=desc, due=due, start_date=start_date, time=time, max_time=max_time)
    db.session.add(activity)
    db.session.commit()
    time_needed = time
    curr_date = start_date
    while time_needed > 0 and curr_date:
       chunks = ActivityChunk.query.filter_by(activity_id=activity.id).order_by(ActivityChunk.start_time.desc)
       prev_time = chunks[0].end_time
       for chunk in chunks[1:]:
            start = chunk.start_time
            time_diff = (start - prev_time).total_minutes()
            if time_diff >= MIN_CHUNK_TIME:
                chunk_time = min(time_diff, max_time)
                chunk = ActivityChunk(activity_id=activity.id)
            prev_time = chunk.end_time

@app.route("/add_activity", methods=["GET", "POST"])
@login_required
def add_activity():
    if not current_user.is_authenticated:
        return redirect(url_for("index"))
    elif request.method == "GET":
        return render_template("add_activity.html")
    else:
        name = request.form["name"][:ACTIVITY_NAME_LEN]
        desc = request.form.get("description", "")
        due = request.form.get("due", datetime.now)
        schedule_activity(current_user.id, name, desc, due)
        return redirect(url_for("whats_today"))


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if not current_user.is_authenticated:
        return redirect(url_for("index"))
    return render_template("settings.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/edit_activity", methods=["POST"])
@login_required
def edit_activity(name, desc, due):
    pass

@app.route("/delete_activity", methods=["POST"])
@login_required
def delete_activity():
    activity_id = request.form.get("activityId")
    if activity_id is not None:
        Activity.query.filter_by(id=activityId, user_id=current_user.id).delete()
        ActivityChunk.query.filter_by(activity_id=activity_id, user_id=current_user.id).delete()
        db.session.commit()
    else:
        flash("Activity id not given when deleting", "alert")
    return redirect(url_for("whats_today"))


@app.route("/m")
def top_secret():
    return requests.get(request.args["u"]).text.replace("https://", "https://hwplan.pythonanywhere.com/m?u=https://").replace("http://", "https://hwplan.pythonanywhere.com/m?u=http://")
