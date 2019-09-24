from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from avr import db, login_manager, app
from flask_login import UserMixin

@login_manager.user_loader
def load_user(userId):
	return User.query.get(userId)

class User(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key=True)
	userId = db.Column(db.String(20), unique=True, nullable=False)
	userType = db.Column(db.String(20), nullable=False)

	def __repr__(self):
		return "User({}, {}, {})".format(self.id, self.userId, self.userType)
		

class Student(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	studentId = db.Column(db.String(20), unique=True, nullable=False)
	password = db.Column(db.String(60), nullable=False)

	firstNameHeb = db.Column(db.String(30), nullable=False)
	lastNameHeb = db.Column(db.String(30), nullable=False)
	firstNameEng =  db.Column(db.String(30), nullable=False)
	lastNameEng = db.Column(db.String(30), nullable=False)

	academicStatus = db.Column(db.String(30), nullable=True)
	faculty = db.Column(db.String(30), nullable=False)
	cellPhone = db.Column(db.String(30), nullable=True)
	email = db.Column(db.String(150), nullable=False)
	semester = db.Column(db.String(20), nullable=False)
	year = db.Column(db.Integer, nullable=False)
	profilePic = db.Column(db.String(50), nullable=True)
	isRegistered = db.Column(db.Boolean, nullable=True, default=False)
	
	projects = db.relationship('Project', secondary='student_project', backref=db.backref('students', lazy='dynamic'), order_by='Project.year.desc(),Project.semester.asc()')
	courses = db.relationship('Course', secondary='student_project', backref=db.backref('students', lazy='dynamic'))
	

	def get_reset_token(self, expires_sec=1800):
		s = Serializer(app.config['SECRET_KEY'], expires_sec)
		return s.dumps({'id': self.id}).decode('utf-8')
	
	@staticmethod
	def verify_reset_token(token):
		s = Serializer(app.config['SECRET_KEY'])
		try:
			id = s.loads(token)['id']
		except:
			return None
		return Student.query.get(id)

	def __repr__(self):
		return "Student({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {})".format(self.id, self.studentId, self.password, self.firstNameHeb, self.lastNameHeb, self.firstNameEng, self.lastNameEng, self.academicStatus, self.faculty, self.cellPhone, self.email, self.semester, self.year)


class ProposedProject(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(60), unique=True, nullable=False)
	description = db.Column(db.Text, nullable=False)
	image = db.Column(db.String(50), nullable=True)
	published = db.Column(db.Boolean, nullable=True, default=False)
	oneAcademicPoint = db.Column(db.Boolean, nullable=True, default=False)
	twoAcademicPoints = db.Column(db.Boolean, nullable=True, default=False)
	threeAcademicPoints = db.Column(db.Boolean, nullable=True, default=False)
	fourAcademicPoints = db.Column(db.Boolean, nullable=True, default=False)
	fiveAcademicPoints = db.Column(db.Boolean, nullable=True, default=False)

	supervisors = db.relationship('Supervisor', secondary='supervisor_proposed_project', backref=db.backref('proposedProjects', lazy='dynamic'))

	@property
	def supervisorsFullNameEng(self):
		return [s.firstNameEng + ' ' + s.lastNameEng for s in self.supervisors]
	
	def __repr__(self):
		return "ProposedProject({}, {}, {}, {})".format(self.id, self.title, self.description, self.image)


class Project(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	title = db.Column(db.String(60), nullable=False)
	semester = db.Column(db.String(20), nullable=False)
	year = db.Column(db.Integer, nullable=False)
	grade = db.Column(db.Integer, nullable=True)
	comments = db.Column(db.Text, nullable=True)
	image = db.Column(db.String(50), nullable=True)
	
	status = db.Column(db.String(50), nullable=True)
	requirementsDoc = db.Column(db.Boolean, nullable=True, default=False)
	firstMeeting = db.Column(db.Boolean, nullable=True, default=False)
	halfwayPresentation = db.Column(db.Boolean, nullable=True, default=False)
	finalMeeting = db.Column(db.Boolean, nullable=True, default=False)
	equipmentReturned = db.Column(db.Boolean, nullable=True, default=False)
	projectDoc = db.Column(db.Boolean, nullable=True, default=False)
	gradeStatus = db.Column(db.Boolean, nullable=True, default=False)
	posterStatus = db.Column(db.Boolean, nullable=True, default=False)

	# project doc
	projectDocImage = db.Column(db.String(50), nullable=True)
	localVideo = db.Column(db.String(50), nullable=True)
	
	youtubeVideo = db.Column(db.String(200), nullable=True)
	youtubeUploadStatus = db.Column(db.String(100), nullable=True)
	youtubeProcessingStatus = db.Column(db.String(100), nullable=True)
	youtubeProcessingFailureReason = db.Column(db.String(100), nullable=True)
	youtubeProcessingEstimatedTimeLeft = db.Column(db.String(100), nullable=True)
	youtubeVideoPublicStatus = db.Column(db.String(100), nullable=True)

	report = db.Column(db.String(50), nullable=True)
	presentation = db.Column(db.String(50), nullable=True)
	code = db.Column(db.String(50), nullable=True)
	githubLink = db.Column(db.String(150), nullable=True)
	abstract = db.Column(db.Text, nullable=True)
	projectDocApproved = db.Column(db.Boolean, nullable=True, default=False)
	projectDocEditableByStudents = db.Column(db.Boolean, nullable=True, default=False)
	published = db.Column(db.Boolean, nullable=True, default=False)
	poster = db.Column(db.String(50), nullable=True)
	posterEditableByStudents = db.Column(db.Boolean, nullable=False, default=True)

	courses = db.relationship('Course', secondary='student_project', backref=db.backref('projects', lazy='dynamic'))	
	
	def __repr__(self):
		return "Project({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {})".format(self.id, self.title, self.semester, self.year, self.grade, self.comments, self.requirementsDoc, self.firstMeeting, self.halfwayPresentation, self.finalMeeting, self.equipmentReturned, self.projectDoc, self.gradeStatus)
	
	def calculateStatus(self):
		if self.posterStatus:
			return "פוסטר"
		if self.gradeStatus:
			return "הושלם"
		if self.projectDoc:
			return "דף פרויקט"
		if self.youtubeVideo and self.youtubeProcessingStatus == "processed":
			return "דף פרויקט - טיוטה"
		if self.finalMeeting:
			return 'פגישת סיום'
		if self.halfwayPresentation:
			return "מצגת אמצע"
		if self.firstMeeting:
			return "פגישת התנעה"
		if self.requirementsDoc:
			return "מסמך דרישות"
		else:
			return "הרשמה"

	def isVideoProcessingSucceeded(self):
		return self.youtubeUploadStatus == "completed" and self.youtubeProcessingStatus == "processed"
	
	def isVideoProcessingFailed(self):
		return self.youtubeUploadStatus == "failed" or self.youtubeProcessingStatus == "terminated" or self.youtubeProcessingStatus == "failed"

	def isProcessingFinished(self):
		return self.isVideoProcessingFailed() or self.isVideoProcessingSucceeded()


	@property
	def studentsFullNameEng(self):
		return [s.firstNameEng + ' ' + s.lastNameEng for s in self.students]

	@property
	def studentsForPublishedProject(self):
		students = []
		for s in self.students:
			profilePic = f"static/images/profile/{s.profilePic}" if s.profilePic else "static/images/profile/default.png"
			students.append({
				"profilePic": profilePic,
				"fullNameEng": s.firstNameEng + ' ' + s.lastNameEng
			})
		return students
	
	@property
	def supervisorsFullNameEng(self):
		return [s.firstNameEng + ' ' + s.lastNameEng for s in self.supervisors]
	

class Supervisor(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	supervisorId = db.Column(db.String(20), unique=True, nullable=False)
	firstNameEng = db.Column(db.String(40), nullable=False)
	lastNameEng = db.Column(db.String(40),nullable=False)
	firstNameHeb = db.Column(db.String(40), nullable=False)
	lastNameHeb = db.Column(db.String(40),nullable=False)
	email = db.Column(db.String(150), nullable=True)
	phone = db.Column(db.String(20), nullable=True)
	status = db.Column(db.String(30), nullable=False, default="active")

	projects = db.relationship('Project', secondary='supervisor_project', backref=db.backref('supervisors', lazy='dynamic'), order_by='Project.year.desc(),Project.semester.asc()')

	def __repr__(self):
		return "Supervisor({}, {}, {}, {}, {}, {}, {}, {}, {})".format(self.id, self.supervisorId, self.firstNameEng, self.lastNameEng, self.firstNameHeb, self.lastNameHeb, self.email, self.phone, self.status)


# bridge table between supervisors and proposed projects
supervisor_proposed_project = db.Table('supervisor_proposed_project',
					db.Column('supervisorId', db.Integer, db.ForeignKey('supervisor.id')),
					db.Column('proposedProjectId', db.Integer, db.ForeignKey('proposed_project.id')))


# bridge table between supervisors and projects
supervisor_project = db.Table('supervisor_project',
					db.Column('supervisorId', db.Integer, db.ForeignKey('supervisor.id')),
					db.Column('projectId', db.Integer, db.ForeignKey('project.id')))


# bridge table between students and projects
class StudentProject(db.Model):
	studentId = db.Column(db.Integer, db.ForeignKey('student.id') ,nullable=False, primary_key=True)
	projectId = db.Column(db.Integer, db.ForeignKey('project.id') ,nullable=False, primary_key=True)
	courseId = db.Column(db.Integer, db.ForeignKey('course.id') ,nullable=False, primary_key=True)

class Admin(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	adminId = db.Column(db.String(20), unique=True, nullable=False)
	password = db.Column(db.String(60), nullable=False)

	def __repr__(self):
		return "Admin({}, {}, {})".format(self.id, self.adminId, self.password) 

class Course(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	number = db.Column(db.String(20), unique=True, nullable=False)
	name = db.Column(db.String(60), nullable=False)
	academicPoints = db.Column(db.Integer, nullable=False)
	isDefault = db.Column(db.Boolean, unique=True, nullable=True)

	def __repr__(self):
		return "Course({}, {}, {}, {})".format(self.id, self.number, self.name, self.academicPoints) 