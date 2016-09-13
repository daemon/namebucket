import cherrypy
import namebucket
import sys
import threading

class NameEndpoint:
  exposed = True
  @cherrypy.tools.json_out()
  def POST(self, name, timestamp):
    return namebucket.queue(name, int(timestamp))

  @cherrypy.tools.json_out()
  def GET(self, name):
    timestamp = namebucket.find(name)
    cherrypy.response.status = 203 if timestamp else 404  
    return timestamp

class UpdateEndpoint:
  exposed = True
  def PUT(self, data):
    with open('namebucket.py', 'w') as f:
      f.write(data)
    print('Shutting down for update...')
    sys.exit(0)
  
def run_engine():
  print('Starting...')
  def run():
    rest_conf = {'/': {'request.dispatch': cherrypy.dispatch.MethodDispatcher()}}
    cherrypy.tree.mount(NameEndpoint(), '/name', rest_conf)
    cherrypy.tree.mount(UpdateEndpoint(), '/update', rest_conf)
    cherrypy.engine.start()
    print('Started.')
    cherrypy.engine.block()
  threading.Thread(target=run).start()

run_engine()
