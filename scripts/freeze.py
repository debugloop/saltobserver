"""
To create a new static mockup, some edits must be made:
    - in views.py, use the workaround described in index()
    - in tempates/contentpage.html, uncomment the bit of js for converting JSON
      (search for a capital JSON in a jinja comment)

After the mockup is created, replace all ajax requests to _get_function_data
with its onsuccess calls to generate_content with static parameters. Yes, I was
to lazy to automate this.
"""

import redis
import json
import datetime

from flask_frozen import Freezer

# ugly hack is ugly
import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
from saltobserver import app

EXAMPLE_JIDS = ['20141217175928161514', '20141117175928161514']
EXAMPLE_MINIONS = ['some.server.example.com', 'someother.server.example.com']

freezer = Freezer(app)


@freezer.register_generator
def get_data_view():
    for minion in EXAMPLE_MINIONS:
        for jid in EXAMPLE_JIDS:
            yield "/_get_function_data/%s/%s/" % (minion, jid)


@freezer.register_generator
def function_view():
    for func in app.config['FUNCTION_QUICKLIST']:
        yield "/functions/%s/" % func


@freezer.register_generator
def job_view():
    for jid in EXAMPLE_JIDS:
        yield "/jobs/%s/" % jid


@freezer.register_generator
def history_view():
    for minion in EXAMPLE_MINIONS:
        for func in app.config['FUNCTION_QUICKLIST']:
            yield "/history/%s/%s/" % (minion, func)

if __name__ == '__main__':
    serv = redis.Redis()
    serv.flushdb()
    jobs = [
        {
            "fun_args": [],
            "jid": EXAMPLE_JIDS[0],
            "return": {
                "file_|-/etc/salt/minion.d/redis.conf_|-/etc/salt/minion.d/redis.conf_|-managed": {
                    "comment": "File /etc/salt/minion.d/redis.conf is in the correct state",
                    "name": "/etc/salt/minion.d/redis.conf",
                    "start_time": "21:30:27.380777",
                    "result": True,
                    "duration": 17.293,
                    "__run_num__": 34,
                    "changes": {}
                },
                "file_|-/etc/salt/minion_|-/etc/salt/minion_|-managed": {
                    "comment": "File /etc/salt/minion updated",
                    "name": "/etc/salt/minion",
                    "start_time": "21:30:25.525359",
                    "result": True,
                    "duration": 727.88,
                    "__run_num__": 28,
                    "changes": "some"
                }
            },
            "retcode": 0,
            "success": True,
            "fun": "state.highstate",
        },
        {
            "fun_args": [],
            "jid": EXAMPLE_JIDS[1],
            "return": True,
            "retcode": 0,
            "success": True,
            "fun": "test.ping",
        }
    ]

    for job in jobs:
        for minion in EXAMPLE_MINIONS:
            job['id'] = minion
            serv.set('{0}:{1}'.format(job['id'], job['jid']), json.dumps(job))
            serv.lpush('{0}:{1}'.format(job['id'], job['fun']), job['jid'])
            serv.sadd('minions', job['id'])
            serv.sadd('jids', job['jid'])

    app.config['USE_LIVEUPDATES'] = False
    app.config['FREEZER_DESTINATION'] = '../scripts/frozen'
    app.config['FREEZER_BASE_URL'] = 'http://analogbyte.github.io/saltobserver/'
    freezer.freeze()
