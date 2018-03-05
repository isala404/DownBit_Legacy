import configparser
import logging
import os
import re
import sqlite3
import sys
from datetime import datetime


class Storage(object):
    def __init__(self):
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        if not os.path.exists('data'):
            os.makedirs('data')
        self.conn = sqlite3.connect('data/database.db')
        self.c = self.conn.cursor()

        self.c.execute(
            '''CREATE TABLE IF NOT EXISTS "Downloads" ( `ID` INTEGER PRIMARY KEY AUTOINCREMENT, `RSSID` INTEGER, 
            `Name` TEXT DEFAULT ' ', `Method` TEXT NOT NULL, `URL` TEXT NOT NULL, `AddedTime` NUMERIC DEFAULT ' ', 
            `DownloadedTime` NUMERIC DEFAULT ' ', `Path` TEXT DEFAULT '/mnt', `FileSize` REAL DEFAULT ' ', 
            `DownloadedSize` REAL DEFAULT ' ', `optionalARGS` TEXT DEFAULT ' ', `Downloaded` NUMERIC DEFAULT 0 )''')
        self.c.execute(
            '''CREATE TABLE IF NOT EXISTS "RSSFeeds" ( `ID` INTEGER PRIMARY KEY AUTOINCREMENT, `Name` TEXT, 
            `Feed` TEXT, `DownloadPath` TEXT, `Includes` TEXT, `Excludes` TEXT DEFAULT '#&*,$#', `Type` TEXT, 
            `Quality` TEXT DEFAULT '720p', `LastMatch` TEXT );''')
        self.c.execute("SELECT * FROM RSSFeeds")
        if len(self.c.fetchall()) == 0:
            self.c.execute(
                '''INSERT INTO RSSFeeds(Name,Feed,DownloadPath,Type) VALUES ('Sentdex','https://www.youtube.com/feeds/videos.xml?channel_id=UCfzlCWGWYyIQ0aLC5w48gBQ','~/sentdex/Downloads/','Youtube')''')
            self.conn.commit()

    def get(self, query, *pars, readOne=False):
        DB.Logger.log.info("Reading Data --> {} - {}".format(query, pars))
        try:
            self.c.execute(query, pars)
            if readOne:
                return self.c.fetchone()
            else:
                return self.c.fetchall()
        except Exception as e:
            DB.Logger.log.exception(e)

    def put(self, query, *pars):
        DB.Logger.log.info("Writing Data --> {} - {}".format(query, pars))
        try:
            self.c.execute(query, pars)
            self.conn.commit()
        except Exception as e:
            DB.Logger.log.exception(e)

    def getid(self, table, value, column):
        self.c.execute("SELECT * FROM (?) WHERE (?) = (?)", (table, column, value))
        return int(self.c.fetchone()[0])

    def mark_downloaded(self, id):
        time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.put(
            "UPDATE Downloads SET Downloaded = 1, DownloadedTime = (?)  WHERE id = (?);", time, id)

    def addtodownload(self, id, name, method, url, path, arg=''):
        time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.put(
            'INSERT INTO Downloads (RSSID,Name, Method,URL,AddedTime,Path,optionalARGS,Downloaded) VALUES (?, ?, ?, ?, ?, ?, ?, ?);',
            id, name, method, url, time, path, arg, False)

    def update_lastmatch(self, id, value):
        self.put("UPDATE RSSFeeds SET LastMatch = (?) WHERE id = (?);", value, id)


class ConfigParser(object):
    def __init__(self):
        try:
            os.chdir(os.path.dirname(os.path.abspath(__file__)))
            self.config = configparser.ConfigParser()
            self.config.read('data/config.ini')
        except Exception as e:
            DB.Logger.log.exception(e)

    def getSetting(self, option, section="DownBit"):
        return self.config[section][option]

    def getSettingInt(self, option, section="DownBit"):
        return int(self.config[section][option])

    def getSettingBool(self, option, section="DownBit"):
        return bool(self.config[section][option])

    def isDLTime(self):
        dltimes = self.getSetting('DownloadHours').split(',')
        dltimes = list(map(int, dltimes))
        time = int(datetime.now().strftime('%H'))
        if time in dltimes:
            return True
        else:
            return False


class Logger(object):
    def __init__(self):
        try:
            self.buildFailed = False
            os.chdir(os.path.dirname(os.path.abspath(__file__)))
            if not os.path.exists('data'):
                os.makedirs('data')
            file_name = "data/DownBit.log"
            if os.path.isfile(file_name + ".5"):
                os.remove(file_name + ".5")
            for i in range(4, 0, -1):
                if os.path.isfile('{}.{}'.format(file_name, i)):
                    os.rename('{}.{}'.format(file_name, i), '{}.{}'.format(file_name, i + 1))

            if os.path.isfile(file_name):
                os.rename(file_name, file_name + '.1')

            logFormatter = logging.Formatter(
                fmt='%(asctime)-10s %(levelname)-10s: %(module)s:%(lineno)-d -  %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S')

            self.log = logging.getLogger()
            self.log.setLevel(self.loglevel())

            fileHandler = logging.FileHandler(file_name)
            fileHandler.setFormatter(logFormatter)
            self.log.addHandler(fileHandler)
            consoleHandler = logging.StreamHandler()
            consoleHandler.setFormatter(logFormatter)
            self.log.addHandler(consoleHandler)
        except Exception as e:
            self.log.exception(e)

    @staticmethod
    def loglevel():
        config = ConfigParser()
        level = config.getSetting('LogLevel')
        if level == 'critical':
            return 50
        elif level == 'debug':
            return 10
        elif level == 'error':
            return 40
        else:
            return 20


class DownBit(object):
    def __init__(self):
        try:
            self.Logger = Logger()
            self.cfg = ConfigParser()
            self.Storage = Storage()
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            error = "{} {} {}".format(exc_type, fname, exc_tb.tb_lineno)
            print(str(type(e).__name__) + " : " + str(e), file=sys.stderr)
            print(error, file=sys.stderr)

    @staticmethod
    def clear(s):
        return re.sub('[^A-Za-z0-9 ]+', '', s).strip(" ")

    def exe(self, cmd):
        self.Logger.log.info('executing cmd - ' + cmd)
        try:
            f = os.popen(cmd)
            out = f.read()
            for line in out.split("\n"):
                self.Logger.log.info("output " + line)
            return out
        except Exception as e:
            self.Logger.log.exception(e)

    @staticmethod
    def isMatch(name, includes, excludes):
        ins_matched = False
        exes_matched = False
        brake_main = False
        for ins in includes.split('||'):
            for include in ins.split(','):
                if not include.lower().strip() in name.lower():
                    ins_matched = False
                    break
                else:
                    ins_matched = True
            if ins_matched:
                brake_main = True
            else:
                if brake_main:
                    break
                else:
                    continue
        if excludes != '':
            for exclude in excludes.split(','):
                if exclude.lower().strip() in name.lower():
                    exes_matched = True
                    break
                else:
                    exes_matched = False
        if ins_matched and not exes_matched:
            return True
        else:
            return False


DB = DownBit()
