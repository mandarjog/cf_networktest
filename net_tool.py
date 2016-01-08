import requests
import os
import os.path
from flask import Flask, request, redirect
from flask.ext.autodoc import Autodoc
import urllib
import socket
import time

# The following are imported so that these are
# in debug context when needed
import netifaces
import sh


app = Flask(__name__)
auto = Autodoc(app)
port = os.getenv('VCAP_APP_PORT', os.getenv('PORT', '5000'))
tempdir = os.getenv('TMPDIR', '/tmp')

INFO_URL = "https://github.com/status.json"


def is_running(pid):
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def remove_params_and_redirect(params):
    ldict = {k: v for k, v in request.args.iteritems() if k not in params}
    return redirect("{}?{}".format(request.path, urllib.urlencode(ldict)))

NOCACHE = "_nocache"


def run_async(shCmd, host, **kwargs):
    """
    Run an sh command in async mode
    This takes care of _nocache flag and meta refresh
    so any command can be run this way
    """
    hostfile = tempdir + '__{}__'.format(shCmd._path.replace('/', '_')) + host
    pidfile = hostfile + ".pid"
    refresh = """<meta http-equiv="refresh" content="3">"""
    redo = """<a href="{}?{}=1"> Rerun </a>""".format(request.path, NOCACHE)

    if not os.path.isfile(hostfile) or request.args.get(NOCACHE):
        cmd = shCmd(host, _bg=True, _out=hostfile, **kwargs)
        with open(pidfile, "wt") as fl:
            print >> fl, cmd.pid

        if request.args.get(NOCACHE):
            return remove_params_and_redirect([NOCACHE])

    with open(hostfile, "rt") as fl:
        resp = "<pre>" + fl.read() + "</pre>"

    proc_start = os.stat(pidfile).st_ctime
    proc_now = os.stat(hostfile).st_mtime
    with open(pidfile, "rt") as fl:
        pid = int(fl.read())
        if is_running(pid):
            cmdtime = int(time.time()) - proc_start
            resp = (refresh +
                    "\nRunning with pid {}, {} sec \n".format(pid, cmdtime) +
                    resp)
        else:
            cmdtime = proc_now - proc_start
            resp = redo + " ({} sec)\n".format(cmdtime) + resp

    return resp


@app.route('/get/<url>')
@auto.doc()
def get(url):
    """
    attempt an HTTP GET request to the specified url
    """
    if not url.startswith("http"):
        url = "http://" + url

    return ("url: " + url + "\n<p>response:" +
            requests.get(url, timeout=5.0, verify=False).text)


@app.route('/resolve/<host>')
@auto.doc()
def resolve(host):
    """
    resolve host using socket
    """
    return socket.gethostbyname(host)


@app.route('/traceroute/<host>')
@auto.doc()
def traceroute(host):
    """
    run platform traceroute in asynchronous mode
    """
    from sh import traceroute as shCmd
    return run_async(shCmd, host)


@app.route('/ping/<host>')
@auto.doc()
def ping(host):
    """
    run platform ping in asynchronous mode
    """
    from sh import ping as shCmd
    return run_async(shCmd, host, c="10")


@app.route('/dig/<host>')
@auto.doc()
def dig(host):
    """
    run platform dig in asynchronous mode
    """
    from sh import dig as shCmd
    return run_async(shCmd, host)


@app.route('/')
def health():
    return auto.html()


if __name__ == "__main__":
    print "Starting on port =", port
    app.run(host='0.0.0.0', port=int(port), debug=True)
