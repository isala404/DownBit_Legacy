import time
import feedparser

from Core import DB

LOGGER = DB.Logger.log
STORAGE = DB.Storage


def Youtube(id, url, includes, excludes, lastmatch, path):
    try:
        d = feedparser.parse(url)
        lastmatch_ = -1
        for i, entry in enumerate(d['entries']):
            if entry['link'] == lastmatch:
                break
            lastmatch_ = i
        if lastmatch_ > 6:
            lastmatch_ = 0
        for i in range(lastmatch_, -1, -1):
            if includes is None:
                includes_ = d['entries'][i]['title']
            else:
                includes_ = includes
            if DB.isMatch(d['entries'][i]['title'], includes_, excludes):
                STORAGE.addtodownload(id, d['entries'][i]['title'], 'Youtube', d['entries'][i]['link'], path)
                STORAGE.update_lastmatch(id, d['entries'][i]['link'])
    except Exception as e:
        LOGGER.error(
            'There was error while processing this data => {} {} {} {} {} {}'.format(id, url, includes, excludes,
                                                                                     lastmatch, path))
        LOGGER.exception(e)


def Twitch(id, url, includes, excludes, lastmatch, path):
    try:
        d = feedparser.parse(url)
        lastmatch_ = -1
        for i, entry in enumerate(d['entries']):
            if entry['link'] == lastmatch:
                break
            lastmatch_ = i
        if lastmatch_ > 3:
            lastmatch_ = 0
        for i in range(lastmatch_, -1, -1):
            if includes is None:
                includes_ = d['entries'][i]['title']
            else:
                includes_ = includes
            if DB.isMatch(d['entries'][i]['title'], includes_, excludes):
                STORAGE.addtodownload(id, d['entries'][i]['title'], 'Twitch', d['entries'][i]['link'], path)
                STORAGE.update_lastmatch(id, d['entries'][i]['link'])
    except Exception as e:
        LOGGER.error(
            'There was error while processing this data => {} {} {} {} {} {}'.format(id, url, includes, excludes,
                                                                                     lastmatch, path))
        LOGGER.exception(e)


def Torrent(id, url, includes, excludes, lastmatch, path):
    try:
        d = feedparser.parse(url)
        lastmatch_ = -1
        for i, entry in enumerate(d['entries']):
            if str(lastmatch) == str(entry['link']):
                break
            lastmatch_ = i
        if lastmatch_ > 6:
            lastmatch_ = 0
        for i in range(lastmatch_, -1, -1):
            if DB.isMatch(d['entries'][i]['title'], includes, excludes):
                STORAGE.addtodownload(id, d['entries'][i]['title'], 'Torrent', d['entries'][i]['link'], path)
                STORAGE.update_lastmatch(id, d['entries'][i]['link'])
    except Exception as e:
        LOGGER.error(
            'There was error while processing this data => {} {} {} {} {} {}'.format(id, url, includes, excludes,
                                                                                     lastmatch, path))
        LOGGER.exception(e)


def Spotify(id, url, lastmatch, path):
    try:
        d = feedparser.parse(url)
        lastmatch_ = -1
        for i, entry in enumerate(d['entries']):
            if str(lastmatch) == str(entry['count']):
                break
            lastmatch_ = i
        for i in range(lastmatch_, -1, -1):
            STORAGE.addtodownload(id, d['entries'][i]['trackname'], 'Spotify', d['entries'][i]['artistname'],
                                  path, arg=d['entries'][i]['albumname'])
            STORAGE.update_lastmatch(id, d['entries'][i]['count'])
    except Exception as e:
        LOGGER.exception(e)


def YTS(id, url, includes, excludes, lastmatch, path):
    try:
        d = feedparser.parse(url)
        lastmatch_ = -1
        for i, entry in enumerate(d['entries']):
            if str(lastmatch) == str(entry['links'][1]['href']):
                break
            lastmatch_ = i
        for i in range(lastmatch_, -1, -1):
            if DB.isMatch(d['entries'][i]['title'], includes, excludes):
                STORAGE.addtodownload(id, d['entries'][i]['title'], 'Torrent', d['entries'][i]['links'][1]['href'],
                                      path)
                STORAGE.update_lastmatch(id, d['entries'][i]['links'][1]['href'])
    except Exception as e:
        LOGGER.error(
            'There was error while processing this data => {} {} {} {} {} {}'.format(id, url, includes, excludes,
                                                                                     lastmatch, path))
        LOGGER.exception(e)


def SoundCloud(id, url, includes, excludes, lastmatch, path):
    try:
        idx = 1
        d = feedparser.parse(url)
        lastmatch_ = -1
        for i, entry in enumerate(d['entries']):
            try:
                if entry['links'][idx]['href'] == lastmatch:
                    break
                lastmatch_ = i
            except IndexError:
                idx = 0
                if entry['links'][idx]['href'] == lastmatch:
                    break
                lastmatch_ = i

        for i in range(lastmatch_, -1, -1):
            if includes is None:
                includes_ = d['entries'][i]['title']
            else:
                includes_ = includes
            if DB.isMatch(d['entries'][i]['title'], includes_, excludes):
                STORAGE.addtodownload(id, d['entries'][i]['title'], 'SoundCloud', d['entries'][i]['links'][idx]['href'],
                                      path)
                STORAGE.update_lastmatch(id, d['entries'][i]['links'][idx]['href'])
    except Exception as e:
        LOGGER.error(
            'There was error while processing this data => {} {} {} {} {} {}'.format(id, url, includes, excludes,
                                                                                     lastmatch, path))
        LOGGER.critical(str(type(e).__name__) + " : " + str(e))
        LOGGER.critical(DB.Logger.getError())


def main():
    LOGGER.info("Initiating RSS Reader")
    while True:
        for row in STORAGE.get("SELECT * FROM RSSFeeds"):
            ID = row[0]
            Name = row[1]
            URL = row[2]
            Path = row[3]
            Includes = row[4]
            Excludes = row[5]
            Type = row[6]
            LastMatch = row[8]
            if Type == 'Youtube':
                Youtube(ID, URL, Includes, Excludes, LastMatch, Path)
            elif Type == 'Torrent':
                Torrent(ID, URL, Includes, Excludes, LastMatch, Path)
            elif Type == 'Twitch':
                Twitch(ID, URL, Includes, Excludes, LastMatch, Path)
            elif Type == 'YTS':
                YTS(ID, URL, Includes, Excludes, LastMatch, Path)
            elif Type == 'SoundCloud':
                SoundCloud(ID, URL, Includes, Excludes, LastMatch, Path)
            elif Type == 'Spotify':
                Spotify(ID, URL, LastMatch, Path)

        LOGGER.debug("Waiting {} for next session".format(DB.cfg.getSettingInt('RssRefreshTime')))
        time.sleep(DB.cfg.getSettingInt('RssRefreshTime'))


if __name__ == '__main__':
    main()
