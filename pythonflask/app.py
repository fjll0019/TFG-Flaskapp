import bcrypt
from flask import json
from forms import SignupForm,SigninForm
from flask import Flask, request,session, abort,render_template,redirect,url_for
from flask.json import jsonify
from flask_session import Session
from flask_bcrypt import Bcrypt
from config import ApplicationConfig
from models import db,User
from flask_cors import CORS

app = Flask(__name__)
app.config.from_object(ApplicationConfig)

bcrypt=Bcrypt(app)
cors = CORS(app, supports_credentials=True)
server_session = Session(app)
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route("/@me")
def get_curret_user():
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"error" : "Unauthorized"}) ,401
    
    user = User.query.filter_by(id=user_id).first()
    return jsonify({
        "id": user.id,
        "email": user.email
    })

@app.route("/register", methods=['GET','POST'])
def register_user():
    form = SignupForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
                          
        user_exists = User.query.filter_by(email=email).first() is not None

        if user_exists:
            abort(409)
        hashed_password= bcrypt.generate_password_hash(password)
        new_user= User(email=email,password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template("signup_form.html", form=form)

@app.route("/login", methods=['GET','POST'])
def login_user():
    email = request.json["email"]
    password = request.json["password"]

    user = User.query.filter_by(email=email).first()

    if user is None:
        return jsonify({"error": "Unauthorized"}), 401

    if not bcrypt.check_password_hash(user.password, password):
        return jsonify({"error": "Unauthorized"}), 401
    
    session["user_id"] = user.id

    return jsonify({
        "id": user.id,
        "email": user.email
    })


@app.route("/", methods=['GET'])
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)