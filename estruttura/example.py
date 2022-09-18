import collections

import pyrsistent
import six

from estruttura.bases import BaseAttribute, BaseObjectMeta, BaseObject, BaseAttributeManager


class Attribute(BaseAttribute):

    def __get__(self, instance, owner):
        if instance is not None:
            try:
                return instance[self.name]
            except KeyError:
                raise AttributeError(self.name)
        return self


_attributes = collections.OrderedDict()  # type: collections.OrderedDict[str, Attribute]
_foo_attribute = Attribute()
_bar_attribute = Attribute()
_attributes["foo"] = _foo_attribute
_attributes["bar"] = _bar_attribute


class ObjectMeta(BaseObjectMeta):

    @property
    def __kw_only__(cls):
        return False

    @property
    def __attributes__(cls):
        return _attributes


class Object(six.with_metaclass(ObjectMeta, BaseObject)):
    __slots__ = ("__state",)
    __hash__ = None  # type: ignore

    foo = _foo_attribute
    bar = _bar_attribute

    def __init__(self, *args, **kwargs):
        manager = BaseAttributeManager(type(self).__attributes__)
        self.__state = pyrsistent.pmap(manager.get_initial_values(*args, **kwargs))

    def __eq__(self, other):
        return self is other

    def __getitem__(self, attribute_name):
        return self.__state[attribute_name]

    def __contains__(self, value):
        for state_value in six.itervalues(self.__state):
            if value == state_value:
                return True
        return False

    def __iter__(self):
        for name, value in six.iteritems(self.__state):
            yield (name, value)

    def __len__(self):
        return len(self.__state)
