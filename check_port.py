import sys
import os
import inspect
import json

requests_path = os.path.dirname(inspect.getfile(inspect.currentframe()))
requests_path = os.path.join(requests_path, 'vendor', 'requests')
sys.path.append(requests_path)

import requests


config = os.path.dirname(inspect.getfile(inspect.currentframe()))
config = os.path.join(config, 'config.json')

data = ''
with open(config) as f:
    data = json.load(f)
    f.close()

url = '%s:%s/api/jobs' % (data['address'], data['port'])

try:
    r = requests.get(url, auth=(data['username'], data['password']))
    if r.status_code == 200:
        print 'Check successfull.'
    else:
        print 'Check failed.'
except Exception as e:
    print 'Check failed: %s' % e
finally:
    raw_input()
