from datetime import timedelta, datetime
from flask import Flask, render_template, url_for, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = b"\xf5Ey\xe9I \xb0\xc6\x80k\x83\xfbU!\xf4\xcal'!\t\x99\xc9\xea\xac\x1b\xafK.q\xef"
app.config['PERMANENT_SESSION_LIFETIME'] =  timedelta(days=3)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///riddles.db"
app.config["SQLALCHEMY_ECHO"] = True
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
    finished_posts = db.relationship('Riddle', secondary=finished, backref='users', lazy='dynamic')


class Riddle(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    title = db.Column(db.String(250), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    answers = db.relationship('Answer', backref='Riddle')
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)


class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    content = db.Column(db.String(250), nullable=False)
    correct = db.Column(db.Boolean, nullable=False)
    riddle_id = db.Column(db.Integer, db.ForeignKey("riddle.id"), nullable=False)

@app.route("/riddle/<int:riddle_id>", methods=["GET", "POST"])
def question(riddle_id):
    if request.method == "GET":
        return Riddle.query.filter_by(id=riddle_id).first().content


@app.route("/", methods=["GET"])
def index():
    if request.method == "GET":
        posts = Riddle.query.order_by(desc(Riddle.date)).paginate(per_page=5)
        return render_template("index.html", pagination=posts, p=1)


@app.route('/<int:page>')
def page(page):
    if page < 2:
        return redirect(url_for("index"))
    posts = Riddle.query.order_by(desc(Riddle.date)).paginate(per_page=5, page=page)
    return render_template("index.html", pagination=posts, p=page)


@app.route("/create", methods=["GET", "POST"])
def create():
    if "user_id" not in session:
        return redirect(url_for("login"))
    exists = User.query.with_entities(Riddle.id).filter_by(id=session["user_id"]).first()
    if not exists:
        session.pop("user_id", None)
        return redirect(url_for("login"))
        
    if request.method == "GET":
        return render_template("create.html")

    title = request.form.get("title")
    content = request.form.get("content")
    if not title or not content:
        return render_template("create.html", message="Non of the inputs should be empty")
    if len(title) > 50:
        return render_template("create.html", message="The maximum title length should be 50 characters")
    amount = request.form.get("amount")
    if not isint(amount):
        return render_template("create.html", message="The amount of answers should be an integer.")
    amount = int(amount)
    if amount > 10 or amount < 2:
        return render_template("create.html", message="The amount of answers should be between 2 and 10.")
    answers = []
    for i in range(amount):
        try:
            answers.append(request.form.get(f"answer{i}"))
            if len(answers[i]) > 250:
                return render_template("create.html", message="The maximum answer length should be 250 characters.")
        except:
            print("write answer")
            return render_template("create.html", message="An error has occured.")
    correct = request.form.get("correct")
    if not correct:
        return render_template("create.html", message="Non of the inputs should be empty")
    if not isint(correct):
        return render_template("create.html", message="An error has occured.")
    correct = int(correct)
    riddle = Riddle(title=title, content=content, author_id=session["user_id"])
    db.session.add(riddle)
    db.session.commit()
    for index, answer in enumerate(answers):
        c = False
        if index == correct:
            c = True
        a = Answer(content=answer, correct=c, riddle_id=riddle.id)
        db.session.add(a)
    db.session.commit()
    return redirect(url_for("index"))

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

def isint(a):
    try:
        int(a)
        return True
    except ValueError:
        return False