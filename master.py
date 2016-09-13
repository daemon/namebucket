import json
import requests

def print_help():
  def print_line(usage, desc):
    print('%-16s: %s' % (usage, desc))
  print_line('?', 'This menu')
  print_line('a <name> <time>', 'Adds a name to be caught. Timestamp is in Unix time (secs).')
  print_line('d <name>', 'Removes the name from catching queue')
  print_line('u', 'Updates all slaves with the current namebucket.py')
  print_line('q', 'Quit')

def add_name(slaves, name, timestamp):
  for slave in slaves:
    endpoint = "http://%s/name" % slave
    try:
      r = requests.post(endpoint, data=dict(name=name, timestamp=timestamp))
      print("%-24s Added: %s" % (slave, json.loads(r.content.decode('utf-8'))))
    except:
      print("Couldn't reach %s" % endpoint)

def del_name(slaves, name):
  for slave in slaves:
    endpoint = "http://%s/name" % slave
    try:
      r = requests.delete(endpoint, data=dict(name=name))
      print("%-24s Deleted: %s" % (slave, json.loads(r.content.decode('utf-8'))))
    except:
      pass #TODO
  

def update(slaves):
  with open('namebucket.py') as f:
    content = f.read()
  for slave in slaves:
    endpoint = "http://%s/update" % slave
    try:
      requests.put(endpoint, data=dict(data=content))
      print("%-24s: update info sent" % slave)
    except:
      print("Couldn't reach %s" % endpoint)

def main():
  print_help()
  with open('slaves.txt') as f:
    slaves = f.read().splitlines()
  while True:
    line = input('> ')
    toks = line.split(' ')
    if not toks:
      continue
    cmd = toks[0]
    if cmd == '?':
      print_help()
    elif cmd == 'a' and len(toks) >= 3:
      add_name(slaves, toks[1], int(toks[2]))
    elif cmd == 'd' and len(toks) >= 2:
      del_name(toks[1])
    elif cmd == 'u':
      update(slaves)
    elif cmd == 'q':
      return

main()
