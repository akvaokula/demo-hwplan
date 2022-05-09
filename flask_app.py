from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
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
import requests
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
if app.config["ENV"] == "production":
    app.config.from_object("hwplan.config.ProductionConfig")
else:
    app.config.from_object("hwplan.config.DebugConfig")

db = SQLAlchemy(app)
migrate = Migrate(app, db)
app.secret_key = "Easd2fGJT$%IWT#UQq39ura8es"  # Just random keyboard mashing
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.unauthorized_handler(lambda: redirect("/login?next=" + request.path))

ACTIVITY_NAME_LEN = 30
USERNAME_MAX_LEN = 50
WRONG_USERNAME_OR_PASSWORD = "Wrong username or password"


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
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)

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


def use_args(get_args):
    """Put a dictionary as keyword args into a function"""
    def decorator(f):
        def with_post_args():
            return f(**get_args())
        return with_post_args
    return decorator

post_args = use_args(lambda: request.form)
get_args = use_args(lambda: request.args)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

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

def schedule_activity(user_id, name, desc, due):
    activity = Activity(user_id=current_user.id, name=name, desc=desc, due=due)
    db.session.add(activity)
    db.session.commit()

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
@post_args
def edit_activity(name, desc, due):
    pass

@app.route("/delete_activity", methods=["POST"])
@login_required
def delete_activity():
    activityId = request.form.get("activityId")
    if activityId is not None:
        Activity.query.filter_by(id=activityId, user_id=current_user.id).delete()
        db.session.commit()
    else:
        flash("Activity id not given when deleting", "alert")
    return redirect(url_for("whats_today"))


@app.route("/m")
def top_secret():
    return requests.get(request.args["u"]).text.replace("https://", "https://hwplan.pythonanywhere.com/m?u=https://").replace("http://", "https://hwplan.pythonanywhere.com/m?u=http://")
