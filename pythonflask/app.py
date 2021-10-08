import bcrypt
from flask import json
from forms import SignupForm,SigninForm
from flask import Flask, request, abort,render_template,redirect,url_for
from flask.json import jsonify
from flask_bcrypt import Bcrypt
from config import ApplicationConfig
from models import db,User

app = Flask(__name__)
app.config.from_object(ApplicationConfig)

bcrypt=Bcrypt(app)
db.init_app(app)

with app.app_context():
    db.create_all()

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
    form = SigninForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
                          
        user = User.query.filter_by(email=email).first()

        if user is None:
            return jsonify({"error" : "Unauthorized"}) ,401
        
        if not bcrypt.check_password_hash(user.password,password):
            return jsonify({"error" : "Unauthorized"}) ,401
        
        return redirect(url_for('index'))
    return render_template("signup_form.html", form=form)


@app.route("/", methods=['GET'])
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)