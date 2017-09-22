import configparser
import logging
import os
import re
import sqlite3
from datetime import datetime


class database:
    def __init__(self):
        try:
            os.chdir(os.path.dirname(os.path.abspath(__file__)))
            self.conn = sqlite3.connect('database/database.db')
            self.c = self.conn.cursor()
        except Exception as e:
            logger.critical(str(type(e).__name__) + " : " + str(e))

    def read(self, query):
        logger.info("Reading Data --> {}".format(query))
        try:
            self.c.execute(query)
            return self.c.fetchall()
        except Exception as e:
            logger.critical(str(type(e).__name__) + " : " + str(e))

    def read_hide(self, query):
        try:
            self.c.execute(query)
            return self.c.fetchall()
        except Exception as e:
            logger.critical(str(type(e).__name__) + " : " + str(e))

    def write(self, query):
        logger.info("Writing Data --> {}".format(query))
        try:
            self.c.execute(query)
            self.conn.commit()
        except Exception as e:
            logger.critical(str(type(e).__name__) + " : " + str(e))

    def lastmatch(self, table, column, id, value):
        lastmatch = self.read_hide("SELECT {} FROM {} WHERE id = {};".format(column, table, id))
        if str(lastmatch[0][0]) == str(value):
            return True
        else:
            logger.info('Updating last match for {} table where id = {} to {}'.format(table, id, value))
            self.write("UPDATE {} SET {} = '{}' WHERE id = {};".format(table, column, value, id))
            return False

    def getid(self, table, value, column):
        return int(self.read_hide("SELECT * from '{}' WHERE {} = '{}'".format(table, column, value))[0][0])

    def mark_downloaded(self, url):
        time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.write(
            "UPDATE downloads SET state = 'downloaded', downloaded_time = '{}'  WHERE url = '{}';".format(time, url))

    def delete(self, table, id):
        self.write("DELETE FROM '{}' WHERE id = '{}'".format(table, id))

    def addtodownload(self, name, method, url, path, provider):
        time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.write(
            "INSERT INTO downloads (name,method,url,provider,added_time,path,state) VALUES ('{}', '{}', '{}', '{}', '{}', '{}', '{}')".format(
                name, method, url, provider, time, path, "downloading"))

    def update_lastmatch(self, table, column, id, value):
        self.write("UPDATE {} set {} = '{}' where id = '{}'".format(table, column, value, id))


def exe(cmd):
    logger.info('executing cmd - ' + cmd)
    try:
        f = os.popen(cmd)
        out = f.read()
        for line in out.split("\n"):
            logger.info("output " + line)
        return out
    except Exception as e:
        logger.critical(str(type(e).__name__) + " : " + str(e))


def clear(s):
    return re.sub('[^A-Za-z0-9 ]+', '', s).strip(" ")


def dltime():
    dltimes = config('DownBit', 'DownloadHours').split(',')
    dltimes = list(map(int, dltimes))
    time = int(datetime.now().strftime('%H'))
    if time in dltimes:
        return True
    else:
        return False


def config(section, sub):
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    config = configparser.ConfigParser()
    config.read('config/config.ini')
    return config[section][sub]


def uniqifie(seq, idfun=None):
    # https://www.peterbe.com/plog/rs-benchmark
    # order preserving
    if idfun is None:
        def idfun(x): return x

        seen = {}
        result = []
    for item in seq:
        marker = idfun(item)
        # in old Python versions:
        # if seen.has_key(marker)
        # but in new ones:
        if marker in seen: continue
        seen[marker] = 1
        result.append(item)
    return result


def logger(file_name):
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    file_name = "logs/" + file_name

    if not os.path.exists('logs'):
        os.makedirs('logs')

    if os.path.isfile(file_name + ".5"):
        os.remove(file_name + ".5")
    if os.path.isfile(file_name + ".4"):
        os.rename(file_name + ".4", file_name + ".5")
    if os.path.isfile(file_name + ".3"):
        os.rename(file_name + ".3", file_name + ".4")
    if os.path.isfile(file_name + ".2"):
        os.rename(file_name + ".2", file_name + ".3")
    if os.path.isfile(file_name + ".1"):
        os.rename(file_name + ".1", file_name + ".2")
    if os.path.isfile(file_name):
        os.rename(file_name, file_name + ".1")
        if os.path.isfile(file_name):
            os.remove(file_name)

    logFormatter = logging.Formatter(fmt='%(asctime)-10s %(levelname)-10s: %(module)s:%(lineno)-d -  %(message)s',
                                     datefmt='%Y-%m-%d %H:%M:%S')

    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.INFO)
    if config('DownBit', 'LogLevel') == "info":
        rootLogger.setLevel(logging.INFO)
    elif config('DownBit', 'LogLevel') == "debug":
        rootLogger.setLevel(logging.DEBUG)
    elif config('DownBit', 'LogLevel') == "error":
        rootLogger.setLevel(logging.ERROR)
    elif config('DownBit', 'LogLevel') == "critical":
        rootLogger.setLevel(logging.CRITICAL)
    fileHandler = logging.FileHandler(file_name)
    fileHandler.setFormatter(logFormatter)
    rootLogger.addHandler(fileHandler)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    rootLogger.addHandler(consoleHandler)

    return rootLogger


logger = logger('DownBit.log')
