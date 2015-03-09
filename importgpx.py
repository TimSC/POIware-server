import web, os
import gpxutils, poidatabase

if __name__=="__main__":

	curdir = os.path.dirname(__file__)
	db = web.database(dbn='sqlite', db=os.path.join(curdir, 'data.db'))
	
	dbInt = poidatabase.DbInt(db)

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

