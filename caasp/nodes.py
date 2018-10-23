#!/usr/bin/env python
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

from .cmdbase import CmdBase
from .common import *

log = logging.getLogger(__name__)

###################
# Minions
###################

class CaaSPNodes(CmdBase):
    prompt = prompt('caaspctl:nodes')

    def do_db(self, line):
        log.info('Getting the list of nodes from the database')
        print_iterator(exec_sql_in_db(DB_QUERY_MINIONS_CMD, wait=True))

    def do_ls(self, line):
        '''
        List all the nodes the Salt master knows about.
        '''
        print_iterator(get_salt_keys())

    def do_accepted(self, line):
        '''
        Print the nodes accepted
        '''
        log.info('Minions accepted')
        print_iterator(get_salt_keys_accepted())

    def do_num_accepted(self, line):
        '''
        Print the number of nodes accepted so far.
        '''
        log.info('Number of nodes accepted')
        print(get_salt_keys_accepted_num())

    def do_accept(self, line):
        '''
        Block waiting for (at least) NUM nodes to be accepted

        Usage:

        # block waiting until 6 nodes have been accepted
        > accept 6
        '''
        if not line:
            raise CommandError('must provide a number')

        num = int(line)

        log.info('Waiting for (at least) %d nodes to be accepted', num)
        print_iterator(wait_for_num_keys_accepted(num))
        print_iterator(get_salt_keys_accepted())

    def do_rejected(self, line):
        '''
        Print the list of nodes that have been rejected.
        '''
        log.info('Minions rejected')
        print_iterator(get_salt_keys_rejected())

    def do_masters(self, line):
        '''
        Print the list of nodes where the kube-master role has been assigned
        '''
        log.info('Masters:')
        print_iterator(get_role_nodenames('masters'))

    def do_nodes(self, line):
        '''
        Print the list of nodes where the kube-minion role has been assigned
        '''
        log.info('Minions:')
        print_iterator(get_role_nodenames('nodes'))

