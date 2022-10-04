import copy

import six

from basicco import mangling, runtime_final
from estruttura import (
    DELETED,
    AttributeMap,
    ClassStructureMeta,
    ClassStructure,
    PrivateClassStructure,
    InteractiveClassStructure,
)
from tippo import Any, TypeVar, Type

from ._data import DataMeta, Data
from ._relationship import DataRelationship
from ._attribute import DataAttribute


T_co = TypeVar("T_co", covariant=True)  # covariant value type


class DataClassMeta(DataMeta, ClassStructureMeta):
    __attribute_type__ = DataAttribute  # type: Type[DataAttribute]
    __relationship_type__ = DataRelationship  # type: Type[DataRelationship]

    @staticmethod
    def __edit_dct__(this_attribute_map, attribute_map, name, bases, dct, **kwargs):
        # type: (AttributeMap, AttributeMap, str, tuple[Type, ...], dict[str, Any], **Any) -> dict[str, Any]

        # Convert attributes to slots.
        slots = list(dct.get("__slots__", ()))
        dct_copy = dict(dct)
        for attribute_name, attribute in six.iteritems(this_attribute_map):
            del dct_copy[attribute_name]
            slot_name = mangling.unmangle(attribute_name, name)
            slots.append(slot_name)
        dct_copy["__slots__"] = tuple(slots)

        return dct_copy


# noinspection PyAbstractClass
class ProtectedDataClass(six.with_metaclass(DataClassMeta, ClassStructure, Data)):
    """Protected data class."""

    __slots__ = ()
    __kwargs__ = {
        "frozen": True,
        "gen_init": True,
        "gen_hash": True,
        "gen_eq": True,
        "gen_repr": True,
    }

    @runtime_final.final
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

    @runtime_final.final
    def __init_state__(self, new_values):
        # type: (dict[str, Any]) -> None
        for name, value in six.iteritems(new_values):
            object.__setattr__(self, name, value)


# noinspection PyAbstractClass
class PrivateDataClass(ProtectedDataClass, PrivateClassStructure):
    """Private data class."""

    __slots__ = ()

    @runtime_final.final
    def __update_state__(self, new_values, old_values):
        # type: (PDC, dict[str, Any], dict[str, Any]) -> PDC
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


PDC = TypeVar("PDC", bound=PrivateDataClass)


# noinspection PyAbstractClass
class DataClass(PrivateDataClass, InteractiveClassStructure):
    """Data class."""

    __slots__ = ()
