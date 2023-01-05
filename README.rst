.. logo_start
.. raw:: html

   <p align="center">
     <a href="https://github.com/brunonicko/estruttura">
         <picture>
            <object data="./_static/estruttura.svg" type="image/png">
                <source srcset="./docs/source/_static/estruttura_white.svg" media="(prefers-color-scheme: dark)">
                <img src="./docs/source/_static/estruttura.svg" width="60%" alt="estruttura" />
            </object>
         </picture>
     </a>
   </p>
.. logo_end

.. image:: https://github.com/brunonicko/estruttura/workflows/MyPy/badge.svg
   :target: https://github.com/brunonicko/estruttura/actions?query=workflow%3AMyPy

.. image:: https://github.com/brunonicko/estruttura/workflows/Lint/badge.svg
   :target: https://github.com/brunonicko/estruttura/actions?query=workflow%3ALint

.. image:: https://github.com/brunonicko/estruttura/workflows/Tests/badge.svg
   :target: https://github.com/brunonicko/estruttura/actions?query=workflow%3ATests

.. image:: https://readthedocs.org/projects/estruttura/badge/?version=stable
   :target: https://estruttura.readthedocs.io/en/stable/

.. image:: https://img.shields.io/github/license/brunonicko/estruttura?color=light-green
   :target: https://github.com/brunonicko/estruttura/blob/main/LICENSE

.. image:: https://static.pepy.tech/personalized-badge/estruttura?period=total&units=international_system&left_color=grey&right_color=brightgreen&left_text=Downloads
   :target: https://pepy.tech/project/estruttura

.. image:: https://img.shields.io/pypi/pyversions/estruttura?color=light-green&style=flat
   :target: https://pypi.org/project/estruttura/

Overview
--------
`estruttura` provides abstract data structures.

Motivation
----------
`estruttura` was born out of the need for a similar interface between the `datta <https://github.com/brunonicko/datta>`_
and `objetto <https://github.com/brunonicko/objetto>`_ packages.

Relationship
------------
`estruttura` provides a `Relationship` class that contains information about the values stored in the `Structures`_,
such as typing (with support for runtime type checking), serialization, validation, conversion, etc.

.. code:: python

    >>> from six import string_types
    >>> from estruttura import Relationship, exceptions
    >>> def converter(value):
    ...     if isinstance(value, string_types) and "." in value:
    ...         return float(value)
    ...     elif not isinstance(value, float):
    ...         return int(value)
    ...
    >>> def validator(value):
    ...     if value > 10:
    ...         raise exceptions.ValidationError(value)
    ...
    >>> relationship = Relationship(types=(int, float), converter=converter, validator=validator)
    >>> relationship.process_value("3.3")
    3.3

Structures
----------
`estruttura` offers all the class combinations of the concepts described below.

Private Structure
^^^^^^^^^^^^^^^^^
Holds data internally and only allow for changes privately.

User Structure
^^^^^^^^^^^^^^
Allows for changing of the data by external clients (public).

Proxy Structure
^^^^^^^^^^^^^^^
Wraps another structure and acts as a view of its data.
Proxy structures can even point to other proxy structures.

.. code:: python

    >>> from estruttura import ProxyMutableListStructure
    >>> from estruttura.examples import MutableList
    >>> l = MutableList(range(3))
    >>> p = ProxyMutableListStructure(l)
    >>> list(p) == [0, 1, 2]
    True
    >>> l.append(3)
    >>> list(p) == [0, 1, 2, 3]
    True

Immutable Structure
^^^^^^^^^^^^^^^^^^^
Only allows data changes through copying.
Immutable structures are hashable.

.. code:: python

    >>> from estruttura.examples import ImmutableList
    >>> l_a = ImmutableList()
    >>> l_b = l_a.extend(range(3))
    >>> list(l_b) == [0, 1, 2]
    True

Mutable Structure
^^^^^^^^^^^^^^^^^
Allows in-place data changes.
Mutable structures are not hashable.

.. code:: python

    >>> from estruttura.examples import MutableList
    >>> l = MutableList()
    >>> l.extend(range(3))
    >>> list(l) == [0, 1, 2]
    True

Dict Structure
^^^^^^^^^^^^^^
Dictionary-like data structure class.

.. code:: python

    >>> from estruttura import Relationship
    >>> from estruttura.examples import MutableDict
    >>> class StrIntDict(MutableDict):
    ...     relationship = Relationship(converter=str)
    ...     value_relationship = Relationship(converter=int)
    ...
    >>> StrIntDict({1: "1"})
    StrIntDict({'1': 1})

List Structure
^^^^^^^^^^^^^^
List-like data structure class.

.. code:: python

    >>> from estruttura import Relationship
    >>> from estruttura.examples import MutableList
    >>> class IntList(MutableList):
    ...     relationship = Relationship(converter=int)
    ...
    >>> IntList(["1", 1, 1.0])
    IntList([1, 1, 1])

Set Structure
^^^^^^^^^^^^^
Set-like data structure class.

.. code:: python

    >>> from estruttura import Relationship
    >>> from estruttura.examples import MutableSet
    >>> class IntSet(MutableSet):
    ...     relationship = Relationship(converter=int)
    ...
    >>> IntSet({"1", 1, 1.0})
    IntSet({1})

Structure
^^^^^^^^^
Dataclass-like structure class that has a schema defined by attributes.

.. code:: python

    >>> import math
    >>> from estruttura import Attribute, Relationship, getter
    >>> from estruttura.examples import ImmutableClass
    >>> class Point(ImmutableClass):
    ...     x = Attribute()
    ...     y = Attribute()
    ...     d = Attribute(serializable=True)
    ...     @getter(d, dependencies=(x, y))
    ...     def _(self):
    ...         return math.sqrt(self.x**2 + self.y**2)
    ...
    >>> Point(3, 4)
    Point(3, 4, <d=5.0>)
    >>> Point(3, 4).serialize() == {"x": 3, "y": 4, "d": 5.0}
    True
    >>> Point.deserialize({"x": 3, "y": 4})
    Point(3, 4, <d=5.0>)
