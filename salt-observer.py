from flask import Flask, Response
from flask import render_template, make_response, redirect, url_for, request, abort
from flask_sockets import Sockets

import time
import fnmatch
import gevent
from redis import Redis

app = Flask(__name__)
app.debug=True
sockets = Sockets(app)

@app.route('/_get_function_data/<minion>/<jid>')
def get_function_data(minion, jid):
    data = redis.get('{0}:{1}'.format(minion, jid))
    return Response(response=data, status=200, mimetype="application/json")

@app.route('/jobs/<jid>')
def job(jid):
    ret = list()
    for minion in redis.keys('*:%s' % jid):
        ret.append(minion.split(':')[0])
    timestamp = time.strptime(jid, "%Y%m%d%H%M%S%f")
    return render_template('jobs.html', minions=ret, time=time.strftime('%Y-%m-%d, at %H:%M:%S', timestamp))

@app.route('/jobs')
def jobsearch():
    # get param or
    if request.args.get('job', None):
        return redirect(url_for('jobsearch', function=request.args.get('job')))
    return render_template('jobform.html')

@app.route('/history/<minion>/<function>')
def history(minion, function):
    ret = list()
    try:
        for jid in redis.lrange('{0}:{1}'.format(minion, function), 0, -1):
            timestamp = time.strptime(jid, "%Y%m%d%H%M%S%f")
            ret.append((jid, time.strftime('%Y-%m-%d, at %H:%M:%S', timestamp)))
    except Exception:
        pass
    return render_template('history.html', jids=ret)

@app.route('/history')
def historysearch():
    if request.args.get('minion', None) and request.args.get('function', None):
        return redirect(url_for('history', minion=request.args.get('minion'), function=request.args.get('function')))
    return render_template('historyform.html')

@app.route('/functions/<function>')
def function(function):
    ret = list()
    for minion in redis.sort('minions', alpha=True):
        try:
            jid = redis.lindex('{0}:{1}'.format(minion, function), 0)
            timestamp = time.strptime(jid, "%Y%m%d%H%M%S%f")
            ret.append((minion, jid, time.strftime('%Y-%m-%d, at %H:%M:%S', timestamp)))
        except Exception:
            continue
    return render_template('functions.html', functions=ret)

@app.route('/functions')
def functionsearch():
    # get param or
    if request.args.get('function', None):
        return redirect(url_for('functions', function=request.args.get('function')))
    return render_template('functionform.html')

@app.route('/')
def functions():
    # get param or default, but always redirect to function view
    return redirect(url_for('function', function=request.args.get('function', 'state.highstate')))
