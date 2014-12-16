DEBUG = False

# If set to false, flask's url handling will be used for external libraries.
# The static directory contains a script to download all dependencies.
USE_CDN = True

# This configures the function list shown in the webinterface's navbar.
FUNCTION_QUICKLIST = ['state.highstate', 'state.sls', 'pkg.upgrade', 'test.ping']

REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_PASS = None
