#Recipe for apache: http://webpy.org/cookbook/mod_wsgi-apache
#Jinja2 templating using solution 2 from: http://webpy.org/cookbook/template_jinja

#sudo apt-get install apache2 libapache2-mod-wsgi python-dev python-jinja2

import web, os, sys, datetime, json, math
sys.path.append(os.path.dirname(__file__))
import poidatabase, StringIO, gpxutils
#import conf
from jinja2 import Environment,FileSystemLoader
from xml.sax.saxutils import escape

class Api(object):
	def GET(self):
		return self.Render()

	def POST(self):
		return self.Render()

	def RequireParams(self, webInput, params):
		status = None
		for p in params:
			if p not in webInput:
				status = "400 Bad Request"
				return status
		return None

	def Render(self):
		webInput = web.input()
		dataDb = web.ctx.dataDb
		dataDbInt = poidatabase.DbInt(dataDb)
		
		if "action" not in webInput:
			web.ctx.status = '400 Bad Request'
			web.header('Content-Type', 'text/plain')
			return "An action must be defined"

		action = webInput["action"]

		if action == "query":
			requiredParams = ["lat", "lon"]
			stat = self.RequireParams(webInput, requiredParams)
			if stat is not None:
				web.ctx.status = stat
				web.header('Content-Type', 'text/plain')
				return "Required parameters" + str(requiredParams)

			lat = float(webInput["lat"])
			lon = float(webInput["lon"])

			#Spatial query
			result = dataDbInt.GetRecordsNear(lat, lon)

			out = StringIO.StringIO()
			gpxWriter = gpxutils.GpxWriter(out)
			lat = float(webInput["lat"])
			lon = float(webInput["lon"])

			for row in result:
				extensions = {"poiware":{"version": row["version"], "poiid": row["poiid"]}}

				gpxWriter.Waypoint(row["lat"], row["lon"], name=row["name"], extensions = extensions)
				#gpxWriter.append({"name":row["name"], "lat": row["lat"], "lon": row["lon"], "dataset": row["dataset"], "version": row["version"]})

			del gpxWriter

			web.header('Content-Type', 'text/xml')
			return out.getvalue()

		if action == "get":
			requiredParams = ["poiid"]
			stat = self.RequireParams(webInput, requiredParams)
			if stat is not None:
				web.ctx.status = stat
				web.header('Content-Type', 'text/plain')
				return "Required parameters" + str(requiredParams)

			poiidsSplit = webInput["poiid"].split(",")
			poiids = map(int, poiidsSplit)
	
			sqlFrag = []
			sqlArgs = {}
			for i, poiid in enumerate(poiids):
				arg = "a{0}".format(i)
				sqlFrag.append("poiid=${0}".format(arg))
				sqlArgs[arg] = poiid
			sqlStatement = " OR ".join(sqlFrag)

			result = dataDb.select("pois", where=sqlStatement, vars=sqlArgs)
			result = list(result)
			if len(result) < 1:
				web.ctx.status = '404 Not found'
				web.header('Content-Type', 'text/plain')
				return "Record not found"

			out = []
			out.append('<?xml version="1.0" encoding="UTF-8" ?>\n')
			out.append("<pois>\n")
			for rowResult in result:
				rowResult = dict(rowResult)

				out.append("<poi poiid='{0}' version='{1}'>\n".format(rowResult["poiid"], rowResult["version"]))
	
				del rowResult["poiid"]
				del rowResult["version"]

				for k in rowResult:
					out.append("<{0}>".format(k))
					out.append(escape(str(rowResult[k])))
					out.append("</{0}>\n".format(k))

				out.append("</poi>\n")
			out.append("</pois>\n")
			web.header('Content-Type', 'text/xml')



			return "".join(out)

		web.header('Content-Type', 'text/plain')
		return "Unknown action"

urls = (
	'/api', 'Api',
	)

def RenderTemplate(template_name, **context):
	extensions = context.pop('extensions', [])
	globals = context.pop('globals', {})

	jinja_env = Environment(
			loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')),
			extensions=extensions,
			)
	jinja_env.globals.update(globals)
	jinja_env.filters['datetime'] = Jinja2DateTime

	#jinja_env.update_template_context(context)
	return jinja_env.get_template(template_name).render(context)

def InitDatabaseConn():
	curdir = os.path.dirname(__file__)
	web.ctx.dataDb = web.database(dbn='sqlite', db=os.path.join(curdir, 'data.db'))
	#web.ctx.users = web.database(dbn='sqlite', db=os.path.join(curdir, 'users.db'))
	web.ctx.session = session

web.config.debug = 1
app = web.application(urls, globals())
curdir = os.path.dirname(__file__)
app.add_processor(web.loadhook(InitDatabaseConn))

session = web.session.Session(app, web.session.DiskStore(os.path.join(curdir,'sessions')),)

application = app.wsgifunc()

