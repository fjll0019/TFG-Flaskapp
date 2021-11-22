import bcrypt
from flask import json
from flask import Flask, request,session, abort,render_template,redirect,url_for,send_from_directory
from flask.json import jsonify
from flask_session import Session
from flask_bcrypt import Bcrypt
from config import ApplicationConfig
from models import db,User,Datos
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename, send_file
import os
from elasticsearch import Elasticsearch

app = Flask(__name__)
app.config.from_object(ApplicationConfig)
UPLOAD_FOLDER = 'static/imgs'
UPLOAD_FOLDER2 = 'static/data'

ALLOWED_EXTENSIONS = set(['png', 'jpg'])

#es= Elasticsearch()


app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['UPLOAD_FOLDER2'] = UPLOAD_FOLDER2

bcrypt=Bcrypt(app)
cors = CORS(app, supports_credentials=True)
server_session = Session(app)
db.init_app(app)

with app.app_context():
    db.create_all()

class Usuario:
  def __init__(self, name, email,datos):
    self.name = name
    self.email = email
    self.datos = datos
  def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)

@app.route("/@me", methods=['GET'])
def get_curret_user():
    user_id = session.get("user_id")
    user = User.query.filter_by(id=user_id).first()
    if user==None:
        return jsonify({"error" : "Unauthorized"}) ,401
    
    user = User.query.filter_by(id=user_id).first()
    datas=[]
    datos = Datos.query.filter_by(owner_id=user.id).all()
    for data in datos:
        datas.append(data.name)
    print(datas)
    return jsonify({
        "id": user.id,
        "email": user.email,
        "nombre" : user.nombre,
        "avatar": user.avatar,
        "data": datas,
        "rol" : user.rol
       
    })
@app.route("/listUsers", methods=['GET'])
def get_user_list():
    user_id = session.get("user_id")
    user = User.query.filter_by(id=user_id).first()
    if user==None:
        return jsonify({"error" : "Unauthorized"}) ,401
    if user.rol!="ADMIN":
        return jsonify({"error" : "Unauthorized"}) ,401

    list =[]
    users = User.query.filter_by().all()
    for user in users:
        datas=[]
        datos = Datos.query.filter_by(owner_id=user.id).all()
        for data in datos:
            datas.append(data.name)
        list.append(Usuario(user.nombre,user.email,datos))
    usuarios = []
    for user in list:
        user = user.toJSON()
        userData = json.loads(user)
        usuarios.append(userData)
    print(usuarios)
    return ({
        "usuarios": usuarios
    })

@app.route("/register", methods=['GET','POST'])
def register_user():

    email = request.json["email"]
    password = request.json["password"]
    nombre=""           
    user_exists = User.query.filter_by(email=email).first() is not None

    if user_exists:
        abort(409)
    hashed_password= bcrypt.generate_password_hash(password)

    if email== "admin@gmail.com":
        new_user= User(email=email,password=hashed_password,nombre=email,rol="ADMIN")  
    else:
        new_user= User(email=email,password=hashed_password,nombre=email)  
    new_datos = Datos()
    new_datos.owner = new_user.id  
    db.session.add(new_datos) 
    db.session.add(new_user)

    db.session.commit()  
    session["user_id"] = new_user.id
    session["user_email"] = new_user.email
    if(new_user.nombre=="nombre por defecto" or new_user.nombre==None):
        nombre= "user1"
    else:
        nombre=new_user.nombre
    return jsonify({
        "id": new_user.id,
        "email": new_user.email,
        "nombre": nombre,
        "avatar": new_user.avatar,
        "rol": new_user.rol
    })

@app.route("/delete", methods=['GET','POST'])
def delete_user():
    user_id= session["user_id"]
    User.query.filter_by(id=user_id).delete()
    db.session.commit()  
    return "Se ha eliminado el usuario correctamente"

@app.route("/deleteData", methods=['GET','POST'])
def delete_data():
    filename = request.json["filename"]
    user_id= session["user_id"]
    Datos.query.filter_by(owner_id=user_id,nombre=filename).delete()
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

    if (user.nombre == "nombre por defecto" or user.nombre!= nombre and nombre!=""):
        user.nombre=nombre
        cambio=cambio+1
    
    if (user.email!= nombre and email!=""):
        user.email=email
        session["user_email"]=email
        cambio=cambio+1
    if cambio==0:
        return "No ha habido ningún cambio"
   

    else:
        db.session.commit()
        return jsonify({
            "nombre": user.nombre,
            "email": user.email,
            "avatar": user.avatar,
        })

@app.route("/password", methods=['GET','POST'])
def update_password():
    user = User.query.filter_by(email=session["user_email"]).first()
    password = request.json["password"]
    lastpassword = request.json["lastPass"]

    if user is None:
        return jsonify({"error": "Unauthorized"}), 401

    if not bcrypt.check_password_hash(user.password, lastpassword):
        return jsonify({"error": "La contraseña actual no es correcta"}), 403

    if bcrypt.check_password_hash(user.password, password):
        return jsonify({"error": "La contraseña a la que se intenta cambiar es la misma"}), 400

    if (password!=""):
        hashed_password= bcrypt.generate_password_hash(password)
        user.password=hashed_password
        db.session.commit()
        return jsonify({
            "nombre": user.nombre,
            "email": user.email,
            "avatar": user.avatar
        })


@app.route("/login", methods=['GET','POST'])
def login_user():
    email = request.json["email"]
    password = request.json["password"]
    nombre=""
    user = User.query.filter_by(email=email).first()

    if user is None:
        return jsonify({"error": "Unauthorized"}), 401

    if not bcrypt.check_password_hash(user.password, password):
        return jsonify({"error": "Unauthorized"}), 401
    
    else:
        nombre=user.nombre
    
    session["user_id"] = user.id
    session["user_email"] = user.email
    return jsonify({
        "id": user.id,
        "email": user.email,
        "nombre": nombre,
        "avatar": user.avatar
    })
@app.route("/logout", methods=['GET','POST'])
def logut():
    session.clear
    
@app.route("/uploadfile", methods=['GET','POST'])    
def upload_file():

    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error" : "Unauthorized"}) ,401
    
    user = User.query.filter_by(id=user_id).first()
    if request.method == 'POST':
        file = request.files['file']
        print("file es:")
        print(file)
        if file.filename == '':
            return jsonify({"error": "No se ha seleccionado un fichero"}), 404
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            user.avatar=filename
            db.session.commit()
            return jsonify({
                "file": filename
            })

@app.route("/uploadData", methods=['GET','POST'])    
def upload_data():

    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error" : "Unauthorized"}) ,401
    
    user = User.query.filter_by(id=user_id).first()
    if request.method == 'POST':
        file = request.files['file']
        print("file es:")
        print(file)
        if file.filename == '':
            return jsonify({"error": "No se ha seleccionado un fichero"}), 404
        if file:
            filename = secure_filename(file.filename)
           
            datos = Datos.query.filter_by(owner_id=user.id,name=filename).all()
            for data in datos:
                if(data.name==filename):
                    return jsonify({
                     "error" : "Fallo, el archivo está repetido"
                    }),409
            data = Datos(name=filename,owner_id=user.id)
            db.session.add(data)
            db.session.commit()
            print("nuevo fichero")
            print(filename)
            datos = Datos.query.filter_by(owner_id=user.id).all()
            print("Ficheros del usuario")
            datas=[]
            for data in datos:
                datas.append(data.name)
            print(datas)
            file.save(os.path.join(app.config['UPLOAD_FOLDER2'], filename))
            return jsonify({
            "id": user.id,
            "email": user.email,
            "nombre": user.nombre,
             "data" : datas
            })
    return jsonify({
        "error" : "Fallo al subir el archivo"
    }),500
            
@app.route("/", methods=['GET'])
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)