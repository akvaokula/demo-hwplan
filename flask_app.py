
# A very simple Flask Hello World app for you to get started with...

from flask import Flask, render_template, current_user

app = Flask(__name__)
app.config['DEBUG'] = True

SQLALCHEMY_DATABASE_URI = f"mysql+mysqlconnecttor://{hwplan}:{passphrase}@hwplan.mysql.pythonanywhere-services.com/hwplan$default"
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 299

@app.route('/', methods=['GET', 'POST'])
def index():
    if current_user.is_authenticated:
    return render_template("index.html")

@app.route('/signup')
def signup():
    return render_template("signup.html")

@app.route('/signin')
def signin():
    return render_template("signin.html")

@app.route('/signedin')
    return render_template("signedin.html")

