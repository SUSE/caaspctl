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

import argparse

from .apply import CaaSPApply
from .cmdbase import CmdBase
from .common import *
from .config import CaaSPConfig
from .nodes import CaaSPNodes
from .roles import CaaSPRoles

#
# Command line arguments
#
parser = argparse.ArgumentParser(
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    description='A utility for managing CaaSP',
    epilog="")

parser.add_argument('args',
                    nargs=argparse.REMAINDER,
                    help='commands to run (get more info with "help")')

verbose_group = parser.add_argument_group(
    title='Logging/verbosity')

verbose_group.add_argument('--debug',
                           dest='debug',
                           default=False,
                           action='store_true',
                           help='use debug logging')

script_group = parser.add_argument_group(
    title='Loading commands from scripts')

script_group.add_argument('--script',
                          dest='script',
                          metavar='FILE',
                          default='',
                          help='read a list of commands from a script')
script_group.add_argument('--script-only',
                          dest='script_only',
                          default=True,
                          action='store_true',
                          help='quit after running the script')
script_group.add_argument('--script-begin',
                          dest='script_begin',
                          metavar='STAGE',
                          default='',
                          help='process the script after stage <STAGE>')

commands_group = parser.add_argument_group(
    title='Commands processing',
    description='How commands are processed from command line or from the loop')

commands_group.add_argument('--loop',
                            dest='loop',
                            default=False,
                            action='store_true',
                            help='the loop is only started when no commands are provided in command line. With this flag, the loop is started even when commands are provided as arguments')
commands_group.add_argument('--commands-pre',
                            dest='commands_pre',
                            default=False,
                            action='store_true',
                            help='process commands from arguments BEFORE processing scripts')
commands_group.add_argument('--exit-on-error',
                            dest='exit_on_err',
                            default=False,
                            action='store_true',
                            help='exit on any errors instead of just printing the error message')
commands_group.add_argument('--skip-rc-files',
                            dest='skip_rc_files',
                            default=False,
                            action='store_true',
                            help='do not load automatically the RC files')

readline.set_completer_delims(' \t\n')


class CaaSP(CmdBase):
    """ CaaSP command line """

    prompt = prompt('caaspctl')
    intro = "CaaSP control tool.\n"

    def __init__(self, args):
        CmdBase.__init__(self, args)
        self.config = CaaSPConfig(self, args)
        self.apply = CaaSPApply(self, args)
        self.nodes = CaaSPNodes(self, args)
        self.roles = CaaSPRoles(self, args)

    def _subcommand(self, sub_cmd, line):
        if len(line) > 0:
            sub_cmd.onecmd(line)
        else:
            sub_cmd.cmdloop()

    def do_config(self, line):
        '''Configuration variables.'''
        self._subcommand(self.config, line)

    def do_apply(self, line):
        '''Apply changes to the cluster.'''
        self._subcommand(self.apply, line)

    def do_nodes(self, line):
        '''Nodes management.'''
        self._subcommand(self.nodes, line)

    def do_roles(self, line):
        '''Roles for nodes.'''
        self._subcommand(self.roles, line)

    def do_version(self, line):
        '''
        Print the version.
        '''
        print(VERSION)
        return True


def main():
    args = parser.parse_args()

    loglevel = (logging.DEBUG if args.debug else logging.INFO)
    log = logging.getLogger(__name__)
    logging.basicConfig(stream=sys.stderr,
                        format=FORMAT,
                        level=loglevel)

    try:
        import coloredlogs

        # By default the install() function installs a handler on the root logger,
        # this means that log messages from your code and log messages from the
        # libraries that you use will all show up on the terminal.
        coloredlogs.install(fmt=FORMAT, level=loglevel)
    except ImportError:
        log.debug('"coloredlogs" not available')

    caasp_cmd = CaaSP(args)

    if not args.skip_rc_files:
        caasp_cmd.try_rc_files(CAASPCTL_RC_FILES)

    if len(args.args) > 0 and args.commands_pre:
        caasp_cmd.command_line_args(args.args)

    if args.script:
        if args.script_begin:
            log.info('Will start execution at stage "%s"', args.script_begin)
            caasp_cmd.blocked = True

        for script in args.script:
            try:
                caasp_cmd.load_script(script)
            except Exception as e:
                log.critical('Could not read file %s: %s', script, e)
                sys.exit(1)

        caasp_cmd.blocked = False

        if args.script_only:
            log.debug('we were running only scripts: exitting...')
            sys.exit(0)

    if len(args.args) > 0 and not args.commands_pre:
        caasp_cmd.command_line_args(args.args)

    if not args.args or args.loop:
        caasp_cmd.cmdloop()


if __name__ == "__main__":
    main()
