from unittest import TestCase
import json

from fac.utils import JSONDict, JSONList


class TestJSONDict(TestCase):
    def setUp(self):
        self.orig = {'foo': 42, 'bar': True, 'baz': [1, 2], 'qux': {'lok': 3}}
        self.d = JSONDict(self.orig)

    def test_json(self):
        self.assertDictEqual(json.loads(str(self.d)), self.orig)

    def test_read(self):
        self.assertEqual(self.d.foo, 42)
        self.assertEqual(self.d.bar, True)
        self.assertEqual(self.d.baz, [1, 2])
        self.assertEqual(self.d.qux, {'lok': 3})
        self.assertEqual(self.d.qux.lok, 3)

    def test_write(self):
        self.d.foo = 43
        self.assertEqual(self.d.foo, 43)
        self.d.qux.lok = 45
        self.assertEqual(self.d.qux.lok, 45)
        self.d.other = "hey"
        self.assertEqual(self.d.other, "hey")

    def test_no_attr(self):
        with self.assertRaises(AttributeError):
            self.d.nope

        self.assertTrue(self.d.qux)
        with self.assertRaises(AttributeError):
            self.d.qux.nope


class TestJSONList(TestCase):
    def setUp(self):
        self.orig = ["foo", "bar", 42, True]
        self.l = JSONList(self.orig)
        self.d = JSONDict({'foo': [{'bar': 0}, {'bar': 1}]})

    def test_json(self):
        self.assertListEqual(json.loads(str(self.l)), self.orig)

    def test_read(self):
        self.assertEqual(self.d.foo[0], {'bar': 0})
        self.assertEqual(self.d.foo[1], {'bar': 1})
        self.assertEqual(self.d.foo[0].bar, 0)
        self.assertEqual(self.d.foo[1].bar, 1)

    def test_write(self):
        self.d.foo[0].bar = 42
        self.assertEqual(self.d.foo[0].bar, 42)
        self.d.foo[0] = {'baz': 1}
        self.assertEqual(self.d.foo[0].baz, 1)
        self.d.foo[0].baz = 42
        self.assertEqual(self.d.foo[0].baz, 42)
        self.d.foo.append({'baz': 10})
        self.assertEqual(self.d.foo[2].baz, 10)
        self.d.foo.insert(0, {'qux': 20})
        self.assertEqual(self.d.foo[0].qux, 20)
