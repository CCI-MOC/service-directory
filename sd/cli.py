# Copyright 2013-2014 Massachusetts Open Cloud Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the
# License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an "AS
# IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied.  See the License for the specific language
# governing permissions and limitations under the License.

"""This module implements the HaaS command line tool."""
from haas import config
from haas.config import cfg

import logging
import inspect
import sys
import urllib
import requests

from functools import wraps

command_dict = {}
usage_dict = {}

def cmd(f):
    """A decorator for CLI commands.

    This decorator firstly adds the function to a dictionary of valid CLI
    commands, secondly adds exception handling for when the user passes the
    wrong number of arguments, and thirdly generates a 'usage' description and
    puts it in the usage dictionary.
    """
    @wraps(f)
    def wrapped(*args, **kwargs):
        try:
            f(*args, **kwargs)
        except TypeError:
            # TODO TypeError is probably too broad here.
            sys.stderr.write('Wrong number of arguements.  Usage:\n')
            help(f.__name__)
    command_dict[f.__name__] = wrapped
    def get_usage(f):
        args, varargs, _, _ = inspect.getargspec(f)
        showee = [f.__name__] + ['<%s>' % name for name in args]
        args = ' '.join(['<%s>' % name for name in args])
        if varargs:
            showee += ['<%s...>' % varargs]
        return ' '.join(showee)
    usage_dict[f.__name__] = get_usage(f)
    return wrapped


def check_status_code(response):
    if response.status_code < 200 or response.status_code >= 300:
        sys.stderr.write('Unexpected status code: %d\n' % response.status_code)
        sys.stderr.write('Response text:\n')
        sys.stderr.write(response.text + "\n")
    else:
        sys.stdout.write(response.text + "\n")

# TODO: This function's name is no longer very accurate.  As soon as it is
# safe, we should change it to something more generic.
def object_url(*args):
    url = cfg.get('client', 'endpoint')
    for arg in args:
        url += '/' + urllib.quote(arg,'')
    return url


@cmd
def serve():
    """Start the HaaS API server"""
    if cfg.has_option('devel', 'debug'):
        debug = cfg.getboolean('devel', 'debug')
    else:
        debug = False
    # We need to import api here so that the functions within it get registered
    # (via `rest_call`), though we don't use it directly:
    from haas import model, http, api
    model.init_db()
    http.serve(debug=debug)

@cmd
def init_db():
    """Initialize the database"""
    from sd import model
    model.init_db(create=True)

@cmd
def service_create(service, service_type, api, endpoint)
    """Create a service"""
    url = object_url('service', service)
    check_status_code(requests.put(url, data={
        'service_type': service_type,
        'api': api,
        'endpoint': endpoint}))

@cmd
def service_delete(project)
    """Delete a service"""
    url = object_url('service', service)
    check_status_code(requests.delete(url))

@cmd
def api_create(api)
    """Register an API"""
    url = object_url('api', api)
    check_status_code(requests.put(url, data={'password': password}))

@cmd
def api_delete(api)
    """Remove an API"""
    url = object_url('api', api)
    check_status_code(requests.delete(url))

@cmd
def help(*commands):
    """Display usage of all following <commands>, or of all commands if none are given"""
    if not commands:
        sys.stderr.write('Usage: %s <command> <arguments...> \n' % sys.argv[0])
        sys.stderr.write('Where <command> is one of:\n')
        commands = sorted(command_dict.keys())
    for name in commands:
        # For each command, print out a summary including the name, arguments,
        # and the docstring (as a #comment).
        sys.stderr.write('  %s\n' % usage_dict[name])
        sys.stderr.write('      %s\n' % command_dict[name].__doc__)

def main():
    """Entry point to the CLI.

    There is a script located at ${source_tree}/scripts/haas, which invokes
    this function.
    """
    config.load()

    if cfg.has_option('general', 'log_level'):
        LOG_SET = ["CRITICAL", "DEBUG", "ERROR", "FATAL", "INFO", "WARN",
                   "WARNING"]
        log_level = cfg.get('general', 'log_level').upper()
        if log_level in LOG_SET:
            # Set to mnemonic log level
            logging.basicConfig(level=getattr(logging, log_level))
        else:
            # Set to 'warning', and warn that the config is bad
            logging.basicConfig(level=logging.WARNING)
            logging.getLogger(__name__).warning(
                "Invalid debugging level %s defaulted to WARNING"% log_level)
    else:
        # Default to 'warning'
        logging.basicConfig(level=logging.WARNING)

    if len(sys.argv) < 2 or sys.argv[1] not in command_dict:
        # Display usage for all commands
        help()
    else:
        command_dict[sys.argv[1]](*sys.argv[2:])

