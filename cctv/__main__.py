from cctv import CCTV
from discovery import CCTVScanner
from getpass import getpass

config = {
	"username": "admin",
	"SN" : None,
	"IP" : "192.168.1.29"
}

camera = CCTV(config["username"], getpass("getpass: "), SN=config["SN"], ip=config["IP"])
camera.get_SN()
camera.snapshot()


scanner = CCTVScanner()
scanner.scan_network("192.168.1.0/24")
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

