import os
import secrets
from shutil import copyfile
import datetime
from avr import app
import traceback
from PIL import Image
from avr.youtubeUpload import youtubeUpload
from avr import database
from avr import db
from avr.models import Project
import time


def deleteLocalFile(filePath):
	try:
		os.remove(filePath)
		app.logger.info(f'deleted: {filePath}')
	except OSError as e:
		app.logger.error('Could not delete file: {}, {}\n{}'.format(filePath, e, traceback.format_exc()))


def set_youtube_video_public(appArg, projectId):
	with appArg.app_context():
		try:
			project = database.getProjectById(projectId)
			success = youtubeUpload.setVideoToPublic(project.youtubeVideo)
			if success:
				database.updateProject(project.id, {
					"youtubeVideoPublicStatus": "success",
					"projectDocApproved": True,
					"projectDocEditableByStudents": False
				})
				database.updateProjectStatus(project.id, {
					"projectDoc": True
				})
			else:
				database.updateProject(project.id, {
					"youtubeVideoPublicStatus": "failed"
				})
		except Exception as e:
			app.logger.error('Error is: {}\n{}'.format(e, traceback.format_exc()))
			database.updateProject(project.id, {
				"youtubeVideoPublicStatus": "failed"
			})


def update_youtube_video_processing_details(projectId):
	while True:
		try:
			project = database.getProjectById(projectId)
			database.updateProject(project.id, {
				"youtubeProcessingStatus": "checking"
			})
			result = youtubeUpload.getProcessingDetails(videoId=project.youtubeVideo)
			if result:
				if result["pageInfo"]["totalResults"] != 0:				
					failedStatus = {"deleted", "failed", "rejected"}
					if result["items"][0]["status"]["uploadStatus"] in failedStatus:
						database.updateProject(project.id, {
							"youtubeVideo": "",		# to avoid trying to delete this video next time bacause it won't succeed
							"youtubeProcessingFailureReason": "",
							"youtubeProcessingStatus": "terminated",
							"youtubeProcessingEstimatedTimeLeft": ""
						})
						break

					elif result["items"][0]["status"]["uploadStatus"] == "uploaded":
						youtubeVideo = project.youtubeVideo
						youtubeProcessingStatus = ""
						processingFailureReason = ""
						youtubeProcessingEstimatedTimeLeft = project.youtubeProcessingEstimatedTimeLeft
						if not "processingDetails" in result["items"][0]:	# processing failed for some reason, no info given
							youtubeVideo = ""
							youtubeProcessingStatus = "terminated"
						else:
							if result["items"][0]["processingDetails"]["processingStatus"] == "failed":
								youtubeProcessingStatus = "failed"
								processingFailureReason = result["items"][0]["processingDetails"]["processingFailureReason"]
							elif result["items"][0]["processingDetails"]["processingStatus"] == "terminated":
								youtubeProcessingStatus = "terminated"
								youtubeVideo = ""
							elif result["items"][0]["processingDetails"]["processingStatus"] == "processing":
								youtubeProcessingStatus = "processing"
								if "processingProgress" in result["items"][0]["processingDetails"]:
									youtubeProcessingEstimatedTimeLeft = result["items"][0]["processingDetails"]["processingProgress"]["timeLeftMs"]
	
						database.updateProject(project.id, {
							"youtubeVideo": youtubeVideo,
							"youtubeProcessingStatus": youtubeProcessingStatus,
							"youtubeProcessingFailureReason": processingFailureReason,
							"youtubeProcessingEstimatedTimeLeft": youtubeProcessingEstimatedTimeLeft
						})
						if youtubeProcessingStatus != "processing":
							break

					elif result["items"][0]["status"]["uploadStatus"] == "processed":
						database.updateProject(project.id, {
							"youtubeProcessingStatus": "processed",
							"youtubeProcessingEstimatedTimeLeft": "",
							"youtubeProcessingFailureReason": "",
							"status": "דף פרויקט - טיוטה"
						})
						break
		

				else:	# video processing failed because something was wrong with the video file or it was a duplicate of a video already uploaded
					database.updateProject(project.id, {
						"youtubeVideo": "",		# to avoid trying to delete this video next time bacause it won't succeed
						"youtubeProcessingFailureReason": "",
						"youtubeProcessingStatus": "terminated",
						"youtubeProcessingEstimatedTimeLeft": ""
					})
					break

			else:
				database.updateProject(project.id, {
					"youtubeProcessingStatus": ""
				})
		except Exception as e:
			app.logger.error('Error is: {}\n{}'.format(e, traceback.format_exc()))
		
		time.sleep(3.0)


def upload_video_to_youtube(appArg, projectId):
	with appArg.app_context():
		try:
			project = database.getProjectById(projectId)
			database.updateProject(project.id, {
				"youtubeUploadStatus": "uploading"
			})
			videoPath = os.path.join(appArg.root_path, "static", "project_doc", "video", project.localVideo)
			success = youtubeUpload.uploadVideo(
				videoPath=videoPath, 
				title=project.title, 
				description=project.abstract, 
				keywords="technion, technion avr, technion project, virtual reality lab, augmented reality lab"
			)
			if success:
				deleteLocalFile(videoPath)
				app.logger.info(f"Local video: {videoPath} was deleted")
				database.updateProject(project.id, {
					"localVideo": "",
					"youtubeVideo": success,
					"youtubeUploadStatus": "completed"
				})
				update_youtube_video_processing_details(projectId)
			else:
				database.updateProject(project.id, {
					"youtubeUploadStatus": "failed"
				})
		except Exception as e:
			app.logger.error('Error is: {}\n{}'.format(e, traceback.format_exc()))
			database.updateProject(project.id, {
				"youtubeUploadStatus": "failed"
			})


def overwrite_youtube_video(appArg, projectId):
	with appArg.app_context():
		try:
			project = database.getProjectById(projectId)
			database.updateProject(project.id, {
				"youtubeUploadStatus": "deleting current"
			})
			deleteVideoResult, deleteVideoInfo = youtubeUpload.deleteVideo(project.youtubeVideo)
			if (deleteVideoResult == "success") or (deleteVideoResult == "failure" and deleteVideoInfo == "videoNotFound"):
				database.updateProject(project.id, {
					"youtubeVideo": "",
				})
				database.updateProjectStatus(project.id, {
					"projectDoc": False
				})
				upload_video_to_youtube(appArg, projectId)
			else:
				database.updateProject(project.id, {
					"youtubeUploadStatus": "failed"
				})
		except Exception as e:
			app.logger.error('Error is: {}\n{}'.format(e, traceback.format_exc()))
			database.updateProject(project.id, {
				"youtubeUploadStatus": "failed"
			})


def delete_image(imageName, folder):
	if imageName is not None:
		imageFolder = os.path.join(app.root_path, 'static', 'images', folder)
		try:
			os.remove(os.path.join(imageFolder, imageName))
		except OSError as e:
			app.logger.error('could not delete image {}, Error is: {}\n{}'.format(os.path.join(imageFolder, imageName), e, traceback.format_exc()))


def delete_proposed_project_image(imageName):
	delete_image(imageName, "proposed_projects")

def delete_project_image(imageName):
	delete_image(imageName, "projects")

def delete_profile_image(imageName):
	delete_image(imageName, "profile")


def copy_project_image_from_proposed_project(matchingImageName):
	random_hex = secrets.token_hex(8)
	_, matchingExt = os.path.splitext(matchingImageName)
	newImageName = random_hex + matchingExt
	sourcePath = os.path.join(app.root_path, 'static', 'images', 'proposed_projects', matchingImageName)
	destinationFolder = os.path.join(app.root_path, 'static', 'images', 'projects')
	if not os.path.exists(destinationFolder):
		try:
			os.makedirs(destinationFolder)
		except Exception as e:
			app.logger.error('could not make dir {}, Error is: {}\n{}'.format(destinationFolder, e, traceback.format_exc()))
	try:
		copyfile(sourcePath, os.path.join(destinationFolder, newImageName))
		return newImageName
	except Exception as e:
		app.logger.error('could not copyfile {}, Error is: {}\n{}'.format(sourcePath, e, traceback.format_exc()))


def save_form_file(file, folder):
	random_hex = secrets.token_hex(8)
	_, fileExt = os.path.splitext(file.filename)
	fileExt = fileExt.lower()
	fileName = random_hex + fileExt
	fileFolder = os.path.join(app.root_path, folder)
	
	if not os.path.exists(fileFolder):
		try:
			os.makedirs(fileFolder)
		except Exception as e:
			app.logger.error('could not make dir {}, Error is: {}\n{}'.format(fileFolder, e, traceback.format_exc()))

	filePath = os.path.join(fileFolder, fileName)
	# if this file name is already taken, try maximum 20 other random file names
	for i in range(20):
		if not os.path.isfile(filePath):
			break
		fileName = secrets.token_hex(8) + fileExt
		filePath = os.path.join(fileFolder, fileName)
	file.save(filePath)

	return fileName

	

def save_form_image(form_image, folder):
	random_hex = secrets.token_hex(8)
	_, imageExt = os.path.splitext(form_image.filename)
	imageExt = imageExt.lower()
	imageName = random_hex + imageExt
	imageFolder = os.path.join(app.root_path, 'static', 'images', folder)
	
	if not os.path.exists(imageFolder):
		try:
			os.makedirs(imageFolder)
		except Exception as e:
			app.logger.error('could not make dir {}, Error is: {}\n{}'.format(imageFolder, e, traceback.format_exc()))

	imagePath = os.path.join(imageFolder, imageName)
	# if this file name is already taken, try maximum 20 other random file names
	for i in range(20):
		if not os.path.isfile(imagePath):
			break
		imageName = secrets.token_hex(8) + imageExt
		imagePath = os.path.join(imageFolder, imageName)
	form_image.save(imagePath)
	if imageExt == ".tga":
		# convert tga image to png
		im = Image.open(imagePath)
		rgb_im = im.convert('RGB')
		oldImageName = imageName
		imageName = imageName.replace("tga", "png")
		newImgPath = os.path.join(imageFolder, imageName)
		rgb_im.save(newImgPath)
		# delete old tga image
		delete_image(oldImageName, imageFolder)

	return imageName

def getRegistrationSemester():
	currentMonth = int(datetime.datetime.now().strftime("%m"))
	if currentMonth >= 1 and currentMonth <= 6:
		return "Spring"
	else:
		return "Winter"

def getRegistrationYear():
	currentMonth = int(datetime.datetime.now().strftime("%m"))
	currentYear = int(datetime.datetime.now().strftime("%Y"))
	if currentMonth >= 1 and currentMonth <= 6:
		return currentYear
	else:
		return currentYear+1

def getCurrentYear():
	currentMonth = int(datetime.datetime.now().strftime("%m"))
	currentYear = int(datetime.datetime.now().strftime("%Y"))
	if currentMonth >= 10:
		return currentYear+1
	else:
		return currentYear

def getCurrentSemester():
	currentMonth = int(datetime.datetime.now().strftime("%m"))
	if currentMonth >= 10 or currentMonth <= 2:
		return "Winter"
	else:
		return "Spring"