import os
import time
import urllib.request

import bs4 as bs

from Core import DB

LOGGER = DB.Logger.log
STORAGE = DB.Storage
EXE = DB.exe


def YoutubeDL(id, name, url, path, quality, arg, playlist=False):
    def getQuality(s):
        if s is '720p':
            return 22
        elif s is 'MP3':
            return 140
        else:
            return 18

    if not playlist:
        EXE('youtube-dl -o "{}{} [%(id)s].%(ext)s" {} -f {} --max-filesize {} -c --no-progress {}'.format(
            name, url, path, getQuality(quality), DB.cfg.getSetting('YoutubeMaxFileSize'), arg
        ))
    else:
        EXE(
            'youtube-dl -o "{}%(playlist)s/%(playlist_index)s-%(title)s_[%(id)s].%(ext)s" {} -f {} --max-filesize {} -c --no-progress {}'.format(
                name, url, path, getQuality(quality), DB.cfg.getSetting('YoutubeMaxFileSize'), arg
            ))
    STORAGE.mark_downloaded(id)


def Torrent(id, url, path, arg):
    EXE("deluge-console add '{}' -p '{}' {}".format(
        url, path, arg
    ))
    STORAGE.mark_downloaded(id)


def Direct(id, name, url, path, arg):
    os.mkdir(path)
    EXE("wget '{}' -O '{}{}' -c {}".format(
        url, path, name, arg
    ))
    if os.path.isfile(path + name):
        STORAGE.mark_downloaded(id)


def Weeb(id, name, url, path):
    os.mkdir(path)
    source = urllib.request.urlopen(url).read()
    soup = bs.BeautifulSoup(source, 'lxml')

    js_text = soup.find_all('div', class_='pcat-jwplayer')[0].find('script', type="text/javascript").text.split('\n')
    if 'http' in js_text[10].strip().strip('file: "').strip('",'):
        link = js_text[10].strip().strip('file: "').strip('",')
    else:
        link = js_text[6].strip().strip('file: "').strip('",')

    EXE("wget '{}' -O '{}{}.mp4' -c".format(
        link, path, name
    ))
    if os.path.isfile(path + name):
        STORAGE.mark_downloaded(id)

def main():
    LOGGER.info("Initiating RSS Downloader")
    while True:
        try:
            if True:
                for row in STORAGE.get('SELECT * FROM Downloads WHERE Downloaded = 0;'):
                    ID = row[0]
                    Quality = row[1]
                    Name = DB.clear(row[2])
                    Type = row[3]
                    URL = row[4]
                    Path = row[7]
                    ARG = row[9]
                    if Type == 'Youtube':
                        YoutubeDL(ID, Name, URL, Path, Quality, ARG)
                    elif Type == 'Youtube-Playlist':
                        YoutubeDL(ID, Name, URL, Path, Quality, ARG, playlist=True)
                    elif Type == 'Torrent':
                        Torrent(ID, URL, Path, ARG)
                    elif Type == 'Weeb':
                        Weeb(ID, URL, Path, ARG)
                    else:
                        Direct(ID, Name, URL, Path, ARG)
        except Exception as e:
            LOGGER.critical(str(type(e).__name__) + " : " + str(e))
            LOGGER.critical(DB.Logger.getError())
        LOGGER.debug("Waiting 120 seconds for next session")
        time.sleep(120)


if __name__ == '__main__':
    main()
