
import sys
import json
import requests
import time
import os

InsecureRequestWarning = requests.packages.urllib3.exceptions.InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

#-------------------------------------------------------------------------------

import settings

#-------------------------------------------------------------------------------

get = requests.get
post = requests.post
delete = requests.delete

def request(method, path, **kwargs):
	response = method(path, **kwargs, verify=False)
	retry_on_too_many = kwargs.get('retry_on_429', True)

	if response.status_code == 429 and retry_on_too_many:
		time.sleep(1)
		response = method(path, **kwargs, verify=False)
		
	return response

#-------------------------------------------------------------------------------

def load_file(file):
	with open(file) as fd:
		return fd.read()


def login_file(credentialFile):
	credential = load_file(credentialFile)
	response = request(post, f"{settings.SERVER_ADDRESS}/login",
		headers={'content-type': 'application/json'},
		data=credential)

	result = response.json()
	return result


users_dir = 'usuarios'

def load_users():
	result = list()

	for user_file in os.listdir(users_dir): 
		full_path = f"{users_dir}/{user_file}"
		contents = load_file(full_path)
		data = json.loads(contents)
		result.append(data)

	return result

#-------------------------------------------------------------------------------

def login_userdata(login, password):

	credential = f'''{{

		"login": "{login}",
		"password": "{password}"

	}}'''

	response = request(post, f"{settings.SERVER_ADDRESS}/login",
		headers={'content-type': 'application/json'},
		data=credential)

	result = response.json()
	return result

#-------------------------------------------------------------------------------

def announce(text):
	def decorator(decorated_function):
		def wrapped():
			print(f"{text}... ", end="");
			sys.stdout.flush()

			try:
				decorated_function()
				print("OK")

			except Exception as e:
				print(f"FAILED => {str(e)}")
				raise e

		return wrapped
	return decorator


