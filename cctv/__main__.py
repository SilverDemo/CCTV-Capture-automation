from cctv import CCTV
from onvif_cctv import ONVIF_CCTV
from discovery import CCTVScanner
from getpass import getpass
import os
from pathlib import Path

project_root = Path(os.path.dirname(os.path.abspath(__file__)))

config = {
	"username": "admin",
	"SN" : None,
	"IP" : "192.168.100.41"
}


camera = ONVIF_CCTV(config["username"], getpass("getpass: "), SN=config["SN"], ip=config["IP"], wsdl=(project_root / "../wsdl_cache"), port=10000)
camera.get_SN()

camera.display_image(camera.snapshot())

exit(0)
scanner = CCTVScanner()
scanner.scan_network("192.168.100.0/24")
scanner.wait()
result = scanner.get_results()
scanner.print_results()
# print(result)

cctvs = []

for found in result:
	ip, ports = found
	is_CCTV = False
	for port in ports:
		no, _ = port
		if no == 37777:
			is_CCTV = True
			break
	if is_CCTV:
		cam = CCTV(config["username"], config["password"], ip=ip)
		if cam.get_SN():
			cctvs.append(cam)

print(cctvs)

