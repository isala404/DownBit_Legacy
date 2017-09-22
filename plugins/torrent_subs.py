import feedparser
from DownBit import logger, database, dltime, clear, exe, config, uniqifie
import time

db = database()
RssRefreshTime = int(config('DownBit', 'RssRefreshTime'))


def checklast(name, url):
    id_ = db.getid('youtube_subs', name, 'youtuber')
    out = db.lastmatch('youtube_subs', 'last_video', id_, url)
    return out


def good_torrent(name, includes, excludes):
    for include in includes:
        if include.lower() in name:
            continue
        else:
            return False
    for exclude in excludes:
        if exclude.lower() in name:
            return False
    return True


def torrent_subs():
    logger.info("Torrent RSS Plugin Initiating")
    while 1:
        try:
            for row in db.read("SELECT * FROM rss_subs"):
                url = row[2]
                d = feedparser.parse(url)
                for entry in d['entries']:
                    includes = row[4].split(';')
                    excludes = row[5].split(';')

                    if good_torrent(entry['title'].lower(), includes, excludes):
                        if entry['link'] != row[6]:
                            db.addtodownload(entry['title'], "torrent-subs", entry['link'], row[3], '')
                            db.update_lastmatch('rss_subs', 'last_match', row[0], entry['link'])
                        break

            if dltime():
                for row in db.read("SELECT * FROM downloads WHERE method = 'torrent-subs'"):
                    if row[11] == "downloading":
                        exe("deluge-console add '{}' -p '{}' ".format(row[3], row[7]))
                        db.mark_downloaded(row[3])

            logger.debug("Waiting {} for next session".format(RssRefreshTime))
            time.sleep(int(RssRefreshTime))

        except Exception as e:
            logger.critical(str(type(e).__name__) + " : " + str(e))


if __name__ == '__main__':
    torrent_subs()
