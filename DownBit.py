import smtplib
import socket
import sys
import time
from datetime import datetime as dt
from multiprocessing import Process
from Core import DB
from RSSDownloader import main as RSSDownloader
from RSSReader import main as RSSReader
import os

LOGGER = DB.Logger.log
STORAGE = DB.Storage


def is_connected():
    try:
        host = socket.gethostbyname("www.google.com")
        _ = socket.create_connection((host, 80), 2)
        return True
    except Exception as e_:
        DB.Logger.log.debug(str(type(e_).__name__) + " : " + str(e_))
    return False


def sendEmail(downloads):
    server = smtplib.SMTP(DB.cfg.getSetting('STMPServer'), DB.cfg.getSettingInt('STMPPort'))
    server.starttls()
    server.login(DB.cfg.getSetting('SenderEmail'), DB.cfg.getSetting('SenderEmailPassword'))

    msg = "Downloads for Today\n"
    for download in downloads:
        msg += "\n{}".format(download[0])

    LOGGER.info('Sending the Daily Email for ' + DB.cfg.getSetting('ReceiverEmail'))
    server.sendmail(DB.cfg.getSetting('SenderEmail'), DB.cfg.getSetting('ReceiverEmail'), msg)
    server.quit()


try:
    if __name__ == '__main__':
        LOGGER.info("##########################################################")
        LOGGER.info("##################### Starting ###########################")
        LOGGER.info("##########################################################")

        if not is_connected():
            LOGGER.info("Waiting for Internet Connection")

        while not is_connected():
            time.sleep(10)

        try:
            RSSReader = Process(target=RSSReader)
            RSSDownloader = Process(target=RSSDownloader)

            RSSReader.start()
            RSSDownloader.start()

        except Exception as e:
            LOGGER.critical(str(type(e).__name__) + " : " + str(e))
            RSSReader.terminate()
            RSSDownloader.terminate()
            LOGGER.info("##########################################################")
            LOGGER.info("#################### Restating ###########################")
            LOGGER.info("##########################################################")
            os.execv(sys.executable, [sys.executable] + sys.argv)
        if len(sys.argv) > 1:
            LOGGER.info("DownBit Build Testing Mod Activated")
            time.sleep(360)
            if DB.Logger.buildFailed:
                RSSReader.terminate()
                RSSDownloader.terminate()
                LOGGER.info("##########################################################")
                LOGGER.info("################### Terminating ##########################")
                LOGGER.info("##########################################################")
            else:
                LOGGER.info("DownBit New Build Successfully Passed\n\n")
                RSSReader.terminate()
                RSSDownloader.terminate()
                LOGGER.info("##########################################################")
                LOGGER.info("################### Terminating ##########################")
                LOGGER.info("##########################################################")
        else:
            while True:
                if str(dt.now().strftime('%H:%M')) == '08:00':
                    data = STORAGE.get(
                        "select Name from Downloads where DownloadedTime >= Datetime('{} 00:00:00') ".format(
                            str(dt.now().strftime('%Y-%m-%d'))))
                    sendEmail(data)
                time.sleep(60)
except KeyboardInterrupt:
    RSSReader.terminate()
    RSSDownloader.terminate()
    LOGGER.error("KeyboardInterrupt Stopping DownBit")
    LOGGER.info("##########################################################")
    LOGGER.info("################### Terminating ##########################")
    LOGGER.info("##########################################################")
