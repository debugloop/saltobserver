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
    # Get the return data of the some match to find the executed function
    # (which is the same on all minions by definition).
    # This is only used to display the correct function before any minion
    # is clicked.
    if minions:
        return_data = json.loads(redis.get("{0}:{1}".format(minions.pop(), jid)))
        function = return_data.get('fun', 'invalid_data_in_redis')
    else:
        function = "none"
    try:
        timestamp = time.strptime(jid, "%Y%m%d%H%M%S%f")
        at_time = time.strftime('%Y-%m-%d, at %H:%M:%S', timestamp)
    except ValueError:
        at_time = None  # JS will gobble this
    return render_template('jobs.html', minions=ret, time=at_time, successful_runs=len([success for _, success in ret if success]), function=function)


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
            timestring = time.strftime('%Y-%m-%d, at %H:%M:%S', timestamp)
        except ValueError:
            continue  # ignore invalid
        ret.append((jid, _get_success(minion, jid), timestring))
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
        if not redis.exists('{0}:{1}'.format(minion, function)):
            continue
        jid = redis.lindex('{0}:{1}'.format(minion, function), 0)
        try:
            timestamp = time.strptime(jid, "%Y%m%d%H%M%S%f")
            timestring = time.strftime('%Y-%m-%d, at %H:%M:%S', timestamp)
        except ValueError:
            continue  # ignore invalid
        functions.append((minion, jid, _get_success(minion, jid), timestring))
    return render_template('functions.html', functions=functions, successful_runs=len([success for _, _, success, _  in functions if success]))


@app.route('/functions/')
def functionsearch():
    if request.args.get('function', None):
        return redirect(url_for('functions', function=request.args.get('function')))
    return render_template('functionform.html')


@app.route('/')
def index():
    ''' return functions(app.config['DEFAULT_FUNCTION']) '''  # work around for mitsuhiko/werkzeug#382, if needed
    return redirect(url_for('functions', function=request.args.get('function', app.config['DEFAULT_FUNCTION'])))
