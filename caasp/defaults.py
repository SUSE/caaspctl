#
# Copyright 2018 SUSE LINUX GmbH, Nuernberg, Germany..
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
#
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Authors: (please add yourself when contributing)
#
#   - Alvaro Saurin <alvaro.saurin@suse.com>
#

# logging format
# https://docs.python.org/2/library/logging.html#logrecord-attributes
FORMAT = '# %(asctime)s [%(levelname)s] %(message)s'

# the version for this
VERSION = "0.1"

# some orchestrations and arguments
ORCH_BOOTSTRAP = 'kubernetes'
ORCH_UPDATE = 'update'
ORCH_OPTS = "-l debug --force-color --hard-crash"

# some key container (partial) names
CONTAINER_SALT_MASTER = "salt-master"
CONTAINER_SALT_API = "salt-api"
CONTAINER_VELUM = "velum-dashboard"
CONTAINER_MARIADB = "velum-mariadb"
CONTAINER_OPENLDAP = "openldap"

CONTAINER_START_TIMEOUT = 300

# where admin certificates will be generated to
CERT_ADMIN_DIR = "/root/certs"

UPDATE_GRAIN = "tx_update_reboot_needed"

# the database we use
DB_NAME = "velum_production"

# password file in the database container
DB_PASSWORD_FILE = '/var/lib/misc/infra-secrets/mariadb-root-password'

# command for inserting in the database, querying, etc...
# - pillar
DB_INSERT_PILLAR_CMD = \
    'DELETE FROM pillars WHERE pillar=\'{key}\' AND value=\'{value}\'; ' + \
    'INSERT INTO pillars (pillar, value) VALUES (\'{key}\', \'{value}\');'
DB_QUERY_PILLAR_CMD = 'SELECT * FROM pillars;'
DB_FLUSH_PILLAR_CMD = 'TRUNCATE TABLE pillars;'
# - minions
DB_QUERY_MINIONS_CMD = 'SELECT * FROM minions;'
# - events
DB_QUERY_EVENTS_CMD = 'SELECT data FROM salt_events ORDER BY alter_time;'
DB_FLUSH_EVENTS_CMD = 'TRUNCATE TABLE salt_events;'

# RC files that are automatically loaded on startup
# can be used for doing some actions or setting default values
CAASPCTL_RC_FILES = [
    '.caaspctl.rc',
    '.caaspctlrc',
    'caaspctl.rc',
    'caaspctlrc',
    '~/.caaspctl.rc',
    '~/.caaspctlrc',
    '~/caaspctl.rc',
    '~/caaspctlrc'
]

COLORS = {
    'HEADER': '\033[95m',
    'BLUE': '\033[94m',
    'GREEN': '\033[92m',
    'RED': '\033[91m',
    'ENDC': '\033[0m',
    'BOLD': '\033[1m',
    'UNDERLINE': '\033[4m'
}

PROMPT_COLORS = ['UNDERLINE', 'BLUE']
