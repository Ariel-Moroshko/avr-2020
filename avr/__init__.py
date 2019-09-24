import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_marshmallow import Marshmallow
from flask_mail import Mail

from sqlalchemy_utils import database_exists
from sqlalchemy import Table, MetaData
from sqlalchemy.sql import text
from sqlalchemy_views import CreateView, DropView
import traceback

app = Flask(__name__)

# initialize the log handler
logHandler = RotatingFileHandler('siteLog.log', maxBytes=1000000, backupCount=5, encoding='utf8')
logHandler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
# set the log handler level
logHandler.setLevel(logging.INFO)
# set the app logger level
app.logger.setLevel(logging.INFO)
app.logger.addHandler(logHandler) 

app.config['SECRET_KEY'] = ''
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
ma = Marshmallow(app)
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER')
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS')
#app.config['MAIL_USERNAME'] = ""
#app.config['MAIL_PASSWORD'] = ""
mail = Mail(app)
app.config['RECAPTCHA_PUBLIC_KEY'] = ''
app.config['RECAPTCHA_PRIVATE_KEY'] = ''
app.config['RECAPTCHA_DATA_ATTRS'] = {'theme': 'light'}
app.config['JSON_AS_ASCII'] = False
app.config['MAX_CONTENT_LENGTH'] = 800 * 1024 * 1024  # 800MB max file upload limit.

# this import should be at the bottom to avoid circular import
from avr import routes


if not database_exists("sqlite:///"+os.path.join("avr", "site.db")):
	try:
		db.create_all()
		# create students table view
		studentsView = Table('students_view', MetaData())
		view_definition = text("SELECT student.id, student.profilePic, project.year, project.semester, student.studentId, student.firstNameHeb, student.lastNameHeb, project.title as lastProjectTitle, project.status as lastProjectStatus, project.id as lastProjectId FROM student LEFT JOIN project ON project.id = (SELECT project.id FROM project LEFT JOIN student_project ON student_project.projectId=project.id WHERE student_project.studentId=student.id ORDER BY project.year DESC, project.semester ASC LIMIT 1)")
		create_view = CreateView(studentsView, view_definition)
		db.session.execute(create_view)
	except Exception as e:
		app.logger.error('{}\n{}'.format(e, traceback.format_exc()))

