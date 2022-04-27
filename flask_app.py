
# A very simple Flask Hello World app for you to get started with...

from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def homepage():
    return render_template("index.html")

@app.route('/signup')
def signup():
    return render_template("signup.html")

@app.route('/signin')
def signin():
    return render_template("signin.html")

