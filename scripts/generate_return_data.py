from redis import Redis
import json
import datetime

class ReturnDataGenerator:
    def __init__(self, redis=Redis(), minion_list=['some.minion.example.com', 'someother.minion.example.com']):
        self.redis = redis
        self.minions = minion_list

    def generate(self, jid='{0:%Y%m%d%H%M%S%f}'.format(datetime.datetime.now()), fun="state.highstate"):
        ret = {
                "fun_args": [],
                "jid": jid,
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
                "fun": fun,
                }

        for minion in self.minions:
            ret['id'] = minion
            self._write(ret)

    def _write(self, ret):
        """
        This function needs to correspond to this:
        https://github.com/saltstack/salt/blob/develop/salt/returners/redis_return.py#L88
        """
        self.redis.set('{0}:{1}'.format(ret['id'], ret['jid']), json.dumps(ret))
        self.redis.lpush('{0}:{1}'.format(ret['id'], ret['fun']), ret['jid'])
        self.redis.sadd('minions', ret['id'])
        self.redis.sadd('jids', ret['jid'])

if __name__ == '__main__':
    ReturnDataGenerator().generate()
