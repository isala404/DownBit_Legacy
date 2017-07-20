import os
import psutil
import sys
from DownBit import logger,config
from multiprocessing import Process
from plugins.youtube import youtube
from plugins.yts import yts
from plugins.torrent_subs import torrent_subs
import time
import socket


REMOTE_SERVER = "www.google.com"
def is_connected():
	try:
		host = socket.gethostbyname(REMOTE_SERVER)
		s = socket.create_connection((host, 80), 2)
		return True
	except:
		pass
	return False




def restart_program():
	"""Restarts the current program, with file objects and descriptors
	   cleanup
	"""

	try:
		p = psutil.Process(os.getpid())
		for handler in p.get_open_files() + p.connections():
			os.close(handler.fd)
	except Exception as e:
		logger.critical(str(type(e).__name__) + " : " + str(e))

	python = sys.executable
	os.execl(python, python, *sys.argv)


if __name__=='__main__':
		logger.info("##########################################################")
		logger.info("##################### Starting ###########################")
		logger.info("##########################################################")

		if not is_connected():
			logger.info("Waiting for Internet Connection")

		while not is_connected():
			time.sleep(10)

		try:
			youtube = Process(target = youtube)
			youtube.start()

			torrent_subs = Process(target = torrent_subs)
			torrent_subs.start()

			yts = Process(target = yts)
			yts.start()

		except Exception as e:
			restart_program()
			logger.critical(str(type(e).__name__)+" : "+str(e))
