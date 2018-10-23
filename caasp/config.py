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


from .common import *
from .errors import CommandError
from .cmdbase import CmdBase

log = logging.getLogger(__name__)


class CaaSPConfig(CmdBase):

    prompt = prompt('caaspctl:config')

    def do_set(self, line):
        '''
        Set some config variable

        Usage:

        > config set api:server:external_fqdn 192.168.122.4
        '''
        line = line.strip()
        line_comps = [] if not line else line.split(' ')

        if len(line_comps) != 2:
            raise CommandError(
                'set requires two arguments: the key and the value')

        key, value = line_comps[0].strip(), line_comps[1].strip()
        log.info('Setting the %s to %s', key, value)
        print_iterator(pillar_db_insert(key, value, wait=True))

    def do_load(self, line):
        '''
        Load config variables from a file

        The file is expected to be formed by lines with with form "<KEY> <VALUE>".

        Usage:

        $ cat <<EOF>/etc/caasp-config.lst
        addons:tiller   true
        addons:dns      true
        EOF

        > config load /etc/caasp-config.lst
        '''
        filename = line
        log.info('Loading config variables from %s', filename)
        wait_for_db()
        with open(filename, 'r') as f:
            for line in f.readlines():
                line = line.strip()

                if not line or line.startswith('#'):
                    continue

                line_comps = re.split('\s{2,}', line.strip())
                if len(line_comps) < 2:
                    log.error('could not parse config variable: "%s"', line)
                    continue

                key, value = line_comps[0].strip(), line_comps[1].strip()
                print_iterator(pillar_db_insert(key, value))

    def do_get(self, line):
        '''
        Get a config variable.

        Usage:

        > config get api:server:external_fqdn
        '''
        line = line.strip()
        line_comps = [] if not line else line.split(' ')

        if len(line_comps) >= 2:
            key, where = line_comps
            cmd = 'pillar.get {key}'.format(**locals())
        elif len(line_comps) == 1:
            print(line_comps)
            where = 'ca'
            key = line_comps[0]
            cmd = 'pillar.get {key}'.format(**locals())
        else:
            where = 'ca'
            key = 'all'
            cmd = 'pillar.items'.format(**locals())

        log.info('Getting %s at %s', key, where)
        out_it = exec_in_salt(cmd, compound=where,
                              color=True, out='yaml', wait=True)
        print_iterator(out_it)

    # TODO: this should probably be removed...
    def do_db(self, line):
        '''
        Get the list of config variables in the database.

        Usage:

        > pillar db
        '''
        log.info('Getting pillar database')
        print_iterator(exec_sql_in_db(DB_QUERY_PILLAR_CMD, wait=True))

    # TODO: this should probably be removed...
    def do_flush(self, line):
        '''
        Flush the config variables database.

        Important: this will not get rid of all the pillars Salt
                   obtains from the pillar/*.sls files.

        Usage:

        > pillar flush
        '''
        log.info('Flushing pillar database')
        print_iterator(exec_sql_in_db(DB_FLUSH_PILLAR_CMD, wait=True))

    # TODO: this should probably be removed...
    def do_refresh(self):
        '''
        Refresh the config vars populated to minions.
        '''
        log.info('Refreshing pillars')
        print_iterator(exec_in_salt('saltutil.refresh_pillar', compound='*'))

