
import web, os, math

class DistLatLon(object):
	#Based on http://stackoverflow.com/a/1185413/4288232

	def __init__(self, latDeg, lonDeg):
		self.R = 6371.
		lat = math.radians(latDeg)
		lon = math.radians(lonDeg)
		self.x = self.R * math.cos(lat) * math.cos(lon)
		self.y = self.R * math.cos(lat) * math.sin(lon)
		self.z = self.R * math.sin(lat)

	def Dist(self, latDeg, lonDeg):
		lat = math.radians(latDeg)
		lon = math.radians(lonDeg)
		x2 = self.R * math.cos(lat) * math.cos(lon)
		y2 = self.R * math.cos(lat) * math.sin(lon)
		z2 = self.R * math.sin(lat)
	
		dist2 = math.pow(self.x - x2, 2.) + math.pow(self.y - y2, 2.) + math.pow(self.z - z2, 2.)
		if dist2 < 0.:
			return 0.
		return math.pow(dist2, 0.5)

class DbInt(object):
	def __init__(self, db):
		self.db = db

	def InitSchema(self):
		self.db.query('CREATE TABLE IF NOT EXISTS pois(poiid INTEGER PRIMARY KEY, dataset INTEGER, name TEXT, lat REAL, lon REAL, data TEXT, version INTEGER)')
		self.db.query('CREATE TABLE IF NOT EXISTS datasets(dataset INTEGER PRIMARY KEY, owner INTEGER, name TEXT, public TINYINT)')
	
		# Spatial index
		try:
			self.db.query('''CREATE VIRTUAL TABLE IF NOT EXISTS pos USING rtree(id, minLat, maxLat, minLon, maxLon);''')

		except Exception as err:
			print "Could not create table pos,", err

	def DropEverything(self):
		self.db.query('DROP TABLE IF EXISTS pois')
		self.db.query('DROP TABLE IF EXISTS datasets')
		self.db.query('DROP TABLE IF EXISTS pos')

	def Clear(self):
		self.db.delete('pois', where="1=1")
		self.db.delete('datasets', where="1=1")
		self.db.delete('pos', where="1=1")

	def AddPois(self, datasetId, pois):
		tmp = []
		for wpt in pois:
			tmp.append({"dataset":datasetId, "name":wpt["name"], "lat":float(wpt["lat"]), "lon":float(wpt["lon"]), "version": 1})
		rowIds = self.db.multiple_insert("pois", values = tmp)

		tmp2 = []
		for wpt, rowId in zip(pois, rowIds):
			tmp2.append({"id": rowId, 
				"minLat":float(wpt["lat"]), "maxLat":float(wpt["lat"]), 
				"minLon":float(wpt["lon"]), "maxLon":float(wpt["lon"])})
		rowIds = self.db.multiple_insert("pos", values = tmp2)

		return rowIds

	def AddDataset(self, name, owner, settings):
		datasetId = self.db.insert("datasets", owner = 1, name = "Test data", public = 1)
		return datasetId

	def GetRecordsNear(self, lat, lon, radius = 10.0, maxRecs = 100):

		latHWidth = math.degrees(radius / 6371.)
		lonHWidth = math.degrees(radius / (6371. * math.cos(math.radians(lat))))
		vrs = {}
		conds = []

		if lat is not None:
			conds.append("minLat>=$minLat AND maxLat<=$maxLat")
			vrs['minLat'] = lat-latHWidth
			vrs['maxLat'] = lat+latHWidth

		if lon is not None:
			conds.append("minLon>=$minLon AND maxLon<=$maxLon")
			vrs['minLon'] = lon-lonHWidth
			vrs['maxLon'] = lon+lonHWidth
	
		if len(conds) > 0:
			cond = " AND ".join(conds)
		else:
			cond = "1=1"

		results = self.db.select("pos", where=cond, vars=vrs)
		sortableResults = []

		if lat is not None and lon is not None:
			calcDist = DistLatLon(lat, lon)
		else:
			calcDist = None

		resultsInRoi = []
		for spatialRecord in results:
		
			rowId = spatialRecord["id"]
			lat = 0.5 * (spatialRecord["minLat"] + spatialRecord["maxLat"])
			lon = 0.5 * (spatialRecord["minLon"] + spatialRecord["maxLon"])

			#Calculate distance from query location
			if calcDist is not None:
				dist = calcDist.Dist(lat, lon)
			else:
				dist = None

			#Check if in search area
			if dist is not None and dist > radius:
				continue		

			resultsInRoi.append((dist, rowId))

		#Sort records by distance from query location
		resultsInRoi.sort()

		#Limit number of results
		if maxRecs is not None:
			resultsInRoi = resultsInRoi[:maxRecs]

		#Get complete records
		collectResults = []
		for dist, poiid in resultsInRoi:
			results = self.db.select("pois", where="poiid=$poiid", vars={"poiid": poiid})
			collectResults.extend([dict(tmp) for tmp in results])
		return collectResults

