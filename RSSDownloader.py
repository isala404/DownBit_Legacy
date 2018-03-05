import os
import time
from Core import DB

LOGGER = DB.Logger.log
STORAGE = DB.Storage
EXE = DB.exe


def YoutubeDL(id, name, url, path, quality, arg, playlist=False):
    def getQuality(s):
        if s == '720p':
            return 22
        elif s == 'MP3':
            return 140
        elif s == '480p':
            return '"bestvideo[height<=480][ext=mp4]+bestaudio/[height <=? 480]"'
        else:
            LOGGER.info("{} is a Unknown Quality setting Quality to 360p".format(s))
            return 18

    if not playlist:
        EXE('youtube-dl -o "{}{} [%(id)s].%(ext)s" {} -f {} --max-filesize {} -c --no-progress {}'.format(
            path, name, url, getQuality(quality), DB.cfg.getSetting('YoutubeMaxFileSize'), arg
        ))
    else:
        EXE(
            'youtube-dl -o "{}%(playlist)s/%(playlist_index)s-%(title)s_[%(id)s].%(ext)s" {} -f {} --max-filesize {} '
            '-c --no-progress {}'.format(
                path, url, getQuality(quality), DB.cfg.getSetting('YoutubeMaxFileSize'), arg
            ))
    STORAGE.mark_downloaded(id)


def Twitch(id, name, url, path, quality, arg):
    EXE('screen -dmS Twitch-dl youtube-dl -o "{}{}.%(ext)s" {} -f {} --max-filesize {} -c --no-progress -v {}'.format(
        path, name, url, quality, DB.cfg.getSetting('TwitchMaxFileSize'), arg
    ))
    STORAGE.mark_downloaded(id)


def Spotify(id, name, url, path, album):
    EXE('youtube-dl "ytsearch:{} {} Audio" -o "{}{} - {} [%(id)s].%(ext)s" -f 140 -c --no-progress --extract-audio'
        ' --audio-format mp3'.format(url, name, path, url.split(',')[0], name))

    EXE('id3tool -t "{}" -r "{}" -a "{}" "{}{}"'.format(
        name, url.split(',')[0], album, path,
        [i for i in os.listdir(path) if '{} - {}'.format(url.split(',')[0], name) in i][0]
    ))
    STORAGE.mark_downloaded(id)


def Torrent(id, url, path, arg):
    EXE('deluge-console add "{}" -p "{}" {}'.format(
        url, path, arg
    ))
    STORAGE.mark_downloaded(id)


def Direct(id, name, url, path, arg):
    if '.' not in name[-5:] and '.' in url[-5:]:
        name += '.' + url.split('.')[-1]
    if not os.path.isdir(path):
        os.makedirs(path)
    EXE('wget "{}" -O "{}{}" -c {}'.format(
        url, path, name, arg
    ))
    if path.endswith('.mp3'):
        EXE('id3tool -t "{}" -r "{}" "{}{}"'.format(
            name, name.split(' ')[0], path, name
        ))
    STORAGE.mark_downloaded(id)


def main():
    LOGGER.info("Initiating RSS Downloader")
    while True:
        if DB.cfg.isDLTime():
            for row in STORAGE.get('SELECT * FROM Downloads WHERE Downloaded = 0;'):
                try:
                    ID = row[0]
                    Name = DB.clear(row[2])
                    Type = row[3]
                    URL = row[4]
                    Path = row[7]
                    ARG = row[9]
                    if Type == 'Youtube':
                        Quality = STORAGE.get('SELECT Quality FROM RSSFeeds WHERE ID = (?);', row[1])[0][0]
                        YoutubeDL(ID, Name, URL, Path, Quality, ARG)
                    elif Type == 'Youtube-Playlist':
                        Quality = STORAGE.get('SELECT Quality FROM RSSFeeds WHERE ID = (?);', row[1])[0][0]
                        YoutubeDL(ID, Name, URL, Path, Quality, ARG, playlist=True)
                    elif Type == 'Torrent':
                        Torrent(ID, URL, Path, ARG)
                    elif Type == 'Twitch':
                        Quality = STORAGE.get('SELECT Quality FROM RSSFeeds WHERE ID = (?);', row[1])[0][0]
                        Twitch(ID, Name, URL, Path, Quality, ARG)
                    elif Type == 'Direct':
                        Direct(ID, Name, URL, Path, ARG)
                    elif Type == 'SoundCloud':
                        Direct(ID, Name, URL, Path, ARG)
                    elif Type == 'Spotify':
                        Spotify(ID, Name, URL, Path, ARG)

                except Exception as e:
                    LOGGER.critical(str(type(e).__name__) + " : " + str(e))
                    LOGGER.critical(DB.Logger.getError())
                    pass
        LOGGER.debug("Waiting 120 seconds for next session")
        time.sleep(120)


if __name__ == '__main__':
    main()
