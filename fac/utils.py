import sys
import json
from collections import UserDict, UserList

__all__ = ['JSONList', 'JSONDict', 'prompt']


class JSONList(UserList):
    def __init__(self, data=None):
        self.data = [] if data is None else data

    def __getitem__(self, i):
        return _wrap(self.data[i])

    def __setitem__(self, i, val):
        self.data[i] = _unwrap(val)

    def __str__(self):
        return json.dumps(self.data)


class JSONDict(UserDict):
    data = None

    def __init__(self, data=None):
        self.data = {} if data is None else data

    def __getattr__(self, name):
        try:
            return super().__getattribute__(name)
        except AttributeError as ex:
            try:
                return _wrap(self.data[name])
            except KeyError:
                raise ex

    def __setattr__(self, name, val):
        try:
            super().__getattribute__(name)
        except AttributeError:
            self.data[name] = _unwrap(val)
        else:
            return super().__setattr__(name, val)

    def __str__(self):
        return json.dumps(self.data, sort_keys=True)


def _wrap(obj):
    if isinstance(obj, dict):
        return JSONDict(obj)
    elif isinstance(obj, list):
        return JSONList(obj)
    else:
        return obj


def _unwrap(obj):
    if isinstance(obj, UserList) or isinstance(obj, UserDict):
        return obj.data
    return obj


def prompt(prompt='Continue?', choices='Y/n'):
    default_choice = None
    for choice in choices:
        if choice.isupper():
            default_choice = choice.lower()
            break

    while True:
        print(
            '%s [%s]' % (prompt, choices),
            end=' ', flush=True
        )

        reply = sys.stdin.readline().strip().lower()

        if not reply:
            return default_choice
        elif reply in choices.lower() and reply != '/':
            return reply
        else:
            print('Please answer with one of %s.' % choices)
