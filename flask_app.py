from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import login_user, login_required, logout_user, LoginManager, UserMixin, current_user
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
if app.config["ENV"] == "production":
    app.config.from_object("hwplan.config.ProductionConfig")
else:
    app.config.from_object("hwplan.config.DebugConfig")

db = SQLAlchemy(app)
migrate = Migrate(app, db)
app.secret_key = "Easd2fGJT$%IWT#UQq39ura8es" # Just random keyboard mashing
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.unauthorized_handler(lambda: redirect('/login?next=' + request.path))

ACTIVITY_NAME_LEN = 30

class User(UserMixin):
    def __init__(self, username, password_hash):
        self.username = username
        self.password_hash = password_hash

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return self.username

all_users = {
    "admin": User("admin", generate_password_hash("secret")),
    "alice": User("alice", generate_password_hash("foo")),
    "bob": User("bob", generate_password_hash("bar"))
}

class Activity(db.Model):
    __tablename__ = "activities"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(ACTIVITY_NAME_LEN))
    desc = db.Column(db.String(4096))

@login_manager.user_loader
def load_user(user_id):
    return all_users.get(user_id)

@app.route('/', methods=["GET", "POST"])
@app.route('/index', methods=["GET", "POST"])
def index():
    if current_user.is_authenticated:
        return whats_today()
    else:
        return render_template("index.html")

@app.route('/signup', methods=["GET", "POST"])
def signup():
    return render_template("signup.html")

LOGIN_PAGE = "login.html"
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "GET":
        # Just getting the sign in page, not signed in yet
        return render_template(LOGIN_PAGE)

    # Submitted the signin form
    username = request.form["username"]
    password = request.form["password"]
    if username not in all_users:
        flash("Wrong username or password", "alert")
        return render_template(LOGIN_PAGE)
    user = all_users[username]
    if not user.check_password(password):
        flash("Wrong username or password", "alert")
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
        return redirect(url_for('index'))
    return render_template("whats_today.html", activities=Activity.query.all())

@app.route("/calendar", methods=["GET", "POST"])
@login_required
def calendar():
    if not current_user.is_authenticated:
        return redirect(url_for('index'))
    return render_template("calendar.html")

@app.route("/add_activity", methods=["GET", "POST"])
@login_required
def add_activity():
    if not current_user.is_authenticated:
        return redirect(url_for('index'))
    elif request.method == "GET":
        return render_template("add_activity.html")
    else:
        name = request.form.get("name")[:ACTIVITY_NAME_LEN]
        desc = request.form.get("description", "")
        activity = Activity(name=name, desc=desc)
        db.session.add(activity)
        db.session.commit()
        return redirect(url_for("whats_today"))

@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if not current_user.is_authenticated:
        return redirect(url_for('index'))
    return render_template("settings.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return render_template("index.html")
