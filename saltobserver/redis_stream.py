from saltobserver import app
import gevent

from redis import Redis

import json
import time

redis = Redis(
        host=app.config['REDIS_HOST'],
        port=app.config['REDIS_PORT'],
        db=app.config['REDIS_DB'],
        password=app.config['REDIS_PASS'])
redis.config_set('notify-keyspace-events', 'Kls')

class RedisStream(object):
    def __init__(self):
        self.clients = list()
        self.pubsub = Redis().pubsub()
        self.pubsub.psubscribe(["__keyspace@0__:{0}:*.*".format(minion) for minion in redis.smembers('minions')])

    def _generator(self):
        for message in self.pubsub.listen():
            if message['type'] == 'pmessage':
                minion_id = message['channel'].split(':')[1]
                function = message['channel'].split(':')[2]
                jid = redis.lindex('{0}:{1}'.format(minion_id, function), 0)
                timestamp = time.strptime(jid, "%Y%m%d%H%M%S%f")
                yield dict(minion_id=minion_id, function=function, jid=jid, time=time.strftime('%Y-%m-%d, at %H:%M:%S', timestamp))

    def register(self, client, function):
        self.clients.append((client, function))

    def send_or_discard_connection(self, client_tupl, data):
        client, function = client_tupl
        try:
            client.send(json.dumps(data))
        except Exception as e:
            print e
            self.clients.remove(client_tupl)

    def run(self):
        for data in self._generator():
            for client, function in self.clients:
                if data['function'] == function:
                    gevent.spawn(self.send_or_discard_connection, (client, function), data)

    def start(self):
        gevent.spawn(self.run)
