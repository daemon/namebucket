import datetime
import json
import os
import re
import random
import requests
import sys
import time

class ChangeNameRequest:
  def __init__(self, session, user_id, password):
    self.session = session
    self.password = password
    self.user_id = user_id
    self.url = 'https://account.mojang.com/me/renameProfile/%s' % self.user_id 
    self.load_csrf_tok()

  def load_csrf_tok(self):
    r = self.session.get(self.url)
    content = r.content.decode('utf-8')
    pattern = re.compile('name="authenticityToken" value="(.+?)"')
    m = re.search(pattern, content)
    self.csrf_tok = m.group(1)

  def execute(self, new_name):
    data = dict(authenticityToken=self.csrf_tok, newName=new_name, password=self.password)
    r = self.session.post(self.url, data)
    print(r.content.decode('utf-8'))

def login_account(username, password):
  s = requests.Session()
  r = s.get('https://account.mojang.com/login')
  content = r.content.decode('utf-8')
  pattern = re.compile('name="authenticityToken" value="(.+?)"')
  try:
    m = re.search(pattern, content)
    csrf_tok = m.group(1)
    form_data = dict(authenticityToken=csrf_tok, username=username, password=password)
    r = s.post('https://account.mojang.com/login', form_data)
    content = r.content.decode('utf-8')
    pattern = re.compile('<a href="/me/renameProfile/(.+?)">Change</a>')
    m = re.search(pattern, content)
    user_id = m.group(1)
    return (user_id, s)
  except:
    return None

def login_auth(username, password):
  payload = '''{
    "agent": {
        "name": "Minecraft",
        "version": 1
    },
    "username": "%s",
    "password": "%s"
  }''' % (username, password)
  r = requests.post('https://%s/authenticate', (login_auth.authserver_host, payload))
  return json.loads(r.content.decode('utf-8'))
login_auth.authserver_host = 'authserver.mojang.com'

def check_name(token, name):
  with requests.Session() as s:
    url = 'https://%s/user/profile/agent/minecraft/name/%s' % (check_name.api_host, name)
    headers = {}
    headers["Access-Control-Request-Headers"] = "authorization"
    headers["Access-Control-Request-Method"] = "GET"
    headers["User-Agent"] = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'
    headers["Accept-Language"] = "en-US,en;q=0.8"
    headers["Accept"] = "*/*"
    headers["Host"] = "api.mojang.com"
    headers["Origin"] = "https://minecraft.net"
    headers["Referer"] = "https://minecraft.net/en/store/minecraft/"
    r = requests.Request('OPTIONS', url, headers=headers)
    r = r.prepare()
    del r.headers['Content-Length']
    r = s.send(r)
    del headers["Access-Control-Request-Headers"]
    del headers["Access-Control-Request-Method"]
    headers["Authorization"] = "Bearer %s" % token
    headers["Accept"] = "application/json, text/javascript, */*; q=0.01"
    r = s.get(url, headers=headers)
  return r.status_code == 404
check_name.api_host = 'api.mojang.com'

def catch_name(token, name, length, request):
  start = time.time()
  while start + length > time.time():    
    if check_name(token, name):
      print('Available at %s' % str(datetime.datetime.now()))
      request.execute(name)
      return
    time.sleep(1)

'''
Names to dropcatch
'''
names = {}
def queue(name, timestamp):
  save_names()
  print ("Queued %s" % name)
  for n, t in names.items():
    if abs(t - timestamp) < 80:
      return False
  names[name] = timestamp
  return True

def find(name):
  if name in names:
    return names[name]
  return None

def save_names():
  with open('names.json', 'w') as f:
    f.write(json.dumps(names))

def load_names():
  try:
    with open('names.json') as f:
      names = json.loads(f.read())
  except:
    with open('names.json', 'w') as f:
      pass

def load_conf():
  try:
    with open('config.json') as f:
      return json.loads(f.read())
  except:
    config = dict(username='username', password='password')
    config['api-mojang-host'] = ''
    config['authserver-mojang-host'] = ''
    with open('config.json', 'w') as f:
      f.write(json.dumps(config, indent=2))
    sys.exit(0)

def start():
  cfg = load_conf()
  username = cfg['username']
  password = cfg['password']
  mojang_api_host = cfg['mojang-api-host']
  mojang_authsrv_host = cfg['mojang-authserver-host']
  if mojang_api_host:
    check_name.api_host = mojang_api_host
  if mojang_authsrv_host:
    login_auth.authserver_host = mojang_authsrv_host
  load_names()
  last = 0
  delay = 0
  while True:
    if last + delay < time.time():
      response = login_auth(username, password)
      info = login_account(username, password)
      if not info:
        print('Failed to login to account server!')
        time.sleep(5)
        continue
      request = ChangeNameRequest(info[1], info[0], password)
      try:
        auth_bearer = response['accessToken']
      except KeyError:
        print(response['errorMessage'])
        time.sleep(5)
        continue
      last = time.time()
      delay = 7200 + random.randint(0, 600)
    for name in list(names):
      ts = names[name]
      if ts < time.time():
        del names[name]
        continue
      if ts - time.time() < 40:
        print('Attempting to catch %s...' % name)
        del names[name]
        catch_name(auth_bearer, name, 80, request)
    time.sleep(5)

