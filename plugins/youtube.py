import feedparser
from DownBit import logger, database, dltime, clear, exe, config
import time

db = database()
RssRefreshTime = int(config('DownBit', 'RssRefreshTime'))


def checklast(name, url):
    id = db.getid('youtube_subs', name, 'youtuber')
    out = db.lastmatch('youtube_subs', 'last_video', id, url)
    return out


def youtube():
    logger.info("Youtube Plugin Initiating")
    logger.debug("Connecting to Database to Update youtube_subs")
    while 1:
        try:
            for row in db.read("SELECT * FROM youtube_subs"):
                logger.debug("Getting Info about " + row[1])
                d = feedparser.parse('https://www.youtube.com/feeds/videos.xml?channel_id=' + row[2])
                link = d['entries'][0]['link']
                title = clear(d['entries'][0]['title'])
                if not checklast(row[1], link):
                    logger.debug("Adding Data to DB ")
                    if row[3] == "mp4":
                        db.addtodownload(title, "yt-mp4", link, row[5] + "/", d['entries'][0]['author'])
                        db.update_lastmatch('youtube_subs', 'last_video', row[0], link)
                    if row[3] == "mp3":
                        db.addtodownload(title, "yt-mp3", link, row[5] + "/", d['entries'][0]['author'])
                        db.update_lastmatch('youtube_subs', 'last_video', row[0], link)
                else:
                    logger.debug("Info is already added or Downloaded")
        except Exception as e:
            logger.critical(str(type(e).__name__) + " : " + str(e))
            time.sleep(1)
        try:
            for row in db.read(
                    "SELECT * FROM downloads WHERE(method = 'yt-mp4' OR method = 'yt-mp3' OR method = 'yt-pl')"):
                if dltime():
                    if row[11] == "downloading":
                        if row[2] == "yt-mp4":
                            out = exe(
                                'youtube-dl -o "{}{} [%(id)s].%(ext)s" {} -f 22 --max-filesize {} -c --no-progress'.format(
                                    row[7], clear(row[1]), row[3], config('Youtube', 'MaxFileSize')))
                            if "File is larger than max-filesize" in out:
                                logger.info("Lowering Quality Due to Large File Size")
                                exe(
                                    'youtube-dl -o "{}{} [%(id)s].%(ext)s" {} -f 18 -c --no-progress'.format(
                                        row[7], clear(row[1]), row[3]))
                            db.mark_downloaded(row[3])
                        elif row[2] == "yt-mp3":
                            exe(
                                'youtube-dl -o "{}{} [%(id)s].%(ext)s" {} -f 140 -c --no-progress'.format(
                                    row[7], clear(row[1]), row[3]))
                            db.mark_downloaded(row[3])
                        elif row[2] == "yt-pl":
                            exe(
                                'youtube-dl -o "{}%(playlist)s/%(playlist_index)s-%(title)s_[%(id)s].%(ext)s" {} -f 22 -c --no-progress {}'.format(
                                    row[7], row[3], row[10]))
                            db.mark_downloaded(row[3])

            logger.debug("Waiting {} for next session".format(RssRefreshTime))
            time.sleep(int(RssRefreshTime))
        except Exception as e:
            logger.critical(str(type(e).__name__) + " : " + str(e))
            time.sleep(1)

if __name__ == '__main__':
    youtube()
