from onvif import ONVIFCamera
from cctv import CCTV
import requests
import numpy as np
import cv2

class ONVIF_CCTV(CCTV):
	def __init__(self, username, password, ip=None, SN=None, wsdl=None):
		super().__init__(username, password, ip, SN)
		if self.ip is None:
			raise Exception("ONVIF need IP to operation")

		# Split into IP and port (default to 80 if no port is specified)
		address = ip
		if ":" in address:
			ip, port_str = address.split(":")
			port = int(port_str)
		else:
			ip = address
			port = 80  # Default HTTP port

		self.onvif = ONVIFCamera(ip, port, username, password, wsdl)
		self.media_service = None

	def get_SN(self):
		device_info = self.onvif.devicemgmt.GetDeviceInformation()
		return device_info.SerialNumber

	def snapshot(self, channel=1, savepath=None):
		try: 
			if self.media_service is None:
				self.media_service = self.onvif.create_media_service()

			profiles = self.media_service.GetProfiles()
			profile_token = profiles[0].token
			snapshot_uri = self.media_service.GetSnapshotUri({'ProfileToken': profile_token})
			response = requests.get(
				snapshot_uri.Uri,
				auth=requests.auth.HTTPDigestAuth(self.username, self.password),
				stream=True
			)

			if response.status_code != 200:
				raise Exception(f"Failed to get snapshot. Status code: {response.status_code}")

			image_data = response.content

			if savepath:
				with open(savepath, 'wb') as f:
					f.write(image_data)
				print(f"Snapshot saved to {savepath}")
			
			return image_data
		
		except Exception as e:
			print(f"Error getting snapshot: {e}")
			return None

	def display_image(self, image_data):
		"""Display the image using OpenCV (optional)"""
		try:
			# Convert bytes to numpy array
			nparr = np.frombuffer(image_data, np.uint8)
			img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
			
			# Display the image
			cv2.imshow('Camera Snapshot', img)
			cv2.waitKey(0)
			cv2.destroyAllWindows()
		except Exception as e:
			print(f"Error displaying image: {e}")