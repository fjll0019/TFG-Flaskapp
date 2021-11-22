from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from uuid import uuid4

from sqlalchemy.orm import relationship
db = SQLAlchemy()

def get_uuid():
    return uuid4().hex

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.String(32), primary_key=True,unique=True,default=get_uuid)
    email = db.Column(db.String(345), unique = True)
    password = db.Column(db.Text, nullable= False)
    nombre = db.Column(db.String(70), default="nombre por defecto")
    avatar = db.Column(db.String(70), default="avatar.jpg")
    rol = db.Column(db.String(70), default="USER")
    datos= db.relationship('Datos',backref='users')



class Datos(db.Model):
    __tablename__ = "datos"
    id_datos = db.Column(db.String(32), primary_key=True,unique=True,default=get_uuid)
    owner_id = db.Column(db.String(32), ForeignKey('users.id'))
    name = db.Column(db.String(70), default="fichero por defecto")
