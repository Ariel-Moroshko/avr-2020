import http.client as httplib
import httplib2
import os
import random
import sys
import time
import json
import traceback
import logging
from logging.handlers import RotatingFileHandler
import secrets

from apiclient.discovery import build
from apiclient.errors import HttpError
from apiclient.http import MediaFileUpload
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow
from argparse import Namespace


ytlogger = logging.getLogger('youtubeUpload')
ytlogHandler = RotatingFileHandler(os.path.join(os.path.dirname(__file__), 'youtubeUploadLog.log'), maxBytes=1000000, backupCount=5)
ytlogHandler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
ytlogger.setLevel(logging.INFO)
ytlogger.addHandler(ytlogHandler) 

num_of_clients = 6

# Explicitly tell the underlying HTTP transport library not to retry, since
# we are handling retry logic ourselves.
httplib2.RETRIES = 1

# Maximum number of times to retry before giving up.
MAX_RETRIES = 10

# Always retry when these exceptions are raised.
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, httplib.NotConnected,
  httplib.IncompleteRead, httplib.ImproperConnectionState,
  httplib.CannotSendRequest, httplib.CannotSendHeader,
  httplib.ResponseNotReady, httplib.BadStatusLine)

# Always retry when an apiclient.errors.HttpError with one of these status
# codes is raised.
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

VALID_PRIVACY_STATUSES = ("public", "private", "unlisted")


def get_authenticated_service(args, clientNum):
	credentials_path = os.path.join(os.path.dirname(__file__), "credentials", str(clientNum))
	CLIENT_SECRETS_FILE = os.path.join(credentials_path, "client_secrets.json")
	YOUTUBE_API_SERVICE_NAME = "youtube"
	YOUTUBE_API_VERSION = "v3"
	YOUTUBE_UPLOAD_SCOPE = ["https://www.googleapis.com/auth/youtube", "https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.force-ssl"]
	MISSING_CLIENT_SECRETS_MESSAGE = "Missing client_secrets.json file"

	flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE, scope=YOUTUBE_UPLOAD_SCOPE, message=MISSING_CLIENT_SECRETS_MESSAGE)	
	storage = Storage( os.path.join(credentials_path, "oauth2.json") )
	credentials = storage.get()

	if credentials is None or credentials.invalid:
		credentials = run_flow(flow, storage, args)

	return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,	http=credentials.authorize(httplib2.Http()))

def start_delete_process(clientNum, videoId):
	youtube = start_auth_process(clientNum)
	if not youtube:
		return False
	try: 
		delete_request = youtube.videos().delete(id=videoId).execute()
		ytlogger.info(f"Successfully deleted video with id: {videoId}")
		return ("success", "")
	except HttpError as e:
		response = json.loads(e.content)
		reason = ""
		if "errors" in response["error"]:
			reason = response["error"]["errors"][0]["reason"]		
		if reason == "videoNotFound":
			return ("failure", "videoNotFound")
		elif reason == "quotaExceeded" or reason == "dailyLimitExceeded":
			return ("failure", "quotaExceeded")
	except Exception as e:
		ytlogger.error("{}\n{}".format(e, traceback.format_exc()))
	return ("failure", "")


def deleteVideo(videoId):
	# try number of clients to increase quota limit
	result = "failure"
	info = ""
	for i in range(1, num_of_clients+1):
		ytlogger.info(f"Client {i} trying to delete...")
		result, info = start_delete_process(i, videoId)
		if result == "success" or (result == "failure" and info == "videoNotFound"):
			break
		ytlogger.info(f"Client {i} couldn't delete, info: {info}, trying next client...")
	if result == "failure":
		if info == "videoNotFound":
			ytlogger.info(f"Couldn't delete video {videoId} because it was not found :(")
		else:
			ytlogger.info(f"All clients failed, couldn't delete video {videoId} :(")
	return (result, info)
	

def initialize_upload(youtube, options):
	tags = []
	if options["keywords"]:
		tags = options["keywords"].split(",")
	tag_video_identifier = secrets.token_hex(8)
	tags.append(tag_video_identifier)

	body=dict(
		snippet=dict(
		  title=options["title"],
		  description=options["description"],
		  tags=tags,
		  categoryId=options["category"]
		),
		status=dict(
		  privacyStatus=options["privacyStatus"]
		)
	)

	# Call the API's videos.insert method to create and upload the video.
	insert_request = youtube.videos().insert(
		part=",".join(body.keys()),
		body=body,
		# The chunksize parameter specifies the size of each chunk of data, in
		# bytes, that will be uploaded at a time. Set a higher value for
		# reliable connections as fewer chunks lead to faster uploads. Set a lower
		# value for better recovery on less reliable connections.
		#
		# Setting "chunksize" equal to -1 in the code below means that the entire
		# file will be uploaded in a single HTTP request. (If the upload fails,
		# it will still be retried where it left off.) This is usually a best
		# practice, but if you're using Python older than 2.6 or if you're
		# running on App Engine, you should set the chunksize to something like
		# 1024 * 1024 (1 megabyte).
		media_body=MediaFileUpload(options["file"], chunksize=-1, resumable=True)
	)

	return resumable_upload(insert_request, tag_video_identifier)

# This method implements an exponential backoff strategy to resume a
# failed upload.
def resumable_upload(insert_request, tag_video_identifier):
	response = None
	error = None
	retry = 0
	while response is None:
		try:
			ytlogger.info("Trying to upload file...")
			status, response = insert_request.next_chunk()
			ytlogger.info(f"response is: {response}")
			if 'id' in response:
				ytlogger.info("Video id '%s' was successfully uploaded." % response['id'])
				return response['id']
			else:
				ytlogger.error("The upload failed with an unexpected response: %s" % response)
				return False
		except HttpError as e:
			if e.resp.status in RETRIABLE_STATUS_CODES:
				error = "A retriable HTTP error %d occurred:\n%s" % (e.resp.status,
																 e.content)
			else:
				raise
				
		except RETRIABLE_EXCEPTIONS as e:
			error = "A retriable error occurred: %s" % e
		
		except Exception as e:
			ytlogger.error("Unknown error: {}\n{}".format(e, traceback.format_exc()))
			return False

		if error is not None:
			ytlogger.error(error)
			retry += 1
			if retry > MAX_RETRIES:
				ytlogger.error(f"No longer attempting to retry. response is: {response}")
				# delete partially uploaded video by using the tag_video_identifier we set earlier
				deletePartiallyUploadedVideo(tag_video_identifier)
				return False

			max_sleep = 2 ** retry
			sleep_seconds = random.random() * max_sleep
			ytlogger.error("Sleeping %f seconds and then retrying..." % sleep_seconds)
			time.sleep(sleep_seconds)


def start_auth_process(clientNum):
	args = Namespace(auth_host_name='localhost', auth_host_port=[8090], noauth_local_webserver=False, logging_level="ERROR")
	try:
		youtube = get_authenticated_service(args, clientNum)	
		return youtube
	except Exception as e:
		ytlogger.error("{}\n{}".format(e, traceback.format_exc()))
	return False

def start_upload_process(clientNum, videoPath, title, description, keywords):
	youtube = start_auth_process(clientNum)
	if not youtube:
		return False
	data = {
		"category": '28', 
		"description": description, 
		"file": videoPath,
		"keywords": keywords,
		"privacyStatus": 'unlisted',
		"title": title
	}
	try:
		uploadSuccess = initialize_upload(youtube, data)
		return uploadSuccess
	except HttpError as e:
		response = json.loads(e.content)
		quotaExceeded = False
		if "error" in response:
			if "errors" in response["error"]:
				reason = response["error"]["errors"][0]["reason"]
				if reason == "quotaExceeded" or reason == "dailyLimitExceeded":
					quotaExceeded = True
					ytlogger.info("Couldn't upload file, quota exceeded")
		if not quotaExceeded:
			ytlogger.error("An HTTP error %d occurred:\n%s" % (e.resp.status, e.content))
	except Exception as e:
		ytlogger.error("{}\n{}".format(e, traceback.format_exc()))
	return False


def uploadVideo(videoPath, title, description, keywords):
	# try number of clients to increase quota limit
	success = False
	for i in range(1, num_of_clients+1):
		ytlogger.info(f"Client {i} trying to upload...")
		success = start_upload_process(clientNum=i, videoPath=videoPath, title=title, description=description, keywords=keywords)
		if success:
			break
		ytlogger.info(f"Client {i} couldn't upload, trying next client...")
	if not success:
		ytlogger.info(f"All clients failed, couldn't upload the video :(")
	return success


def start_setVideoToPublic_process(clientNum, videoId):
	youtube = start_auth_process(clientNum)
	if not youtube:
		return False
	try: 
		delete_request = youtube.videos().update(part="status", body={
			"id": videoId,
			"status": {
				"privacyStatus": "public",
				"embeddable": "true",
				"publicStatsViewable": "true"
			}
		}).execute()
		ytlogger.info(delete_request)
		ytlogger.info(f"Successfully set video: {videoId} to public")
		return True
	except Exception as e:
		ytlogger.error("{}\n{}".format(e, traceback.format_exc()))
	return False


def setVideoToPublic(videoId):
	# try number of clients to increase quota limit
	success = False
	for i in range(1, num_of_clients+1):
		ytlogger.info(f"Client {i} trying to set video to public...")
		success = start_setVideoToPublic_process(i, videoId)
		if success:
			break
		ytlogger.info(f"Client {i} couldn't set video to public, trying next client...")
	if not success:
		ytlogger.info(f"All clients failed, couldn't set video {videoId} to public :(")
	return success


def start_getProcessingDetails_process(clientNum, videoId):
	youtube = start_auth_process(clientNum)
	if not youtube:
		return False
	try: 
		request = youtube.videos().list(part="processingDetails,status", id=videoId).execute()
		ytlogger.info(f"Successfully got processing details of video: {videoId}: {request}")
		return request
	except HttpError as e:
		response = json.loads(e.content)
		if "error" in response:
			if "errors" in response["error"]:
				reason = response["error"]["errors"][0]["reason"]
				if reason == "dailyLimitExceeded" or reason == "quotaExceeded":
					ytlogger.info(f"Couldn't get processing details of {videoId}, quota exceeded")
	except Exception as e:
		ytlogger.error("{}\n{}".format(e, traceback.format_exc()))
	return False


def getProcessingDetails(videoId):
	# try number of clients to increase quota limit
	success = False
	for i in range(1, num_of_clients+1):
		ytlogger.info(f"Client {i} trying to get processing details")
		success = start_getProcessingDetails_process(i, videoId)
		if success:
			break
		ytlogger.info(f"Client {i} couldn't get processing details, trying next client...")
	if not success:
		ytlogger.info(f"All clients failed, couldn't get processing details of video {videoId} :(")
	return success


def start_delete_partially_uploaded_video_process(clientNum, tag_video_identifier):
	youtube = start_auth_process(clientNum)
	if not youtube:
		return False
	try: 
		request = youtube.search().list(part="snippet", forMine=True, type="video", q=tag_video_identifier).execute()
		if request['pageInfo']['totalResults'] == 1:
			videoId = request['items'][0]['id']['videoId']
			success = start_delete_process(clientNum, videoId)
			return success
		else:
			ytlogger.error(f"Tried to delete partially uploaded video {tag_video_identifier} but the video was not found...")
	except Exception as e:
		ytlogger.error("{}\n{}".format(e, traceback.format_exc()))
	return False


def deletePartiallyUploadedVideo(tag_video_identifier):
	# try number of clients to increase quota limit
	success = False
	for i in range(1, num_of_clients+1):
		ytlogger.info(f"Client {i} trying to delete partially uploaded video {tag_video_identifier}")
		success = start_delete_partially_uploaded_video_process(i, tag_video_identifier)
		if success:
			break
		ytlogger.info(f"Client {i} couldn't delete partially uploaded video, trying next client...")
	if not success:
		ytlogger.info(f"All clients failed, couldn't delete partially uploaded video {tag_video_identifier} :(")


if __name__ == '__main__':	
	print("#"*50)
	""" youtube = start_auth_process(1)
	request = youtube.videos().update(part="status", body={
		"id": "Ai_RXz6TMGU",
		"status": {
			"embeddable": "true"
		}
	}).execute()
	print(request) """