from flask import Flask
import os
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///PaperManagement.db"
db.init_app(app)
app.config['SECRET_KEY'] = 'random_key'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024
path = os.getcwd()

UPLOAD_FOLDER = os.path.join(path, 'uploads')

if not os.path.isdir(UPLOAD_FOLDER):
    os.mkdir(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

from blog import routes
