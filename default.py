#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2011 XBMC-Russia, HD-lab Team, E-mail: dev@hd-lab.ru
#   Writer (c) 12/03/2011, Kostynoy S.A., E-mail: seppius2@gmail.com
#
#   This Program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2, or (at your option)
#   any later version.
#
#   This Program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; see the file COPYING.  If not, write to
#   the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#   http://www.gnu.org/licenses/gpl.html
import sys
import re
import os
import urllib
import urllib2
import json

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

icon = xbmc.translatePath(os.path.join(os.getcwd().replace(';', ''), 'icon.png'))
h = int(sys.argv[1])

Addon = xbmcaddon.Addon(id='plugin.video.tvrain.ru')
__language__ = Addon.getLocalizedString

addon_icon = Addon.getAddonInfo('icon')
addon_fanart = Addon.getAddonInfo('fanart')
addon_path = Addon.getAddonInfo('path')
addon_type = Addon.getAddonInfo('type')
addon_id = Addon.getAddonInfo('id')
addon_author = Addon.getAddonInfo('author')
addon_name = Addon.getAddonInfo('name')
addon_version = Addon.getAddonInfo('version')

headers = {
	'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:36.0) Gecko/20100101 Firefox/36.0',
	'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
	'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
	'Accept-Charset': 'utf-8, utf-16, *;q=0.1',
	'Referer': 'https://tvrain.ru/'
}

headers2 = [
	('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:36.0) Gecko/20100101 Firefox/36.0'),
	('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
	('Accept-Language', '	ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3'),
	('Accept-Charset', 'utf-8, utf-16, *;q=0.1'),
	('Referer', 'https://tvrain.ru/'),
	('X-Requested-With', 'XMLHttpRequest')
]

import cookielib

if sys.platform == 'win32' or sys.platform == 'win64':
	cook_file = xbmc.translatePath('special://temp/' + 'tvrain.cookies').decode('utf-8')
else:
	cook_file = xbmc.translatePath('special://temp/' + 'tvrain.cookies')


def showMessage(heading, message, times=3000, pics=addon_icon):
	try: xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s, "%s")' % (heading.encode('utf-8'), message.encode('utf-8'), times, pics.encode('utf-8')))
	except Exception, e:
		xbmc.log('[%s]: showMessage: Transcoding UTF-8 failed [%s]' % (addon_id, e), 2)
		try: xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s, "%s")' % (heading, message, times, pics))
		except Exception, e:
			xbmc.log('[%s]: showMessage: exec failed [%s]' % (addon_id, e), 3)


def do_login(urlOpener, cookiejar):
	urlOpener.addheaders = headers2
	request = urllib2.Request("https://tvrain.ru/login/")
	url = urlOpener.open(request)
	http = url.read()
	r1 = re.compile('<input\s.*?value="(.+?)"\s.*?name="YII_CSRF_TOKEN"', re.DOTALL).findall(http)

	urlOpener.addheaders = []
	values = {'yt0': 'Войти', 'User[email]': Addon.getSetting('login'), 'User[password]': Addon.getSetting('password'),
			  'YII_CSRF_TOKEN': r1[0]}
	data = urllib.urlencode(values)
	request = urllib2.Request("https://tvrain.ru/login/", data, headers)
	url = urlOpener.open(request)
	http = url.read()
	auth = False
	for cook in cookiejar:
		if cook.name == 'RAIN_PROJECT':
			auth = True
			Addon.setSetting('auth', '1')
		print "%s=%s" % (cook.name, cook.value)
	cookiejar.save(cook_file)
	return auth


def GET(targeturl, post=None):
	cookiejar = cookielib.MozillaCookieJar()
	urlOpener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookiejar))
	auth = False
	if Addon.getSetting('auth') == '1':
		try:
			cookiejar.load(cook_file)
			for cook in cookiejar:
				if cook.name == 'RAIN_PROJECT': auth = True
		except:
			auth = do_login(urlOpener, cookiejar)
	if Addon.getSetting('auth') != '1' and Addon.getSetting('login'):
		auth = do_login(urlOpener, cookiejar)
	if not auth:
		Addon.setSetting('auth', '0')
	else:
		Addon.setSetting('auth', '1')
	request = urllib2.Request(url=targeturl, data=post, headers=headers)
	try:
		url = urlOpener.open(request)
		http = url.read()
		url.close()
	except Exception, e:
		showMessage('Ошибка соединения', e)
		sys.exit()
	return http


def getitems(params):
	try:
		http = GET('https://tvrain.ru/live/')
		#print http
		r1 = re.compile("new LivePlayer\\('liveplayer', \\$\\.parseJSON\\('(.+)'").findall(http);
		#r1 = re.compile('streams = (\[.*?\])', re.DOTALL).findall(http)
		if len(r1) > 0:
			jstr = r1[0]
			#jstr = re.sub('\\s', '', r1[0]).replace("'", '"')
			xbmc.log('Json:' + jstr)
			stream_urls = [json.loads(jstr)]
			xbmc.log("Stream urls: " + str(stream_urls), 1)
			listing = []
			for url in stream_urls:
				# Set additional info for the list item.
				title = 'Auto quality'				
				r2 = re.compile('([0-9]+p)_tvrain').findall(url)
				if len(r2) > 0:
					title = r2[0]
				list_item = xbmcgui.ListItem(label=title)
				list_item.setInfo('video', {'title': title})
				# Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
				# Here we use the same image for all items for simplicity's sake.
				# In a real-life plugin you need to set each image accordingly.
				#list_item.setArt({'thumb': video['thumb'], 'icon': video['thumb'], 'fanart': video['thumb']})
				# Set 'IsPlayable' property to 'true'.
				# This is mandatory for playable items!
				list_item.setProperty('IsPlayable', 'true')
				listing.append((url, list_item, False))
			
			xbmcplugin.addDirectoryItems(h, listing, len(listing))
			xbmcplugin.endOfDirectory(h)
			#play_item = xbmcgui.ListItem(path=stream_url)
			# Pass the item to the Kodi player.
			#xbmcplugin.setResolvedUrl(h, True, listitem=play_item)
			return
	except Exception, e:
		xbmc.log(str(e), 1)
		pass


def get_params(paramstring):
	param = []
	if len(paramstring) >= 2:
		params = paramstring
		cleanedparams = params.replace('?', '')
		if (params[len(params) - 1] == '/'):
			params = params[0:len(params) - 2]
		pairsofparams = cleanedparams.split('&')
		param = {}
		for i in range(len(pairsofparams)):
			splitparams = {}
			splitparams = pairsofparams[i].split('=')
			if (len(splitparams)) == 2:
				param[splitparams[0]] = splitparams[1]
	if len(param) > 0:
		for cur in param:
			param[cur] = urllib.unquote_plus(param[cur])
	return param

params = get_params(sys.argv[2])
try:
	func = params['func']
	del params['func']
except:
	func = None
	xbmc.log('[%s]: Primary input' % addon_id, 1)
	getitems(params)
if func != None:
	try: pfunc = globals()[func]
	except:
		pfunc = None
		xbmc.log('[%s]: Function "%s" not found' % (addon_id, func), 4)
		showMessage('Internal addon error', 'Function "%s" not found' % func, 2000)
	if pfunc: pfunc(params)

