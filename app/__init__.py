from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config.from_object('app.config.Config')
db = SQLAlchemy()
migrate = Migrate(app, db)
db.init_app(app)
bcrypt = Bcrypt(app)

from app import routes
