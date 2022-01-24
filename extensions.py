# extensions.py

from flask_cors import CORS
from flask_mail import Mail
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
cors = CORS()
bcrypt = Bcrypt()
