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

import os
import glob as gb
import traceback
from cmd import Cmd

from .common import *
from .errors import CommandError


def complete_path(path):
    if os.path.isdir(path):
        return gb.glob(os.path.join(path, '*'))
    else:
        return gb.glob(path + '*')


class CmdBase(Cmd):
    '''
    Base for all the command-line processing classes
    '''

    def __init__(self, args, top=None):
        Cmd.__init__(self)
        self.args = args
        self.last_exc = None
        self.blocked = False
        self.current_script = ''
        self.top = top

    def abort(self):
        self.do_traceback('')
        log.critical(on_color('RED', 'aborting execution'))
        sys.exit(1)

    def is_interactive(self):
        if self.top:
            return self.top.is_interactive()
        else:
            return (self.stdin == sys.stdin)

    def command_line_args(self, cmd_args):
        line = ' '.join(cmd_args)
        for command in line.split(';'):
            self.onecmd(command)

    def onecmd(self, line):
        try:
            if not self.blocked or line == 'EOF' or line.startswith('stage'):
                return Cmd.onecmd(self, line)
            else:
                return False
        except subprocess.CalledProcessError as e:
            log.info(on_color('RED', 'Command error: ' + str(e)))
            if self.args.exit_on_err or not self.is_interactive():
                self.abort()
        except KeyboardInterrupt as e:
            log.info(on_color('RED', '[interrupted]'))
            if self.args.exit_on_err or not self.is_interactive():
                self.last_exc = sys.exc_info()
                self.abort()

    def cmdloop(self, intro=None):
        if self.intro:
            print(self.intro)

        while True:
            try:
                Cmd.cmdloop(self, intro="")
                self.postloop()
                break
            except subprocess.CalledProcessError as e:
                log.info(on_color('RED', 'Command error: ' + str(e)))
                if self.args.exit_on_err or not self.is_interactive():
                    self.abort()
            except KeyboardInterrupt as e:
                log.info(on_color('RED', '[interrupted]'))
                if self.args.exit_on_err or not self.is_interactive():
                    self.last_exc = sys.exc_info()
                    self.abort()
            except Exception as e:
                self.last_exc = sys.exc_info()

                if not self.is_interactive():
                    # we are running in batch mode
                    log.critical(
                        on_color('RED', 'exception catched in batch mode: %s'), e)
                    self.abort()

                log.critical(on_color('RED', 'exception catched !!! %s'), e)
                log.critical(
                    on_color('RED', 'get more details with "traceback".'))

    def precmd(self, line):
        if line.lstrip().startswith('#'):
            return ''

        if len(line.strip()) == 0:
            return line

        # replace all the `some-shell-command`
        def sh_replacer(text):
            cmd = text[1:-1]  # remove the ``
            log.debug('replacing %s by shell output', cmd)
            out = subprocess.check_output(
                cmd, stderr=subprocess.STDOUT, shell=True)
            return out.decode('utf-8').rstrip()

        line = replace_pattern(r"`.*`", sh_replacer, line)

        # replace all the {% some-python-code %}
        def python_replacer(text):
            code = text[2:-2]  # remove the {%%}
            log.debug('replacing %s by python evaluation', code)
            return str(self.eval(code))

        line = replace_pattern(r"\{\%.*\%\}", python_replacer, line)

        line = expandvars(line)

        return line

    def default(self, line):
        line = line.lstrip()

        if line.startswith('>'):
            # evaluate python code
            return self.do_eval(line[1:])

        if line.startswith('!'):
            # run a local command
            return self.do_shell(line[1:])

        if line == '..':
            return True

        Cmd.default(self, line)

    def try_rc_files(self, rc_files):
        log.debug('Trying to load RC files...')
        for maybe_rc_file in rc_files:
            maybe_rc_file = os.path.expandvars(maybe_rc_file)
            if os.path.exists(maybe_rc_file):
                try:
                    self.load_script(maybe_rc_file)
                except Exception as e:
                    log.critical('Could not read rc file %s: %s',
                                 maybe_rc_file, e)
                    sys.exit(1)

    def load_script(self, script):
        log.info('Loading commands from "%s"', script)

        old_stdin = self.stdin
        old_prompt = self.prompt
        old_intro = self.intro
        old_use_rawinput = self.use_rawinput

        self.use_rawinput = False
        self.prompt = ''
        self.intro = ''
        self.current_script = os.path.abspath(script)

        try:
            with open(script, 'rt') as script_fd:
                self.stdin = script_fd
                self.cmdloop()
        finally:
            script_fd.close()

            # restore the previous settings
            self.stdin = old_stdin
            self.prompt = old_prompt
            self.intro = old_intro
            self.use_rawinput = old_use_rawinput
            self.current_script = ''

    def do_load(self, line):
        '''
        Load a script with commands.
        '''
        filename = line
        if not os.path.isabs(filename):
            this_filename = os.path.realpath(__file__)
            this_dirname = os.path.dirname(this_filename)
            cur_script_dirname = os.path.dirname(self.current_script)

            log.debug('try to guess the real name of %s', filename)
            for i in [filename,
                      os.path.join(this_dirname, filename),
                      os.path.join(cur_script_dirname, filename)]:
                log.debug('trying %s', i)
                if os.path.exists(i):
                    filename = i
                    break

        if os.path.exists(filename):
            self.load_script(filename)
        else:
            log.error('could not load script at %s', filename)

    def complete_do_load(self, text, line, start_idx, end_idx):
        return complete_path(text)

    def do_shell(self, line):
        '''
        Run a shell command in the local machine.
        Notes:

        * there is shortcut with the ! character (ie, "! ls -lisa")

        Usage:

        > sh ls /
        > sh cat README.txt
        > ! ls /
        '''
        if execute_interactive(line) != 0:
            log.error('command failed')

    def do_traceback(self, line):
        '''Get a traceback for the last exception. '''
        if self.last_exc:
            traceback.print_exception(*self.last_exc)
            self.last_exc = None

    def do_quiet(self, line):
        '''Set quiet mode.'''
        logging.basicConfig(stream=sys.stderr,
                            format=FORMAT,
                            level=logging.INFO)

    def do_print(self, line):
        '''Quit.'''
        log.info(line)

    def do_EOF(self, line):
        return True

    def do_quit(self, line):
        '''Quit.'''
        return self.do_EOF(line)

    def eval(self, code):
        gl = globals()
        return eval(code, {'root': gl['caasp_cmd']}, {})

    def do_eval(self, line):
        print(self.eval(line))

    def emptyline(self):
        # ignore empty lines instead of repeating last command
        pass

    def do_stage(self, line):
        '''
        Mark the beginning of a new stage.
        '''
        if not line:
            raise CommandError('no stage specified')

        stage = line
        log.debug('reached stage "%s" (waiting "%s")s',
                  stage, self.args.script_begin)
        if str(stage) == str(self.args.script_begin):
            log.debug('stage %s reached: unblocking input', self.args.script_begin)
            self.blocked = False
