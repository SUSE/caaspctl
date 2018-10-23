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

import logging
import os
import re
import readline
import subprocess
import sys
import time
from datetime import datetime, timedelta

from .defaults import *
from .errors import CommandError, ContainerWaitTimeout, ContainerNotFoundException

readline.set_completer_delims(' \t\n')
log = logging.getLogger(__name__)


def execute(cmd, sudo=False, password=None):
    ''' Execute a command '''
    assert (isinstance(cmd, str))

    for line in cmd.splitlines():
        line = line.strip()
        if not line:
            continue

        if sudo:
            if password:
                cmd = "echo %s | sudo -S %s" % (password, line)
            else:
                cmd = "sudo -S %s" % (line)
        else:
            cmd = line

        log.debug('Running "%s"', cmd)
        popen = subprocess.Popen(
            cmd, shell=True, stdout=subprocess.PIPE, universal_newlines=True)
        for stdout_line in iter(popen.stdout.readline, ""):
            yield stdout_line

        popen.stdout.close()
        return_code = popen.wait()
        if return_code:
            raise subprocess.CalledProcessError(return_code, cmd)


def execute_interactive(cmd, sudo=False, password=None):
    ''' Execute an interactive command, returning the `retcode` '''
    assert (isinstance(cmd, str))

    if sudo:
        cmd = "echo %s | sudo -S %s" % (password, cmd)

    log.debug('Starting interactive command "%s"', cmd)
    return subprocess.call(cmd, shell=True)


def execute_now(cmd, strip_nls=True):
    res = []
    for line in cmd.splitlines():
        line = line.strip()
        if not line:
            continue

        out = str(subprocess.check_output(line, shell=True))
        if strip_nls:
            out = out.strip('\n')

        res.append(out)

    if strip_nls:
        return ' '.join(res)
    else:
        return '\n'.join(res)


#########################
# Containers
#########################

def get_regular_container(name):
    docker_ps_out = execute_now('docker ps')
    for line in docker_ps_out.split('\n'):
        fields = re.split('\s{2,}', line.strip())
        cid = fields[0]
        cname = fields[-1]
        if name in cname:
            return cid

    return None


def get_container(name):
    return get_regular_container("k8s_{name}_velum".format(name=name))


def get_cid(name):
    ''' Get the real container for an 'alias' (like 'db' or 'salt') '''
    if name in ['salt-master', 'salt']:
        return get_container(CONTAINER_SALT_MASTER)
    elif name in ['velum']:
        return get_container(CONTAINER_VELUM)
    elif name in ['mariadb', 'mysql', 'maria', 'db']:
        return get_container(CONTAINER_MARIADB)
    elif name in ['api', 'salt-api', 'API']:
        return get_container(CONTAINER_SALT_API)
    elif name in ['ldap', 'openldap']:
        return get_container(CONTAINER_OPENLDAP)
    else:
        return get_container(name)


def wait_for_container(name, timeout=CONTAINER_START_TIMEOUT):
    '''Wait for a container to be up and running'''
    timeout_limit = datetime.now() + timedelta(seconds=timeout)
    while datetime.now() <= timeout_limit:
        try:
            cid = get_cid(name)
            if cid:
                log.debug('container %s is running with ID %s', name, cid)
                return
        except:
            pass

        log.debug('docker: waiting for "{}" ({} left)...'.format(
            name, timeout_limit - datetime.now()))
        time.sleep(5)

    raise ContainerWaitTimeout('timeout while waiting for {}'.format(name))


def exec_in_container(name, cmd, wait=False):
    ''' Run a command in a container '''
    if wait:
        wait_for_container(name)

    try:
        c = get_cid(name)
    except Exception as e:
        log.debug('could not find container %s: %s', name, e)
        c = None

    if not c:
        raise ContainerNotFoundException(
            'could not find container {name}'.format(name=name))

    cmd = 'docker exec {} {}'.format(c, cmd)
    log.debug('docker: executing in "%s" command "%s"', c, cmd)
    for line in execute(cmd):
        if line:
            yield line


# TODO: how to invoke a rake task??
def exec_rake_task(task, *args, **kargs):
    ''' Run a rake task in the Velum container '''
    log.debug('rake: executing Rake task "%s"', task)
    cmd = "rake ".format()
    for line in exec_in_container("velum", cmd, wait=True):
        yield line


#########################
# database
#########################


def get_db_password(filename=DB_PASSWORD_FILE):
    ''' Get the database password '''
    cmd = 'cat ' + filename
    for line in exec_in_container('db', cmd, wait=True):
        return line.strip()  # return only the first line


def exec_sql_in_db(cmd, **kwargs):
    ''' Run a SQL command in the database '''
    password = get_db_password()
    log.debug('Using password %s', password)
    cmd = 'mysql -uroot -p\'{password}\' -B -t -e "{cmd}" {db}'.format(
        cmd=cmd, db=DB_NAME, password=password)
    for line in exec_in_container('db', cmd, **kwargs):
        yield line


def wait_for_db(db=None, timeout=CONTAINER_START_TIMEOUT):
    ''' Wait for a specific database to be ready '''
    db = db or DB_NAME
    password = get_db_password()
    log.debug('using password %s', password)

    timeout_limit = datetime.now() + timedelta(seconds=timeout)
    while datetime.now() <= timeout_limit:
        try:
            for line in exec_sql_in_db('SHOW DATABASES;'):
                if db in line:
                    log.debug('Database "%s" seems to be ready', db)
                    return
        except:
            pass

        log.info("Waiting for database {} ({} left)...".format(
            db, timeout_limit - datetime.now()))
        time.sleep(5)

    raise ContainerWaitTimeout(
        'timeout while waiting for database {}'.format(db))


# TODO: remove this and use some rake tasks for adding new pillars
def pillar_db_insert(key, value, **kwargs):
    ''' Insert a value for a pillar (replacing any previous value) '''
    log.info('Adding pillar "%s"="%s"', key, value)
    cmd = DB_INSERT_PILLAR_CMD.format(**locals())
    for line in exec_sql_in_db(cmd, **kwargs):
        yield line


#########################
# Salt
#########################


def get_salt_where_from(name):
    if not name:
        return '*'

    try:
        return {
            '*': '*',
            'all': '*',
            'cluster': '*',
            'ca': 'G@roles:ca',
            'admin': 'G@roles:admin',
            'kube-master': 'G@roles:kube-master',
            'kube-masters': 'G@roles:kube-master',
            'master': 'G@roles:kube-master',
            'masters': 'G@roles:kube-master',
            'kube-minion': 'G@roles:kube-minion',
            'kube-minions': 'G@roles:kube-minion',
            'minion': 'G@roles:kube-minion',
            'minions': 'G@roles:kube-minion',
            'nodes': 'P@roles:kube-(master|minion)',
            'workers': 'P@roles:kube-(master|minion)'
        }[name.lower()]
    except KeyError:
        return name


def exec_in_salt(cmd,
                 compound=None,
                 color=False,
                 newlines=True,
                 ignore_stderr=True,
                 out=None,
                 salt_args='',
                 debug=False,
                 **kwargs):
    debug_level = 'critical' if not debug else 'debug'
    color_arg = '--force-color' if color else '--no-color'

    if compound:
        compound_arg = " -C '{}'".format(get_salt_where_from(compound))
    else:
        compound_arg = ''

    cmd_args = '{compound_arg} --log-level={debug_level} {salt_args} '.format(
        **locals())

    if out:
        cmd_args += ' --out={} --out-indent=4'.format(out)
    elif newlines:
        cmd_args += ' --out=newline_values_only '

    # TODO: add other matchers

    cmd = '/usr/bin/salt {cmd_args} {cmd}'.format(**locals())
    if ignore_stderr:
        cmd = cmd + ' 2>/dev/null'

    for line in exec_in_container('salt', cmd, **kwargs):
        if line:
            yield line


def exec_salt_runner(cmd, **kwargs):
    opts = kwargs.pop('salt_args', ORCH_OPTS)
    cmd = '/usr/bin/salt-run {} --force-color {}'.format(opts, cmd)
    for line in exec_in_container('salt-master', cmd, **kwargs):
        yield line


def exec_salt_key(cmd, **kwargs):
    cmd = '/usr/bin/salt-key --force-color ' + cmd
    for line in exec_in_container('salt-master', cmd, **kwargs):
        yield line


def get_salt_keys(status='all'):
    for line in exec_salt_key('-l ' + status, wait=True):
        yield line


def get_salt_keys_accepted():
    for line in get_salt_keys(status='acc'):
        yield line


def get_salt_keys_rejected():
    for line in get_salt_keys(status='rej'):
        yield line


def get_salt_keys_accepted_num():
    out = list(exec_salt_key('-l acc', wait=True))
    return len(out[1:])


def wait_for_num_keys_accepted(num_keys, timeout=CONTAINER_START_TIMEOUT):
    log.info("Waiting for %d Salt keys to be accepted...", num_keys)
    wait_for_container('salt')

    timeout_limit = datetime.now() + timedelta(seconds=timeout)
    while datetime.now() <= timeout_limit:
        # accept all the pending keys
        # this will fail if no keys have been submitted yet
        try:
            for line in exec_salt_key('--accept-all --yes'):
                yield line
        except:
            pass

        num_accepted = get_salt_keys_accepted_num()
        if num_accepted >= num_keys:
            return

        log.info("Waiting for %d Salt keys to be accepted: %d accepted (%s secs left)...",
                 num_keys, num_accepted, str(timeout_limit - datetime.now()))
        time.sleep(5)

    raise ContainerWaitTimeout(
        'timeout waiting for {} to be accepted'.format(num_keys))


SALT_AVAIL_SYNC = ['all', 'engines', 'grains', 'beacons', 'utils', 'returners',
                   'modules', 'renderers', 'log_handlers', 'states', 'sdb', 'proxymodules', 'output']


def salt_sync(what='all'):
    what = what.strip().lower()
    if what not in SALT_AVAIL_SYNC:
        raise CommandError('unknown sync target "{}"'.format(what))

    log.info('Synchronizing %s', what)
    cmd = 'saltutil.sync_{} refresh=True'.format(what)
    for line in exec_in_salt(cmd, compound='*', wait=True):
        yield line


def grain_set(where, key, value):
    log.info("Setting grain %s=%s in %s", key, value, where)
    cmd = 'grains.set "{}" "{}"'.format(key, value)
    for line in exec_in_salt(cmd, compound=where, wait=True):
        yield line


def grain_append(where, key, value):
    log.info("Appending grain %s=%s in %s", key, value, where)
    cmd = 'grains.append "{}" "{}"'.format(key, value)
    for line in exec_in_salt(cmd, compound=where, wait=True):
        yield line


def grain_get(where, key):
    log.info("Getting grain %s in %s", key, where)
    cmd = 'grains.get {}'.format(key)
    for line in exec_in_salt(cmd, compound=where, wait=True):
        yield line


def grain_ls(where):
    log.info("Listing grains (in '%s')", where)
    cmd = 'grains.ls'
    for line in exec_in_salt(cmd, compound=where, wait=True):
        yield line


def grain_items(where):
    log.info("Listing grains (in '%s')", where)
    cmd = 'grains.items'
    for line in exec_in_salt(cmd, compound=where, wait=True, out='yaml'):
        yield line


#########################
# aux
#########################


def get_role_nodenames(role, timeout=CONTAINER_START_TIMEOUT):
    ''' Get the nodename for all the nodes with a specific role '''
    log.debug("get-role-nodenames: getting nodenames for {}...".format(role))
    timeout_limit = datetime.now() + timedelta(seconds=timeout)
    while datetime.now() <= timeout_limit:
        try:
            for line in grain_get(role, 'nodename'):
                yield line
        except Exception as e:
            log.warning(
                'get-role-nodenames: while waiting for nodename for %s: %s', role, e)

        log.debug("get-role-nodenames: waiting for result for {} ({} left)...".format(
            role, timeout_limit - datetime.now()))
        time.sleep(5)

    raise Exception('could not get nodename for {}'.format(role))


#########################
# Output/conversions
#########################


def replace_pattern(pat, replacer, line):
    for t in re.finditer(pat, line):
        txt = str(t.group())
        out = replacer(txt)
        line = line.replace(txt, out)
    return line


def value_to_native(val):
    if isinstance(val, str):
        try:
            return int(val)
        except ValueError:
            pass

        if val.lower() in ["true", "yes", "on"]:
            return True
        elif val.lower() in ["false", "no", "off"]:
            return False

        val = os.path.expandvars(val)

        # in case it is a quoted string, remove them
        if val[0] in ['\'', '"']:
            return val[1:-1]

    return val


def expandvars(path):
    return re.sub(r'(?<!\\)\$[A-Za-z_][A-Za-z0-9_]*', '', os.path.expandvars(path))


def on_color(color, txt):
    res = ''
    if isinstance(color, list):
        res += ''.join([COLORS[x] for x in color])
    else:
        res += COLORS[color]

    return res + txt + COLORS['ENDC']


def prompt(txt):
    return on_color(PROMPT_COLORS, '{} >'.format(txt)) + ' '


def print_iterator(it, **kwargs):
    for line in it:
        sys.stdout.write(line)
