from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['DEBUG'] = True

SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnecttor://hwplan:passphrase@hwplan.mysql.pythonanywhere-services.com/hwplan$default"
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

@app.route('/', methods=["GET", "POST"])
def index():
    return render_template("index.html")

@app.route('/signup')
def signup():
    return render_template("signup.html")

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == "GET":
        return render_template("signin.html", error=False)
    elif request.form["username"] != "admin" or request.form["password"] != "secret":
        return render_template("signin.html", error=True)
    else:
        return redirect(url_for("signedin"))

@app.route('/signedin')
def signedin():
    return render_template("signedin.html")
