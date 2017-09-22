from DownBit import logger, database, dltime, exe, config
import bs4 as bs
import urllib.request
import time


def getVidLink(url):
    source = urllib.request.urlopen(url).read()
    soup = bs.BeautifulSoup(source, 'lxml')
    for div in soup.find_all('div', class_='pcat-jwplayer'):
        js_text = div.find('script', type="text/javascript").text.split('\n')
        link = js_text[10].strip().strip('file: "').strip('",')
        if 'http' in link:
            return link
        else:
            return js_text[6].strip().strip('file: "').strip('",')


def checkName(link, names):
    for name in names:
        if name in link:
            continue
        else:
            return False
    return True


def getEpisodeLink(URL, names):
    source = urllib.request.urlopen(URL).read()
    soup = bs.BeautifulSoup(source, 'lxml')
    for url in soup.find_all('a'):
        if checkName(url.get('href'), names):
            return url.get('href')


db = database()
RssRefreshTime = int(config('DownBit', 'RssRefreshTime'))


def checkEpisode(url, keyword, season, episode, name):
    name = '{} S{}E{}'.format(name, season.zfill(2), episode.zfill(2))
    logger.debug("Getting link for " + name)
    episodeLink = getEpisodeLink(url, keyword.split(';') + ['season-' + season + '-', 'episode-' + episode + '-'])
    return episodeLink


def weeb():
    logger.info("Weeb Plugin Initiating")
    logger.debug("Connecting to Database to Update weeb")
    while 1:
        try:
            for row in db.read("SELECT * FROM weeb"):
                id_num = row[0]
                url = row[2]
                keyword = row[3]
                season = row[4]
                episode = row[5]
                name = row[1]

                episodeLink = checkEpisode(url, keyword, str(season), str(episode), name)
                if episodeLink is None:
                    episodeLink = checkEpisode(url, keyword, str(season), str(episode + 1), name)
                    if episodeLink is None:
                        episodeLink = checkEpisode(url, keyword, str(season + 1), str(1), name)
                        if episodeLink is None:
                            logger.debug("Nothing found for " + '{} S{}E{}'.format(name, str(season).zfill(2),
                                                                                   str(episode).zfill(2)))
                            logger.debug(
                                "Skipping " + '{} S{}E{}'.format(name, str(season).zfill(2), str(episode).zfill(2)))
                        else:
                            db.addtodownload('{} S{}E{}'.format(name, str(season + 1).zfill(2), str(0).zfill(2)),
                                             "weeb-dl", episodeLink, '{}Season {}/'.format(row[6], season), '')
                            db.update_lastmatch('weeb', 'Episode', id_num, 0)
                            db.update_lastmatch('weeb', 'Season', id_num, season + 1)
                    else:
                        db.addtodownload('{} S{}E{}'.format(name, str(season).zfill(2), str(episode + 1).zfill(2)),
                                         "weeb-dl", episodeLink, '{}Season {}/'.format(row[6], season), '')
                        db.update_lastmatch('weeb', 'Episode', id_num, episode + 2)
                else:
                    db.addtodownload('{} S{}E{}'.format(name, str(season).zfill(2), str(episode).zfill(2)), "weeb-dl",
                                     episodeLink, '{}Season {}/'.format(row[6], season), '')
                    db.update_lastmatch('weeb', 'Episode', id_num, episode + 1)


        except Exception as e:
            logger.critical(str(type(e).__name__) + " : " + str(e))
            time.sleep(1)

        try:
            if dltime():
                for row in db.read("SELECT * FROM downloads WHERE method = 'weeb-dl'"):
                    if row[11] == "downloading":
                        url = getVidLink(row[3])
                        exe("wget '{}' -O '{}{}.mp4' -c".format(url, row[7], row[1]))
                        db.mark_downloaded(row[3])
        except Exception as e:
            logger.critical(str(type(e).__name__) + " : " + str(e))
            time.sleep(1)

        logger.debug("Waiting {} for next session".format(RssRefreshTime))
        time.sleep(RssRefreshTime)


if __name__ == '__main__':
    weeb()
