import time
import urllib.request

import bs4 as bs
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
        LOGGER.critical(str(type(e).__name__) + " : " + str(e))
        LOGGER.critical(DB.Logger.getError())


def Torrent(id, url, includes, excludes, lastmatch, path):
    try:
        d = feedparser.parse(url)
        lastmatch_ = -1
        for i, entry in enumerate(d['entries']):
            if str(lastmatch) == str(entry['link']):
                break
            lastmatch_ = i
        for i in range(lastmatch_, -1, -1):
            if DB.isMatch(d['entries'][i]['title'], includes, excludes):
                STORAGE.addtodownload(id, d['entries'][i]['title'], 'Torrent', d['entries'][i]['link'], path)
                STORAGE.update_lastmatch(id, d['entries'][i]['link'])
    except Exception as e:
        LOGGER.error(
            'There was error while processing this data => {} {} {} {} {} {}'.format(id, url, includes, excludes,
                                                                                     lastmatch, path))
        LOGGER.critical(str(type(e).__name__) + " : " + str(e))
        LOGGER.critical(DB.Logger.getError())


def Weeb(id, name, url, includes, excludes, lastmatch, path):
    def getEpisodeURL(seriesURL, _includes, _excludes):
        source = urllib.request.urlopen(seriesURL).read()
        soup = bs.BeautifulSoup(source, 'lxml')
        for _URL in soup.find_all('a'):
            if DB.isMatch(_URL.get('href'), _includes, _excludes):
                return _URL.get('href')
        return False

    def getLast(_lastmatch, _ins, s=0, _e=0):
        _Season = int(_lastmatch[1:3]) + s
        _Episode = int(_lastmatch[-2:]) + _e
        if _e is False:
            _Episode = 1
        _ins += ',season-' + str(_Season) + ',episode-' + str(_Episode) + '-'
        return _Season, _Episode, _ins

    try:
        if lastmatch[0] == 'S':
            Season, Episode, ins = getLast(lastmatch, includes, _e=1)
            link = getEpisodeURL(url, ins, excludes)
            if not link:
                Season, Episode, ins = getLast(lastmatch, includes, _e=2)
                link = getEpisodeURL(url, ins, excludes)
                if not link:
                    Season, Episode, ins = getLast(lastmatch, includes, s=1, _e=False)
                    link = getEpisodeURL(url, ins, excludes)
                    if not link:
                        return False
            name += 'S{}E{}'.format(str(Season).zfill(2), str(Episode).zfill(2))
            STORAGE.update_lastmatch(id, 'S{}E{}'.format(str(Season).zfill(2), str(Episode).zfill(2)))
        else:
            Episode = int(lastmatch[1:])
            includes += ',episode-' + str(Episode + 1)
            link = getEpisodeURL(url, includes, excludes)
            if not link:
                includes += ',episode-' + str(Episode + 2) + '-'
                link = getEpisodeURL(url, includes, excludes)
                if not link:
                    return False
            Episode = str(Episode + 1).zfill(2)
            STORAGE.update_lastmatch(id, 'E{}'.format(Episode))

            name += 'E{}'.format(Episode)

        STORAGE.addtodownload(id, name, 'Weeb', link, path)
    except Exception as e:
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
            elif Type == 'Weeb':
                Weeb(ID, Name, URL, Includes, Excludes, LastMatch, Path)
            elif Type == 'Torrent':
                Torrent(ID, URL, Includes, Excludes, LastMatch, Path)

        LOGGER.debug("Waiting {} for next session".format(DB.cfg.getSettingInt('RssRefreshTime')))
        time.sleep(DB.cfg.getSettingInt('RssRefreshTime'))


if __name__ == '__main__':
    main()
