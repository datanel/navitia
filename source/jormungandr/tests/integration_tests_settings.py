# encoding: utf-8

import logging

# Start the thread at startup, True in production, False for test environments
START_MONITORING_THREAD = False

#URI for postgresql
# postgresql://<user>:<password>@<host>:<port>/<dbname>
#http://docs.sqlalchemy.org/en/rel_0_9/dialects/postgresql.html#psycopg2
SQLALCHEMY_DATABASE_URI = 'postgresql://navitia:navitia@localhost/jormun'

# disable authentication
PUBLIC = True

REDIS_HOST = 'localhost'

REDIS_PORT = 6379

# index of the redis data base used (integer from 0 to 15)
REDIS_DB = 0

REDIS_PASSWORD = None

# disable the redis cache (if no cache, redis is not used at all)
CACHE_DISABLED = False

# life time tfo authentication data, in the cache (in seconds)
AUTH_CACHE_TTL = 300

# logger configuration
LOGGER = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'default': {
            'level': 'INFO',
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout"
        },
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'level': 'DEBUG',
            'propagate': True
        },
    }
}