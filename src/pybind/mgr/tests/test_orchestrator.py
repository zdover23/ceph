from __future__ import absolute_import

from tests import mock

import pytest

from ceph.deployment import inventory
from orchestrator import raise_if_exception, Completion, ProgressReference
from orchestrator import InventoryHost, DaemonDescription
from orchestrator import OrchestratorValidationError


def _test_resource(data, resource_class, extra=None):
    # ensure we can deserialize and serialize
    rsc = resource_class.from_json(data)
    rsc.to_json()

    if extra:
        # if there is an unexpected data provided
        data.update(extra)
        with pytest.raises(OrchestratorValidationError):
            resource_class.from_json(data)


def test_inventory():
    json_data = {
        'name': 'host0',
        'addr': '1.2.3.4',
        'devices': [
            {
                'sys_api': {
                    'rotational': '1',
                    'size': 1024,
                },
                'path': '/dev/sda',
                'available': False,
                'rejected_reasons': [],
                'lvs': []
            }
        ]
    }
    _test_resource(json_data, InventoryHost, {'abc': False})
    for devices in json_data['devices']:
        _test_resource(devices, inventory.Device)

    json_data = [{}, {'name': 'host0', 'addr': '1.2.3.4'}, {'devices': []}]
    for data in json_data:
        with pytest.raises(OrchestratorValidationError):
            InventoryHost.from_json(data)


def test_daemon_description():
    json_data = {
        'hostname': 'test',
        'daemon_type': 'mon',
        'daemon_id': 'a'
    }
    _test_resource(json_data, DaemonDescription, {'abc': False})


def test_raise():
    c = Completion()
    c._exception = ZeroDivisionError()
    with pytest.raises(ZeroDivisionError):
        raise_if_exception(c)


def test_promise():
    p = Completion(value=3)
    p.finalize()
    assert p.result == 3


def test_promise_then():
    p = Completion(value=3).then(lambda three: three + 1)
    p.finalize()
    assert p.result == 4


def test_promise_mondatic_then():
    p = Completion(value=3)
    p.then(lambda three: Completion(value=three + 1))
    p.finalize()
    assert p.result == 4


def some_complex_completion():
    c = Completion(value=3).then(
        lambda three: Completion(value=three + 1).then(
            lambda four: four + 1))
    return c

def test_promise_mondatic_then_combined():
    p = some_complex_completion()
    p.finalize()
    assert p.result == 5


def test_promise_flat():
    p = Completion()
    p.then(lambda r1: Completion(value=r1 + ' there').then(
        lambda r11: r11 + '!'))
    p.finalize('hello')
    assert p.result == 'hello there!'


def test_side_effect():
    foo = {'x': 1}

    def run(x):
        foo['x'] = x

    foo['x'] = 1
    Completion(value=3).then(run).finalize()
    assert foo['x'] == 3


def test_progress():
    c = some_complex_completion()
    mgr = mock.MagicMock()
    mgr.process = lambda cs: [c.finalize(None) for c in cs]

    progress_val = 0.75
    c._last_promise().then(
        on_complete=ProgressReference(message='hello world',
                                      mgr=mgr,
                                      completion=lambda: Completion(
                                          on_complete=lambda _: progress_val))
    )
    mgr.remote.assert_called_with('progress', 'update', c.progress_reference.progress_id, 'hello world', 0.0, [('origin', 'orchestrator')])

    c.finalize()
    mgr.remote.assert_called_with('progress', 'complete', c.progress_reference.progress_id)

    c.progress_reference.update()
    mgr.remote.assert_called_with('progress', 'update', c.progress_reference.progress_id, 'hello world', progress_val, [('origin', 'orchestrator')])
    assert not c.progress_reference.effective

    progress_val = 1
    c.progress_reference.update()
    assert c.progress_reference.effective
    mgr.remote.assert_called_with('progress', 'complete', c.progress_reference.progress_id)


def test_with_progress():
    mgr = mock.MagicMock()
    mgr.process = lambda cs: [c.finalize(None) for c in cs]

    def execute(y):
        return str(y)

    def run(x):
        def two(_):
            return execute(x * 2)

        return Completion.with_progress(
            message='message',
            on_complete=two,
            mgr=mgr

        )
    c = Completion(on_complete=lambda x: x * 10).then(run)._first_promise
    c.finalize(2)
    assert c.result == '40'
    c.progress_reference.update()
    assert c.progress_reference.effective


def test_exception():

    def run(x):
        raise KeyError(x)

    c = Completion(value=3).then(run)
    c.finalize()
    with pytest.raises(KeyError):
        raise_if_exception(c)


def test_fail():
    c = Completion().then(lambda _: 3)
    c._first_promise.fail(KeyError())
    assert isinstance(c.exception, KeyError)

    with pytest.raises(ValueError,
                  match='Invalid State: called fail, but Completion is already finished: {}'.format(
                      str(ZeroDivisionError()))):
        c._first_promise.fail(ZeroDivisionError())


def test_pretty_print():
    mgr = mock.MagicMock()
    mgr.process = lambda cs: [c.finalize(None) for c in cs]

    def add_one(x):
        return x+1

    c = Completion(value=1, on_complete=add_one).then(
        str
    ).add_progress('message', mgr)

    assert c.pretty_print() == """<Completion>[
       add_one(1),
       str(...),
       ProgressReference(...),
]"""
    c.finalize()
    assert c.pretty_print() == """<Completion>[
(done) add_one(1),
(done) str(2),
(done) ProgressReference('2'),
]"""

    p = some_complex_completion()
    assert p.pretty_print() == """<Completion>[
       <lambda>(3),
       lambda x: x(...),
]"""
    p.finalize()
    assert p.pretty_print() == """<Completion>[
(done) <lambda>(3),
(done) <lambda>(4),
(done) lambda x: x(5),
(done) lambda x: x(5),
]"""

    assert p.result == 5

