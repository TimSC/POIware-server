#ogr2ogr -f KML output.kml input.shp

#0 kml
#1 Document
#2 Folder
#3 name
#3 Placemark
#4 name
#4 ExtendedData
#5 SchemaData
#6 SimpleData

import bz2, json, poidatabase, web, os
import xml.parsers.expat
from shapely.geometry import Polygon, LineString, LinearRing, Point, MultiPolygon, MultiPoint
import shapely.wkt

def TitleCase(txt):
	txtSpl = txt.split(" ")
	txtSpl = [tmp.capitalize() for tmp in txtSpl]
	return " ".join(txtSpl)

class ParseKml(object):
	def __init__(self):
		self.depth = 0
		self.count = 0
		self.dataBuffer = []
		self.extendedData = {}
		self.lastAttr = None
		self.placeName = None
		self.shapePoints = []
		self.shapeLineStrings = []
		self.shapeLinearRings = []
		self.shapeOuterPolys = []
		self.shapeInnerPolys = []
		self.shapeType = None
		self.shapeSubType = None
		self.dbInt = None
		self.datasetId = None
		self.kmlGeoms = ["Point","LineString","LinearRing",
			"Polygon","MultiGeometry","Model",
			"gx:Track"]
		self.geomDepth = 0

	def StartEl(self, name, attrs):
		#print self.depth, name, attrs
		if name in ["SimpleData", "coordinates", "name"]:
			self.dataBuffer = []

		if name == "ExtendedData":
			self.extendedData = {}

		if name in self.kmlGeoms:
			if self.geomDepth == 0:
				self.shapeType = name
			self.geomDepth += 1

		if name in ["outerBoundaryIs", "innerBoundaryIs"]:
			self.shapeSubType = name

		if name == "Placemark":
			self.count += 1
			if self.count % 1000 == 0:
				print self.count

		self.depth += 1
		self.lastAttr = attrs

	def EndEl(self, name):
		if name == "SimpleData":
			txt = "".join(self.dataBuffer)
			self.dataBuffer = []
			self.extendedData[self.lastAttr["name"]] = txt

		if name == "coordinates":
			txt = "".join(self.dataBuffer)

			txtSp1 = txt.split(" ")
			ptList = []
			for pttxt in txtSp1:

				txtSp2 = pttxt.split(",")
				nums = tuple(map(float, txtSp2))
				ptList.append(nums)

			if self.shapeType == "Point":
				self.shapePoints.extend(ptList)
			if self.shapeType == "LineString":
				self.shapeLineStrings.append(ptList)
			if self.shapeType == "LinearRing":
				self.shapeLinearRings.append(ptList)
			if self.shapeSubType == "outerBoundaryIs":
				self.shapeOuterPolys.append(ptList)
			if self.shapeSubType == "innerBoundaryIs":
				self.shapeInnerPolys.append(ptList)

			self.dataBuffer = []

		if name == "name":
			txt = "".join(self.dataBuffer)
			self.placeName = txt
			self.dataBuffer = []

		if name == "Placemark":
			pn = None
			if self.placeName is not None:
				pn = TitleCase(self.placeName)
				pn = pn.replace("\n", "")
				pn = pn.replace("\r", "")

			shape = None
	
			if self.shapeType in ["Polygon"]:
				#print self.shapeType, len(self.shapeOuterPolys), len(self.shapeInnerPolys)
				shape = Polygon(self.shapeOuterPolys[0], self.shapeInnerPolys)

			if self.shapeType in ["MultiGeometry"]:
				outer = map(Polygon, self.shapeOuterPolys)
				inner = map(Polygon, self.shapeInnerPolys)

				poly = []
				for o in outer:
					ihit = []
					for i in inner:
						if o.intersects(i):
							ihit.append(i.exterior.coords)
					poly.append(Polygon(o.exterior.coords, ihit))
				shape = MultiPolygon(poly)

			if self.shapeType == "LineString":
				shape = LineString(self.shapeLineStrings[0])

			if self.shapeType == "LinearRing":
				shape = LinearRing(self.shapeLinearRings[0])

			if self.shapeType == "Point":
				if len(self.shapePoints) == 1:
					shape = Point(self.shapePoints[0])
				else:
					shape = MultiPoint(self.shapePoints)

			if shape is None:
				raise RuntimeError("Unknown shape type: "+str(self.shapeType))

			repPoint = None
			if shape is not None:
				tmp = shape.representative_point()
				repPoint = tuple(tmp.coords[0])

			#print self.placeName, self.shape, self.extendedData
			self.dbInt.AddPois(self.datasetId, [{"dataset":self.datasetId, "name": self.placeName, 
				"lat":float(repPoint[1]), "lon":float(repPoint[0]), "version": 1}])
			self.extendedData = {}
			self.placeName = None
			self.shapePoints = []
			self.shapeOuterPolys = []
			self.shapeInnerPolys = []
			self.shapeLineStrings = []
			self.shapeLinearRings = []
			self.shapeType = None

		if name in self.kmlGeoms:
			self.geomDepth -= 1

		if name in ["outerBoundaryIs", "innerBoundaryIs"]:
			self.shapeSubType = None

		self.depth -= 1

	def CharData(self, data):
		self.dataBuffer.append(data)
		#print data

	def ParseFile(self, ha):
		parser = xml.parsers.expat.ParserCreate()

		parser.StartElementHandler = self.StartEl
		parser.EndElementHandler = self.EndEl
		parser.CharacterDataHandler = self.CharData

		parser.ParseFile(ha)


if __name__=="__main__":

	curdir = os.path.dirname(__file__)
	db = web.database(dbn='sqlite', db=os.path.join(curdir, 'data.db'))
	t = db.transaction()
	inFi = bz2.BZ2File("SM.kml.bz2", "r")
	dbInt = poidatabase.DbInt(db)

	datasetId = dbInt.AddDataset("Sch Mon", 1, {"public": 1})

	ep = ParseKml()
	ep.dbInt = dbInt
	ep.datasetId = datasetId
	ep.ParseFile(inFi)

	t.commit()

	ep.db = None
	
	del ep
	del dbInt
	del db

