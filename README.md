# `caaspctl`: a simple, scriptable _cli_ for CaaSP

## Installation

There are multiple ways you can install the `caaspctl` binary.

* you can build the rpm with `make dist-rpm` and install it in a
  CaaSP Amin Node with `transactional-update pkg install caaspctl.rpm`
  (see [the docs](https://www.suse.com/documentation/suse-caasp-3/singlehtml/book_caasp_admin/book_caasp_admin.html#sec.admin.software.transactional-updates.command)
  for more details). Once installed, the `caaspctl` will be available in
  the standard PATH.

* you can create an _"executable"_ zip with `make dist-zip`. This file can
  be copied to a CaaSP Admin Node. The `caaspctl` tool will need to be
  run with `python caaspctl.zip`.

## Usage

* You can enter the cli:

  ```bash
  $ caaspctl
  CaaSP control tool.
  
  caaspctl > config
  caaspctl:config > ?
  
  Documented commands (type help <topic>):
  ========================================
  db     get   load   quiet  refresh  shell  traceback
  flush  help  print  quit   set      stage
  
  Undocumented commands:
  ======================
  EOF  eval
  
  caaspctl:config > ? set
  
          Set a config in the database.
  
          Usage:
  
          > config set api:server:external_fqdn 192.168.122.4
          
  caaspctl:config > set api:server:external_fqdn 192.168.122.4
  ```

* You can run commands directly as arguments

  ```bash
  $ caaspctl config set api:server:external_fqdn 192.168.122.4
  ```

  or multiple commands by concatenating them with `;`:

```bash
  $ caaspctl 'minions accept 6 ; config set api:server:external_fqdn 192.168.122.4'
  ```

* or you can run all your commands in a script

  ```bash
  $ cat <<EOF>myscript.txt
  # accept all the three minions
  accept 3
  
  # and then set some config
  config set api:server:external_fqdn 192.168.122.4
  EOF
  
  $ caaspctl --script myscript.txt
  ```

### Development

* You can run the `caaspctl` command locally with `python -m caasp`.

## Status

Alpha, we are still fixing bugs...



