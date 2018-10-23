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


# TODO: this must be replaced for some rake tasks for assigning roles to nodes
class CaaSPRoles(CmdBase):
    prompt = prompt('caaspctl:roles')

    def do_set(self, line):
        '''
        Set the role for a node.

        Usage:

        # set the master role in a node
        > roles set '5dbc5880c5284d6a8df0813aaa975bf9' kube-master
        '''
        line = line.strip()
        line_comps = [] if not line else line.split(' ')

        if len(line_comps) != 2:
            raise CommandError(
                'set requires three arguments: where and role')

        where, value = line_comps[0].strip(), line_comps[1].strip()
        log.info('Setting the %s role at %s', value, where)
        print_iterator(grain_append(where, "roles", value))

    def do_get(self, line):
        '''
        Get the role for a node

        Usage:

        > roles get '5dbc5880c5284d6a8df0813aaa975bf9'
        '''
        line = line.strip()

        if len(line) == 0:
            line = '*'

        log.info('Getting roles at %s', line)
        print_iterator(grain_get(line, "roles"))