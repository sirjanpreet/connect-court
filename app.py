import os

from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3


app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"



@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template('login.html')
    print(request.form.get("username"))
    print(request.form.get("password"))
    return render_template("home")


if __name__ == '__main__':
    app.run(debug=True, port=5000)