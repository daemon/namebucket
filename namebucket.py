import json
import os
import re
import requests
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
  r = requests.post('https://authserver.mojang.com/authenticate', payload)
  return json.loads(r.content.decode('utf-8'))

def check_name(token, name):
  with requests.Session() as s:
    url = 'https://api.mojang.com/user/profile/agent/minecraft/name/%s' % name
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

def catch_name(token, name, length, interval, request):
  start = time.time()
  while start + length > time.time():    
    avail = check_name(token, name)
    os.system('date')
    print('Available: %s' % avail)
    if avail:
      request.execute(name)
      return
    time.sleep(interval)

'''
Names to dropcatch
'''
names = {}
def queue(name, timestamp):
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

def main():
  username = 'user'
  password = 'password'
  response = login_auth(username, password)
  info = login_account(username, password)
  print(info)
  if not info:
    print('Failed to login to account server!')    
    return
  request = ChangeNameRequest(info[1], info[0], password)
  print(request.csrf_tok)
  try:
    auth_bearer = response['accessToken']
  except KeyError:
    print(response['errorMessage'])
    return
  print("Bearer token: %s" % auth_bearer)
  name = 'poor'
  catch_name(auth_bearer, name, 80, 0.15, request)  

main()
