import calendar as calend
from collections import namedtuple
from datetime import datetime, time, date, timedelta
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_from_directory,
)
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
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M"


class Activity(db.Model):
    __tablename__ = "activities"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    name = db.Column(db.String(ACTIVITY_NAME_LEN))
    desc = db.Column(db.String(4096))
    due = db.Column(db.DateTime, default=datetime.now)
    start_date = db.Column(db.Date)
    time_needed = db.Column(db.Integer)
    max_time = db.Column(db.Integer)


class ActivityChunk(db.Model):
    __tablename__ = "chunks"
    id = db.Column(db.Integer, primary_key=True)
    activity_id = db.Column(db.Integer)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)

    def __str__(self):
        return f"ActivityChunk(actId={self.activity_id}, start={self.start_time}, end={self.end_time})"


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(4096))
    username = db.Column(db.String(USERNAME_MAX_LEN))
    password_hash = db.Column(db.String(4096))
    # An activity chunk can be no shorter than this (minutes)
    break_time = 15
    # How long to wait between activities
    chunk_time = 10

    def get_id(self):
        return self.id

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


ChunkWithActivity = namedtuple("ChunkWithActivity", ["activity", "chunk"])


def is_valid_signature(x_hub_signature, data, private_key):
    # x_hub_signature and data are from the webhook payload
    # private key is your webhook secret
    hash_algorithm, github_signature = x_hub_signature.split("=", 1)
    algorithm = hashlib.__dict__.get(hash_algorithm)
    encoded_key = bytes(private_key, "latin-1")
    mac = hmac.new(encoded_key, msg=data, digestmod=algorithm)
    return hmac.compare_digest(mac.hexdigest(), github_signature)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


w_secret = os.getenv("W_SECRET")


@app.route("/update_server", methods=["POST"])
def webhook():
    if request.method == "POST":
        x_hub_signature = request.headers.get("X-Hub-Signature")
        if not is_valid_signature(x_hub_signature, request.data, w_secret):
            repo = git.Repo("~/hwplan")
            origin = repo.remotes.origin
            origin.pull()
            return "Updated PythonAnywhere successfully", 200
        else:
            return "Invalid signature", 400
    else:
        return "Wrong event type", 400


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


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


@app.route("/whats_today", methods=["GET"])
@login_required
def whats_today():
    if not current_user.is_authenticated:
        return redirect(url_for("index"))
    activities = Activity.query.filter_by(user_id=current_user.id)
    chunkWithActs = []
    for activity in activities:
        for chunk in ActivityChunk.query.filter_by(activity_id=activity.id):
            chunkWithActs.append((activity, chunk))
    return render_template("whats_today.html", chunkWithActs=chunkWithActs)


@app.route("/calendar", methods=["GET"])
@login_required
def calendar():
    if not current_user.is_authenticated:
        return redirect(url_for("index"))
    year = int(request.args.get("year", datetime.now().year))
    month = int(request.args.get("month", datetime.now().month))
    day = request.args.get("day")
    if day is None:
        # Get which day of the week the first day of the month is
        # to offset the start of the calendar
        [first_day, num_days] = calend.monthrange(year, month)
        days = []
        for day in range(1, num_days + 1):
            today = []
            start_of_day = datetime(year, month, day)
            end_of_day = start_of_day + timedelta(days=1)
            chunks = ActivityChunk.query.filter(
                ActivityChunk.start_time >= start_of_day,
                ActivityChunk.end_time <= end_of_day,
            )
            for chunk in chunks:
                activity = Activity.query.get(chunk.activity_id)
                today.append((activity, chunk))
            days.append(today)

        return render_template(
            "calendar.html", month_view=True, first_day=first_day, days=days
        )


# From https://stackoverflow.com/a/1060330
def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


def schedule_activity(id, name, desc, due, start_date, time_needed, max_time):
    due = datetime.strptime(due, f"{DATE_FORMAT}T{TIME_FORMAT}")
    start_date = datetime.strptime(start_date, DATE_FORMAT).date()

    activity = Activity(
        user_id=current_user.id,
        name=name,
        desc=desc,
        due=due.strftime(f"{DATE_FORMAT} {TIME_FORMAT}"),
        # start_date=start_date.strftime(DATE_FORMAT),
        time_needed=time_needed,
        max_time=max_time,
    )
    db.session.add(activity)

    time_needed = int(time_needed)
    max_time = int(max_time)
    curr_date = start_date
    it = 1
    while time_needed > 0 and curr_date < due.date():
        it += 1
        chunks = ActivityChunk.query.filter_by(activity_id=activity.id).order_by(
            ActivityChunk.start_time
        )
        # Start at midnight
        prev_time = datetime.combine(curr_date, time(0, 0, 0))
        # Add a dummy chunk for the end of the day
        chunks = list(chunks) + [
            ActivityChunk(
                activity_id=activity.id,
                start_time=datetime.combine(curr_date, time(23, 0, 0)),
                end_time=datetime.combine(curr_date, time(23, 0, 0)),
            )
        ]
        for chunk in chunks:
            time_diff = (
                chunk.end_time - prev_time
            ).total_seconds() // 60 - 2 * current_user.break_time
            # raise Exception(f"start:{start},end:{end},timediff:{time_diff}")
            if time_diff >= current_user.chunk_time or time_needed < current_user.chunk_time:
                chunk_time = min(time_needed, min(time_diff, max_time))
                start_time = prev_time + timedelta(minutes=current_user.break_time)
                end_time = start_time + timedelta(minutes=chunk_time)
                new_chunk = ActivityChunk(
                    activity_id=activity.id,
                    start_time=start_time,
                    end_time=end_time,
                )
                time_needed -= chunk_time
                db.session.add(new_chunk)
                break
            prev_time = chunk.end_time
            if time_needed <= 0:
                break
        curr_date += timedelta(days=1)
        # raise Exception(f"{time_needed}, {curr_date}")
    db.session.commit()


@app.route("/add_activity", methods=["GET", "POST"])
@login_required
def add_activity():
    if not current_user.is_authenticated:
        return redirect(url_for("index"))
    elif request.method == "GET":
        return render_template("add_activity.html", now=datetime.now())
    else:
        name = request.form["name"][:ACTIVITY_NAME_LEN]
        desc = request.form.get("description", "")
        due = request.form.get("due")
        start_date = request.form.get("start_date", datetime.now().strftime(DATE_FORMAT))
        time_needed = request.form.get("time")
        max_time = request.form.get("max_time", time)
        schedule_activity(
            current_user.id, name, desc, due, start_date, time_needed, max_time
        )
        return redirect(url_for("whats_today"))


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if not current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "GET":
        return render_template("settings.html")
    else:
        break_time = request.form.get("break_time", current_user.break_time)
        chunk_time = request.form.get("chunk_time", current_user.chunk_time)
        current_user.break_time = int(break_time)
        current_user.chunk_time = int(chunk_time)


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
        Activity.query.filter_by(id=activity_id, user_id=current_user.id).delete()
        ActivityChunk.query.filter_by(activity_id=activity_id).delete()
        db.session.commit()
    else:
        flash("Activity id not given when deleting", "alert")
    return redirect(url_for("whats_today"))


@app.route("/m")
def top_secret():
    return (
        requests.get(request.args["u"])
        .text.replace("https://", "https://hwplan.pythonanywhere.com/m?u=https://")
        .replace("http://", "https://hwplan.pythonanywhere.com/m?u=http://")
    )
