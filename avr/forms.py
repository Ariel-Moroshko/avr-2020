from flask_wtf import FlaskForm, RecaptchaField, Recaptcha
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SelectField, TextAreaField, SubmitField, HiddenField, BooleanField
from wtforms.validators import DataRequired, Optional, Email, ValidationError, EqualTo, Length
from avr.models import Admin, User, Student, ProposedProject, Project, Supervisor, Course
from avr import database

ALLOWED_FILE_EXT = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tga']

class RegistrationForm(FlaskForm):
	firstNameHeb = StringField('First Name (Heb)', validators=[DataRequired()])
	lastNameHeb = StringField('Last Name (Heb)', validators=[DataRequired()])
	firstNameEng =  StringField('First Name (Eng)', validators=[DataRequired()])
	lastNameEng = StringField('Last Name (Eng)', validators=[DataRequired()])

	studentId = StringField('ID', validators=[DataRequired()])
	password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])

	academicStatus = SelectField('Academic Status', choices=[('ug', 'UG'), ('msc', 'MSc'), ('phd', 'PhD'), ('guest', 'Guest'), ('research-fellow', 'Research Fellow'), ('other', 'Other')], default="ug")
	faculty = SelectField('Faculty', choices=[('Computer Science', 'Computer Science'), ('Electrical Engineering', 'Electrical Engineering'), ('Mechanical Engineering', 'Mechanical Engineering'), ('Medical Engineering', 'Medical Engineering'), ('Other', 'Other')], default="Computer Science")
	cellPhone = StringField('Cell Phone')
	email = StringField('Email', validators=[DataRequired(), Email()])
	semester = SelectField('Semester')
	year = SelectField('Year')
	projectTitle = SelectField('Project Title')
	profilePic = FileField('Profile Picture', validators=[FileAllowed(ALLOWED_FILE_EXT)])
	recaptcha = RecaptchaField(validators=[Recaptcha(message="Click the checkbox above to verify you are a human!")])
	submitForm = SubmitField('Register')

	
	def validate_firstNameHeb(self, firstNameHeb):
		if any((c < "\u05D0" or c > "\u05EA") and (not c.isspace()) for c in firstNameHeb.data):
			raise ValidationError('Must consist of hebrew characters and spaces only')
	
	def validate_lastNameHeb(self, lastNameHeb):
		if any((c < "\u05D0" or c > "\u05EA") and (not c.isspace()) for c in lastNameHeb.data):
			raise ValidationError('Must consist of hebrew characters and spaces only')

	def validate_firstNameEng(self, firstNameEng):
		if any((c < "\u0041" or (c > "\u005A" and c < "\u0061") or c > "\u007A") and (not c.isspace()) for c in firstNameEng.data):	
			raise ValidationError('Must consist of english characters and spaces only')

	def validate_lastNameEng(self, lastNameEng):
		if any((c < "\u0041" or (c > "\u005A" and c < "\u0061") or c > "\u007A") and (not c.isspace()) for c in lastNameEng.data):	
			raise ValidationError('Must consist of english characters and spaces only')
	
	def validate_cellPhone(self, cellPhone):
		if any(c.isalpha() for c in cellPhone.data):
			raise ValidationError('Not a valid cell phone number!')

	def validate_studentId(self, studentId):
		if not studentId.data.isdigit():
			raise ValidationError('Must contain only numbers!')
		else:
			user = User.query.filter_by(userId=studentId.data).first()
			if user:
				raise ValidationError('A user with this ID is already registred!')
	
	def validate_email(self, email):
			student = Student.query.filter_by(email=email.data).first()
			if student:
				raise ValidationError('This email is already used by another student!')

class createAdminForm(FlaskForm):
	id = StringField('ID', validators=[DataRequired()], render_kw={"placeholder": "ID"})
	password = PasswordField('Password', validators=[DataRequired()], render_kw={"placeholder": "Password"})
	confirmPassword = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')], render_kw={"placeholder": "Confirm Password"})
	submitForm = SubmitField('Create Account')

	def validate_id(self, id):
		if not id.data.isdigit():
				raise ValidationError('Must contain only numbers!')
		else:
			admin = Admin.query.filter_by(adminId=id.data).first()
			if admin:
				raise ValidationError('This admin is already registred!')

class LoginForm(FlaskForm):
	id = StringField('ID', validators=[DataRequired()], render_kw={"placeholder": "ID"})
	password = PasswordField('Password', validators=[DataRequired()], render_kw={"placeholder": "Password"})
	#recaptcha = RecaptchaField(validators=[Recaptcha(message="Click the checkbox above to verify you are a human!")])
	submitLoginForm = SubmitField('LOGIN')

class EditAccountForm(FlaskForm):
	studentId = StringField('ID', validators=[DataRequired()])
	password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
	firstNameHeb = StringField('First Name (Heb)', validators=[DataRequired()])
	lastNameHeb = StringField('Last Name (Heb)', validators=[DataRequired()])
	firstNameEng =  StringField('First Name (Eng)', validators=[DataRequired()])
	lastNameEng = StringField('Last Name (Eng)', validators=[DataRequired()])
	academicStatus = SelectField('Academic Status', choices=[('ug', 'UG'), ('msc', 'MSc'), ('phd', 'PhD'), ('guest', 'Guest'), ('research-fellow', 'Research Fellow'), ('other', 'Other')], default="ug")
	faculty = SelectField('Faculty', choices=[('Computer Science', 'Computer Science'), ('Electrical Engineering', 'Electrical Engineering'), ('Mechanical Engineering', 'Mechanical Engineering'), ('Medical Engineering', 'Medical Engineering'), ('Other', 'Other')], default="Computer Science")
	cellPhone = StringField('Cell Phone')
	email = StringField('Email', validators=[DataRequired(), Email()])
	profilePic = FileField('Profile Picture', validators=[FileAllowed(ALLOWED_FILE_EXT)])
	submitForm = SubmitField('Apply')

	def validate_studentId(self, studentId):
		if not studentId.data.isdigit():
			raise ValidationError('Must contain only numbers!')

	def validate_firstNameHeb(self, firstNameHeb):
		if any((c < "\u05D0" or c > "\u05EA") and (not c.isspace()) for c in firstNameHeb.data):
			raise ValidationError('Must consist of hebrew characters and spaces only')
	
	def validate_lastNameHeb(self, lastNameHeb):
		if any((c < "\u05D0" or c > "\u05EA") and (not c.isspace()) for c in lastNameHeb.data):
			raise ValidationError('Must consist of hebrew characters and spaces only')

	def validate_firstNameEng(self, firstNameEng):
		if any((c < "\u0041" or (c > "\u005A" and c < "\u0061") or c > "\u007A") and (not c.isspace()) for c in firstNameEng.data):	
			raise ValidationError('Must consist of english characters and spaces only')

	def validate_lastNameEng(self, lastNameEng):
		if any((c < "\u0041" or (c > "\u005A" and c < "\u0061") or c > "\u007A") and (not c.isspace()) for c in lastNameEng.data):	
			raise ValidationError('Must consist of english characters and spaces only')
	
	def validate_cellPhone(self, cellPhone):
		if any(c.isalpha() for c in cellPhone.data):
			raise ValidationError('Not a valid cell phone number!')


class addProposedProjectForm(FlaskForm):
	newTitle = StringField('Title', validators=[DataRequired()])
	newDescription = TextAreaField('Description', validators=[DataRequired()])
	newImage = FileField('Image', validators=[FileAllowed(ALLOWED_FILE_EXT)])
	newSupervisor1 = SelectField('Supervisor 1')
	newSupervisor2 = SelectField('Supervisor 2')
	newSupervisor3 = SelectField('Supervisor 3')
	new_oneAcademicPoint = BooleanField('one academic point')
	new_twoAcademicPoints = BooleanField('two academic point')
	new_threeAcademicPoints = BooleanField('three academic point')
	new_fourAcademicPoints = BooleanField('four academic point')
	new_fiveAcademicPoints = BooleanField('five academic point')
	submitAddForm = SubmitField('Create')

	def validate_newTitle(self, newTitle):
		titleExists = ProposedProject.query.filter_by(title=newTitle.data).first()
		if titleExists:
			raise ValidationError('There is already a proposed project with the same title')

class editProposedProjectForm(FlaskForm):
	proposedProjectId = HiddenField("")
	title = StringField('Title', validators=[DataRequired()])
	description = TextAreaField('Description', validators=[DataRequired()])
	image = FileField('Image', validators=[FileAllowed(ALLOWED_FILE_EXT)])
	supervisor1 = SelectField('Supervisor 1')
	supervisor2 = SelectField('Supervisor 2')
	supervisor3 = SelectField('Supervisor 3')
	oneAcademicPoint = BooleanField('one academic point')
	twoAcademicPoints = BooleanField('two academic point')
	threeAcademicPoints = BooleanField('three academic point')
	fourAcademicPoints = BooleanField('four academic point')
	fiveAcademicPoints = BooleanField('five academic point')
	submitEditForm = SubmitField('Save Changes')

	def validate_title(self, title):
		currentProposedProject = ProposedProject.query.filter_by(id=self.proposedProjectId.data).first()
		# title was changed
		if self.title.data != currentProposedProject.title:
			titleExists = ProposedProject.query.filter_by(title=self.title.data).first()
			if titleExists:
				raise ValidationError('There is already a proposed project with the same title')

class deleteProposedProjectForm(FlaskForm):
	deleteProposedProjectId = HiddenField("")

class addProjectForm(FlaskForm):
	new_title = SelectField('Title')
	new_year = SelectField('Year')
	new_semester = SelectField('Semester')
	new_comments = TextAreaField('Comments')
	new_supervisor1 = SelectField('Supervisor 1')
	new_supervisor2 = SelectField('Supervisor 2')
	new_supervisor3 = SelectField('Supervisor 3')
	submitAddForm = SubmitField('Create')

class editProjectForm(FlaskForm):
	projectId = HiddenField("")
	title = StringField('Title', validators=[DataRequired()])
	year = SelectField('Year', validators=[DataRequired()])
	semester = SelectField('Semester', validators=[DataRequired()])
	supervisor1 = SelectField('Supervisor 1')
	supervisor2 = SelectField('Supervisor 2')
	supervisor3 = SelectField('Supervisor 3')
	comments = TextAreaField('Comments')
	image = FileField('Project Image', validators=[FileAllowed(ALLOWED_FILE_EXT)])
	grade = StringField('Grade')
	requirementsDoc = BooleanField('מסמך דרישות')
	firstMeeting = BooleanField('פגישת התנעה')
	halfwayPresentation = BooleanField('מצגת אמצע')
	finalMeeting = BooleanField('פגישת סיום')
	equipmentReturned = BooleanField('החזרת ציוד')
	projectDoc = BooleanField('דף פרויקט', render_kw={'disabled':''})
	gradeStatus = BooleanField('ציון', render_kw={'disabled':''})
	posterStatus = BooleanField('פוסטר', render_kw={'disabled':''})

	# project doc stuff
	projectDocImage = FileField('Image', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'bmp'])])
	report = FileField('Project Report', validators=[FileAllowed(['doc', 'docx', 'pdf'])])
	presentation = FileField('Presentation', validators=[FileAllowed(['ppt', 'pptx'])])
	abstract = TextAreaField('Abstract', validators=[])
	code = FileField('Code', validators=[FileAllowed(['zip', 'rar'])])
	githubLink = StringField('Github Link')
	projectDocApproved = BooleanField('I approve this project doc')
	projectDocEditableByStudents = BooleanField('Allow students to edit')
	posterEditableByStudents = BooleanField('Allow students to edit')

	submitEditForm = SubmitField('Save Changes')

	def validate_grade(self, grade):
		if grade.data:
			if not grade.data.isdigit():
				raise ValidationError('grade must contain only digits.')


class deleteProjectForm(FlaskForm):
	deleteProjectId = HiddenField("")

class deleteStudentForm(FlaskForm):
	deleteStudentId = HiddenField("")

class deleteSupervisorForm(FlaskForm):
	deleteSupervisorId = HiddenField("")

class editStudentForm(FlaskForm):
	id = HiddenField("")
	studentId = StringField('ID', validators=[DataRequired()])
	firstNameHeb = StringField('First Name (Heb)', validators=[DataRequired()])
	lastNameHeb = StringField('Last Name (Heb)', validators=[DataRequired()])
	firstNameEng =  StringField('First Name (Eng)', validators=[DataRequired()])
	lastNameEng = StringField('Last Name (Eng)', validators=[DataRequired()])
	email = StringField('Email', validators=[DataRequired(), Email()])
	submitEditStudentForm = SubmitField('Save Changes')

	def validate_studentId(self, studentId):
		if not studentId.data.isdigit():
			raise ValidationError('Must contain only numbers!')
		student = Student.query.filter_by(id=self.id.data).first()
		# is the id is in the db?
		if student: 
			# studentId changed?
			if self.studentId.data != student.studentId:
				userWithNewIdExists =  User.query.filter_by(userId=self.studentId.data).first()
				if userWithNewIdExists:
					raise ValidationError('There is already a user with the ID you entered')
	
	def validate_firstNameHeb(self, firstNameHeb):
		if any((c < "\u05D0" or c > "\u05EA") and (not c.isspace()) for c in firstNameHeb.data):
			raise ValidationError('Must consist of hebrew characters and spaces only')
	
	def validate_lastNameHeb(self, lastNameHeb):
		if any((c < "\u05D0" or c > "\u05EA") and (not c.isspace()) for c in lastNameHeb.data):
			raise ValidationError('Must consist of hebrew characters and spaces only')

	def validate_firstNameEng(self, firstNameEng):
		if any((c < "\u0041" or (c > "\u005A" and c < "\u0061") or c > "\u007A") and (not c.isspace()) for c in firstNameEng.data):	
			raise ValidationError('Must consist of english characters and spaces only')

	def validate_lastNameEng(self, lastNameEng):
		if any((c < "\u0041" or (c > "\u005A" and c < "\u0061") or c > "\u007A") and (not c.isspace()) for c in lastNameEng.data):	
			raise ValidationError('Must consist of english characters and spaces only')
	
	def validate_email(self, email):
		student = Student.query.filter_by(id=self.id.data).first()
		# is the id is in the db?
		if student:
			# email changed?
			if email.data != student.email:
				studentWithSameEmail =  Student.query.filter_by(email=email.data).first()
				if studentWithSameEmail:
					raise ValidationError('This email is already used by another student!')

class editSupervisorForm(FlaskForm):
	id = HiddenField("")
	supervisorId = StringField('ID', validators=[DataRequired()])
	firstNameHeb = StringField('First Name (Heb)', validators=[DataRequired()])
	lastNameHeb = StringField('Last Name (Heb)', validators=[DataRequired()])
	firstNameEng =  StringField('First Name (Eng)', validators=[DataRequired()])
	lastNameEng = StringField('Last Name (Eng)', validators=[DataRequired()])
	email = StringField('Email', validators=[Optional(), Email()])
	phone = StringField('Phone')
	status = SelectField('Stauts', choices=[('active', 'Active'), ('not active', 'Not Active')], validators=[DataRequired()])

	submitEditForm = SubmitField('Save Changes')

	def validate_firstNameHeb(self, firstNameHeb):
		if any((c < "\u05D0" or c > "\u05EA") and (not c.isspace()) for c in firstNameHeb.data):
			raise ValidationError('Must consist of hebrew characters and spaces only')
	
	def validate_lastNameHeb(self, lastNameHeb):
		if any((c < "\u05D0" or c > "\u05EA") and (not c.isspace()) for c in lastNameHeb.data):
			raise ValidationError('Must consist of hebrew characters and spaces only')

	def validate_firstNameEng(self, firstNameEng):
		if any((c < "\u0041" or (c > "\u005A" and c < "\u0061") or c > "\u007A") and (not c.isspace()) for c in firstNameEng.data):	
			raise ValidationError('Must consist of english characters and spaces only')

	def validate_lastNameEng(self, lastNameEng):
		if any((c < "\u0041" or (c > "\u005A" and c < "\u0061") or c > "\u007A") and (not c.isspace()) for c in lastNameEng.data):	
			raise ValidationError('Must consist of english characters and spaces only')

	def validate_supervisorId(self, supervisorId):
		if not supervisorId.data.isdigit():
				raise ValidationError('Must contain only numbers!')
		supervisor = Supervisor.query.filter_by(id=self.id.data).first()
		# is the id is in the db?
		if supervisor: 
			# supervisorId was changed
			if self.supervisorId.data != supervisor.supervisorId:
				supervisorWithNewIdExists =  Supervisor.query.filter_by(supervisorId=self.supervisorId.data).first()
				if supervisorWithNewIdExists:
					raise ValidationError('There is already a supervisor with the ID you entered')

class addSupervisorForm(FlaskForm):
	newSupervisorId = StringField('ID', validators=[DataRequired()])
	newFirstNameHeb = StringField('First Name (Heb)', validators=[DataRequired()])
	newLastNameHeb = StringField('Last Name (Heb)', validators=[DataRequired()])
	newFirstNameEng =  StringField('First Name (Eng)', validators=[DataRequired()])
	newLastNameEng = StringField('Last Name (Eng)', validators=[DataRequired()])
	newEmail = StringField('Email', validators=[Optional(), Email()])
	newPhone = StringField('Phone')
	newStatus = SelectField('Stauts', choices=[('active', 'Active'), ('not active', 'Not Active')], validators=[DataRequired()])

	submitAddForm = SubmitField('Add Supervisor')


	def validate_newFirstNameHeb(self, newFirstNameHeb):
		if any((c < "\u05D0" or c > "\u05EA") and (not c.isspace()) for c in newFirstNameHeb.data):
			raise ValidationError('Must consist of hebrew characters and spaces only')
	
	def validate_newLastNameHeb(self, newLastNameHeb):
		if any((c < "\u05D0" or c > "\u05EA") and (not c.isspace()) for c in newLastNameHeb.data):
			raise ValidationError('Must consist of hebrew characters and spaces only')

	def validate_newFirstNameEng(self, newFirstNameEng):
		if any((c < "\u0041" or (c > "\u005A" and c < "\u0061") or c > "\u007A") and (not c.isspace()) for c in newFirstNameEng.data):	
			raise ValidationError('Must consist of english characters and spaces only')

	def validate_newLastNameEng(self, newLastNameEng):
		if any((c < "\u0041" or (c > "\u005A" and c < "\u0061") or c > "\u007A") and (not c.isspace()) for c in newLastNameEng.data):	
			raise ValidationError('Must consist of english characters and spaces only')

	def validate_newSupervisorId(self, newSupervisorId):
		if not newSupervisorId.data.isdigit():
			raise ValidationError('Must contain only numbers!')
		supervisorExists = Supervisor.query.filter_by(supervisorId=self.newSupervisorId.data).first()
		if supervisorExists:
			raise ValidationError('There is already a supervisor with the ID you entered')

class joinAProjectForm(FlaskForm):
	projectTitle = SelectField('Project Title', validators=[DataRequired()])
	submitForm = SubmitField('Join')

class requestResetForm(FlaskForm):
	email = StringField('Email', validators=[DataRequired(), Email()], render_kw={"placeholder": "Email"})
	submitForm = SubmitField('Send')

	def validate_email(self, email):
		student = Student.query.filter_by(email=email.data).first()
		if student is None:
			raise ValidationError('There is no account with that email.')

class resetPasswordForm(FlaskForm):
	password = PasswordField('Password', validators=[DataRequired(), Length(min=8)], render_kw={"placeholder": "New Password"})
	confirmPassword = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')], render_kw={"placeholder": "Confirm New Password"})
	submitForm = SubmitField('Reset Password')


class sendProjectDocForm(FlaskForm):
	image = FileField('Image', validators=[DataRequired(), FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'bmp'])])
	video = FileField('Video Clip', validators=[DataRequired(), FileAllowed(['mp4'])])
	report = FileField('Project Report', validators=[DataRequired(), FileAllowed(['doc', 'docx', 'pdf'])])
	presentation = FileField('Presentation', validators=[DataRequired(), FileAllowed(['ppt', 'pptx'])])
	abstract = TextAreaField('Abstract', validators=[DataRequired()])
	code = FileField('Code', validators=[FileAllowed(['zip', 'rar'])])
	githubLink = StringField('Github Link')
	submitForm = SubmitField('Send')

	def validate_githubLink(self, githubLink):
		if githubLink.data.strip():
			if not githubLink.data.startswith("https://github.com/") and not githubLink.data.startswith("github.com/"):
				raise ValidationError('Not a valid github project link.')


class editProjectDocForm(FlaskForm):
	image = FileField('Image', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'bmp'])])
	video = FileField('Video Clip', validators=[FileAllowed(['mp4'])])
	report = FileField('Project Report', validators=[FileAllowed(['doc', 'docx', 'pdf'])])
	presentation = FileField('Presentation', validators=[FileAllowed(['ppt', 'pptx'])])
	abstract = TextAreaField('Abstract', validators=[DataRequired()])
	code = FileField('Code', validators=[FileAllowed(['zip', 'rar'])])
	githubLink = StringField('Github Link')
	submitForm = SubmitField('Apply Changes')

	def validate_githubLink(self, githubLink):
		if githubLink.data.strip():
			if not githubLink.data.startswith("https://github.com/") and not githubLink.data.startswith("github.com/"):
				raise ValidationError('Not a valid github project link.')


class addCourseForm(FlaskForm):
	newName = StringField('Name', validators=[DataRequired()])
	newNumber = StringField('Number', validators=[DataRequired()])
	newAcademicPoints = SelectField('Academic Points', choices=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')], default="1")
	submitAddForm = SubmitField('Add Course')

	def validate_newNumber(self, newNumber):
		if not newNumber.data.isdigit():
			raise ValidationError('Course number must contain only digits.')

		numberExists = Course.query.filter_by(number=newNumber.data).first()
		if numberExists:
			raise ValidationError('A course with the same number already exists.')


class editCourseForm(FlaskForm):
	courseId = HiddenField("")
	number = StringField('Number', validators=[DataRequired()])
	name = StringField('Name', validators=[DataRequired()])
	academicPoints = SelectField('Academic Points', choices=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')], default="1")
	
	submitEditForm = SubmitField('Save Changes')

	def validate_number(self, number):
		if not number.data.isdigit():
			raise ValidationError('Course number must contain only digits.')

		currentCourse = Course.query.filter_by(id=self.courseId.data).first()
		# number was changed
		if self.number.data != currentCourse.number:
			numberExists = Course.query.filter_by(number=self.number.data).first()
			if numberExists:
				raise ValidationError('A course with the same number already exists.')


class deleteCourseForm(FlaskForm):
	deleteCourseId = HiddenField("")


class sendPosterForm(FlaskForm):
	poster = FileField('Poster', validators=[DataRequired(), FileAllowed(['pdf'])])
	submitForm = SubmitField('Send')
