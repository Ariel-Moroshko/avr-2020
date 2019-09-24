from avr import models
from avr import db
import json
from avr import utils
from sqlalchemy import or_

############################ Projects ############################

def getProjectById(id):
	return models.Project.query.filter_by(id=id).first()

def getProjectsCount():
	return models.Project.query.count()

def addProject(newProject):
	project = models.Project()
	for field, data in newProject.items():
		project.__setattr__(field, data)
	db.session.add(project)
	db.session.commit()
	return project.id

def updateProject(id, newData):
	project = getProjectById(id)
	for field, data in newData.items():
		project.__setattr__(field, data)
	db.session.commit()

def updateProjectStudents(id, students):
	# delete old students
	models.StudentProject.query.filter_by(projectId=id).delete()
	# add new students
	for s in students:
		studentProject = models.StudentProject(projectId=id, studentId=s["id"], courseId=s["courseId"])
		db.session.add(studentProject)
		# register students
		models.Student.query.filter_by(id=s["id"]).first().isRegistered = True
	db.session.commit()


def updateProjectPublishState(id, state):
	project = getProjectById(id)
	if project is None:
		return None
	if state:
		project.published = True
	else:
		project.published = False
	db.session.commit()
	return True


def updateProjectSupervisors(id, supervisorsIds):
	project = getProjectById(id)
	# delete old supervisors
	project.supervisors = []
	# add new supervisors
	for supervisorId in supervisorsIds:
		project.supervisors.append(getSupervisorById(supervisorId)) 
	db.session.commit()

def updateProjectStatus(id, statusList):
	project = getProjectById(id)
	for field, data in statusList.items():
		project.__setattr__(field, data)
	# overall status
	project.status = project.calculateStatus()
	db.session.commit()

def deleteProject(id):
	project = getProjectById(id)
	# delete all students from project
	models.StudentProject.query.filter_by(projectId=id).delete()
	# delete all supervisors from project
	project.supervisors = []
	# delete project
	db.session.delete(project)
	db.session.commit()

def getProjectsTableData(sort, order, limit, offset, filters):
	filters_query = ""
	if filters:
		filters = json.loads(filters)
		if "year" in filters:
			filters_query += f" AND year='{filters['year']}'"
		if "semester" in filters:
			filters_query += f" AND semester='{filters['semester']}'"
		if "status" in filters:
			if filters['status'] == "ongoing":
				filters_query += f" AND status!='הושלם' AND status!='פוסטר'"
			elif filters['status'] == "הושלם":
				filters_query += f" AND (status='הושלם' OR status='פוסטר')"
			else:
				filters_query += f" AND status='{filters['status']}'"
			
	
	sort_query = ""
	if sort:
		if sort == "year":
			sort_query = " ORDER BY year " + order + ", semester"
		elif sort == "semester":
			sort_query = " ORDER BY semester " + order
		elif sort == "title":
			sort_query = " ORDER BY title " + order
		elif sort == "status":
			sort_query = " ORDER BY status " + order

	
	result_query = db.session.execute("SELECT * FROM project WHERE 1=1" + filters_query + sort_query + " LIMIT " + limit + " OFFSET " + offset)
	count_query = db.session.execute("SELECT count(*) FROM project WHERE 1=1" + filters_query)
	totalResults = count_query.scalar()
	return totalResults, result_query

def getProjectsTableFilters():
	# ------- project title filters
	projectTitleFilters_query = db.session.execute("SELECT DISTINCT title FROM project")
	projectTitleFilters = [{"value": "", "text": "ALL"}]
	for r in projectTitleFilters_query:
		projectTitleFilters.append({
			"value": r.title,
			"text": r.title
		})
	# ------- project status filters
	projectStatusFilters_query = db.session.execute("SELECT DISTINCT status FROM project")
	projectStatusFilters = [{"value": "", "text": "ALL"}, {"value": "ongoing", "text": "Ongoing"}]
	for r in projectStatusFilters_query:
		projectStatusFilters.append({
			"value": r.status,
			"text": r.status
		})
	# ------- year filters
	yearFilters_query = db.session.execute("SELECT DISTINCT year FROM project")
	yearFilters = [{"value": "", "text": "ALL"}]
	for r in yearFilters_query:
		yearFilters.append({
			"value": r.year,
			"text": r.year
		})
	# ------- semester filters
	semesterFilters_query = db.session.execute("SELECT DISTINCT semester FROM project")
	semesterFilters = [{"value": "", "text": "ALL"}]
	for r in semesterFilters_query:
		semesterFilters.append({
			"value": r.semester,
			"text": r.semester
		})
	filterOptions={
		"title": projectTitleFilters,
		"status": projectStatusFilters,
		"year": yearFilters,
		"semester": semesterFilters
	}
	return filterOptions


def getPublishedProjectsYears():
	return [project.year for project in db.session.query(models.Project.year).filter_by(projectDocApproved=True, published=True).order_by(models.Project.year.desc()).distinct()]

def getPublishedProjectsByYear(year):
	return models.Project.query.filter_by(year=year, projectDocApproved=True, published=True).with_entities(models.Project.id, models.Project.projectDocImage, models.Project.title, models.Project.abstract)

def getPublishedProjectDetails(id):
	return models.Project.query.filter_by(id=id, projectDocApproved=True, published=True).first()

############################ Students ############################

def getStudentsCount():
	return models.Student.query.count()

def getStudentById(id):
	return models.Student.query.filter_by(id=id).first()

def getStudentByStudentId(studentId):
	return models.Student.query.filter_by(studentId=studentId).first()

def getStudentByEmail(email):
	return models.Student.query.filter_by(email=email).first()

def getCourseIdForStudentInProject(projectId, studentId):
	studentProject =  models.StudentProject.query.filter_by(projectId=projectId, studentId=studentId).first()
	return studentProject.courseId

def studentHasRelatedProjects(id):
	hasRelatedProjects = models.StudentProject.query.filter_by(studentId=id).first()
	return hasRelatedProjects

def updateStudent(id, newData):
	student = getStudentById(id)
	# update this student in USERS table
	if "studentId" in newData:
		user = models.User.query.filter_by(userId=student.studentId).first()
		user.userId = newData["studentId"]

	for field, data in newData.items():
		student.__setattr__(field, data)
	db.session.commit()

def registerStudent(studentData):
	student = models.Student()
	for field, data in studentData.items():
		student.__setattr__(field, data)
	user = models.User(userId=student.studentId, userType="student")
	db.session.add(student)
	db.session.add(user)
	db.session.commit()

def deleteStudent(id):
	# remove all projects that this student is related to
	models.StudentProject.query.filter_by(studentId=id).delete()
	# remove from users table
	student = getStudentById(id)
	models.User.query.filter_by(userId=student.studentId).delete()
	db.session.delete(student)
	db.session.commit()

def isStudentEnrolledInProject(projectId, studentId):
	return models.StudentProject.query.filter_by(projectId=projectId, studentId=studentId).first()

def getStudentsTableData(sort, order, limit, offset, filters):
	filters_query = ""
	if filters:
		filters = json.loads(filters)
		if "year" in filters:
			if filters['year'] == "----":
				filters_query += f" AND year IS NULL"
			else:
				filters_query += f" AND year='{filters['year']}'"
		if "semester" in filters:
			if filters['semester'] == "----":
				filters_query += f" AND semester IS NULL"
			else:
				filters_query += f" AND semester='{filters['semester']}'"
		if "firstNameHeb" in filters:
			filters_query += " AND ("
			words_splitted = filters['firstNameHeb'].split()
			# search any word in first name
			for word in words_splitted:
				filters_query += f" (firstNameHeb LIKE '%{word}%')"
				if word != words_splitted[-1]:
					filters_query += " OR"
			
			filters_query += " OR"
			# also, search any word in last name
			for word in words_splitted:
				filters_query += f" (lastNameHeb LIKE '%{word}%')"
				if word != words_splitted[-1]:
					filters_query += " OR" 

			filters_query += ")"

			
		if "lastProjectTitle" in filters:
			if filters['lastProjectTitle'] == "NO PROJECT":
				filters_query += f" AND lastProjectTitle IS NULL"
			else:
				filters_query += f" AND lastProjectTitle='{filters['lastProjectTitle']}'"
		if "lastProjectStatus" in filters:
			if filters['lastProjectStatus'] == "----":
				filters_query += f" AND lastProjectStatus IS NULL"
			elif filters['lastProjectStatus'] == "ongoing":
				filters_query += f" AND lastProjectStatus!='הושלם' AND lastProjectStatus!='פוסטר'"
			elif filters['lastProjectStatus'] == "הושלם":
				filters_query += f" AND (lastProjectStatus='הושלם' OR lastProjectStatus='פוסטר')"
			else:
				filters_query += f" AND lastProjectStatus='{filters['lastProjectStatus']}'"
	
	sort_query = ""
	if sort:
		if sort == "year":
			sort_query = " ORDER BY year " + order
		elif sort == "semester":
			sort_query = " ORDER BY semester " + order
		elif sort == "studentId":
			sort_query = " ORDER BY studentId " + order
		elif sort == "firstNameHeb":
			sort_query = " ORDER BY firstNameHeb " + order
		elif sort == "lastNameHeb":
			sort_query = " ORDER BY lastNameHeb " + order
		elif sort == "lastProjectTitle":
			sort_query = " ORDER BY lastProjectTitle " + order
		elif sort == "lastProjectStatus":
			sort_query = " ORDER BY lastProjectStatus " + order

	
	result_query = db.session.execute("SELECT * FROM students_view WHERE 1=1" + filters_query + sort_query + " LIMIT " + limit + " OFFSET " + offset)
	count_query = db.session.execute("SELECT count(*) FROM students_view WHERE 1=1" + filters_query)
	totalResults = count_query.scalar()
	return totalResults, result_query

def getStudentsTableFilters():
	# ------- lastProjectTitle filters
	lastProjectTitleFilters_query = db.session.execute("SELECT DISTINCT lastProjectTitle FROM students_view")
	lastProjectTitleFilters = [{"value": "", "text": "ALL"}]
	for r in lastProjectTitleFilters_query:
		lastProjectTitleFilters.append({
			"value": r.lastProjectTitle or "NO PROJECT",
			"text": r.lastProjectTitle or "NO PROJECT"
		})
	# ------- lastProjectStatus filters
	lastProjectStatusFilters_query = db.session.execute("SELECT DISTINCT lastProjectStatus FROM students_view")
	lastProjectStatusFilters = [{"value": "", "text": "ALL"}, {"value": "ongoing", "text": "Ongoing"}]
	for r in lastProjectStatusFilters_query:
		lastProjectStatusFilters.append({
			"value": r.lastProjectStatus or "----",
			"text": r.lastProjectStatus or "----"
		})
	# ------- year filters
	yearFilters_query = db.session.execute("SELECT DISTINCT year FROM students_view")
	yearFilters = [{"value": "", "text": "ALL"}]
	for r in yearFilters_query:
		yearFilters.append({
			"value": r.year or "----",
			"text": r.year or "----"
		})
	# ------- semester filters
	semesterFilters_query = db.session.execute("SELECT DISTINCT semester FROM students_view")
	semesterFilters = [{"value": "", "text": "ALL"}]
	for r in semesterFilters_query:
		semesterFilters.append({
			"value": r.semester or "----",
			"text": r.semester or "----"
		})
	filterOptions={
		"lastProjectTitle": lastProjectTitleFilters,
		"lastProjectStatus": lastProjectStatusFilters,
		"year": yearFilters,
		"semester": semesterFilters
	}
	return filterOptions

def getStudentsTableForProjectData(sort, order, limit, offset, filters):
	query = models.Student.query.filter()
	if filters:
		filters = json.loads(filters)
		if "registrationYear" in filters:
			query = query.filter_by(year=filters["registrationYear"])
		if "registrationSemester" in filters:
			query = query.filter_by(semester=filters["registrationSemester"])
		if "firstNameHeb" in filters:
			query = query.filter(
					or_(
						*[models.Student.firstNameHeb.like("%"+name+"%") for name in filters["firstNameHeb"].split()],
						*[models.Student.lastNameHeb.like("%"+name+"%") for name in filters["firstNameHeb"].split()],
					)
			) 
	
	if sort:
		if sort == "registrationYear":
			query = query.order_by(models.Student.year.desc() if order == "desc" else models.Student.year.asc())
		elif sort == "registrationSemester":
			query = query.order_by(models.Student.semester.desc() if order == "desc" else models.Student.semester.asc())
		elif sort == "studentId":
			query = query.order_by(models.Student.studentId.desc() if order == "desc" else models.Student.studentId.asc())
		elif sort == "firstNameHeb":
			query = query.order_by(models.Student.firstNameHeb.desc() if order == "desc" else models.Student.firstNameHeb.asc())
		elif sort == "lastNameHeb":
			query = query.order_by(models.Student.lastNameHeb.desc() if order == "desc" else models.Student.lastNameHeb.asc())
	
	totalResults = query.count()
	query_results = query.paginate(int(int(offset)/int(limit))+1, int(limit), False).items
	return totalResults, query_results

def getStudentsTableForProjectFilters():
	# ------- year filters
	years = [{"value": "", "text": "ALL"}]
	for r in db.session.query(models.Student.year).order_by(models.Student.year.desc()).distinct():
		years.append({
			"value": r.year,
			"text": r.year
		})
	# ------- semester filters
	semesters = [{"value": "", "text": "ALL"}]
	for r in db.session.query(models.Student.semester).distinct():
		semesters.append({
			"value": r.semester,
			"text": r.semester
		})
	filterOptions={
		"registrationYear": years,
		"registrationSemester": semesters
	}
	return filterOptions

############################ Courses ############################

def getCoursesCount():
	return models.Course.query.count()

def getCourseById(id):
	return models.Course.query.filter_by(id=id).first()

def getAllCourses():
	return models.Course.query.all()

def getCoursesTableData(sort, order, limit, offset, filters):
	query = models.Course.query.filter()
	if filters:
		filters = json.loads(filters)
		if "name" in filters:
			query = query.filter(models.Course.name.contains(filters["name"]))
		if "number" in filters:
			query = query.filter(models.Course.number.contains(filters["number"]))
	
	if sort:
		if sort == "number":
			query = query.order_by(models.Course.number.desc() if order == "desc" else models.Course.number.asc())
		if sort == "name":
			query = query.order_by(models.Course.name.desc() if order == "desc" else models.Course.name.asc())
		if sort == "academicPoints":
			query = query.order_by(models.Course.academicPoints.desc() if order == "desc" else models.Course.academicPoints.asc())
	
	totalResults = query.count()
	query_results = query.paginate(int(int(offset)/int(limit))+1, int(limit), False).items
	return totalResults, query_results

def updateCourse(id, newData):
	course = getCourseById(id)
	for field, data in newData.items():
		course.__setattr__(field, data)
	db.session.commit()

def addCourse(newCourse):
	course = models.Course()
	for field, data in newCourse.items():
		course.__setattr__(field, data)
	db.session.add(course)
	db.session.commit()
	
def deleteCourse(id):
	course = getCourseById(id)
	isDefaultCourse = course.isDefault
	# check if the course number is associated with a project
	relatedToProject = models.StudentProject.query.filter_by(courseId=id).first()
	if not relatedToProject:
		db.session.delete(course)
		db.session.commit()
		if isDefaultCourse and getCoursesCount() > 0:	# make sure there is a default course
			newDefaultCourse = models.Course.query.first()
			newDefaultCourse.isDefault = True
			db.session.commit()
	return "not deleted" if relatedToProject else "deleted"

def updateDefaultCourse(id):
	course = getCourseById(id)
	previousDefault = models.Course.query.filter_by(isDefault=True).first()
	if previousDefault:
		previousDefault.isDefault = None
		db.session.commit()		# the previous default flag should be deleted before the new one is set because "isDefault" field is unique
	course.isDefault = True
	db.session.commit()

############################ Supervisors ############################

def getSupervisorById(id):
	return models.Supervisor.query.filter_by(id=id).first()

def getAllSupervisors():
	return models.Supervisor.query.all()

def getActiveSupervisors():
	return models.Supervisor.query.filter_by(status="active").all()

def getSupervisorsCount():
	return models.Supervisor.query.count()

def addSupervisor(newSupervisor):
	supervisor = models.Supervisor()
	for field, data in newSupervisor.items():
		supervisor.__setattr__(field, data)
	db.session.add(supervisor)
	db.session.commit()

def updateSupervisor(id, newData):
	supervisor = getSupervisorById(id)
	for field, data in newData.items():
		supervisor.__setattr__(field, data)
	db.session.commit()

def deleteSupervisor(id):
	supervisor = getSupervisorById(id)
	# remove all proposed projects that this supervisor is related to
	supervisor.proposedProjects = []
	# if this supervisor had any projects, don't delete it, just make it "not active"
	hadProjects = supervisor.projects
	if hadProjects:
		supervisor.status = "not active"
	else:
		db.session.delete(supervisor)
	db.session.commit()
	return "not deleted" if hadProjects else "deleted"

def getSupervisorsTableData(sort, order, limit, offset, filters):
	query = models.Supervisor.query.filter()
	if filters:
		filters = json.loads(filters)
		if "status" in filters:
			query = query.filter_by(status=filters["status"])
	
	if sort:
		if sort == "status":
			query = query.order_by(models.Supervisor.status.desc() if order == "desc" else models.Supervisor.status.asc())
		elif sort == "supervisorId":
			query = query.order_by(models.Supervisor.supervisorId.desc() if order == "desc" else models.Supervisor.supervisorId.asc())
		elif sort == "firstNameHeb":
			query = query.order_by(models.Supervisor.firstNameHeb.desc() if order == "desc" else models.Supervisor.firstNameHeb.asc())
		elif sort == "lastNameHeb":
			query = query.order_by(models.Supervisor.lastNameHeb.desc() if order == "desc" else models.Supervisor.lastNameHeb.asc())
	
	totalResults = query.count()
	query_results = query.paginate(int(int(offset)/int(limit))+1, int(limit), False).items
	return totalResults, query_results

############################ Proposed Projects ############################
def getAllPublishedProposedProjects():
	return models.ProposedProject.query.filter_by(published=True).all()

def getAllProposedProjects():	
	return models.ProposedProject.query.all()

def getLimitedProposedProjects(limit):
	return models.ProposedProject.query.limit(limit).all()

def getProposedProjectById(id):
	return models.ProposedProject.query.filter_by(id=id).first()

def getProposedProjectsCount():
	return models.ProposedProject.query.count()

def getProposedProjectByTitle(title):
	return models.ProposedProject.query.filter_by(title=title).first()

def addProposedProject(newProposedProject):
	proposedProject = models.ProposedProject()
	for field, data in newProposedProject.items():
		proposedProject.__setattr__(field, data)
	db.session.add(proposedProject)
	db.session.commit()
	return proposedProject.id

def updateProposedProject(id, newData):
	proposedProject = getProposedProjectById(id)
	for field, data in newData.items():
		proposedProject.__setattr__(field, data)
	db.session.commit()

def updateProposedProjectSupervisors(id, supervisorsIds):
	proposedProject = getProposedProjectById(id)
	# delete old supervisors
	proposedProject.supervisors = []
	# add new supervisors
	for supervisorId in supervisorsIds:
		proposedProject.supervisors.append(getSupervisorById(supervisorId)) 
	db.session.commit()

def updateProposedProjectPublishState(id, state):
	proposedProject = getProposedProjectById(id)
	if proposedProject is None:
		return None
	if state:
		proposedProject.published = True
	else:
		proposedProject.published = False
	db.session.commit()
	return True

def deleteProposedProject(id):
	proposedProject = getProposedProjectById(id)
	# delete all supervisors related to this proposed project
	proposedProject.supervisors = []
	# delete proposed project
	db.session.delete(proposedProject)
	db.session.commit()

def getProposedProjectsTableData(sort, order, limit, offset, filters):
	query = models.ProposedProject.query.filter()
	if filters:
		filters = json.loads(filters)
		if "title" in filters:
			query = query.filter(models.ProposedProject.title.contains(filters["title"]))				
	
	if sort:
		if sort == "title":
			query = query.order_by(models.ProposedProject.title.desc() if order == "desc" else models.ProposedProject.title.asc())
	
	totalResults = query.count()
	query_results = query.paginate(int(int(offset)/int(limit))+1, int(limit), False).items
	return totalResults, query_results

############################ Users ############################

def getUserByUserId(userId):
	return models.User.query.filter_by(userId=userId).first()

############################ Admin ############################

def getAdminByAdminId(adminId):
	return models.Admin.query.filter_by(adminId=adminId).first()

def getAdminsCount():
	return models.Admin.query.count()

def addAdmin(adminData):
	admin = models.Admin()
	for field, data in adminData.items():
		admin.__setattr__(field, data)
	user = models.User(userId=admin.adminId, userType="admin")
	db.session.add(admin)
	db.session.add(user)
	db.session.commit()

############################ Overview ############################

def getLabOverview():
	currentYear = utils.getCurrentYear()
	lastRegistrationSemester = utils.getRegistrationSemester()
	currentSemester = utils.getCurrentSemester()
	totalProjectsThisSemester = db.session.query(models.Project).filter_by(year=currentYear, semester=currentSemester).count()
	finishedProjectsThisSemester = db.session.query(models.Project).filter_by(year=currentYear, semester=currentSemester, gradeStatus=True).count()
	totalProjects = getProjectsCount()

	totalStudents = getStudentsCount()
	studentsThisSemester = db.session.query(models.Student).filter_by(year=currentYear, semester=lastRegistrationSemester).count()
	totalProposedProjects = getProposedProjectsCount()
	totalSupervisors = getSupervisorsCount()
	return {
		"projects": {
			"total": totalProjects,
			"thisSemester": {
				"finished": finishedProjectsThisSemester,
				"total": totalProjectsThisSemester
			}
		},
		"students": {
			"total": totalStudents,
			"thisSemester": studentsThisSemester
		},
		"proposedProjects": {
			"total": totalProposedProjects
		},
		"supervisors": {
			"total": totalSupervisors
		}

	}
