import urllib, urllib2, os, re, xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, sys, string, MormonChannel
from base64 import b64decode
from BeautifulSoup import BeautifulSoup
try:
    import StorageServer
except:
    import storageserverdummy as StorageServer 
try:
    import json
except:
    import simplejson as json


HANDLE = int(sys.argv[1])
PATH = sys.argv[0]
QUALITY_TYPES = {'0':'360p','1':'720p','2':'1080p'}

def make_request(url, headers=None):
        if headers is None:
            headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:15.0) Gecko/20100101 Firefox/15.0.1'}
        try:
            req = urllib2.Request(url,None,headers)
            response = urllib2.urlopen(req)
            data = response.read()
            return data
        except urllib2.URLError, e:
            print 'We failed to open "%s".' % url
            if hasattr(e, 'reason'):
                print 'We failed to reach a server.'
                print 'Reason: ', e.reason
            if hasattr(e, 'code'):
                print 'We failed with error code - %s.' % e.code

def get_params():
        param=[]
        paramstring=sys.argv[2]
        if len(paramstring)>=2:
            params=sys.argv[2]
            cleanedparams=params.replace('?','')
            if (params[len(params)-1]=='/'):
                params=params[0:len(params)-2]
            pairsofparams=cleanedparams.split('&')
            param={}
            for i in range(len(pairsofparams)):
                splitparams={}
                splitparams=pairsofparams[i].split('=')
                if (len(splitparams))==2:
                    param[splitparams[0]]=splitparams[1]
        return param



class Plugin():
    def __init__(self):
        self.cache = StorageServer.StorageServer("ldsvideos", 24)
        self.__settings__ = xbmcaddon.Addon(id='plugin.video.ldsvideos')
        self.__language__ = self.__settings__.getLocalizedString
        self.home = self.__settings__.getAddonInfo('path')
        self.icon = xbmc.translatePath( os.path.join( self.home, 'imgs', 'icon.png' ) )
        self.byufanart = xbmc.translatePath( os.path.join( self.home, 'imgs', 'byu-fanart.jpg' ) )
        self.byuicon = xbmc.translatePath( os.path.join( self.home, 'imgs', 'byu-icon.jpg' ) )
        self.mcicon = xbmc.translatePath( os.path.join( self.home, 'imgs', 'mc-icon.jpg' ) )
        self.mcfanart = xbmc.translatePath( os.path.join( self.home, 'imgs', 'mc-fanart.jpg' ) )
        self.fanart = xbmc.translatePath( os.path.join( self.home, 'imgs', 'gc-fanart.jpg' ) )
	self.ldsicon = self.icon
        self.dlpath = self.__settings__.getSetting('dlpath')

    def resolve_url(self,url):
        print "Resolving URL: %s" % url
        item = xbmcgui.ListItem(path=url)
        xbmcplugin.setResolvedUrl(HANDLE, True, item)

    def get_youtube_link(self,url):
        match=re.compile('https?://www.youtube.com/.+?v=(.+)').findall(url)
        link = 'plugin://plugin.video.youtube/?action=play_video&videoid='+ match[0]
        return link

    def add_link(self, thumb, info, urlparams, fanart=None):
        if not fanart: fanart = self.fanart
        u=PATH+"?"+urllib.urlencode(urlparams)
        item=xbmcgui.ListItem(urlparams['name'], iconImage="DefaultVideo.png", thumbnailImage=thumb)
        item.setInfo(type="Video", infoLabels=info)
        item.setProperty('IsPlayable', 'true')
        item.setProperty('Fanart_Image', fanart)
        try:
            if 'url' in urlparams:
                if urlparams['url'][-4:].upper() == '.MP4':
                    params = urllib.urlencode({'name':urlparams['name'],'url':urlparams['url'],'mode':str(15)})
                    item.addContextMenuItems([('Download','XBMC.RunPlugin(%s?%s)' % (PATH,params))])
        except:
            pass
            
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=item)

    def add_dir(self,thumb,info, urlparams,fanart=None):
        if not fanart: fanart = self.fanart
        u=PATH+"?"+urllib.urlencode(urlparams)
        item=xbmcgui.ListItem(urlparams['name'], iconImage="DefaultFolder.png", thumbnailImage=thumb)
        item.setInfo( type="Video", infoLabels=info )
        item.setProperty('Fanart_Image', fanart)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=item,isFolder=True)

    def download(self,name,url):
        dialog = xbmcgui.Dialog()
        if not self.dlpath:
            dialog.ok("Download", "You must set the download folder location in the", "plugin settings before you can download anything")
            return
        if dialog.yesno("Download", 'Download "%s"?' % name):
            xbmc.executebuiltin('XBMC.Notification("Download","Beginning download...")')
            try:
                req = urllib2.urlopen(url)
                CHUNK = 16 * 1024
                with open(os.path.join(self.dlpath,name + '.mp4'),'wb') as f:
                    for chunk in iter(lambda: req.read(CHUNK), ''):
                        f.write(chunk)
                xbmc.executebuiltin('XBMC.Notification("Download","Download complete")')
            except:
                print str(sys.exc_info())  
                xbmc.executebuiltin('XBMC.Notification("Download","Error downloading file")')
             
    def get_root_menu(self):
        self.add_dir(self.mcicon,{'Title':'Mormon Channel','Plot':'Watch and listen to content from the Mormon Channel'},{'name':'Mormon Channel','mode':14},self.mcfanart)
        self.add_dir(self.byuicon,{'Title':'BYU TV','Plot':'Watch videos from BYU TV'},
	    {'name':'BYU TV','mode':200},self.byufanart)
        self.add_dir(self.ldsicon,{'Title':'LDS.org','Plot':'Watch videos from LDS.org'},
	    {'name':'LDS.org','mode':100})

class BYUTV(Plugin):
    def __init__(self):
        Plugin.__init__(self)
        self.icon = self.byuicon
        self.apiurl = 'http://www.byutv.org/api/Television/'
        self.fanart = self.byufanart
        #self.quality = QUALITY_TYPES[self.__settings__.getSetting('byu_quality')]

    def get_menu(self):
        self.add_link(self.icon,{'Title':'BYU TV','Plot':'BYU TV Live HD'},{'name':'BYU TV Live','mode':6},self.fanart)
        self.add_dir(self.icon,{'Title':'Categories','Plot':'Watch BYU TV videos by category'},{'name':'Categories','mode':8},self.fanart)
        self.add_dir(self.icon,{'Title':'All Shows','Plot':'Watch all BYU TV shows sorted alphabetically'},
                {'name':'Shows A-Z','mode':9,'submode':1},self.fanart)
        self.add_dir(self.icon,{'Title':'Popular Episodes','Plot':'Watch the most viewed BYU TV episodes'},
                {'name':'Popular Episodes','mode':12},self.fanart)

    def play_byu_live(self):
        soup = BeautifulSoup(make_request(self.apiurl + 'GetLiveStreamUrl?context=Android%24US%24Release'))
        urlCode = soup.getText().strip('"')
        reqUrl = 'http://player.ooyala.com/sas/player_api/v1/authorization/embed_code/Iyamk6YZTw8DxrC60h0fQipg3BfL/'+urlCode+'?device=android_3plus_sdk-hook&domain=www.ooyala.com&supportedFormats=mp4%2Cm3u8%2Cwv_hls%2Cwv_wvm2Cwv_mp4'
        data = json.loads(make_request(reqUrl))
        for stream in data['authorization_data'][urlCode]['streams']:
            url = b64decode(stream['url']['data'])
            item = xbmcgui.ListItem(path=url)
            try:
                xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
            except:
                continue
    def get_categories(self):
        data = json.loads(make_request(self.apiurl + 'GetTVShowCategories?context=Android%24US%24Release'))
        for cat in data:
            self.add_dir(self.icon,{'Title':cat['name']},{'name':cat['name'],'mode':9})

    def get_shows(self,submode=None,cat=None):
        if not submode and cat:
            url = self.apiurl + 'GetShowsByCategory?context=Android%24US%24Release&categoryName=' + urllib.quote_plus(cat)
        if submode == 1:  #All shows
            url = self.apiurl + 'GetAllShows?context=Android%24US%24Release'
        data = json.loads(make_request(url))
        for show in data:
            desc = show['description']
            name = show['name']
            guid = show['guid']
            showCat = show['category']
            number = show['episodeCount']
            fanart = show['imageLarge']
            thumb = show['imageThumbnail']
            try: rating = show['rating']
            except: pass
            self.add_dir(thumb,{'Title':name,'Plot':desc,'Mpaa':rating},{'name':name,'mode':10,'guid':guid},fanart)

    def get_seasons(self,sguid):
        url = self.apiurl + "GetShowEpisodesByDate?context=Android%24US%24Release&showGuid=" + sguid
        data = json.loads(make_request(url))
        seasons = []
        fanart = []
        for episode in reversed(data):
            if episode['season'] not in seasons and episode['season']:
                seasons.append(episode['season'])
                fanart.append(episode['largeImage'])
        for index,season in enumerate(seasons):
            self.add_dir(self.icon,{'Title':season},{'name':season,'mode':11,'guid':sguid},fanart[index])
        if not seasons:
            self.get_episodes(None,sguid)

    def get_episodes(self,season,sguid,submode=None):
        if not submode: # By TV show
            url = self.apiurl + "GetShowEpisodesByDate?context=Android%24US%24Release&showGuid=" + sguid
        if submode == 1: # Weekly popular
            url = self.apiurl + "GetMostPopular?context=Android%24US%24Release&granularity=Week&numToReturn=500"
        if submode == 2: # Monly popular
            url = self.apiurl + "GetMostPopular?context=Android%24US%24Release&granularity=Month&numToReturn=500"
        if submode == 3: # Total popular
            url = self.apiurl + "GetMostPopular?context=Android%24US%24Release&granularity=Total&numToReturn=500"
        data = json.loads(make_request(url))
        index = 1
        for episode in reversed(data):
            if episode['season'] == season or submode or not episode['season']:
                desc = episode['description'].encode('utf8')
                name = episode['name'].encode('utf8')
                guid = episode['guid']
                ccurl = episode['captionFileUrl']
                fanart = episode['largeImage']
                date = episode['premiereDate']
                rating = episode['rating']
                duration = int(episode['runtime'])/60
                thumb = episode['thumbImage']
                u = episode['videoPlayUrl']
                show = episode['productionName'].encode('utf8')
                info = {'Title':name,'Plot':desc,'Premiered':date,'Season':season,
                        'TVShowTitle':show,'Mpaa':rating,'Year':date.split('-')[0]}
                if not submode:
                    name = '%02d - %s' % (index,name)
                else:
                    name = '%s - %s' % (show,name)
                self.add_link(thumb,info,{'name':name,'url':u,'mode':5},fanart)
                index = index + 1

    def get_popular(self):
        self.add_dir(self.icon,{'Title':'This Week','Plot':'Watch the most viewed episodes of this week'},
                {'name':'This Week','mode':11,'guid':'N/A','submode':1})
        self.add_dir(self.icon,{'Title':'This Month','Plot':'Watch the most viewed episodes of this month'},
                {'name':'This Month','mode':11,'guid':'N/A','submode':2})
        self.add_dir(self.icon,{'Title':'Ever','Plot':'Watch the most viewed episodes of all time'},
                {'name':'Ever','mode':11,'guid':'N/A','submode':3})

def pint(p, key):
    try:
        return int(p[key])
    except:
        return None

def purl(p, key):
    try:
        return urllib.unquote_plus(p[key])
    except:
        return None

def main():
    xbmcplugin.setContent(HANDLE, 'tvshows')
    params=get_params()
    
    url = purl(params, "url")
    name = purl(params, "name")
    mode=pint(params,"mode")
    submode=pint(params,"submode")

    #print "Mode: "+str(mode)
    #print "URL: "+str(url)
    #print "Name: "+str(name)

    lds = LDSORG()
    byu = BYUTV()
    plugin = Plugin()
    mc = MormonChannel.MormonChannel(plugin)

    if mode==None:
        plugin.get_root_menu()

    else:
      {100: lambda:lds.get_menu(),
       200: lambda:byu.get_menu(),
       2: lambda: lds.get_categories(url),
       3: lambda: lds.resolve_brightcove_req(url),
       4: lambda: lds.get_video_list(url),
       5: lambda: plugin.resolve_url(url),
       6: lambda: byu.play_byu_live(),
       7: lambda: lds.get_conferences(submode,url,name),
       8: lambda: byu.get_categories(),
       9: lambda: byu.get_shows(submode,name),
       10: lambda: byu.get_seasons(purl(params, "guid")),
       11: lambda: byu.get_episodes(name,purl(params, "guid"),submode),
       12: lambda: byu.get_popular(),
       13: lambda: lds.get_featured(),

       # Handle all BYUTV modes
       14: lambda: mc.broker(params),
       15: lambda: plugin.download(name,url)
      }[mode]()

    xbmcplugin.endOfDirectory(HANDLE)


if __name__ == '__main__':
    main()

