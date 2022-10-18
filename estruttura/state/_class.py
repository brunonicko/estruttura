import copy

import six
from basicco.explicit_hash import set_to_none
from basicco.mangling import unmangle
from basicco.runtime_final import final
from tippo import Any, Type, TypeVar

from ..base import (
    BaseClassMeta,
    BaseClass,
    BaseImmutableClassMeta,
    BaseImmutableClass,
    BaseMutableClassMeta,
    BaseMutableClass,
    AttributeMap,
)
from ..constants import DELETED
from ._attribute import StateAttribute, MutableStateAttribute


class ClassStateMeta(BaseClassMeta):
    __attribute_type__ = StateAttribute

    # noinspection PyUnusedLocal
    @staticmethod
    def __edit_dct__(this_attribute_map, attribute_map, name, bases, dct, **kwargs):
        # type: (AttributeMap, AttributeMap, str, tuple[Type, ...], dict[str, Any], **Any) -> dict[str, Any]

        # Convert attributes to slots.
        slots = list(dct.get("__slots__", ()))
        for attribute_name, attribute in six.iteritems(this_attribute_map):
            del dct[attribute_name]
            slot_name = unmangle(attribute_name, name)
            slots.append(slot_name)
        dct["__slots__"] = tuple(slots)

        return dct


# noinspection PyAbstractClass
class ClassState(six.with_metaclass(ClassStateMeta, BaseClass)):
    __slots__ = ()

    @final
    def __getitem__(self, name):
        # type: (str) -> Any
        if name not in type(self).__attributes__:
            error = "no attribute named {!r}".format(name)
            raise KeyError(error)
        try:
            return getattr(self, name)
        except AttributeError:
            pass
        error = "no value for attribute {!r}".format(name)
        raise KeyError(error)

    @final
    def __init_state__(self, new_values):
        # type: (dict[str, Any]) -> None
        for name, value in six.iteritems(new_values):
            object.__setattr__(self, name, value)


class ImmutableClassStateMeta(ClassStateMeta, BaseImmutableClassMeta):
    pass


class ImmutableClassState(six.with_metaclass(ImmutableClassStateMeta, ClassState, BaseImmutableClass)):
    __slots__ = ()

    def __hash__(self):
        # type: () -> int
        return object.__hash__(self)  # TODO: based on attributes

    def __eq__(self, other):
        # type: (object) -> bool
        return self is other  # TODO: based on attributes

    @final
    def __update_state__(self, new_values, old_values):
        # type: (ICS, dict[str, Any], dict[str, Any]) -> ICS
        """
        Update attribute values.

        :return: Transformed.
        """
        if not new_values:
            return self

        self_copy = copy.copy(self)
        for name, value in six.iteritems(new_values):
            if value is DELETED:
                object.__delattr__(self_copy, name)
            else:
                object.__setattr__(self_copy, name, value)

        return self_copy


ICS = TypeVar("ICS", bound=ImmutableClassState)


class MutableClassStateMeta(ClassStateMeta, BaseMutableClassMeta):
    __attribute_type__ = MutableStateAttribute


class MutableClassState(six.with_metaclass(MutableClassStateMeta, ClassState, BaseMutableClass)):
    __slots__ = ()

    @set_to_none
    def __hash__(self):
        error = "{!r} object is not hashable".format(type(self).__name__)
        raise TypeError(error)

    def __eq__(self, other):
        # type: (object) -> bool
        return self is other  # TODO: based on attributes

    @final
    def __update_state__(self, new_values, old_values):
        # type: (MCS, dict[str, Any], dict[str, Any]) -> MCS
        """
        Update attribute values.

        :return: Transformed.
        """
        if not new_values:
            return self

        for name, value in six.iteritems(new_values):
            if value is DELETED:
                object.__delattr__(self, name)
            else:
                object.__setattr__(self, name, value)

        return self


MCS = TypeVar("MCS", bound=MutableClassState)
