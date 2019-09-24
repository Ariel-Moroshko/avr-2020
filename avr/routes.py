import os
import json
from flask import render_template, url_for, flash, redirect, request, jsonify, Response
from avr import app, db, bcrypt, mail
from avr.forms import (RegistrationForm, LoginForm, EditAccountForm, 
						addProposedProjectForm, editProposedProjectForm, 
						deleteProposedProjectForm, addProjectForm, editProjectForm, deleteProjectForm, editStudentForm, deleteStudentForm, editSupervisorForm, 
						deleteSupervisorForm, addSupervisorForm, joinAProjectForm, 
						requestResetForm, resetPasswordForm, createAdminForm, sendProjectDocForm, editProjectDocForm,
						addCourseForm, editCourseForm, deleteCourseForm, sendPosterForm)
from avr.models import (Student, User, Admin, Project, Supervisor, StudentProject,
						ProposedProject, Course)
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
from avr import utils
from avr import database
import traceback
from threading import Thread
import time
from werkzeug.exceptions import RequestEntityTooLarge


@app.route('/logout', methods=['GET'])
def logout():
	logout_user()
	return redirect(url_for('login'))


@app.route('/Admin', methods=['GET'])
def admin():
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	return redirect(url_for('labOverview'))


@app.route('/Admin/Overview', methods=['GET'])
def labOverview():
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	overview = database.getLabOverview()
	return render_template("/admin/labOverview.html", overview=overview)


@app.route('/Admin/Courses', methods=['GET', 'POST'])
def manageCourses():
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	try:
		addForm = addCourseForm()
		editForm = editCourseForm()
		deleteForm = deleteCourseForm()

		if(request.method == 'POST'):
			formName = request.form['pageForm']
			if formName == 'addCourseForm':
				if addForm.validate_on_submit():
					setAsDefaultCourse = None
					totalCourses = database.getCoursesCount()
					if totalCourses == 0:
						setAsDefaultCourse = True
					# create new course
					database.addCourse({
						"number": addForm.newNumber.data,
						"name": addForm.newName.data,
						"academicPoints": addForm.newAcademicPoints.data,
						"isDefault": setAsDefaultCourse
					})
					
					flash('Course was created successfully!', 'success')
					return jsonify({
						"status": "success"
					})
					
				else:
					app.logger.info('In manageCourses, addForm is NOT valid. addForm.errors:{}'.format(addForm.errors))
					return jsonify({
						"status": "error",
						"errors": addForm.errors
					})
			elif formName == 'editCourseForm':
				course = database.getCourseById(editForm.courseId.data)

				if not course:
					app.logger.error('In manageCourses, in editForm, tried to edit a course with id {} that does not exist in the db'.format(editForm.courseId.data))
					return jsonify({
						"status": "courseIdNotFound",
						"id": editForm.courseId.data
					})

				if editForm.validate_on_submit():	
					database.updateCourse(course.id, {
						"number": editForm.number.data,
						"name": editForm.name.data,
						"academicPoints": editForm.academicPoints.data,
					})

					flash(f"Course '{course.name}' was updated successfully!", 'success')
					return jsonify({
						"status": "success"
					})
				else:
					app.logger.info('In manageCourses, editForm is NOT valid. editForm.errors:{}'.format(editForm.errors))
					return jsonify({
						"status": "error",
						"errors": editForm.errors
					})
			elif formName == 'deleteCourseForm':
				course = database.getCourseById(deleteForm.deleteCourseId.data)
				if course:
					deleteResult = database.deleteCourse(course.id)			
					if deleteResult == "deleted":
						flash('Course was deleted successfully!', 'primary')
					else:
						flash(f'Could not delete course {course.number} because it has related projects', 'warning')
				else:
					app.logger.info('could not delete course with id {}, because there is no course with this id'.format(deleteForm.deleteCourseId.data))
					flash("Error: can't delete, course id is not in the db", 'danger')
				return redirect(url_for('manageCourses'))

		return render_template('/admin/courses.html', title="Manage Courses", addForm=addForm, editForm=editForm, deleteForm=deleteForm)
	except Exception as e:
		app.logger.error('In manageCourses, Error is: {}\n{}'.format(e, traceback.format_exc()))
		return redirect(url_for('errorPage'))


@app.route('/Admin/Courses/UpdateDefaultCourse', methods=['POST'])
def updateDefaultCourse():
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	
	try:
		if request.method == "POST":
			courseId = request.form.get("courseId")
			course = database.getCourseById(courseId)
			if not course:
				return jsonify(result="failed", reason="course id was not found")	
			database.updateDefaultCourse(courseId)			
			return jsonify(result="ok")	

	except Exception as e:
		app.logger.error('In UpdateDefaultCourse, error is: {}\n{}'.format(e, traceback.format_exc()))
		return jsonify(result="failed")
	

@app.route('/Admin/Courses/json', methods=['GET', 'POST'])
def getCoursesTableData():
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))

	try:
		sort = request.args.get('sort')
		order = request.args.get('order') or "desc"
		limit = request.args.get('limit') or 10
		offset = request.args.get('offset') or 0
		filters = request.args.get('filter')
		
		totalResults, results = database.getCoursesTableData(sort, order, limit, offset, filters)
		
		rows = []
		for result in results:
			defaultFlag = "<i class='far fa-flag'></i>"
			if result.isDefault:
				defaultFlag = '<i class="fas fa-flag selected" style="color: #1b60e4;"></i>'
			rows.append({
				"id": result.id,
				"number": result.number,
				"name": result.name,
				"academicPoints": result.academicPoints,
				"btnDefault": f"<span name='isDefaultFlag' data-course-id='{result.id}' class='isDefaultFlag'>{defaultFlag}</span>",
				"btnEdit": f"<button type='button' onclick='getCourseData({result.id})' data-course-id='{result.id}' name='btnEdit' class='btn'><i class='fa fa-edit fa-fw'></i><span name='loading' class='spinner-border spinner-border-sm' style='display:none; vertical-align:sub;margin-right: 0.25rem;' role='status'></span><span style='margin-left: 0.4rem;'>Edit</span></button>",
				"btnDelete": f"<button type='button' onclick='deleteCourse({result.id})' name='btnDelete' class='btn' data-toggle='modal' data-target='#deleteCourseModal'><i class='fa fa-trash fa-fw'></i> Delete</button>"
			})

		return jsonify( 
			total=totalResults,
			rows=rows,
			filterOptions={}
		)
		
	except Exception as e:
		app.logger.error('In getCoursesTableData, error is: {}\n{}'.format(e, traceback.format_exc()))
		return jsonify(total=0, rows=[])	


@app.route('/Admin/Courses/<int:id>/json', methods=['GET', 'POST'])
def getCourseData(id):
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	
	try:
		course = database.getCourseById(id)
		if not course:
			return jsonify({})
		courseData = { 
			"id": course.id,
			"number": course.number,
			"name": course.name,
			"academicPoints": course.academicPoints
		}
		return jsonify(courseData)

	except Exception as e:
		app.logger.error('In getCourseData, error is: {}\n{}'.format(e, traceback.format_exc()))
		return jsonify({})
	

@app.route('/Admin/Supervisors/Delete', methods=['POST'])
def deleteSupervisor():
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	try:
		deleteForm = deleteSupervisorForm()
		supervisor = database.getSupervisorById(deleteForm.deleteSupervisorId.data)
		if supervisor:
			deleteResult = database.deleteSupervisor(supervisor.id)			
			if deleteResult == "deleted":
				flash('Supervisor was deleted successfully!', 'primary')
			else:
				flash('Supervisor has related projects, it was NOT deleted. Instead, it became not active.', 'info')
		else:
			app.logger.info('In deleteSupervisor, could not delete supervisor with id {}, because there is no supervisor with this id'.format(deleteForm.deleteSupervisorId.data))
			flash("Error: can't delete, supervisor id is not in the db", 'danger')
		return redirect(url_for('manageSupervisors'))
	except Exception as e:
		app.logger.error('In deleteSupervisor, Error is: {}\n{}'.format(e, traceback.format_exc()))
		return redirect(url_for('errorPage'))


@app.route('/Admin/Supervisors/<int:id>/json', methods=['GET', 'POST'])
def getSupervisorData(id):
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	try:
		supervisor = database.getSupervisorById(id)
		if not supervisor:
			return jsonify({})
		supervisorData = { 
			"id": supervisor.id,
			"supervisorId": supervisor.supervisorId,
			"firstNameHeb": supervisor.firstNameHeb,
			"lastNameHeb": supervisor.lastNameHeb,
			"firstNameEng": supervisor.firstNameEng,
			"lastNameEng": supervisor.lastNameEng,
			"email": supervisor.email or "",
			"phone": supervisor.phone or "",
			"status": supervisor.status
		}
		return jsonify(supervisorData)
	except Exception as e:
		app.logger.error('In getSupervisorData, error is: {}\n{}'.format(e, traceback.format_exc()))
		return jsonify({})


@app.route('/Admin/Supervisors/json', methods=['GET', 'POST'])
def getSupervisorsTableData():
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))

	try:
		sort = request.args.get('sort')
		order = request.args.get('order') or "desc"
		limit = request.args.get('limit') or 10
		offset = request.args.get('offset') or 0
		filters = request.args.get('filter')
		
		totalResults, results = database.getSupervisorsTableData(sort, order, limit, offset, filters)	
		rows = []
		for result in results:
			rows.append({
				"status": result.status,
				"supervisorId": result.supervisorId,
				"firstNameHeb": result.firstNameHeb,
				"lastNameHeb": result.lastNameHeb,
				"email": result.email or "",
				"btnEdit": f"<button type='button' onclick='getSupervisorData({result.id})' data-supervisor-id='{result.id}' name='btnEdit' class='btn'><i class='fa fa-edit fa-fw'></i><span name='loading' class='spinner-border spinner-border-sm' style='display:none; vertical-align:sub;margin-right: 0.25rem;' role='status'></span><span style='margin-left: 0.4rem;'>Edit</span></button>",
				"btnDelete": f"<button type='button' onclick='deleteSupervisor({result.id})' name='btnDelete' class='btn' data-toggle='modal' data-target='#deleteSupervisorModal'><i class='fa fa-trash fa-fw'></i> Delete</button>"
			})

		# get filters options for the table
		# ------- status filters
		status = [{"value": "", "text": "ALL"}, {"value": "active", "text": "active"}, {"value": "not active", "text": "not active"}]

		return jsonify( 
			total=totalResults,
			rows=rows,
			filterOptions={
				"status": status
			})
			
	except Exception as e:
		app.logger.error('In getSupervisorsTableData, error is: {}\n{}'.format(e, traceback.format_exc()))
		return jsonify(total=0, rows=[])	


@app.route('/Admin/Supervisors', methods=['GET', 'POST'])
def manageSupervisors():
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	try:
		addForm = addSupervisorForm()
		editForm = editSupervisorForm()
		deleteForm = deleteSupervisorForm()
		
		if(request.method == 'POST'):
			formName = request.form['sentFormName']
			if formName == 'editSupervisorForm':
				supervisor = database.getSupervisorById(editForm.id.data)
				if not supervisor:
					app.logger.error('In manageSupervisors, in editForm, tried to edit a supervisor with id {} that does not exist in the db'.format(editForm.id.data))
					return jsonify({
						"status": "supervisorIdNotFound",
						"id": editForm.id.data
					})
					
				if editForm.validate_on_submit():
					database.updateSupervisor(supervisor.id, {
						"supervisorId": editForm.supervisorId.data,
						"firstNameEng": editForm.firstNameEng.data.capitalize(),
						"lastNameEng": editForm.lastNameEng.data.capitalize(),
						"firstNameHeb": editForm.firstNameHeb.data,
						"lastNameHeb": editForm.lastNameHeb.data,
						"email": editForm.email.data.strip(),
						"phone": editForm.phone.data,
						"status": editForm.status.data,
					})
					
					flash(f"Supervisor '{supervisor.firstNameEng} {supervisor.lastNameEng}' was updated successfully!", 'success')
					return jsonify({
						"status": "success"
					})
				else:
					app.logger.info('In manageSupervisors, editForm is NOT valid. editForm.errors: {}'.format(editForm.errors))
					return jsonify({
						"status": "error",
						"errors": editForm.errors
					})
			if formName == 'addSupervisorForm':
				if addForm.validate_on_submit():					
					database.addSupervisor({
						"supervisorId": addForm.newSupervisorId.data,
						"firstNameEng": addForm.newFirstNameEng.data.capitalize(),
						"lastNameEng": addForm.newLastNameEng.data.capitalize(),
						"firstNameHeb": addForm.newFirstNameHeb.data,
						"lastNameHeb": addForm.newLastNameHeb.data,
						"email": addForm.newEmail.data.strip(),
						"phone": addForm.newPhone.data,
						"status": addForm.newStatus.data
					})

					flash('Supervisor was created successfully!', 'success')
					return jsonify({
						"status": "success"
					})
				else:
					app.logger.info('In manageSupervisors, addForm is NOT valid. addForm.errors: {}'.format(addForm.errors))
					return jsonify({
						"status": "error",
						"errors": addForm.errors
					})
		return render_template('/admin/supervisors.html', title="Manage Supervisors", editForm=editForm, deleteForm=deleteForm, addForm=addForm)
	except Exception as e:
		app.logger.error('In manageSupervisors, Error is: {}\n{}'.format(e, traceback.format_exc()))
		return redirect(url_for('errorPage'))


@app.route('/Admin/Students/Delete', methods=['POST'])
def deleteStudent():
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	try:
		deleteForm = deleteStudentForm()
		student = database.getStudentById(deleteForm.deleteStudentId.data)
		if student:
			# check if the student is associated with a project
			hasRelatedToProjects = database.studentHasRelatedProjects(student.id)
			if hasRelatedToProjects:
				flash(f"Could not delete student '{student.firstNameEng} {student.lastNameEng}' because it has related projects", 'warning')
			else:
				# delete profile pic if exists
				utils.delete_profile_image(student.profilePic)
				database.deleteStudent(student.id)
				app.logger.info('In deleteStudent, deleting student {}'.format(student))
				flash('Student was deleted successfully!', 'success')
		else:
			app.logger.info('In deleteStudent, could not delete student with id {}, because there is no student with this id'.format(deleteForm.deleteStudentId.data))
			flash("Error: can't delete, student with id {} is not in the db".format(deleteForm.deleteStudentId.data), 'danger')
		return redirect(url_for('manageStudents'))
	except Exception as e:
		app.logger.error('In deleteStudent, Error is: {}\n{}'.format(e, traceback.format_exc()))
		return redirect(url_for('errorPage'))


@app.route('/Admin/Students/<int:id>/json', methods=['GET', 'POST'])
def getStudentData(id):
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	try:
		student = database.getStudentById(id)
		if not student:
			return jsonify({})
		lastProjects = [{"id": p.id, "title": p.title} for p in student.projects]
		studentData = { 
			"id": student.id,
			"profilePic": student.profilePic or "default.png",
			"year": student.year or "",
			"semester": student.semester or "",
			"studentId": student.studentId,
			"firstNameHeb": student.firstNameHeb,
			"lastNameHeb": student.lastNameHeb,
			"firstNameEng": student.firstNameEng,
			"lastNameEng": student.lastNameEng,
			"email": student.email,
			"lastProjects": lastProjects
		}
		return jsonify(studentData)
	except Exception as e:
		app.logger.error('In getStudentsTableData, error is: {}\n{}'.format(e, traceback.format_exc()))
		return jsonify({})


@app.route('/Admin/StudentsForProject/json', methods=['GET', 'POST'])
def getStudentsTableForProjectData():
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))

	try:
		sort = request.args.get('sort')
		order = request.args.get('order') or "desc"
		limit = request.args.get('limit') or 10
		offset = request.args.get('offset') or 0
		filters = request.args.get('filter')
		
		totalResults, results = database.getStudentsTableForProjectData(sort, order, limit, offset, filters)
		
		rows = []
		for result in results:
			profilePic = f"<img style='width:50px;height:50px;margin: 0 0.7rem;' src='/static/images/profile/default.png' alt='default profile pic'>"
			if result.profilePic:	
				profilePic = f"<img style='width:50px;height:50px;margin: 0 0.7rem;' src='/static/images/profile/{result.profilePic}' alt='{result.profilePic}'>"

			rows.append({
				"profilePic": profilePic,
				"registrationYear": result.year,
				"registrationSemester": result.semester,
				"studentId": result.studentId,
				"firstNameHeb": result.firstNameHeb,
				"lastNameHeb": result.lastNameHeb,
				"id": result.id,
				"firstNameEng": result.firstNameEng,
				"lastNameEng": result.lastNameEng,
				"email": result.email,
			})

		# get filters options for the table
		filterOptions = database.getStudentsTableForProjectFilters()

		return jsonify( 
			total=totalResults,
			rows=rows,
			filterOptions=filterOptions
		)
		
	except Exception as e:
		app.logger.error('In getStudentsTableForProjectData, error is: {}\n{}'.format(e, traceback.format_exc()))
		return jsonify(total=0, rows=[])	


@app.route('/Admin/Students/json', methods=['GET', 'POST'])
def getStudentsTableData():
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))

	try:
		sort = request.args.get('sort')
		order = request.args.get('order') or "desc"
		limit = request.args.get('limit') or 10
		offset = request.args.get('offset') or 0
		filters = request.args.get('filter')
		
		totalResults, results = database.getStudentsTableData(sort, order, limit, offset, filters)
		
		rows = []
		for result in results:
			profilePic = f"<img style='width:50px;height:50px;' src='/static/images/profile/default.png' alt='default profile pic'>"
			if result.profilePic:	
				profilePic = f"<img style='width:50px;height:50px;' src='/static/images/profile/{result.profilePic}' alt='{result.profilePic}'>"

			lastProjectTitle = f"<span class='badge shadow-sm' name='studentNOProjectBadge'>NO PROJECT</span>"
			if result.lastProjectTitle:
				lastProjectTitle = f"<button type='button' onclick='getProjectData({result.lastProjectId})' class='btn shadow-sm' name='studentProjectBadge' data-project-id='{result.lastProjectId}' style='white-space: normal;'><span name='loading' class='spinner-border spinner-border-sm' style='display:none; vertical-align:sub;margin-right: 0.5rem;' role='status'></span><span>{result.lastProjectTitle}</span></button>"

			rows.append({
				"profilePic": profilePic,
				"year": result.year or "----",
				"semester": result.semester or "----",
				"studentId": result.studentId,
				"firstNameHeb": result.firstNameHeb,
				"lastNameHeb": result.lastNameHeb,
				"lastProjectTitle": lastProjectTitle,
				"lastProjectStatus": result.lastProjectStatus or "----",
				"btnEdit": f"<button type='button' onclick='getStudentData({result.id})' data-student-id='{result.id}' name='btnEdit' class='btn'><i class='fa fa-edit fa-fw'></i><span name='loading' class='spinner-border spinner-border-sm' style='display:none; vertical-align:sub;margin-right: 0.25rem;' role='status'></span><span style='margin-left: 0.4rem;'>Edit</span></button>",
				"btnDelete": f"<button type='button' onclick='deleteStudent({result.id})' name='btnDelete' class='btn' data-toggle='modal' data-target='#deleteStudentModal'><i class='fa fa-trash fa-fw'></i> Delete</button>"
			})

		# get filters options for the table
		filterOptions = database.getStudentsTableFilters()
		return jsonify( 
			total=totalResults,
			rows=rows,
			filterOptions=filterOptions
		)
		
	except Exception as e:
		app.logger.error('In getStudentsTableData, error is: {}\n{}'.format(e, traceback.format_exc()))
		return jsonify(total=0, rows=[])



@app.route('/Admin/Students', methods=['GET', 'POST'])
def manageStudents():
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	try:
		totalStudents = database.getStudentsCount()
		editForm = editStudentForm()
		edit_ProjectForm = editProjectForm()
		courses = database.getAllCourses()
		deleteForm = deleteStudentForm()
		currentSemester = utils.getRegistrationSemester()
		currentYear = utils.getCurrentYear()
		semesterChoices = [("Winter", "Winter"), ("Spring", "Spring")]
		if currentSemester == "Spring":
			semesterChoices.reverse()

		allSupervisors = database.getAllSupervisors()
		supervisorsChoices = [(str(s.id),s.firstNameEng+" "+s.lastNameEng) for s in allSupervisors]
		supervisorsChoices.insert(0, ('', ''))

		edit_ProjectForm.year.choices = [(currentYear, currentYear), (str(int(currentYear)+1),str(int(currentYear)+1)), (str(int(currentYear)+2),str(int(currentYear)+2))]
		edit_ProjectForm.semester.choices = semesterChoices
		edit_ProjectForm.supervisor1.choices = supervisorsChoices
		edit_ProjectForm.supervisor2.choices = supervisorsChoices
		edit_ProjectForm.supervisor3.choices = supervisorsChoices


		if(request.method == 'POST'):
			formName = request.form['sentFormName']
			if formName == 'editStudentForm':
				student = database.getStudentById(editForm.id.data)
				if not student:
					app.logger.error('In manageStudents, in editForm, tried to edit a student with id {} that does not exist in the db'.format(editForm.id.data))
					return jsonify({
						"status": "studentIdNotFound",
						"id": editForm.id.data
					})
					
				if editForm.validate_on_submit():
					database.updateStudent(student.id, {
						"studentId": editForm.studentId.data,
						"firstNameEng": editForm.firstNameEng.data.capitalize(),
						"lastNameEng": editForm.lastNameEng.data.capitalize(),
						"firstNameHeb": editForm.firstNameHeb.data,
						"lastNameHeb": editForm.lastNameHeb.data,
						"email": editForm.email.data
					})
					
					flash(f"Student '{student.firstNameEng} {student.lastNameEng}' was updated successfully!", 'success')
					return jsonify({
						"status": "success"
					})
				else:
					app.logger.info('In manageStudents, editForm is NOT valid. editForm.errors: {}'.format(editForm.errors))
					return jsonify({
						"status": "error",
						"errors": editForm.errors
					})

		return render_template('/admin/students.html', title="Manage Students", editForm=editForm, editProjectForm=edit_ProjectForm, courses=courses, deleteForm=deleteForm, totalStudents=totalStudents)
	except Exception as e:
		app.logger.error('In manageStudents, error is: {}\n{}'.format(e, traceback.format_exc()))
		return redirect(url_for('errorPage'))


@app.route('/Admin/Projects/UpdatePublishState', methods=['POST'])
def updateProjectPublishState():
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	
	try:
		if request.method == "POST":
			id = request.form.get("id")
			state = request.form.get("state")
			result = database.updateProjectPublishState(id, True if state=="true" else False)
			if result == None:
				return jsonify(result="failed", reason="proposed project id was not found")	
			return jsonify(result="ok")	

	except Exception as e:
		app.logger.error('In updateProjectPublishState, error is: {}\n{}'.format(e, traceback.format_exc()))
		return jsonify(result="failed")



@app.route('/Admin/Projects/<int:id>/json', methods=['GET', 'POST'])
def getProjectData(id):
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	
	try:
		project = database.getProjectById(id)
		if not project:
			return jsonify({})
		studentsInProject = [{
			"id": s.id, 
			"studentId": s.studentId,
			"firstNameHeb": s.firstNameHeb,
			"lastNameHeb": s.lastNameHeb,
			"firstNameEng": s.firstNameEng,
			"lastNameEng": s.lastNameEng,
			"email": s.email,
			"profilePic": f"<img style='width:50px;height:50px;' src='/static/images/profile/{s.profilePic}' alt='{s.profilePic}'>" if s.profilePic else f"<img style='width:50px;height:50px;' src='/static/images/profile/default.png' alt='default profile pic'>"
				
		} for s in project.students]
		for student in studentsInProject:
			student["courseId"] = database.getCourseIdForStudentInProject(id, student["id"])
		supervisors = [{"id": s.id, "fullNameEng": s.firstNameEng+" "+s.lastNameEng} for s in project.supervisors]

		projectData = { 
			"id": project.id,
			"image": project.image,
			"year": project.year or "",
			"semester": project.semester or "",
			"title": project.title,
			"grade": "" if project.grade is None else project.grade,
			"comments": project.comments or "",
			"status": project.status,
			"requirementsDoc": project.requirementsDoc or False,
			"firstMeeting": project.firstMeeting or False,
			"halfwayPresentation": project.halfwayPresentation or False,
			"finalMeeting": project.finalMeeting or False,
			"equipmentReturned": project.equipmentReturned or False,
			"projectDoc": project.projectDoc or False,
			"gradeStatus": project.gradeStatus or False,
			"students": studentsInProject,
			"supervisors": supervisors,
			"projectDocImage": project.projectDocImage or "",
			"localVideo": project.localVideo or "",
			"youtubeVideo": project.youtubeVideo or "",
			"youtubeProcessingStatus": project.youtubeProcessingStatus or "",
			"youtubeVideoPublicStatus": project.youtubeVideoPublicStatus or "",
			"report": project.report or "",
			"presentation": project.presentation or "",
			"code": project.code or "",
			"abstract": project.abstract or "",
			"githubLink": project.githubLink or "",
			"projectDocApproved": project.projectDocApproved or False,
			"projectDocEditableByStudents": project.projectDocEditableByStudents or False,
			"posterStatus": project.posterStatus or False,
			"poster": project.poster or False,
			"posterEditableByStudents": project.posterEditableByStudents or False,
		}

		return jsonify(projectData)

	except Exception as e:
		app.logger.error('In getProjectData, error is: {}\n{}'.format(e, traceback.format_exc()))
		return jsonify({})


@app.route('/Admin/Projects/Delete', methods=['POST'])
def deleteProject():
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	try:
		deleteForm = deleteProjectForm()
		project = database.getProjectById(deleteForm.deleteProjectId.data)
		
		if project:
			# delete project image
			if project.image:
				utils.delete_project_image(project.image)
			# delete project doc files
			if project.projectDocImage:
				utils.deleteLocalFile(os.path.join(app.root_path, "static", "project_doc", "image", project.projectDocImage))
			if project.report:
				utils.deleteLocalFile(os.path.join(app.root_path, "static", "project_doc", "report", project.report))
			if project.presentation:
				utils.deleteLocalFile(os.path.join(app.root_path, "static", "project_doc", "presentation", project.presentation))
			if project.code:
				utils.deleteLocalFile(os.path.join(app.root_path, "static", "project_doc", "code", project.code))
			if project.poster:
				utils.deleteLocalFile(os.path.join(app.root_path, "static", "project_doc", "poster", project.poster))
			# delete project 
			app.logger.info('In deleteProject, deleting {}'.format(project))
			database.deleteProject(project.id)
			flash('Project was deleted successfully!', 'primary')
		else:
			app.logger.error('In deleteProject, could not delete project with id {}, because there is no project with this id'.format(deleteForm.deleteProjectId.data))
			flash("Error: can't delete, project id {} is not in the db".format(deleteForm.deleteProjectId.data), 'danger')
		return redirect(url_for('manageProjects'))
	except Exception as e:
		app.logger.error('In deleteProject, error is: {}\n{}'.format(e, traceback.format_exc()))
		return redirect(url_for('errorPage'))
	

@app.route('/Admin/Projects/json', methods=['GET', 'POST'])
def getProjectsTableData():
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	
	try:
		sort = request.args.get('sort')
		order = request.args.get('order') or "desc"
		limit = request.args.get('limit') or 10
		offset = request.args.get('offset') or 0
		filters = request.args.get('filter')
		
		totalResults, results = database.getProjectsTableData(sort, order, limit, offset, filters)
		
		rows = []	
		for result in results:
			btnPublished = ""
			if result.youtubeVideo:
			 	btnPublished = f"<label class='switch my-auto'><input type='checkbox' name='publishStatusCheckbox' data-id={result.id} class='primary' {'checked' if result.published else ''}><span class='slider round'></span></label>"
				 
			rows.append({
				"image": f"<img style='width:80px;height:70px;' src='/static/images/projects/{result.image}' alt='{result.image}'" if result.image else "",
				"year": result.year,
				"semester": result.semester,
				"title": result.title,
				"status": result.status,
				"btnPublished": btnPublished,
				"btnEdit": f"<button type='button' onclick='getProjectData({result.id})' data-project-id='{result.id}' name='btnEdit' class='btn'><i class='fa fa-edit fa-fw'></i><span name='loading' class='spinner-border spinner-border-sm' style='display:none; vertical-align:sub;margin-right: 0.25rem;' role='status'></span><span style='margin-left: 0.4rem;'>Edit</span></button>",
				"btnDelete": f"<button type='button' onclick='deleteProject({result.id})' name='btnDelete' class='btn' data-toggle='modal' data-target='#deleteProjectModal'><i class='fa fa-trash fa-fw'></i> Delete</button>"
			})

		# get filters options for the table
		filterOptions = database.getProjectsTableFilters()

		return jsonify( 
			total=totalResults,
			rows=rows,
			filterOptions=filterOptions
		)
		
	except Exception as e:
		app.logger.error('In getProjectsTableData, error is: {}\n{}'.format(e, traceback.format_exc()))
		return jsonify(total=0, rows=[])


@app.route('/Admin/Projects/<int:id>/YoutubeVideoPublicStatus', methods=['GET', 'POST'])
def getProjectYoutubePublicStatus(id):
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))

	try:
		project = database.getProjectById(id)
		if not project:
			return jsonify({})
	
		afterChangeAttempt = True if request.form["afterChangeAttempt"] == "true" else False
		if project.youtubeVideoPublicStatus == "failed" and afterChangeAttempt:
			return jsonify({
				"status": "failed"
			})
		
		if project.youtubeVideoPublicStatus != "changing" and project.youtubeVideoPublicStatus != "success":
			database.updateProject(project.id, {
				"youtubeVideoPublicStatus": "changing"
			})
			Thread(target=utils.set_youtube_video_public, kwargs={"appArg": app, "projectId": project.id}).start()
	
		status = project.youtubeVideoPublicStatus
		if status == "success":
			flash(f"Project '{project.title}' was updated successfully!", 'success')
		return jsonify({
			"status": status
		})
			
	except Exception as e:
		app.logger.error('Error is: {}\n{}'.format(e, traceback.format_exc()))
		return jsonify({})	

			

@app.route('/Admin/Projects', methods=['GET', 'POST'])
def manageProjects():
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	try:
		courses = database.getAllCourses()
		addForm = addProjectForm()
		editForm = editProjectForm()
		deleteForm = deleteProjectForm()
		editFormErrorProjectId = ''
		
		currentSemester = utils.getRegistrationSemester()
		currentYear = utils.getRegistrationYear()
		semesterChoices = [("Winter", "Winter"), ("Spring", "Spring")]
		if currentSemester == "Spring":
			semesterChoices.reverse()
		addForm.new_title.choices = [(str(s.id), s.title) for s in database.getAllProposedProjects()]
		addForm.new_year.choices = [(str(currentYear), str(currentYear)), (str(currentYear+1),str(currentYear+1)), (str(currentYear+2),str(currentYear+2))]
		addForm.new_semester.choices = semesterChoices

		allSupervisors = database.getAllSupervisors()
		supervisorsChoices = [(str(s.id),s.firstNameEng+" "+s.lastNameEng) for s in allSupervisors]
		supervisorsChoices.insert(0, ('', ''))
		addForm.new_supervisor1.choices = supervisorsChoices
		addForm.new_supervisor2.choices = supervisorsChoices
		addForm.new_supervisor3.choices = supervisorsChoices

		editForm.year.choices = [(str(currentYear), str(currentYear)), (str(currentYear+1),str(currentYear+1)), (str(currentYear+2),str(currentYear+2))]
		if request.form.get("year"):
			editForm.year.choices.insert(0, (request.form.get("year"), request.form.get("year")))
		editForm.semester.choices = semesterChoices
		editForm.supervisor1.choices = supervisorsChoices
		editForm.supervisor2.choices = supervisorsChoices
		editForm.supervisor3.choices = supervisorsChoices

		if(request.method == 'POST'):
			formName = request.form['sentFormName']
			if formName == 'editProjectForm':
				project = database.getProjectById(editForm.projectId.data)

				if not project:
					app.logger.error('In manageProjects, in editForm, tried to edit a project with id {} that does not exist in the db'.format(editForm.projectId.data))
					return jsonify({
						"status": "projectIdNotFound",
						"id": editForm.projectId.data
					})

				if editForm.validate_on_submit():
					studentsIds = request.form.getlist("students")
					studentsCoursesIds = request.form.getlist("studentsCoursesIds")
					if studentsIds and not studentsCoursesIds:
						return jsonify({
							"status": "noCourseNumbers"
						})

					projectImage = project.image
					if editForm.image.data:
						# delete old image if exists
						app.logger.info('In manageProjects, in editForm, deleting old project image')
						utils.delete_project_image(projectImage)
						projectImage = utils.save_form_image(editForm.image.data, "projects")
					
					database.updateProject(project.id, {
						"title": editForm.title.data.strip(),
						"year": editForm.year.data,
						"semester": editForm.semester.data,
						"comments": editForm.comments.data,
						"grade": editForm.grade.data.strip(),
						"image": projectImage,
						"posterEditableByStudents": editForm.posterEditableByStudents.data,
					})

					# update students in project
					studentsInProject = []
					for i in range(len(studentsIds)):
						studentsInProject.append({
							"id": studentsIds[i],
							"courseId": studentsCoursesIds[i]
						})
					database.updateProjectStudents(project.id, studentsInProject)
					
					# update supervisors in project
					supervisorsIds = set()
					if editForm.supervisor1.data:
						supervisorsIds.add(editForm.supervisor1.data)
					if editForm.supervisor2.data:
						supervisorsIds.add(editForm.supervisor2.data)
					if editForm.supervisor3.data:
						supervisorsIds.add(editForm.supervisor3.data)
					database.updateProjectSupervisors(project.id, supervisorsIds)


					# update status
					database.updateProjectStatus(project.id, {
						"requirementsDoc": editForm.requirementsDoc.data,
						"firstMeeting": editForm.firstMeeting.data,
						"halfwayPresentation": editForm.halfwayPresentation.data,
						"finalMeeting": editForm.finalMeeting.data,
						"equipmentReturned": editForm.equipmentReturned.data,
						"gradeStatus": (True if editForm.grade.data.strip() else False)
					})

					# update project doc - only relevant if students already sent a project doc,
					# assuming if the youtubeVideo exists and it was processed successfully then students already sent project doc. 
					projectDocApproved = False
					if project.youtubeVideo and project.youtubeProcessingStatus == 'processed':		 
						projectDocEditableByStudents = project.projectDocEditableByStudents
						if not project.projectDocApproved:
							projectDocApproved = editForm.projectDocApproved.data
							if projectDocApproved:
								if project.youtubeUploadStatus == "uploading" or project.youtubeUploadStatus == "deleting current":
									return jsonify({
										"status": "studentIsCurrentlyUploading"
									})

								# student edited project doc (but didn't change the video), so the current video is alredy set public, no need to set it again
								elif project.youtubeVideoPublicStatus == "success":
									database.updateProject(project.id, {
										"projectDocApproved": True
									})
									projectDocEditableByStudents = False
									database.updateProjectStatus(project.id, {
										"projectDoc": True
									})
						else:	# project doc already approved
							projectDocEditableByStudents = editForm.projectDocEditableByStudents.data


						projectDocImageFileName = project.projectDocImage
						if editForm.projectDocImage.data:
							if project.projectDocImage:
								utils.deleteLocalFile(os.path.join(app.root_path, "static", "project_doc", "image", project.projectDocImage))
							projectDocImageFileName = utils.save_form_file(editForm.projectDocImage.data, os.path.join("static", "project_doc", "image"))

						reportFileName = project.report
						if editForm.report.data:
							if project.report:
								utils.deleteLocalFile(os.path.join(app.root_path, "static", "project_doc", "report", project.report))
							reportFileName = utils.save_form_file(editForm.report.data, os.path.join("static", "project_doc", "report"))
						
						presentationFileName = project.presentation
						if editForm.presentation.data:
							if project.presentation:
								utils.deleteLocalFile(os.path.join(app.root_path, "static", "project_doc", "presentation", project.presentation))
							presentationFileName = utils.save_form_file(editForm.presentation.data, os.path.join("static", "project_doc", "presentation"))
						
						codeFileName = project.code
						if editForm.code.data:
							if project.code:
								utils.deleteLocalFile(os.path.join(app.root_path, "static", "project_doc", "code", project.code))
							codeFileName = utils.save_form_file(editForm.code.data, os.path.join("static", "project_doc", "code"))
	
						
						database.updateProject(project.id, {
							"projectDocImage": projectDocImageFileName,
							"report": reportFileName,
							"presentation": presentationFileName,
							"code": codeFileName,
							"abstract": editForm.abstract.data,
							"githubLink": editForm.githubLink.data.strip(),
							"projectDocEditableByStudents": projectDocEditableByStudents
						})

						
					elif editForm.projectDocApproved.data:
						return jsonify({
							"status": "videoIsRequired"
						})
					
					if not projectDocApproved:
						flash(f"Project '{project.title}' was updated successfully!", 'success')
					return jsonify({
						"status": "success"
					})
				else:
					app.logger.info('In manageProjects, editForm is NOT valid. editForm.errors: {}'.format(editForm.errors))
					return jsonify({
						"status": "error",
						"errors": editForm.errors
					})

			elif formName == 'addProjectForm':
				if addForm.validate_on_submit():				
					studentsIds = request.form.getlist("students")
					studentsCoursesIds = request.form.getlist("studentsCoursesIds")
					if studentsIds and not studentsCoursesIds:
						return jsonify({
							"status": "noCourseNumbers"
						})
					
					# add new project
					projectTitle = dict(addForm.new_title.choices).get(addForm.new_title.data)
					newImageName = None
					# save project image
					matchingProposedProject = database.getProposedProjectByTitle(projectTitle)
					if matchingProposedProject:
						matchingImageName = matchingProposedProject.image
						if matchingImageName:
							newImageName = utils.copy_project_image_from_proposed_project(matchingImageName)
					

					newProject = {
						"title": projectTitle,
						"year": addForm.new_year.data,
						"semester": addForm.new_semester.data,
						"comments": addForm.new_comments.data,
						"image": newImageName,
						"status": "הרשמה",
						"projectDocEditableByStudents": True
					}
					
					newProjectId = database.addProject(newProject)

					# add students to project
					studentsInProject = []
					for i in range(len(studentsIds)):
						studentsInProject.append({
							"id": studentsIds[i],
							"courseId": studentsCoursesIds[i]
						})
					database.updateProjectStudents(newProjectId, studentsInProject)

					# add supervisors to project
					supervisorsIds = set()
					if addForm.new_supervisor1.data:
						supervisorsIds.add(addForm.new_supervisor1.data)
					if addForm.new_supervisor2.data:
						supervisorsIds.add(addForm.new_supervisor2.data)
					if addForm.new_supervisor3.data:
						supervisorsIds.add(addForm.new_supervisor3.data)
					database.updateProjectSupervisors(newProjectId, supervisorsIds)
					
					flash('Project was created successfully!', 'success')
					return jsonify({
						"status": "success"
					})
				else:
					app.logger.info('In manageProjects, addForm is NOT valid. addForm.errors:{}'.format(addForm.errors))
					return jsonify({
						"status": "error",
						"errors": addForm.errors
					})

		return render_template('/admin/projects.html', title="Manage Projects", courses=courses, addForm=addForm, editForm=editForm, deleteForm=deleteForm, editFormErrorProjectId=editFormErrorProjectId)
	
	except RequestEntityTooLarge as e:
		app.logger.error('In manageProjects, Error is: {}\n{}'.format(e, traceback.format_exc()))
		return jsonify({
			"status": "fileTooLarge",
		})
	except Exception as e:
		app.logger.error('In manageProjects, Error is: {}\n{}'.format(e, traceback.format_exc()))
		return redirect(url_for('errorPage'))



@app.route('/Admin/ProposedProjects/UpdatePublishState', methods=['GET', 'POST'])
def updateProposedProjectPublishState():
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	
	try:
		if request.method == "POST":
			id = request.form.get("id")
			state = request.form.get("state")
			result = database.updateProposedProjectPublishState(id, True if state=="true" else False)
			if result == None:
				return jsonify(result="failed", reason="proposed project id was not found")	
			return jsonify(result="ok")	

	except Exception as e:
		app.logger.error('In updateProposedProjectPublishState, error is: {}\n{}'.format(e, traceback.format_exc()))
		return jsonify(result="failed")


@app.route('/Admin/ProposedProjects/json', methods=['GET', 'POST'])
def getProposedProjectsTableData():
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))

	try:
		sort = request.args.get('sort')
		order = request.args.get('order') or "desc"
		limit = request.args.get('limit') or 10
		offset = request.args.get('offset') or 0
		filters = request.args.get('filter')
		
		totalResults, results = database.getProposedProjectsTableData(sort, order, limit, offset, filters)
		
		rows = []
		for result in results:
			supervisors = database.getProposedProjectById(result.id).supervisorsFullNameEng
			wordsInDescription = result.description.split()
			maxWordsInDescription = 10
			description = " ".join(wordsInDescription[:maxWordsInDescription])
			description += ("..." if len(wordsInDescription) > maxWordsInDescription else "" )
			rows.append({
				"image": f"<img style='width:80px;height:70px;' src='/static/images/proposed_projects/{result.image}' alt='{result.image}'" if result.image else "",
				"title": result.title,
				"description": description,
				"supervisorsNames": ",<br>".join(supervisors),
				"btnPublished": f"<label class='switch my-auto'><input type='checkbox' name='publishStatusCheckbox' data-id={result.id} class='primary' {'checked' if result.published else ''}><span class='slider round'></span></label>",
				"btnEdit": f"<button type='button' onclick='getProposedProjectData({result.id})' data-proposed-project-id='{result.id}' name='btnEdit' class='btn'><i class='fa fa-edit fa-fw'></i><span name='loading' class='spinner-border spinner-border-sm' style='display:none; vertical-align:sub;margin-right: 0.25rem;' role='status'></span><span style='margin-left: 0.4rem;'>Edit</span></button>",
				"btnDelete": f"<button type='button' onclick='deleteProposedProject({result.id})' name='btnDelete' class='btn' data-toggle='modal' data-target='#deleteProposedProjectModal'><i class='fa fa-trash fa-fw'></i> Delete</button>"
			})

		return jsonify( 
			total=totalResults,
			rows=rows,
			filterOptions={}
		)
		
	except Exception as e:
		app.logger.error('In getProposedProjectsTableData, error is: {}\n{}'.format(e, traceback.format_exc()))
		return jsonify(total=0, rows=[])	


@app.route('/Admin/ProposedProjects/Delete', methods=['POST'])
def deleteProposedProjects():
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	try:
		deleteForm = deleteProposedProjectForm()
		proposedProject = database.getProposedProjectById(deleteForm.deleteProposedProjectId.data)
		if proposedProject:
			picFile = proposedProject.image
			# delete image if exists
			if picFile:
				utils.delete_proposed_project_image(picFile)
			
			database.deleteProposedProject(proposedProject.id)
			flash('Proposed Project was deleted successfully!', 'primary')
		else:
			app.logger.info('In deleteProposedProjects, could not delete proposed project with id {}, because there is no proposed project with this id'.format(deleteForm.deleteProposedProjectId.data))
			flash("Error: can't delete, proposed project id is not in the db", 'danger')
		return redirect(url_for('manageProposedProjects'))
	except Exception as e:
		app.logger.error('In deleteProposedProjects, Error is: {}\n{}'.format(e, traceback.format_exc()))
		return redirect(url_for('errorPage'))
	

@app.route('/Admin/ProposedProjects/<int:id>/json', methods=['GET', 'POST'])
def getProposedProjectData(id):
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	
	try:
		proposedProject = database.getProposedProjectById(id)
		if not proposedProject:
			return jsonify({})
		supervisors = [{"id": s.id, "fullNameEng": s.firstNameEng+" "+s.lastNameEng} for s in proposedProject.supervisors]

		proposedProjectData = { 
			"id": proposedProject.id,
			"image": proposedProject.image,
			"title": proposedProject.title,
			"description": proposedProject.description,
			"oneAcademicPoint": proposedProject.oneAcademicPoint or False,
			"twoAcademicPoints": proposedProject.twoAcademicPoints or False,
			"threeAcademicPoints": proposedProject.threeAcademicPoints or False,
			"fourAcademicPoints": proposedProject.fourAcademicPoints or False,
			"fiveAcademicPoints": proposedProject.fiveAcademicPoints or False,
			"supervisors": supervisors
		}

		return jsonify(proposedProjectData)

	except Exception as e:
		app.logger.error('In getProposedProjectData, error is: {}\n{}'.format(e, traceback.format_exc()))
		return jsonify({})


@app.route('/Admin/ProposedProjects', methods=['GET', 'POST'])
def manageProposedProjects():
	if not current_user.is_authenticated or current_user.userType != "admin":
		return redirect(url_for('login'))
	try:
		addForm = addProposedProjectForm()
		editForm = editProposedProjectForm()
		deleteForm = deleteProposedProjectForm()

		# get supervisors
		allSupervisors = database.getAllSupervisors()
		activeSupervisors = database.getActiveSupervisors()
		allSupervisorsChoices = [(str(s.id),s.firstNameEng+" "+s.lastNameEng) for s in allSupervisors]
		activeSupervisorsChoices = [(str(s.id),s.firstNameEng+" "+s.lastNameEng) for s in activeSupervisors]
		allSupervisorsChoices.insert(0, ('', ''))
		activeSupervisorsChoices.insert(0, ('', ''))

		editForm.supervisor1.choices = allSupervisorsChoices
		editForm.supervisor2.choices = allSupervisorsChoices
		editForm.supervisor3.choices = allSupervisorsChoices 

		addForm.newSupervisor1.choices = activeSupervisorsChoices
		addForm.newSupervisor2.choices = activeSupervisorsChoices
		addForm.newSupervisor3.choices = activeSupervisorsChoices 
		
		if(request.method == 'POST'):
			formName = request.form['pageForm']
			if formName == 'addProposedProjectForm':
				if addForm.validate_on_submit():
					picFile = None
					if addForm.newImage.data:
						app.logger.info('In manageProposedProjects, saving image of new proposed project')
						picFile = utils.save_form_image(addForm.newImage.data, "proposed_projects")
					
					# create new proposed project
					newProposedProjectId = database.addProposedProject({
						"title": addForm.newTitle.data,
						"description": addForm.newDescription.data,
						"image": picFile,
						"oneAcademicPoint": addForm.new_oneAcademicPoint.data,
						"twoAcademicPoints": addForm.new_twoAcademicPoints.data,
						"threeAcademicPoints": addForm.new_threeAcademicPoints.data,
						"fourAcademicPoints": addForm.new_fourAcademicPoints.data,
						"fiveAcademicPoints": addForm.new_fiveAcademicPoints.data
					})
					
					# save the supervisors for this proposed project
					supervisorsIds = set()
					if addForm.newSupervisor1.data:
						supervisorsIds.add(int(addForm.newSupervisor1.data))
					if addForm.newSupervisor2.data:
						supervisorsIds.add(int(addForm.newSupervisor2.data))
					if addForm.newSupervisor3.data:
						supervisorsIds.add(int(addForm.newSupervisor3.data))
					database.updateProposedProjectSupervisors(newProposedProjectId, supervisorsIds)
					
					flash('Proposed project created successfully!', 'success')
					return jsonify({
						"status": "success"
					})
				else:
					app.logger.info('In manageProposedProjects, addForm is NOT valid. addForm.errors:{}'.format(addForm.errors))
					return jsonify({
						"status": "error",
						"errors": addForm.errors
					})
			elif formName == 'editProposedProjectForm':
				proposedProject = database.getProposedProjectById(editForm.proposedProjectId.data)

				if not proposedProject:
					app.logger.error('In manageProposedProjects, in editForm, tried to edit a proposed project with id {} that does not exist in the db'.format(editForm.proposedProjectId.data))
					return jsonify({
						"status": "proposedProjectIdNotFound",
						"id": editForm.proposedProjectId.data
					})
					

				if editForm.validate_on_submit():	
					picFile = proposedProject.image
					if editForm.image.data:
						# delete old image if exists
						if picFile:
							utils.delete_proposed_project_image(picFile)
						picFile = utils.save_form_image(editForm.image.data, "proposed_projects")

					database.updateProposedProject(proposedProject.id, {
						"title": editForm.title.data,
						"description": editForm.description.data,
						"image": picFile,
						"oneAcademicPoint": editForm.oneAcademicPoint.data,
						"twoAcademicPoints": editForm.twoAcademicPoints.data,
						"threeAcademicPoints": editForm.threeAcademicPoints.data,
						"fourAcademicPoints": editForm.fourAcademicPoints.data,
						"fiveAcademicPoints": editForm.fiveAcademicPoints.data
					})

					newSupervisorsIds = set()
					if editForm.supervisor1.data:
						newSupervisorsIds.add(int(editForm.supervisor1.data))
					if editForm.supervisor2.data:
						newSupervisorsIds.add(int(editForm.supervisor2.data))
					if editForm.supervisor3.data:
						newSupervisorsIds.add(int(editForm.supervisor3.data))
					database.updateProposedProjectSupervisors(proposedProject.id, newSupervisorsIds)

					flash(f"'{proposedProject.title}' was updated successfully!", 'success')
					return jsonify({
						"status": "success"
					})
				else:
					app.logger.info('In manageProposedProjects, editForm is NOT valid. editForm.errors:{}'.format(editForm.errors))
					return jsonify({
						"status": "error",
						"errors": editForm.errors
					})

		return render_template('/admin/proposedProjects.html', title="Manage Proposed Projects", addForm=addForm, editForm=editForm, deleteForm=deleteForm)
	except Exception as e:
		app.logger.error('In manageProposedProjects, Error is: {}\n{}'.format(e, traceback.format_exc()))
		return redirect(url_for('errorPage'))


@app.route('/ProjectStatus/<int:id>/SendPoster', methods=['GET', 'POST'])
def sendPoster(id):
	if not current_user.is_authenticated:
		return redirect(url_for('login'))
	if current_user.userType == "admin":
		return redirect(url_for('manageProjects'))
	# user is a student
	try:
		student = database.getStudentByStudentId(current_user.userId)
		isStudentEnrolledInProject = database.isStudentEnrolledInProject(id, student.id)
		if not isStudentEnrolledInProject:
			return redirect(url_for('projectStatus', id=id))

		project = database.getProjectById(id)
		allowedToSend = True if project.gradeStatus and project.posterEditableByStudents else False
		
		posterForm = sendPosterForm()

		if allowedToSend and request.method == "POST":
			if posterForm.validate_on_submit():
				if project.poster:
					utils.deleteLocalFile(os.path.join(app.root_path, "static", "project_doc", "poster", project.poster))
				posterFileName = utils.save_form_file(posterForm.poster.data, os.path.join("static", "project_doc", "poster"))
				database.updateProject(id, {
					"poster": posterFileName
				})
				database.updateProjectStatus(project.id, {
					"posterStatus": True,
					"posterEditableByStudents": False
				})
				
				flash("Poster was sent successfully!")
				return jsonify({
					"status": "success"
				})
				
			else:
				app.logger.info('In sendPoster, form is NOT valid. form.errors:{}'.format(posterForm.errors))
				return jsonify({
					"status": "error",
					"errors": posterForm.errors
				})
		elif not allowedToSend and request.method == "POST":
			return jsonify({
				"status": "notAllowed",
			})
		elif request.method == "GET":
			if not allowedToSend:
				flash("You are currently not allowed to send poster.", 'danger')

		return render_template('sendPoster.html', title="Send Project Doc", student=student, posterForm=posterForm, isStudentEnrolledInProject=isStudentEnrolledInProject, allowedToSend=allowedToSend, project=project)

	except RequestEntityTooLarge as e:
		app.logger.error(f"In sendPoster, Error is: {e}")
		return jsonify({
			"status": "fileTooLarge",
		})
	except Exception as e:
		app.logger.error('In sendPoster, Error is: {}\n{}'.format(e, traceback.format_exc()))
		return redirect(url_for('errorPage'))

		

@app.route('/ProjectStatus/<int:id>/YoutubeStatus', methods=['GET', 'POST'])
def getProjectYoutubeUploadStatus(id):
	if not current_user.is_authenticated:
		return redirect(url_for('login'))

	def getStatusStream(projectId):
		project = database.getProjectById(projectId)
		while True:
			db.session.refresh(project)
			result = json.dumps({
				"uploadStatus": project.youtubeUploadStatus,
				"processingStatus": project.youtubeProcessingStatus,
				"processingFailureReason": project.youtubeProcessingFailureReason,
				"processingEstimatedTimeLeft": project.youtubeProcessingEstimatedTimeLeft
			})
			yield "data: {}\n\n".format(result)
			time.sleep(3.0)

	try:
		student = database.getStudentByStudentId(current_user.userId)
		isStudentEnrolledInProject = database.isStudentEnrolledInProject(id, student.id)
		if not isStudentEnrolledInProject:
			return redirect(url_for('projectStatus', id=id))

		project = database.getProjectById(id)
		if not project.projectDocImage:
			return redirect(url_for('projectStatus', id=id))

		
		return Response(getStatusStream(id), mimetype="text/event-stream") 
			
	except Exception as e:
		app.logger.error('Error is: {}\n{}'.format(e, traceback.format_exc()))
		return jsonify({})	


@app.route('/ProjectStatus/<int:id>/SendProjectDoc', methods=['GET', 'POST'])
def sendProjectDoc(id):
	if not current_user.is_authenticated:
		return redirect(url_for('login'))
	if current_user.userType == "admin":
		return redirect(url_for('manageProjects'))
	# user is a student
	try:
		student = database.getStudentByStudentId(current_user.userId)
		isStudentEnrolledInProject = database.isStudentEnrolledInProject(id, student.id)
		if not isStudentEnrolledInProject:
			return redirect(url_for('projectStatus', id=id))

		project = database.getProjectById(id)
		allowedToSend = False
		if project.finalMeeting and not project.projectDocImage:
			allowedToSend = True			

		projectDocForm = sendProjectDocForm()

		if allowedToSend and request.method == "POST":
			if projectDocForm.validate_on_submit():
				videoFileName = utils.save_form_file(projectDocForm.video.data, os.path.join("static", "project_doc", "video"))
				if os.path.getsize(os.path.join(app.root_path, "static", "project_doc", "video", videoFileName)) == 0:
					utils.deleteLocalFile(os.path.join(app.root_path, "static", "project_doc", "video", videoFileName))
					return jsonify({
						"status": "error",
						"errors": {
							"video": "Video file could not be empty."
						}
					})
				imageFileName = utils.save_form_file(projectDocForm.image.data, os.path.join("static", "project_doc", "image"))
				reportFileName = utils.save_form_file(projectDocForm.report.data, os.path.join("static", "project_doc", "report"))
				presentationFileName = utils.save_form_file(projectDocForm.presentation.data, os.path.join("static", "project_doc", "presentation"))
				codeFileName = None
				if projectDocForm.code.data:
					codeFileName = utils.save_form_file(projectDocForm.code.data, os.path.join("static", "project_doc", "code"))
				
				database.updateProject(id, {
					"projectDocImage": imageFileName,
					"localVideo": videoFileName,
					"report": reportFileName,
					"presentation": presentationFileName,
					"abstract": projectDocForm.abstract.data,
					"code": codeFileName,
					"githubLink": projectDocForm.githubLink.data.strip(),
					"projectDocApproved": False,
					"projectDocEditableByStudents": True,
					"youtubeUploadStatus": "uploading",
					"youtubeProcessingStatus": ""
				})

				# upload the video async
				Thread(target=utils.upload_video_to_youtube, kwargs={"appArg": app,	"projectId": project.id}).start()				
				return jsonify({
					"status": "success"
				})
				
			else:
				app.logger.info('In sendProjectDoc, form is NOT valid. form.errors:{}'.format(projectDocForm.errors))
				return jsonify({
					"status": "error",
					"errors": projectDocForm.errors
				})
		elif not allowedToSend and request.method == "POST":
			return jsonify({
				"status": "notAllowed",
			})
		elif request.method == "GET":
			if not allowedToSend:
				flash("You are currently not allowed to send project doc.", 'danger')

		return render_template('sendProjectDoc.html', title="Send Project Doc", student=student, projectDocForm=projectDocForm, isStudentEnrolledInProject=isStudentEnrolledInProject, allowedToSend=allowedToSend, project=project)

	except RequestEntityTooLarge as e:
		app.logger.error('In sendProjectDoc, Error is: {}\n{}'.format(e, traceback.format_exc()))
		return jsonify({
			"status": "fileTooLarge",
		})
	except Exception as e:
		app.logger.error('In sendProjectDoc, Error is: {}\n{}'.format(e, traceback.format_exc()))
		return redirect(url_for('errorPage'))


@app.route('/ProjectStatus/<int:id>/EditProjectDoc', methods=['GET', 'POST'])
def editProjectDoc(id):
	if not current_user.is_authenticated:
		return redirect(url_for('login'))
	if current_user.userType == "admin":
		return redirect(url_for('manageProjects'))
	# user is a student
	try:
		student = database.getStudentByStudentId(current_user.userId)
		isStudentEnrolledInProject = database.isStudentEnrolledInProject(id, student.id)
		if not isStudentEnrolledInProject:
			return redirect(url_for('projectStatus', id=id))

		project = database.getProjectById(id)
		if project.youtubeUploadStatus == "uploading" or (project.youtubeProcessingStatus == "" and project.youtubeUploadStatus == "completed") or project.youtubeProcessingStatus == "checking" or project.youtubeProcessingStatus == "processing":
			return redirect(url_for('projectStatus', id=id))

		allowedToEdit = False
		if project.projectDocImage and project.projectDocEditableByStudents:
			allowedToEdit = True			

		projectDocForm = editProjectDocForm()

		if allowedToEdit and request.method == "POST":
			if projectDocForm.validate_on_submit():
				if (not project.youtubeVideo) and (not projectDocForm.video.data):
					return jsonify({
						"status": "error",
						"errors": {
							"video": "video is required."
						}
					})

				somethingChanged = False
				projectDocImageFileName = project.projectDocImage
				if projectDocForm.image.data:
					somethingChanged = True
					if project.projectDocImage:
						utils.deleteLocalFile(os.path.join(app.root_path, "static", "project_doc", "image", project.projectDocImage))
					projectDocImageFileName = utils.save_form_file(projectDocForm.image.data, os.path.join("static", "project_doc", "image"))

				reportFileName = project.report
				if projectDocForm.report.data:
					somethingChanged = True
					if project.report:
						utils.deleteLocalFile(os.path.join(app.root_path, "static", "project_doc", "report", project.report))
					reportFileName = utils.save_form_file(projectDocForm.report.data, os.path.join("static", "project_doc", "report"))
				
				presentationFileName = project.presentation
				if projectDocForm.presentation.data:
					somethingChanged = True
					if project.presentation:
						utils.deleteLocalFile(os.path.join(app.root_path, "static", "project_doc", "presentation", project.presentation))
					presentationFileName = utils.save_form_file(projectDocForm.presentation.data, os.path.join("static", "project_doc", "presentation"))
				
				codeFileName = project.code
				if projectDocForm.code.data:
					somethingChanged = True
					if project.code:
						utils.deleteLocalFile(os.path.join(app.root_path, "static", "project_doc", "code", project.code))
					codeFileName = utils.save_form_file(projectDocForm.code.data, os.path.join("static", "project_doc", "code"))

				if projectDocForm.githubLink.data != project.githubLink or projectDocForm.abstract.data != project.abstract:
					somethingChanged = True
				if somethingChanged:
					database.updateProject(project.id, {
						"projectDocImage": projectDocImageFileName,
						"report": reportFileName,
						"presentation": presentationFileName,
						"code": codeFileName,
						"abstract": projectDocForm.abstract.data,
						"githubLink": projectDocForm.githubLink.data.strip(),
						"projectDocApproved": False,
						"projectDoc": False,
						"status": "דף פרויקט - טיוטה"
					})

				if projectDocForm.video.data:
					videoFileName = utils.save_form_file(projectDocForm.video.data, os.path.join("static", "project_doc", "video"))
					if os.path.getsize(os.path.join(app.root_path, "static", "project_doc", "video", videoFileName)) == 0:
						utils.deleteLocalFile(os.path.join(app.root_path, "static", "project_doc", "video", videoFileName))
						return jsonify({
							"status": "error",
							"errors": {
								"video": "Video file could not be empty."
							}
						})
					else:
						if project.localVideo:
							utils.deleteLocalFile(os.path.join(app.root_path, "static", "project_doc", "video", project.localVideo))
						database.updateProject(project.id, {
							"localVideo": videoFileName,
							"projectDocApproved": False,
							"projectDoc": False,
							"youtubeUploadStatus": "uploading",
							"youtubeProcessingStatus": "",
							"youtubeProcessingFailureReason": "",
							"youtubeProcessingEstimatedTimeLeft": "",
							"youtubeVideoPublicStatus": ""
						})
						# upload the video async
						if project.youtubeVideo:
							Thread(target=utils.overwrite_youtube_video, kwargs={"appArg": app,	"projectId": project.id}).start()				
						else:
							Thread(target=utils.upload_video_to_youtube, kwargs={"appArg": app,	"projectId": project.id}).start()
					


				if not projectDocForm.video.data:
					flash('Project doc was updated successfully!', 'success')

				return jsonify({
					"status": "success"
				})
				
			else:
				app.logger.info('In editProjectDoc, form is NOT valid. form.errors:{}'.format(projectDocForm.errors))
				return jsonify({
					"status": "error",
					"errors": projectDocForm.errors
				})
		elif not allowedToEdit and request.method == "POST":
			return jsonify({
				"status": "notAllowed"
			})
		elif request.method == "GET":
			if not allowedToEdit:
				flash("You are currently not allowed to edit project doc.", 'danger')
			else:
				projectDocForm.githubLink.data = project.githubLink
				projectDocForm.abstract.data = project.abstract
		return render_template('editProjectDoc.html', title="Edit Project Doc", student=student, projectDocForm=projectDocForm, isStudentEnrolledInProject=isStudentEnrolledInProject, allowedToEdit=allowedToEdit, project=project)
	
	except RequestEntityTooLarge as e:
		app.logger.error('In editProjectDoc, Error is: {}\n{}'.format(e, traceback.format_exc()))
		return jsonify({
			"status": "fileTooLarge",
		})
	except Exception as e:
		app.logger.error('In editProjectDoc, Error is: {}\n{}'.format(e, traceback.format_exc()))
		return redirect(url_for('errorPage'))




@app.route('/ProjectStatus/<int:id>', methods=['GET'])
def projectStatus(id):
	if not current_user.is_authenticated:
		return redirect(url_for('login'))
	if current_user.userType == "admin":
		return redirect(url_for('manageProjects'))
	# user is a student
	try:
		student = database.getStudentByStudentId(current_user.userId)
		project = None
		isStudentEnrolledInProject = database.isStudentEnrolledInProject(id, student.id)
		if not isStudentEnrolledInProject:
			flash("You are not enrolled in this project.", 'danger')
		else:
			project = database.getProjectById(id)

		return render_template('projectStatus.html', title="Project Status", student=student, project=project, isStudentEnrolledInProject=isStudentEnrolledInProject)
	except Exception as e:
		app.logger.error('In projectStatus, Error is: {}\n{}'.format(e, traceback.format_exc()))
		return redirect(url_for('errorPage'))


@app.route('/', methods=['GET'])
def index():
	try:
		proposedProjects = database.getLimitedProposedProjects(5)
		student = None
		admin = None
		if current_user.is_authenticated:
			if current_user.userType == "student":
				student = database.getStudentByStudentId(current_user.userId)
			elif current_user.userType == "admin":
				admin = database.getAdminByAdminId(current_user.userId)
		for p in proposedProjects:
			wordsInDescription = p.description.split()
			maxWordsInDescription = 40
			description = " ".join(wordsInDescription[:maxWordsInDescription])
			description += ("..." if len(wordsInDescription) > maxWordsInDescription else "" )
			p.description = description

		return render_template('index.html', proposedProjects=proposedProjects, student=student, admin=admin)
	except Exception as e:
		app.logger.error('In index page, Error is: {}\n{}'.format(e, traceback.format_exc()))
		return redirect(url_for('errorPage'))


@app.route('/home', methods=['GET'])
def home():
	if not current_user.is_authenticated:
		return redirect(url_for('login'))
	if current_user.userType == "admin":
		return redirect(url_for('labOverview'))
	# user is a student
	try:
		student =  database.getStudentByStudentId(current_user.userId)
		projects = student.projects
		return render_template('studentHome.html', title="Home", student=student, projects=projects)
	except Exception as e:
		app.logger.error('In home, Error is: {}\n{}'.format(e, traceback.format_exc()))
		return redirect(url_for('errorPage'))


@app.route('/Showcase/Project/<int:projectId>', methods=['POST'])
def getPublishedProjectDetails(projectId):
	try:
		project = database.getPublishedProjectDetails(projectId)
		projectDetails = {
			"title": project.title,
			"abstract": project.abstract,
			"supervisors": project.supervisorsFullNameEng,
			"students": project.studentsForPublishedProject,
			"youtubeVideoId": project.youtubeVideo,
			"image": f"static/project_doc/image/{project.projectDocImage}",
			"report": f"static/project_doc/report/{project.report}",
			"presentation": f"static/project_doc/presentation/{project.presentation}",
			"code": f"static/project_doc/code/{project.code}" if project.code else "",
			"githubLink": project.githubLink or "",
		}
		return jsonify(projectDetails)
	except Exception as e:
		app.logger.error('In getPublishedProjectDetails, Error is: {}\n{}'.format(e, traceback.format_exc()))
		return jsonify({})



@app.route('/Showcase/<int:year>', methods=['POST'])
def getPublishedProjectsByYear(year):
	try:
		projects = database.getPublishedProjectsByYear(year)
		results = []
		for project in projects:
			maxCharsInAbstract = 250
			abstract = project.abstract[:maxCharsInAbstract]
			abstract += ("..." if len(project.abstract) > maxCharsInAbstract else "" )

			results.append({
				"id": project.id,
				"title": project.title,
				"image": f"static/project_doc/image/{project.projectDocImage}",
				"abstract": abstract
			})
			
		return jsonify(results)
	except Exception as e:
		app.logger.error('In getPublishedProjectsByYear, Error is: {}\n{}'.format(e, traceback.format_exc()))
		return jsonify({})



@app.route('/Showcase', methods=['GET'])
def showcase():
	try:
		student = None
		admin = None
		if current_user.is_authenticated:
			if current_user.userType == "student":
				student = database.getStudentByStudentId(current_user.userId)
			elif current_user.userType == "admin":
				admin = database.getAdminByAdminId(current_user.userId)

		projectsYears = database.getPublishedProjectsYears()
		return render_template('showcase.html', title="Projects Showcase", projectsYears=projectsYears, student=student, admin=admin)
	except Exception as e:
		app.logger.error('In showcase, Error is: {}\n{}'.format(e, traceback.format_exc()))
		return redirect(url_for('errorPage'))


@app.route('/ProposedProjects', methods=['GET'])
def proposedProjects():
	try:
		student = None
		admin = None
		if current_user.is_authenticated:
			if current_user.userType == "student":
				student = database.getStudentByStudentId(current_user.userId)
			elif current_user.userType == "admin":
				admin = database.getAdminByAdminId(current_user.userId)
		proposedProjects = database.getAllPublishedProposedProjects()
		return render_template('proposedProjects.html', title="Proposed Projects", proposedProjects=proposedProjects, student=student, admin=admin)
	except Exception as e:
		app.logger.error('In proposedProjects, Error is: {}\n{}'.format(e, traceback.format_exc()))
		return redirect(url_for('errorPage'))


def sendResetEmail(student):
	token = student.get_reset_token() 
	recipients=[student.email]
	msg = Message('Password Reset Request', sender='noreply@technion.ac.il', recipients=recipients)
	resetLink = url_for('resetToken', token=token, _external=True)
	msg.html = f'''To reset your password, visit the following link:<br>
	<a href="{resetLink}">{resetLink}</a>'''
	try:
		mail.send(msg)
		return True
	except Exception as e:
		flash('Error: could not send mail', 'danger')
		app.logger.error('In sendResetEmail, could not send mail to {}. Error is: {}\n{}'.format(recipients, e, traceback.format_exc()))
		return False

 
@app.route('/ResetPassword', methods=['GET', 'POST'])
def resetRequest():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	try:
		form = requestResetForm()
		if request.method == "POST":
			if form.validate_on_submit():
				student = database.getStudentByEmail(form.email.data)
				app.logger.info('In resetRequest, sending password reset email to {}'.format(student))
				emailWasSent = sendResetEmail(student)
				if emailWasSent:
					app.logger.info('In resetRequest, email was sent successfully to {}'.format(student))
					flash('An email has been sent with instructions to reset your password.', 'info')
					return redirect(url_for('login'))
			else:
				app.logger.info('In resetRequest, form is NOT valid. form.errors:{}'.format(form.errors))
				flash('There was an error, see details below.', 'danger')
		return render_template('resetRequest.html', title="Reset Password", form=form)
	except Exception as e:
		app.logger.error('In resetRequest, Error is: {}\n{}'.format(e, traceback.format_exc()))
		return redirect(url_for('errorPage'))


@app.route('/ResetPassword/<token>', methods=['GET', 'POST'])
def resetToken(token):
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	try:
		student = Student.verify_reset_token(token)
		if student is None:
			app.logger.info('In resetToken, token was invalid for {}'.format(student))
			flash('Invalid or expired token!', 'danger')
			return redirect(url_for('resetRequest'))
		form = resetPasswordForm()
		
		if request.method == "POST":
			if form.validate_on_submit():
				hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
				app.logger.info('In resetToken, commiting new password to DB for {}'.format(student))
				database.updateStudent(student.id, {
					"password": hashed_password
				})
				flash('Your password has been updated successfully!', 'success')
				return redirect(url_for('login'))
			else:
				app.logger.info('In resetToken, form is NOT valid. form.errors:{}'.format(form.errors))
				flash('There was an error, see details below.', 'danger')
		return render_template('resetToken.html', title="Reset Password", form=form)
	except Exception as e:
		app.logger.error('In resetToken, Error is: {}\n{}'.format(e, traceback.format_exc()))
		return redirect(url_for('errorPage'))

@app.route('/CreateAdminAccount', methods=['GET', 'POST'])
def createAdminAccount():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	try:
		totalAdmins = database.getAdminsCount()
		# allow **only one** admin to register
		if totalAdmins > 0:
			return redirect(url_for('home'))

		form = createAdminForm()
		if request.method == "POST":
			if form.validate_on_submit():
				hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
				# create admin
				database.addAdmin({
					"adminId": form.id.data,
					"password": hashed_password
				})				
				flash('Admin account was created successfully!', 'success')
				return redirect(url_for('login'))
			else:
				app.logger.info('In Create Admin Account, form is NOT valid. form.errors:{}'.format(form.errors))
				flash('There was an error, see details below.', 'danger')
		return render_template('/admin/createAdminAccount.html', title="Create Admin Account", form=form)
	except Exception as e:
		app.logger.error('In createAdminAccount, Error is: {}\n{}'.format(e, traceback.format_exc()))
		return redirect(url_for('errorPage'))

@app.route('/Error', methods=['GET'])
def errorPage():
	return render_template('error.html', title="Error")

@app.route('/login', methods=['GET', 'POST'])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	try:
		form = LoginForm()
		if request.method == "POST":
			if form.validate_on_submit():
				userToLogIn = database.getUserByUserId(form.id.data.strip())
				if userToLogIn:
					if userToLogIn.userType == "admin":
						adminUser = database.getAdminByAdminId(userToLogIn.userId)
						if bcrypt.check_password_hash(adminUser.password, form.password.data):
							login_user(userToLogIn)
							return redirect(url_for('home'))
						else:
							app.logger.info('In Login, admin {} login was unsuccessful, password incorrect'.format(adminUser))
							flash('Login unsuccessful: password is incorrect.', 'danger')
					elif userToLogIn.userType == "student":
						studentUser = database.getStudentByStudentId(userToLogIn.userId)
						if bcrypt.check_password_hash(studentUser.password, form.password.data):
							login_user(userToLogIn)
							return redirect(url_for('home'))
						else:
							flash('Login unsuccessful: password is incorrect.', 'danger')
					else:
						flash('userType is not recognized for this user.', 'danger')
				else:
					flash('Login unsuccessful: user not registered.', 'danger')
			else:
				app.logger.info('In Login, form is NOT valid. form.errors:{}'.format(form.errors))
				if 'csrf_token' in form.errors:
					flash('Error: csrf token expired, please re-enter your credentials.', 'danger')
				else:	
					flash('There was an error, see details below.', 'danger')
		return render_template('login.html', title="Login", form=form)
	except Exception as e:
		app.logger.error('In login, Error is: {}\n{}'.format(e, traceback.format_exc()))
		return redirect(url_for('errorPage'))


@app.route('/register', methods=['GET', 'POST'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	try:
		form = RegistrationForm()
		projectTitleChoices = [('', 'NOT CHOSEN')]
		form.projectTitle.choices = projectTitleChoices
		registrationSemester = utils.getRegistrationSemester()
		registrationYear = utils.getRegistrationYear()
		form.semester.choices = [(registrationSemester, registrationSemester)]
		form.year.choices = [(str(registrationYear), str(registrationYear))]
		if (request.method == 'POST'):
			form.email.data = form.email.data.strip()
			if form.validate_on_submit():				
				picFile = None
				if form.profilePic.data:
					picFile = utils.save_form_image(form.profilePic.data, "profile")
				hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
				database.registerStudent({
					"studentId": form.studentId.data,
					"password": hashed_password,
					"firstNameHeb": form.firstNameHeb.data,
					"lastNameHeb": form.lastNameHeb.data,
					"firstNameEng": form.firstNameEng.data.capitalize(),
					"lastNameEng": form.lastNameEng.data.capitalize(),
					"academicStatus": form.academicStatus.data,
					"faculty": form.faculty.data,
					"cellPhone": form.cellPhone.data,
					"email": form.email.data,
					"semester": registrationSemester,
					"year": registrationYear,
					"profilePic": picFile
				})

				flash('Account created successfully!', 'success')
				return jsonify({
					"status": "success"
				})
			else:
				app.logger.info('In Register, form is NOT valid. form.errors:{}'.format(form.errors))
				return jsonify({
					"status": "error",
					"errors": form.errors
				})
		return render_template('register.html', title="Registration", form=form) 
	
	except RequestEntityTooLarge as e:
		app.logger.error('In register, Error is: {}\n{}'.format(e, traceback.format_exc()))
		return jsonify({
			"status": "fileTooLarge",
		})
	except Exception as e:
		app.logger.error('In register, Error is: {}\n{}'.format(e, traceback.format_exc()))
		return redirect(url_for('errorPage'))


@app.route('/EditAccount', methods=['GET', 'POST'])
def editAccount():
	if not current_user.is_authenticated or current_user.userType == "admin":
		return redirect(url_for('login'))
	try:
		student = database.getStudentByStudentId(current_user.userId)
		form = EditAccountForm()

		if request.method == 'POST':
			form.email.data = form.email.data.strip()
			if form.validate_on_submit():
				if student.studentId != form.studentId.data:
					userWithSameId = database.getUserByUserId(form.studentId.data)
					if userWithSameId:
						return jsonify({
							"status": "error",
							"errors": [
								{"studentId", "There is already a student with the same ID!"}
							]
						})
				if student.email != form.email.data:
					studentWithSameEmail = database.getStudentByEmail(form.email.data)
					if studentWithSameEmail:
						return jsonify({
							"status": "error",
							"errors": [
								{"email", "This email is already used by another student!"}
							]
						})

				profilePic = student.profilePic
				if form.profilePic.data:				
					# delete old profile image
					utils.delete_profile_image(profilePic)
					# save new profile image	
					profilePic = utils.save_form_image(form.profilePic.data, "profile")
				hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')

				database.updateStudent(student.id, {
					"studentId": form.studentId.data,
					"password": hashed_password,
					"firstNameHeb": form.firstNameHeb.data,
					"lastNameHeb": form.lastNameHeb.data,
					"firstNameEng": form.firstNameEng.data.capitalize(),
					"lastNameEng": form.lastNameEng.data.capitalize(),
					"academicStatus": form.academicStatus.data,
					"faculty": form.faculty.data,
					"cellPhone": form.cellPhone.data,
					"email": form.email.data,
					"profilePic": profilePic
				})
				# update userId in current session
				current_user.userId = form.studentId.data
				app.logger.info('In Edit Account, commiting student changes. updated student will be: {}'.format(student))
				flash('Your account was updated successfully!', 'success')
				return jsonify({
					"status": "success"
				})
			else:
				app.logger.info('In Edit Account, form is NOT valid. form.errors:{}'.format(form.errors))
				return jsonify({
					"status": "error",
					"errors": form.errors
				})
		elif request.method == 'GET':
			form.studentId.data = student.studentId
			form.firstNameHeb.data = student.firstNameHeb
			form.lastNameHeb.data = student.lastNameHeb
			form.firstNameEng.data = student.firstNameEng
			form.lastNameEng.data = student.lastNameEng
			form.academicStatus.data = student.academicStatus
			form.faculty.data = student.faculty
			form.cellPhone.data = student.cellPhone
			form.email.data = student.email

		return render_template('editAccount.html', title="Edit Account", form=form, student=student)

	except RequestEntityTooLarge as e:
		app.logger.error('In editAccount, Error is: {}\n{}'.format(e, traceback.format_exc()))
		return jsonify({
			"status": "fileTooLarge",
		})
	except Exception as e:
		app.logger.error('In editAccount, Error is: {}\n{}'.format(e, traceback.format_exc()))
		return redirect(url_for('errorPage'))


@app.route('/ProjectProcess', methods=['GET'])
def projectProcess():
	try:
		student = None
		admin = None
		if current_user.is_authenticated:
			if current_user.userType == "student":
				student = database.getStudentByStudentId(current_user.userId)
			elif current_user.userType == "admin":
				admin = database.getAdminByAdminId(current_user.userId)
		return render_template('howToEnroll.html', title="Project Process", student=student, admin=admin)
	except Exception as e:
		app.logger.error('In projectProcess, Error is: {}\n{}'.format(e, traceback.format_exc()))
		return redirect(url_for('errorPage'))