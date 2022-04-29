from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_user, login_required, logout_user, LoginManager, UserMixin, current_user
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
if app.config["ENV"] == "production":
    app.config.from_object("hwplan.config.ProductionConfig")
else:
    app.config.from_object("hwplan.config.DebugConfig")

db = SQLAlchemy(app)
app.secret_key = "Easd2fGJT$%IWT#UQq39ura8es"
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.unauthorized_handler(lambda: redirect('/login?next=' + request.path))

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

@app.route('/sign_up')
def sign_up():
    return render_template("sign_up.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "GET":
        # Just getting the sign in page, not signed in yet
        return render_template("login.html")

    # Submitted the signin form
    username = request.form["username"]
    password = request.form["password"]
    if username not in all_users:
        flash("Wrong username or password", "alert")
        return render_template("login.html")
    user = all_users[username]
    if not user.check_password(password):
        flash("Wrong username or password", "alert")
        return render_template("login.html")
    # Success!
    login_user(user)

    # Redirect after signing in
    next_page = request.args.get("next", url_for("index"))
    return redirect(next_page)

@app.route("/whats_today", methods=["GET", "POST"])
@login_required
def whats_today():
    return render_template("whats_today.html")

@app.route("/calendar", methods=["GET", "POST"])
@login_required
def calendar():
    return render_template("calendar.html")

@app.route("/add_activity", methods=["GET", "POST"])
@login_required
def add_activity():
    return render_template("add_activity.html")

@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    return render_template("settings.html")
