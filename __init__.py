import os
import psutil
import sys
from DownBit import logger, database, config
from multiprocessing import Process
from plugins.youtube import youtube
from plugins.yts import yts
from plugins.torrent_subs import torrent_subs
from plugins.weeb import weeb
import time
import socket
import smtplib
from datetime import datetime as dt

REMOTE_SERVER = "www.google.com"


def is_connected():
    try:
        host = socket.gethostbyname(REMOTE_SERVER)
        _ = socket.create_connection((host, 80), 2)
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


def sendEmail(downloads, sender_email=config('DownBit', 'SenderEmail'), password=config('DownBit', 'SenderEmailPassword'), receiver=config('DownBit', 'ReceiverEmail')):
    server = smtplib.SMTP(config('DownBit', 'STMPServer'), int(config('DownBit', 'STMPPort')))
    server.starttls()
    server.login(sender_email, password)

    msg = "Downloads for Today\n"
    for download in downloads:
        msg += "\n{}".format(download[0])

    logger.info('Sending the Daily Email for '+receiver)
    server.sendmail(sender_email, receiver, msg)
    server.quit()


if __name__ == '__main__':
    logger.info("##########################################################")
    logger.info("##################### Starting ###########################")
    logger.info("##########################################################")

    if not is_connected():
        logger.info("Waiting for Internet Connection")

    while not is_connected():
        time.sleep(10)

    try:
        youtube = Process(target=youtube)
        youtube.start()

        torrent_subs = Process(target=torrent_subs)
        torrent_subs.start()

        yts = Process(target=yts)
        yts.start()

        weeb = Process(target=weeb)
        weeb.start()

    except Exception as e:
        restart_program()
        logger.critical(str(type(e).__name__) + " : " + str(e))

    while True:
        if str(dt.now().strftime('%H:%M')) == '08:00':
            db = database()
            data = db.read("select name from downloads where downloaded_time >= Datetime('{} 00:00:00') ".format(
                str(dt.now().strftime('%Y-%m-%d'))))
            sendEmail(data)
        time.sleep(60)