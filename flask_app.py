
# A very simple Flask Hello World app for you to get started with...

from flask import Flask, render_template, current_user

app = Flask(__name__)

app.config['DEBUG'] = True

@app.route('/')
def homepage():
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

