import redis
import json
import datetime

serv = redis.Redis()
ret = {
        "fun_args": [],
        "jid": '{0:%Y%m%d%H%M%S%f}'.format(datetime.datetime.now()),
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
        }
minions = ['some.server.example.com', 'someother.server.example.com']

for minion in minions:
    ret['id'] = minion
    serv.set('{0}:{1}'.format(ret['id'], ret['jid']), json.dumps(ret))
    serv.lpush('{0}:{1}'.format(ret['id'], ret['fun']), ret['jid'])
    serv.sadd('minions', ret['id'])
    serv.sadd('jids', ret['jid'])
