import os
import time
from Core import DB
import eyed3
from urllib.request import urlretrieve as download

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
    if not os.path.exists(path):
        os.makedirs(path)
    EXE('nohup youtube-dl -o "{}{}.%(ext)s" {} -f {} --max-filesize {} -c --no-progress -v '
        '{} > "{}{}.txt" 2>&1 &'.format(path, name, url, quality, DB.cfg.getSetting('TwitchMaxFileSize'),
                                        arg, path, name))
    STORAGE.mark_downloaded(id)


def Spotify(id, name, img_url, path, album):
    TrackName = name.split(';;;')[0]
    ArtistName = name.split(';;;')[1].split(',')[0]
    EXE('youtube-dl "ytsearch:{0} {1} Audio" -o "{2}{0} - {1} [%(id)s].%(ext)s" -f 140 -c --no-progress --extract-audio'
        ' --audio-format mp3 --max-filesize 15m'.format(ArtistName, TrackName, path))
    song_path = [i for i in os.listdir(path) if '{} - {}'.format(ArtistName, TrackName) in i and i.endswith('.mp3')][0]
    saved_name = os.path.join(path, song_path)
    audiofile = eyed3.load(saved_name)
    audiofile.tag.artist = u"{}".format(name.split(';;;')[1])
    audiofile.tag.album = u"{}".format(album)
    audiofile.tag.album_artist = u"{}".format(ArtistName)
    dl_dir = "/tmp/{}-{}.jpg".format(TrackName, ArtistName)
    download(img_url, dl_dir)
    audiofile.tag.title = u"{}".format(TrackName)
    audiofile.tag.images.set(3, open(dl_dir, "rb").read(), "image/jpeg", u"")
    audiofile.tag.save()
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
                    ARG = row[10]
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
                        Spotify(ID, row[2], URL, Path, ARG)
                except Exception as e:
                    LOGGER.exception(e)
        LOGGER.debug("Waiting 120 seconds for next session")
        time.sleep(120)


if __name__ == '__main__':
    main()
