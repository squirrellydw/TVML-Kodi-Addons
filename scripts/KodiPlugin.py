import xml.etree.ElementTree as ET
import os, sys, re
import importlib
import bridge
import utils
import Plugin

sys.path.append(os.path.join('scripts', 'kodi'))

def convert_kodi_tags_to_html_tags(s):
	s = s.replace('[B]', '<b>')
	s = s.replace('[/B]', '</b>')
	s = s.replace('[I]', '<i>')
	s = s.replace('[/I]', '</i>')
	return s


class KodiPlugin:
	def __init__(self, dir):
		self.dir = dir
		tree = ET.parse(os.path.join(dir, 'addon.xml'))
		for e in tree.iter('addon'):
			self.name = e.attrib['name']
			self.id = e.attrib['id']
		for e2 in tree.iter('extension'):
			if e2.attrib['point'] == 'xbmc.python.pluginsource':
				self.script = e2.attrib['library']
		self.icon = os.path.join(self.dir, 'icon.png')
		self.module = self.script[:-3]
		self.menuurl = '/menu/{}'.format(utils.b64encode(self.id))
		
	def settings(self, bridge, url):
		import xbmc
		xbmc.bridge = bridge
		import xbmcaddon
		xbmcaddon.Addon(self.id).openSettings()
			
	
	def run(self, bridge, url):
		if url.startswith('http') or url.startswith('https'):
			bridge.play(url, type_='video')
			return
		import xbmc
		xbmc.bridge = bridge
		import Container
		xbmc.Container = Container.Container(self)
		if type(url) is not str:
			raise Exception('Kodi plugin only accepts one string argument')
		sys.path.append(os.path.join(os.getcwd(), self.dir))
		fp = open(os.path.join(os.getcwd(), self.dir, self.script), 'rb')
		#old_sys_argv = sys.argv
		#plugin://plugin.video.youtube/play/?video_id=sa7kZXOHAtI
		#/playlist/PLpSnlSGciSWPewHLHBq5HFLJBGhHrsKnJ/
		#file://plugin.video.KIDSIL/default.py?url=plugin%3A%2F%2Fplugin.video.youtube%2Fplaylist%2FPLpSnlSGciSWPewHLHBq5HFLJBGhHrsKnJ%2F&mode=8&name=%D7%A6%D7%95%D7%9D+%D7%A6%D7%95%D7%9D&iconimage=http%3A%2F%2Fcfvod.kaltura.com%2Fp%2F1068292%2Fsp%2F106829200%2Fthumbnail%2Fentry_id%2F1_ojk9szi3%2Fversion%2F100011%2Facv%2F221%2Fwidth%2F1024%2Fheight%2F584&description=1
		#m = re.search('(.*://[^/]*([^?]*))*(\?*.*)', url)
		#if not m:
		#	return None
		#url = m.group(3)
		#script = m.group(2) if m.group(2) else os.path.join('file://{}'.format(self.id),self.script)
		if '?' in url:
			sys.argv = [url.split('?')[0], '1', '?{}'.format(url.split('?')[1])]
		else:
			sys.argv = [url, '1', '']
		m = re.search('.*://[^/]*(/.*)', sys.argv[0])
		if m:
			sys.argv[0] = m.group(1)
		
		if not sys.argv[0]:
			sys.argv[0] = os.path.join('file://{}'.format(self.id),self.script)
		#sys.argv = [script, '1', url]
		print 'Calling plugin {} with {}'.format(self.name, sys.argv)
		import xbmcplugin
		import imp
		import urlparse
		xbmcplugin.items = []
		imp.load_module(self.module, fp, os.path.join(os.getcwd(), self.dir), ('.py', 'rb', imp.PY_SOURCE))
		fp.close()
		sys.path.remove(os.path.join(os.getcwd(), self.dir))
		#sys.argv = old_sys_argv
		items = xbmcplugin.items
		print 'Plugin {} ended with: {}'.format(self.name, items)
		ans = []
		items = xbmcplugin.items
		from Plugin import Item
		if len(items) == 1 and hasattr(items[0], 'path'):
			return items
		for item in items:
			#url, title, subtitle=None, icon=None, details=None, menuurl='', info={})
			i = Item(url=item['url'], title=convert_kodi_tags_to_html_tags(item['listitem'].label), subtitle=item['listitem'].getProperty('subtitle'), icon=item['listitem'].thumbnailImage if item['listitem'].thumbnailImage != 'DefaultFolder.png' else '', details=item['listitem'].getProperty('details'),info=item['listitem'].infos)
			infos = item['listitem'].infos
			if 'poster' in infos:
				i.icon = infos['poster']
			if 'plot' in infos:
				i.details = infos['plot']
			if 'year' in infos:
				i.subtitle = infos['year']
			ans.append(i)
		return ans