#from dotenv import load_dotenv
import os

#load_dotenv()
SECRET_KEY="psgkjasdpgkajsdpgasdkjg"
class ApplicationConfig:
    SECRET_KEY= 'SECRET_KEY'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_DATABASE_URI = r"sqlite:///./db.sqlite"