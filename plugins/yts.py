import feedparser
from DownBit import logger, database, dltime, exe, config
import time

db = database()
RssRefreshTime = int(config('DownBit', 'RssRefreshTime'))


def yts():
    logger.info("YTS Plugin Initiating")
    while 1:
        try:
            movies = db.read("SELECT id,name,quality,path FROM yts")
            logger.debug("Reading YTS RSS Feed")
            d = feedparser.parse('https://yts.ag/rss')
            for entry in d['entries']:
                title = entry['title']
                link = entry['links'][1]['href']
                for movie in movies:
                    if movie[1].lower() in title.lower() and movie[2] in title:
                        db.addtodownload(title, "torrent-yts", link, movie[3], '')
                        db.write("DELETE from yts WHERE id = {}".format(int(movie[0])))

            if dltime():
                for row in db.read("SELECT * FROM downloads WHERE method = 'torrent-yts'"):
                    if row[11] == "downloading":
                        exe("deluge-console add '{}' -p '{}' ".format(row[3], row[7]))
                        db.mark_downloaded(row[3])

            logger.debug("Waiting {} for next session".format(RssRefreshTime))
            time.sleep(int(RssRefreshTime))

        except Exception as e:
            logger.critical(str(type(e).__name__) + " : " + str(e))


if __name__ == '__main__':
    yts()
