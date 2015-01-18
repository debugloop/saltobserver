from saltobserver import app, redis_pool
import gevent

from redis import Redis
from distutils.version import StrictVersion

import json
import time


class RedisStream(object):

    def __init__(self):
        self.redis = Redis(connection_pool=redis_pool)
        app.logger.debug("Using Redis version %s." % self.redis.info()['redis_version'])
        actual_version = StrictVersion(self.redis.info()['redis_version'])
        minimum_version = StrictVersion("2.8.0")
        if actual_version < minimum_version:
            raise NotImplementedError
        self.redis.config_set('notify-keyspace-events', 'Kls')
        self.pubsub = self.redis.pubsub()
        self.pubsub.psubscribe(["__keyspace@0__:{0}:*.*".format(minion) for minion in self.redis.smembers('minions')])
        self.clients = list()

    def _generator(self):
        for message in self.pubsub.listen():
            if message['type'] == 'pmessage':
                app.logger.debug("Message received from Redis, building data packet.")
                minion_id = message['channel'].split(':')[1]
                function = message['channel'].split(':')[2]
                jid = self.redis.lindex('{0}:{1}'.format(minion_id, function), 0)
                success = True if json.loads(self.redis.get('{0}:{1}'.format(minion_id, jid))).get('retcode') == 0 else False
                timestamp = time.strptime(jid, "%Y%m%d%H%M%S%f")
                yield dict(minion_id=minion_id, function=function, jid=jid, success=success, time=time.strftime('%Y-%m-%d, at %H:%M:%S', timestamp))

    def register(self, client, function):
        self.clients.append((client, function))
        app.logger.debug("Client %s (function %s) registered." % (client, function))

    def send_or_discard_connection(self, client_tupl, data):
        client, function = client_tupl
        try:
            client.send(json.dumps(data))
            app.logger.debug("Data for jid %s sent to %s (function %s)" % (data['jid'], client, function))
        except Exception as e:
            self.clients.remove(client_tupl)
            app.logger.debug("%s (function %s) removed with reason: %s" % (client, function, e))

    def run(self):
        for data in self._generator():
            sent = 0
            for client, function in self.clients:
                if data['function'] == function:
                    gevent.spawn(self.send_or_discard_connection, (client, function), data)
                    sent = sent + 1
            app.logger.debug("Attempted to send data packet sent to %s of %s clients." % (sent, len(self.clients)))

    def start(self):
        gevent.spawn(self.run)
