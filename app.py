#Recipe for apache: http://webpy.org/cookbook/mod_wsgi-apache
#Jinja2 templating using solution 2 from: http://webpy.org/cookbook/template_jinja

#sudo apt-get install apache2 libapache2-mod-wsgi python-dev python-jinja2

import web, os, sys, datetime, json
sys.path.append(os.path.dirname(__file__))
#import conf
from jinja2 import Environment,FileSystemLoader

class Api(object):
	def GET(self):
		dataDb = web.ctx.dataDb
		result = dataDb.select("pois")

		out = []
		for row in result:
			out.append({"name":row["name"], "lat": row["lat"], "lon": row["lon"], "dataset": row["dataset"], "version": row["version"]})

		return json.dumps(out)

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

#web.config.debug = conf.debug
app = web.application(urls, globals())
curdir = os.path.dirname(__file__)
app.add_processor(web.loadhook(InitDatabaseConn))

session = web.session.Session(app, web.session.DiskStore(os.path.join(curdir,'sessions')),)

application = app.wsgifunc()
