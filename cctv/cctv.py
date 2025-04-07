import requests
from requests.auth import HTTPDigestAuth
from PIL import Image
import io
import re

class CCTV:
	def __init__(self, username, password, ip=None, SN=None):
		self.username = username
		self.password = password
		self.ip = ip
		self.SN = SN
		self.session = requests.Session()

	def __str__(self):
		return f"CCTV(ip={self.ip}, SN={self.SN})"

	def __repr__(self):
		return self.__str__()

	def connect(self):
		if self.ip is None and self.SN is None:
			raise Exception("CCTV need IP or SN")
		if not self.SN:
			self.get_SN()
		if not self.SN:
			raise Exception(f"Cannot find CCTV's SN for {ip}")

		return 0

	def snapshot(self, channel=1):
		SNAPSHOT_URL = f"http://{self.ip}/cgi-bin/snapshot.cgi?channel={channel}"

		try:
			# Send GET request with digest authentication
			response = self.session.get(
				SNAPSHOT_URL,
				auth=HTTPDigestAuth(self.username, self.password),
				timeout=10
			)
			
			# Check if request was successful
			if response.status_code == 200:
				# Open the image using PIL
				image = Image.open(io.BytesIO(response.content))
				
				# Save the image to file
				image.save("camera_snapshot.jpg")
				# print("Snapshot saved successfully as camera_snapshot.jpg")
				
				# Optionally show the image
				# image.show()
				return image
			else:
				print(f"Failed to get snapshot. Status code: {response.status_code}")
				print(f"Response: {response.text}")

		# except requests.exceptions.RequestException as e:
		# 	print(f"Error connecting to camera: {e}")
		# except IOError as e:
		# 	print(f"Error handling image: {e}")
		except Exception as e:
			raise e

	def get_SN(self):
		if not self.ip:
			raise Exception("Cannot find SN without IP")
		SN_URL = f"http://{self.ip}/cgi-bin/magicBox.cgi?action=getSerialNo"

		try:
			# Send GET request with digest authentication
			response = self.session.get(
				SN_URL,
				auth=HTTPDigestAuth(self.username, self.password),
				timeout=10
			)
			
			# Check if request was successful
			if response.status_code == 200:
				match = re.search(r'sn=([A-Z0-9]+)', response.text)
				if match:
					serial_number = match.group(1)
					self.SN = serial_number
					return True

			return False

	def display_image(self, image_data):
		image.show()


		# except requests.exceptions.RequestException as e:
		# 	print(f"Error connecting to camera: {e}")
		# except IOError as e:
		# 	print(f"Error handling image: {e}")
		except Exception as e:
			raise e
			


