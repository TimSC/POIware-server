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

import bz2, json, importScheduledMonuments, os, web
import poidatabase
import xml.parsers.expat

if __name__=="__main__":

	curdir = os.path.dirname(__file__)
	db = web.database(dbn='sqlite', db=os.path.join(curdir, 'data.db'))	
	t = db.transaction()

	inFi = bz2.BZ2File("LB.kml.bz2", "r")
	dbInt = poidatabase.DbInt(db)

	datasetId = dbInt.AddDataset("Sch Mon", 1, {"public": 1})

	ep = importScheduledMonuments.ParseKml()
	ep.dbInt = dbInt
	ep.datasetId = datasetId
	ep.ParseFile(inFi)

	t.commit()

	del dbInt
	ep.dbInt = None
	del ep
	del db
