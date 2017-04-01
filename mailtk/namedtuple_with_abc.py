#!/usr/bin/env python3
# Copyright (c) 2011 Jan Kaliszewski (zuo). Available under the MIT License.

"""
namedtuple_with_abc.py:
* named tuple mix-in + ABC (abstract base class) recipe,

Import this module to patch collections.namedtuple() factory function
-- enriching it with the 'abc' attribute (an abstract base class + mix-in
for named tuples) and decorating it with a wrapper that registers each
newly created named tuple as a subclass of namedtuple.abc.

How to import:
    import collections, namedtuple_with_abc
or:
    import namedtuple_with_abc
    from collections import namedtuple
    # ^ in this variant you must import namedtuple function
    #   *after* importing namedtuple_with_abc module
or simply:
    from namedtuple_with_abc import namedtuple

Simple usage example:
    class Credentials(namedtuple.abc):
        _fields = 'username password'
        def __str__(self):
            return ('{0.__class__.__name__}'
                    '(username={0.username}, password=...)'.format(self))
    print(Credentials("alice", "Alice's password"))

For more advanced examples -- see below the "if __name__ == '__main__':".
"""

import operator
from collections import namedtuple
from abc import ABCMeta, abstractproperty

__all__ = ('namedtuple',)


class _NamedTupleABCMeta(ABCMeta):
    '''The metaclass for the abstract base class + mix-in for named tuples.'''
    def __new__(mcls, name, bases, namespace):
        my_fields = namespace.get('_fields')
        base_fields = None
        for base in bases:
            base_fields = getattr(base, '_fields', None)
            if base_fields is not None:
                break
        my_fields = list(namedtuple('_', my_fields or '')._fields)
        if base_fields:
            base_fields = list(namedtuple('_', base_fields)._fields)
            base_fields.extend(k for k in dir(base)
                               if isinstance(getattr(base, k), property))
            inner_name = 'inner_%s' % base.__name__.lower()
            my_fields.insert(0, inner_name)
            for f in base_fields:
                namespace[f] = property(
                    operator.attrgetter('%s.%s' % (inner_name, f)))
        if my_fields:
            basetuple = namedtuple(name, my_fields)
            bases = (basetuple,) + bases
            namespace.pop('_fields', None)
            namespace.setdefault('__doc__', basetuple.__doc__)
            namespace.setdefault('__slots__', ())
        return ABCMeta.__new__(mcls, name, bases, namespace)


class _NamedTupleABC(metaclass=_NamedTupleABCMeta):
    '''The abstract base class + mix-in for named tuples.'''
    pass


namedtuple.abc = _NamedTupleABC


if __name__ == '__main__':

    '''Examples and explanations'''

    # Simple usage

    class MyRecord(namedtuple.abc):
        _fields = 'x y z'  # such form will be transformed into ('x', 'y', 'z')
        def _my_custom_method(self):
            return list(self._asdict().items())
    # (the '_fields' attribute belongs to the named tuple public API anyway)

    rec = MyRecord(1, 2, 3)
    print(rec)
    print(rec._my_custom_method())
    print(rec._replace(y=222))
    print(rec._replace(y=222)._my_custom_method())

    # Custom abstract classes...

    class MyAbstractRecord(namedtuple.abc):
        def _my_custom_method(self):
            return list(self._asdict().items())

    try:
        MyAbstractRecord()  # (abstract classes cannot be instantiated)
    except TypeError as exc:
        print(exc)

    class AnotherAbstractRecord(MyAbstractRecord):
        def __str__(self):
            return '<<<{0}>>>'.format(super(AnotherAbstractRecord,
                                            self).__str__())

    # ...and their non-abstract subclasses

    class MyRecord2(MyAbstractRecord):
        _fields = 'a, b'

    class MyRecord3(AnotherAbstractRecord):
        _fields = 'p', 'q', 'r'

    rec2 = MyRecord2('foo', 'bar')
    print(rec2)
    print(rec2._my_custom_method())
    print(rec2._replace(b=222))
    print(rec2._replace(b=222)._my_custom_method())

    rec3 = MyRecord3('foo', 'bar', 'baz')
    print(rec3)
    print(rec3._my_custom_method())
    print(rec3._replace(q=222))
    print(rec3._replace(q=222)._my_custom_method())

   # You can also subclass non-abstract ones...

    class MyRecord33(MyRecord3):
        def __str__(self):
            return '< {0!r}, ..., {0!r} >'.format(self.p, self.r)

    rec33 = MyRecord33(MyRecord3('foo', 'bar', 'baz'))
    print(rec33)
    print(rec33._my_custom_method())
    # print(rec33._replace(q=222))
    # print(rec33._replace(q=222)._my_custom_method())

    # ...and even extend the magic '_fields' attribute again

    class MyRecord345(MyRecord3):
        _fields = 'h i j k'

    rec345 = MyRecord345(MyRecord3(1, 2, 3), 4, 3, 2, 1)
    print(rec345)
    print(rec345._my_custom_method())
    print(rec345._replace(h=222))
    print(rec345._replace(h=222)._my_custom_method())
