
import web, os
import gpxutils

if __name__=="__main__":

	curdir = os.path.dirname(__file__)
	db = web.database(dbn='sqlite', db=os.path.join(curdir, 'data.db'))

	if 0:
		db.query('DROP TABLE pois')
		db.query('DROP TABLE datasets')

	db.query('CREATE TABLE IF NOT EXISTS pois(poiid INTEGER PRIMARY KEY, dataset INTEGER, name TEXT, lat REAL, lon REAL, data TEXT, version INTEGER)')
	db.query('CREATE TABLE IF NOT EXISTS datasets(dataset INTEGER PRIMARY KEY, owner INTEGER, name TEXT, public TINYINT)')
	
	if 0:
		db.delete('pois', where="1=1")
		db.delete('datasets', where="1=1")

	t = db.transaction()
	datasetId = db.insert("datasets", owner = 1, name = "Test data", public = 1)
	
	reader = gpxutils.GpxReader()
	reader.Read("20150305.gpx")

	tmp = []
	for wpt in reader.waypoints:
		tmp.append({"dataset":datasetId, "name":wpt["name"], "lat":float(wpt["lat"]), "lon":float(wpt["lon"]), "version": 1})

	db.multiple_insert("pois", values = tmp)
	t.commit()

	del db

