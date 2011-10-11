#!/usr/bin/env python -u
##############################################################################
#
# Copyright (c) 2007 Agendaless Consulting and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the BSD-like license at
# http://www.repoze.org/LICENSE.txt.  A copy of the license should accompany
# this distribution.  THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL
# EXPRESS OR IMPLIED WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND
# FITNESS FOR A PARTICULAR PURPOSE
#
##############################################################################

# A event listener meant to be subscribed to SUPERVISOR_STATE_CHANGE_RUNNING
# events, which will start only as many processes of a certain type
# as there are cpu's available. This is useful for running many single
# threaded processes at the same time.

# A supervisor config snippet that tells supervisor to use this script
# as a listener is below.
#
# [eventlistener:httpok]
# command=python -u /bin/rubber -p instance
# events=SUPERVISOR_STATE_CHANGE_RUNNING

doc = """\
rubber.py [-p processpattern] [-o cpuoffset] [-n numprocesses]

Options:

--programs (-p):
  Spec for which program names to control. Glob syntax such as "instance*" is supported.

--num (-n):
  The number of processes to run. Defaults to "auto" which will set this to the number of cpu cores detected
  when rubber first starts

--offset (-o):
  A number to modify the --num argument by. For instance if --num=auto and --offset=-2 and the detected cores was
  4 then the number of processes set to run would be 2.

The -p option may be specified more than once, allowing for
specification of multiple processes.

A sample invocation:

rubber.py -p program* -p group1:program2 -o -2

"""

import os
import sys
import time
import urlparse
import xmlrpclib

from supervisor import childutils
from supervisor.states import ProcessStates
from supervisor.options import make_namespec


import os,re,subprocess
import fnmatch

def  determineNumberOfCPUs():
    """ Number of virtual or physical CPUs on this system, i.e.
    user/real as output by time(1) when called with an optimally scaling
    userspace-only program"""

    # Python 2.6+
    try:
        import multiprocessing
        return multiprocessing.cpu_count()
    except (ImportError,NotImplementedError):
        pass

    # POSIX
    try:
        res = int(os.sysconf('SC_NPROCESSORS_ONLN'))

        if res > 0:
            return res
    except (AttributeError,ValueError):
        pass

    # Windows
    try:
        res = int(os.environ['NUMBER_OF_PROCESSORS'])

        if res > 0:
            return res
    except (KeyError, ValueError):
        pass

    # jython
    try:
        from java.lang import Runtime
        runtime = Runtime.getRuntime()
        res = runtime.availableProcessors()
        if res > 0:
            return res
    except ImportError:
        pass

    # BSD
    try:
        sysctl = subprocess.Popen(['sysctl', '-n', 'hw.ncpu'],
                                      stdout=subprocess.PIPE)
        scStdout = sysctl.communicate()[0]
        res = int(scStdout)

        if res > 0:
            return res
    except (OSError, ValueError):
        pass

    # Linux
    try:
        res = open('/proc/cpuinfo').read().count('processor\t:')

        if res > 0:
            return res
    except IOError:
        pass

    # Solaris
    try:
        pseudoDevices = os.listdir('/devices/pseudo/')
        expr = re.compile('^cpuid@[0-9]+$')

        res = 0
        for pd in pseudoDevices:
            if expr.match(pd) != None:
                res += 1

        if res > 0:
            return res
    except OSError:
        pass

    # Other UNIXes (heuristic)
    try:
        try:
            dmesg = open('/var/run/dmesg.boot').read()
        except IOError:
            dmesgProcess = subprocess.Popen(['dmesg'], stdout=subprocess.PIPE)
            dmesg = dmesgProcess.communicate()[0]

        res = 0
        while '\ncpu' + str(res) + ':' in dmesg:
            res += 1

        if res > 0:
            return res
    except OSError:
        pass

    raise Exception('Can not determine number of CPUs on this system')


def usage():
    print doc
    sys.exit(255)

class Rubber:
    connclass = None
    def __init__(self, rpc, programs, offset, num):
        self.rpc = rpc
        self.programs = programs
        self.offset = offset
        self.num = num
        self.stdin = sys.stdin
        self.stdout = sys.stdout
        self.stderr = sys.stderr

    def listProcesses(self, state=None):
        return [x for x in self.rpc.supervisor.getAllProcessInfo()
                   if x['name'] in self.programs and
                      (state is None or x['state'] == state)]

    def runforever(self, test=False):
        # Do it when we first run
        self.checkProcesses()

        while 1:
            # we explicitly use self.stdin, self.stdout, and self.stderr
            # instead of sys.* so we can unit test this code
            headers, payload = childutils.listener.wait(self.stdin, self.stdout)

            if not headers['eventname'].startswith('SUPERVISOR_STATE_CHANGE_RUNNING'):
                # do nothing with supervisor events
                childutils.listener.ok(self.stdout)
                if test:
                    break
                continue

            self.checkProcesses()
            if test:
                break


    def checkProcesses(self):
        """ Start or stop matching processes to match required process count
        """

        def write(msg):
            self.stderr.write('%s\n' % msg)
            self.stderr.flush()
#            messages.append(msg)


        act = False

        try:
            specs = self.rpc.supervisor.getAllProcessInfo()
        except Exception, why:
            write('Exception retrieving process info %s, not acting' % why)
            return
        #import pdb; pdb.set_trace()

        if self.num < 0:
            cpus = determineNumberOfCPUs()
        else:
            cpus = self.num
        torun = cpus + self.offset
#            import pdb; pdb.set_trace()

        def match(spec):
            name = spec['name']
            group = spec['group']
            namespec = make_namespec(name, group)
            for pattern in self.programs:
                if fnmatch.fnmatch(name, pattern) or fnmatch.fnmatch(namespec, pattern):
                    return True
            return False

        totest = []
        totest = [spec['name'] for spec in specs if match(spec)]

        write('%d cores. Running %d of %d  processes %s' % (cpus,torun, len(totest),totest))
        running = 0
        for spec in specs:
            if match(spec):
                if spec['state'] is ProcessStates.STOPPED:
                    if running < torun:
                        self.start(spec, write)
                        running += 1
                else:
                    running += 1
                    if running > torun:
                        self.stop(spec, write)

        childutils.listener.ok(self.stdout)


    def stop(self, spec, write):
        namespec = make_namespec(spec['group'], spec['name'])
        if spec['state'] is ProcessStates.STOPPED:
            return
        write('%s is in RUNNING state, stopping' % namespec)
        try:
            self.rpc.supervisor.stopProcess(namespec)
        except xmlrpclib.Fault, what:
            write('Failed to stop process %s: %s' % (
                namespec, what))

    def start(self, spec, write):
        namespec = make_namespec(spec['group'], spec['name'])
        if spec['state'] is ProcessStates.RUNNING:
            return

        try:
            self.rpc.supervisor.startProcess(namespec)
        except xmlrpclib.Fault, what:
            write('Failed to start process %s: %s' % (
                namespec, what))
        else:
            write('%s started' % namespec)


def main(argv=sys.argv):
    import getopt
    short_args="hp:o:n:"
    long_args=[
        "help",
        "program=",
        "offset=",
        "num="
        ]
    arguments = argv[1:]
    try:
        opts, args = getopt.getopt(arguments, short_args, long_args)
    except:
        usage()

    if not opts:
        usage()

    programs = []
    offset = 0
    num = -1

    for option, value in opts:

        if option in ('-h', '--help'):
            usage()

        if option in ('-p', '--program'):
            programs.append(value)

        if option in ('-o', '--offset'):
            offset = int(value)

        if option in ('-n', '--num'):
            if value == "auto":
                num = -1
            else:
                num = int(value)

    url = arguments[-1]

    try:
        rpc = childutils.getRPCInterface(os.environ)
    except KeyError, why:
        if why[0] != 'SUPERVISOR_SERVER_URL':
            raise
        sys.stderr.write('rubber must be run as a supervisor event '
                         'listener\n')
        sys.stderr.flush()
        return

    prog = Rubber(rpc, programs, offset, num)
    prog.runforever()

if __name__ == '__main__':
    main()
    
    
    
