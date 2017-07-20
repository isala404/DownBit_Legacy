import feedparser
from DownBit import logger,database,dltime,clear,exe,config,uniqifie
import time

db = database()
RssRefreshTime = int(config('DownBit','RssRefreshTime'))

def checklast(name,url):
	id = db.getid('youtube_subs',name,'youtuber')
	out = db.lastmatch('youtube_subs', 'last_video', id, url)
	return out

def good_torrent(name,includes,excludes):
	for include in includes:
		if include.lower() in name:
			#print(include,'('+type(include)+')', 'is in', name, '('+type(name)+')')
			#print("{}({}) is in {}({})".format(include, type(include), name, type(name)))
			continue
		else:
			#print("{}({}) is not in {}({})".format(include, type(include), name, type(name)))
			return False
	for exclude in excludes:
		if exclude.lower() in name:
			print('fuck')
			return False
	#print('it true bro')
	return True
def torrent_subs():
	logger.info("Torrent RSS Plugin Initiating")
	logger.debug("Connecting to Database to Update Youtubers")
	while 1:
		try:
			urls = uniqifie(db.read("SELECT url FROM rss_subs"))
			torrents_subs = db.read("SELECT * FROM rss_subs")
			for url in urls:
				url = url[0]
				d = feedparser.parse(url)
				for row in torrents_subs:
					if row[2] in url:
						for entry in d['entries']:

							includes = row[4].split(';')
							try:
								excludes = row[5].split(';')
							except:
								excludes = ["djfioefioefjeifhikfdifhewiqe0jkweolfjdfjeiojwediowhdfjrihg","dfdswerjlksdwlewlmdwoaaerwewerfwew"]

							if  good_torrent(entry['title'].lower(),includes,excludes):
								if entry['link'] != row[6]:
									db.addtodownload(entry['title'], "torrent-subs", entry['link'], row[3], '')
									db.update_lastmatch('rss_subs', 'last_match', row[0], entry['link'])


			if dltime():
				for row in db.read("SELECT * FROM downloads WHERE method = 'torrent-subs'"):
					if row[11] == "downloading":
						exe("deluge-console add '{}' -p '{}' ".format(row[3],row[7]))
						db.mark_downloaded(row[3])



			logger.debug("Waiting {} for next session".format(RssRefreshTime))
			time.sleep(int(RssRefreshTime))


		except Exception as e:
			logger.critical(str(type(e).__name__) + " : " + str(e))

if __name__== '__main__':
	torrent_subs()