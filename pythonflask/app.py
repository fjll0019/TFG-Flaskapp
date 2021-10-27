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
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object(ApplicationConfig)

bcrypt=Bcrypt(app)
cors = CORS(app, supports_credentials=True)
server_session = Session(app)
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route("/@me", methods=['GET'])
def get_curret_user():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error" : "Unauthorized"}) ,401
    
    user = User.query.filter_by(id=user_id).first()
    return jsonify({
        "id": user.id,
        "email": user.email,
        "nombre" : user.nombre
    })

@app.route("/register", methods=['GET','POST'])
def register_user():

    email = request.json["email"]
    password = request.json["password"]
                          
    user_exists = User.query.filter_by(email=email).first() is not None

    if user_exists:
        abort(409)
    hashed_password= bcrypt.generate_password_hash(password)
    new_user= User(email=email,password=hashed_password,nombre=email)       
    db.session.add(new_user)
    db.session.commit()  
    session["user_id"] = new_user.id
    session["user_email"] = new_user.email
    return jsonify({
        "id": new_user.id,
        "email": new_user.email
    })

@app.route("/delete", methods=['GET','POST'])
def delete_user():
    user_id= session["user_id"]
    User.query.filter_by(id=user_id).delete()
    db.session.commit()  
    return "Se ha eliminado el usuario correctamente"


@app.route("/perfil", methods=['GET','POST'])
def update_user():
    email = request.json["email"]
    nombre = request.json["nombre"]
    cambio=0
    aux =session["user_email"]
    user = User.query.filter_by(email=aux).first()
    if user is None:
        return jsonify({"error": "Unauthorized"}), 401

    if (user.nombre == "nombre por defecto" or user.nombre!= nombre):
        user.nombre=nombre
        cambio=cambio+1
    
    if (user.email!= nombre):
        user.email=email
        session["user_email"]=email
        cambio=cambio+1

    if cambio==0:
        return "No ha habido ningún cambio"
    else:
        db.session.commit()
        return jsonify({
            "nombre": user.nombre,
            "email": user.email
        })

@app.route("/password", methods=['GET','POST'])
def update_password():
    user = User.query.filter_by(email=session["user_email"]).first()
    password = request.json["password"]

    if user is None:
        return jsonify({"error": "Unauthorized"}), 401

    if(user.password==password):
        return jsonify({"error": "La contraseña a la que se intenta cambiar es la misma"}), 400

    if (user.password!=""):
        user.password=password
        db.session.commit()
        return jsonify({
            "email": user.email,
            "password" : user.password
        })


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
    session["user_email"] = user.email
    return jsonify({
        "id": user.id,
        "email": user.email
    })


@app.route("/", methods=['GET'])
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)