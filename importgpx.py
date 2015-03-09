
import web, os
import gpxutils

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

if __name__=="__main__":

	curdir = os.path.dirname(__file__)
	db = web.database(dbn='sqlite', db=os.path.join(curdir, 'data.db'))
	
	dbInt = DbInt(db)

	if 1:
		dbInt.DropEverything()

	dbInt.InitSchema()

	if 0:
		dbInt.Clear()

	t = db.transaction()
	datasetId = dbInt.AddDataset("Test data", 1, {"public": 1})
	
	reader = gpxutils.GpxReader()
	reader.Read("20150305.gpx")

	rowIds = dbInt.AddPois(datasetId, reader.waypoints)

	t.commit()

	del db
	print rowIds

