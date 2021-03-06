#!/usr/bin/env python
from datetime import date
from xml.etree.ElementTree import ElementTree
from xml.parsers import expat
import os, codecs
from xml.sax.saxutils import escape

class GpxWriter:
	def __init__(self, fi):
		self.fi = fi
		#self.fi = codecs.open(filename, "w", "utf-8")
		self.fi.write('<?xml version="1.0" encoding="UTF-8" ?>\n')
		self.fi.write('<gpx version="1.0" creator="gpxutils.py" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.topografix.com/GPX/1/0" xsi:schemaLocation="http://www.topografix.com/GPX/1/0 http://www.topografix.com/GPX/1/0/gpx.xsd">')

	def StartTrack(self, name=None):
		self.fi.write("<trk>\n")
		if name is not None: self.fi.write(u"<name>"+escape(name)+"</name>\n")
 
	def StartTrackSeg(self):
		self.fi.write("<trkseg>")

	def TrackPoint(self,lat,lon,ele,time):
		self.fi.write('<trkpt lat="'+str(lat)+'" lon="'+str(lon)+'">\n')
		self.fi.write('<ele>'+str(ele)+'</ele>\n')
		self.fi.write('<time>'+date.fromtimestamp(float(time)).isoformat()+'</time>\n')
		self.fi.write('</trkpt>\n')

	def EndTrackSeg(self):
		self.fi.write("</trkseg>")

	def EndTrack(self):
		self.fi.write("</trk>")

	def Waypoint(self, lat, lon, name=None, ele=None, time=None, description = None, extensions = None):
		self.fi.write('<wpt lat="'+str(lat)+'" lon="'+str(lon)+'">\n')
		print ele
		if ele is not None: self.fi.write('<ele>'+float(ele)+'</ele>\n')
		if description is not None: self.fi.write(u'<desc>'+escape(description)+'</desc>\n')
		if time is not None: self.fi.write('<time>'+date.fromtimestamp(float(time)).isoformat()+'</time>\n')
		if name is not None: self.fi.write(u'<name>'+escape(name)+'</name>\n')
		#<cmt></cmt>
		#<link href=""><text></text></link>
		#<sym></sym>
		#<type></type>

		if extensions is not None:

			self.fi.write(u'<extensions>\n')
			for extension in extensions:
				self.fi.write(u'<{0}>\n'.format(extension))
				extData = extensions[extension]
				for k in extData:
					self.fi.write(u'<{0}>{1}</{0}>\n'.format(k, escape(str(extData[k]))))
				self.fi.write(u'</{0}>\n'.format(extension))
			self.fi.write(u'</extensions>\n')

		self.fi.write('</wpt>\n')

	def __del__(self):
		if self.fi is None: return
		self.fi.write("</gpx>\n")
		self.fi = None

class GpxReader:
	
	def Read(self,filename):
		#print "Parsing xml"
		doc = ElementTree(file=filename)
		self.waypoints = []
		for el in doc.getroot():
			if str(el.tag) != "{http://www.topografix.com/GPX/1/0}wpt":
				continue

			lat = float(el.attrib['lat'])
			lon = float(el.attrib['lon'])

			childname = el.find("{http://www.topografix.com/GPX/1/0}name")
			name = None
			if childname is not None: 
				name = str(childname.text.encode("utf-8"))

			childDescription = el.find("{http://www.topografix.com/GPX/1/0}description")
			description = None
			if childDescription is not None: 
				description = str(childDescription.text.encode("utf-8"))

			externalId = None
			extensions = el.find("{http://www.topografix.com/GPX/1/0}extensions")
			if extensions is not None:
				externalId = extensions.find("{http://www.topografix.com/GPX/1/0}id")
				if externalId is not None:
					externalId = str(externalId.text.encode("utf-8"))

			#print lat, lon, name, externalId
			self.waypoints.append({"lat": lat, "lon": lon, "name": name, "externalId": externalId, "description": description})

class GpxReaderStream:
	def __init__ (self):
		self.textBuff = ""
		self.waypoints = []
		self.currentPt = {}
		self.progressFunc = None

	def CharacterData(self, data):
		data = data.strip()
		if data:
			data = data.encode('utf-8')
			self.textBuff += data + "\n"

	def StartElement(self,name, attr):
		name = name.encode('utf-8')
		self.textBuff = ""
		#print name
		if name == "wpt":
			self.currentPt['lat'] = float(attr['lat'])
			self.currentPt['lon'] = float(attr['lon'])

	def EndElement(self,name):
		name = name.encode('utf-8')
		#print name
		if name == "name":
			self.currentPt['name'] = self.textBuff.strip()
		if name == "description":
			self.currentPt['description'] = self.textBuff.strip()
		if name == "externalId":
			self.currentPt['externalId'] = self.textBuff.strip()

		self.textBuff = ""
		if name == "wpt":
			#print self.currentPt
			self.waypoints.append(self.currentPt)
			self.currentPt = {}

	def Read(self, fName):
		xmlParser = expat.ParserCreate()
		xmlParser.CharacterDataHandler = self.CharacterData
		xmlParser.StartElementHandler = self.StartElement
		xmlParser.EndElementHandler = self.EndElement

		fileSize = os.path.getsize(fName)
		fi = open(fName,"rt")
		count = 0
		#print fileSize
		while 1:
			data = fi.read(1024)
			count = count + len(data)
			if data == "":
				break
			xmlParser.Parse(data, 0)
			progress = float(count)/float(fileSize)
			#print self.progressFunc 
			if self.progressFunc is not None:
				self.progressFunc(progress)
		xmlParser.Parse("", 1)

