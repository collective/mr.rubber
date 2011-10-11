import sys
import unittest
from StringIO import StringIO

class HTTPOkTests(unittest.TestCase):
    def _getTargetClass(self):
        from mrrubber.rubber import Rubber
        return Rubber
    
    def _makeOne(self, *opts):
        return self._getTargetClass()(*opts)

    def _makeOnePopulated(self, programs, offset=0, exc=None):
#        if response is None:
        response = DummyResponse()
        rpc = DummyRPCServer()
        prog = self._makeOne(rpc, programs,offset)
        prog.stdin = StringIO()
        prog.stdout = StringIO()
        prog.stderr = StringIO()
        prog.connclass = make_connection(response, exc=exc)
        return prog

    def test_listProcesses_no_programs(self):
        programs = []
        prog = self._makeOnePopulated(programs)
        specs = list(prog.listProcesses())
        self.assertEqual(len(specs), 0)

    def test_listProcesses_w_RUNNING_programs_default_state(self):
        programs = ['foo']
        prog = self._makeOnePopulated(programs)
        specs = list(prog.listProcesses())
        self.assertEqual(len(specs), 1)
        self.assertEqual(specs[0],
                         DummySupervisorRPCNamespace.all_process_info[0])

    def test_listProcesses_w_nonRUNNING_programs_default_state(self):
        programs = ['bar']
        prog = self._makeOnePopulated(programs)
        specs = list(prog.listProcesses())
        self.assertEqual(len(specs), 1)
        self.assertEqual(specs[0],
                         DummySupervisorRPCNamespace.all_process_info[1])

    def test_listProcesses_w_nonRUNNING_programs_RUNNING_state(self):
        programs = ['bar']
        prog = self._makeOnePopulated(programs)
        specs = list(prog.listProcesses(ProcessStates.RUNNING))
        self.assertEqual(len(specs), 0, (prog.programs, specs))


    def test_runforever_stop_one_process(self):
        programs = ['foo', 'bar', 'baz_01', 'notexisting']
        prog = self._makeOnePopulated(programs, offset=-1)
        prog.stdin.write('eventname:SUPERVISOR_STATE_CHANGE_RUNNING len:0\n')
        prog.stdin.seek(0)
        prog.runforever(test=True)
        lines = prog.stderr.getvalue().split('\n')
        #self.assertEqual(len(lines), 7)
        self.assertEqual(lines[0],
                         ("2 cores. Running 1 of 4  processes ['foo', 'bar', "
                          "'baz_01', 'notexisting']")
                         )
        self.assertEqual(lines[1], 'bar is in RUNNING state, stopping')

    def test_runforever_start_one_process(self):
        programs = ['foo', 'bar', 'baz_01', 'notexisting']
        prog = self._makeOnePopulated(programs, offset=+1)
        prog.stdin.write('eventname:SUPERVISOR_STATE_CHANGE_RUNNING len:0\n')
        prog.stdin.seek(0)
        prog.runforever(test=True)
        lines = prog.stderr.getvalue().split('\n')
        #self.assertEqual(len(lines), 7)
        self.assertEqual(lines[0],
                         ("2 cores. Running 3 of 4  processes ['foo', 'bar', "
                          "'baz_01', 'notexisting']")
                         )
        self.assertEqual(lines[1], 'baz:baz_01 started')



def make_connection(response, exc=None):
    class TestConnection:
        def __init__(self, hostport):
            self.hostport = hostport

        def request(self, method, path):
            if exc:
                raise ValueError('foo')
            self.method = method
            self.path = path

        def getresponse(self):
            return response

    return TestConnection

class DummyResponse:
    status = 200
    reason = 'OK'
    body = 'OK'
    def read(self):
        return self.body

class DummyRPCServer:
    def __init__(self):
        self.supervisor = DummySupervisorRPCNamespace()
        self.system = DummySystemRPCNamespace()

class DummySystemRPCNamespace:
    pass

import time
from supervisor.process import ProcessStates

_NOW = time.time()

_FAIL = [ {
        'name':'FAILED',
        'group':'foo',
        'pid':11,
        'state':ProcessStates.RUNNING,
        'statename':'RUNNING',
        'start':_NOW - 100,
        'stop':0,
        'spawnerr':'',
        'now':_NOW,
        'description':'foo description',
        },
{
        'name':'SPAWN_ERROR',
        'group':'foo',
        'pid':11,
        'state':ProcessStates.RUNNING,
        'statename':'RUNNING',
        'start':_NOW - 100,
        'stop':0,
        'spawnerr':'',
        'now':_NOW,
        'description':'foo description',
        },]

class DummySupervisorRPCNamespace:
    _restartable = True
    _restarted = False
    _shutdown = False
    _readlog_error = False


    all_process_info = [
        {
        'name':'foo',
        'group':'foo',
        'pid':11,
        'state':ProcessStates.RUNNING,
        'statename':'RUNNING',
        'start':_NOW - 100,
        'stop':0,
        'spawnerr':'',
        'now':_NOW,
        'description':'foo description',
        },
        {
        'name':'bar',
        'group':'bar',
        'pid':12,
        'state':ProcessStates.FATAL,
        'statename':'FATAL',
        'start':_NOW - 100,
        'stop':_NOW - 50,
        'spawnerr':'screwed',
        'now':_NOW,
        'description':'bar description',
        },
        {
        'name':'baz_01',
        'group':'baz',
        'pid':12,
        'state':ProcessStates.STOPPED,
        'statename':'STOPPED',
        'start':_NOW - 100,
        'stop':_NOW - 25,
        'spawnerr':'',
        'now':_NOW,
        'description':'baz description',
        },
        ]

    def getAllProcessInfo(self):
        return self.all_process_info

    def startProcess(self, name):
        from supervisor import xmlrpc
        from xmlrpclib import Fault
        if name.endswith('SPAWN_ERROR'):
            raise Fault(xmlrpc.Faults.SPAWN_ERROR, 'SPAWN_ERROR')
        return True

    def stopProcess(self, name):
        from supervisor import xmlrpc
        from xmlrpclib import Fault
        if name.endswith('FAILED'):
            raise Fault(xmlrpc.Faults.FAILED, 'FAILED')
        return True
    

def test_suite():
    return unittest.findTestCases(sys.modules[__name__])

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
