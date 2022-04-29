from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_user, LoginManager, UserMixin, current_user
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

@app.route('/sign_in', methods=['GET', 'POST'])
def sign_in():
    if request.method == "GET":
        # Just getting the sign in page, not signed in yet
        return render_template("sign_in.html")

    # Submitted the signin form
    username = request.form["username"]
    password = request.form["password"]
    if username not in all_users:
        flash("Wrong username or password")
        return render_template("sign_in.html")
    user = all_users[username]
    if not user.check_password(password):
        flash("Wrong username or password", "alert")
        return render_template("sign_in.html")
    # Success!
    login_user(user)
    return redirect(url_for("/"))

@app.route("/whats_today", methods=["GET", "POST"])
def whats_today():
    return render_template("whats_today.html")
