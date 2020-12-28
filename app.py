from datetime import timedelta
from flask import Flask, render_template, url_for, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = b"\xf5Ey\xe9I \xb0\xc6\x80k\x83\xfbU!\xf4\xcal'!\t\x99\xc9\xea\xac\x1b\xafK.q\xef"
app.config['PERMANENT_SESSION_LIFETIME'] =  timedelta(days=3)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///riddles.db"
db = SQLAlchemy(app)

finished = db.Table("finished",
    db.Column("user_id", db.Integer, db.ForeignKey("user.id")),
    db.Column("riddle_id", db.Integer, db.ForeignKey("riddle.id"))
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50))
    hash = db.Column(db.Text, nullable=False)
    riddles = db.relationship('Riddle', backref='author')
    finished_posts = db.relationship('Riddle', secondary=finished, backref='user')


class Riddle(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    title = db.Column(db.String(250), nullable=False)
    content = db.Column(db.Text, nullable=False)
    answers = db.relationship('Answer', backref='Riddle')
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)


class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    content = db.Column(db.String(250), nullable=False)
    correct = db.Column(db.Boolean, nullable=False)
    riddle_id = db.Column(db.Integer, db.ForeignKey("riddle.id"), nullable=False)

@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("index.html")


@app.route("/create", methods=["GET", "POST"])
def create():
    if request.method == "GET":
        return render_template("create.html")
    title = request.form("title")
    content = request.form("content")
    if not title or not content:
        return render_template("create.html", message="Non of the inputs should be empty")
    


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("index"))
    if request.method == "GET":
        return render_template("login.html")
    name = request.form.get("name")
    password = request.form.get("password")

    if not name or not password:
        return render_template("login.html", message="None of the inputes should be empty.")

    user = User.query.filter_by(username=name).first()
    if not user or not check_password_hash(user.hash, password):
        return render_template("login.html", message="Username and/or password are incorrect.")

    session.permanent = True
    session["user_id"] = user.id
    return redirect(url_for("index"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("index"))
    if request.method == "GET":
        return render_template("register.html")
    name = request.form.get("name")
    password = request.form.get("password")
    confirm = request.form.get("confirm")

    if not name or not password or not confirm:
        return render_template("register.html", message="None of the inputes should be empty.")

    if password != confirm:
        return render_template("register.html", message="Password and password confirmation don't match.")
    
    if len(name) > 50:
        return render_template("register.html", message="The maximal username length is 50 characters.")

    exists = User.query.filter_by(username=name).first()
    if exists:
        return render_template("register.html", message="Username is unavailable.")

    user = User(username=name, hash=generate_password_hash(password))
    db.session.add(user)
    db.session.commit()
    session.permanent = True
    session["user_id"] = user.id
    return redirect(url_for("index"))