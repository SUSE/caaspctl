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

import json

from .cmdbase import CmdBase
from .common import *
from .errors import OrchestrationFailure


class CaaSPApply(CmdBase):
    prompt = prompt('caaspctl:apply')

    def _run_orchestration(self, orch, orch_args='', pillar={}):
        assert (orch)
        orchestration = orch or ORCH_BOOTSTRAP

        log.info('orchestration: starting "%s"...', orch)

        if pillar:
            orch_args += ' pillar=\'{}\''.format(
                json.dumps(pillar, separators=(',', ':')))

        if len(orch_args) > 0:
            log.info('orchestration: arguments: %s', orch_args)

        print_iterator(salt_sync())

        log.info('orchestration: doing %s for real...', orch)
        cmd = 'state.orchestrate orch.{orch} {orch_args}'.format(**locals())
        try:
            for line in exec_salt_runner(cmd, salt_args=ORCH_OPTS):
                sys.stdout.write(line)
        except Exception as e:
            raise OrchestrationFailure(
                'orchestration {} failed: {}'.format(orch, e))
        else:
            log.info('orchestration: %s finished', orch)

    def do_bootstrap(self, line):
        '''
        Run the bootstrap orchestration.
        '''
        self._run_orchestration(ORCH_BOOTSTRAP, line)

    def do_update(self, line):
        '''
        Run the update orchestration.
        '''
        self._run_orchestration(ORCH_UPDATE, line)
