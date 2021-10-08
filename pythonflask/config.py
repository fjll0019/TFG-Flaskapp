#from dotenv import load_dotenv
from operator import truediv
import os
import redis

#load_dotenv()
SECRET_KEY="psgkjasdpgkajsdpgasdkjg"
class ApplicationConfig:
    SECRET_KEY= 'SECRET_KEY'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_DATABASE_URI = r"sqlite:///./db.sqlite"

    SESSION_TYPE = "redis"
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_REDIS = redis.from_url("redis://127.0.0.1:6379")