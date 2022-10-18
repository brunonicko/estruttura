import six
from basicco.mangling import unmangle
from basicco.runtime_final import final
from basicco.obj_state import get_state, update_state
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


# noinspection PyAbstractClass
class ClassState(six.with_metaclass(ClassStateMeta, BaseClass)):
    __slots__ = ()


class ImmutableClassStateMeta(ClassStateMeta, BaseImmutableClassMeta):

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


class ImmutableClassState(six.with_metaclass(ImmutableClassStateMeta, ClassState, BaseImmutableClass)):
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

    @final
    def __update_state__(self, new_values, old_values):
        # type: (ICS, dict[str, Any], dict[str, Any]) -> ICS
        if not new_values:
            return self

        cls = type(self)
        self_copy = cls.__new__(cls)
        state = dict((n, v) for n, v in six.iteritems(get_state(self)) if n not in new_values)
        update_state(self_copy, state)
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
    __slots__ = ("__internal",)

    @final
    def __getitem__(self, name):
        # type: (str) -> Any
        return self.__internal[name]

    @final
    def __init_state__(self, new_values):
        # type: (dict[str, Any]) -> None
        self.__internal = new_values

    @final
    def __update_state__(self, new_values, old_values):
        # type: (MCS, dict[str, Any], dict[str, Any]) -> MCS
        if not new_values:
            return self

        for name, value in six.iteritems(new_values):
            if value is DELETED:
                del self.__internal[name]
            else:
                self.__internal[name] = value

        return self


MCS = TypeVar("MCS", bound=MutableClassState)
