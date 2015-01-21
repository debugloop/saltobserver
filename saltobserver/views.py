from saltobserver import app, redis_pool

from flask import Response
from flask import render_template, redirect, url_for, request

from redis import Redis

import json
import time

def _get_success(minion, jid):
    redis = Redis(connection_pool=redis_pool)
    return True if json.loads(redis.get('{0}:{1}'.format(minion, jid))).get('retcode') == 0 else False


@app.route('/_get_function_data/<minion>/<jid>/')
def get_function_data(minion, jid):
    """AJAX access for loading function/job details."""
    redis = Redis(connection_pool=redis_pool)
    data = redis.get('{0}:{1}'.format(minion, jid))
    return Response(response=data, status=200, mimetype="application/json")


@app.route('/jobs/<jid>/')
def jobs(jid):
    ret = list()
    redis = Redis(connection_pool=redis_pool)
    data = None
    # Avoid using something like redis.keys("*:{0}".format(jid)) by cross
    # checking minion IDs.
    # The following comes in at O(|minion IDs|), while 'keys' takes O(|keys in
    # redis|). Using the keys operation is not recommended for production use
    # either way.
    minions = [minion for minion in redis.sort('minions', alpha=True) if redis.exists("{0}:{1}".format(minion, jid))]
    for minion in minions:
        ret.append((minion, _get_success(minion, jid)))
    else:
        # Get the return data of the last match to find the executed function
        # (which is the same on all minions by definition).
        # This is only used to display the correct function before any minion
        # is clicked.
        return_data = json.loads(redis.get("{0}:{1}".format(minion, jid)))
        function = return_data.get('fun', 'invalid_data_in_redis')
    try:
        timestamp = time.strptime(jid, "%Y%m%d%H%M%S%f")
        at_time = time.strftime('%Y-%m-%d, at %H:%M:%S', timestamp)
    except ValueError:
        at_time = None  # JS will gobble this
    return render_template('jobs.html', minions=ret, time=at_time, function=function)


@app.route('/jobs/')
def jobsearch():
    if request.args.get('jid', None):
        return redirect(url_for('jobs', jid=request.args.get('jid')))
    return render_template('jobform.html')


@app.route('/history/<minion>/<function>/')
def history(minion, function):
    ret = list()
    redis = Redis(connection_pool=redis_pool)
    for jid in redis.lrange('{0}:{1}'.format(minion, function), 0, -1):
        try:
            timestamp = time.strptime(jid, "%Y%m%d%H%M%S%f")
            ret.append((jid, _get_success(minion, jid), time.strftime('%Y-%m-%d, at %H:%M:%S', timestamp)))
        except ValueError:  # from either time.strptime or json.loads
            # should never occur when dealing with real data
            pass
    return render_template('history.html', jids=ret)


@app.route('/history/')
def historysearch():
    if request.args.get('minion', None) and request.args.get('function', None):
        return redirect(url_for('history', minion=request.args.get('minion'), function=request.args.get('function')))
    return render_template('historyform.html')


@app.route('/functions/<function>/')
def functions(function):
    functions = list()
    times_list = list()
    redis = Redis(connection_pool=redis_pool)
    for minion in redis.sort('minions', alpha=True):
        try:
            jid = redis.lindex('{0}:{1}'.format(minion, function), 0)
            timestamp = time.strptime(jid, "%Y%m%d%H%M%S%f")
            times_run = redis.llen('{0}:{1}'.format(minion, function))
            if times_run > 0:
                times_list.append(times_run)
            functions.append((minion, jid, _get_success(minion, jid), time.strftime('%Y-%m-%d, at %H:%M:%S', timestamp)))
        except Exception:  # TODO: make this more specific
            continue
    return render_template('functions.html', functions=functions, average_run=float(sum(times_list)) / len(times_list) if len(times_list) > 0 else 0)


@app.route('/functions/')
def functionsearch():
    if request.args.get('function', None):
        return redirect(url_for('functions', function=request.args.get('function')))
    return render_template('functionform.html')


@app.route('/')
def index():
    ''' return functions(app.config['DEFAULT_FUNCTION']) '''  # work around for mitsuhiko/werkzeug#382, if needed
    return redirect(url_for('functions', function=request.args.get('function', app.config['DEFAULT_FUNCTION'])))
