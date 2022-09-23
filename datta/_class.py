import copy
import functools

import six

from basicco import mangling, runtime_final, state
from estruttura import (
    MISSING,
    DELETED,
    SupportsKeysAndGetItem,
    AttributeMap,
    BaseClassMeta,
    BasePrivateClass,
    BaseInteractiveClass,
)
from tippo import Any, TypeVar, Type, Iterable, Tuple, TypeAlias, overload

from ._bases import BaseDataMeta, BaseData
from ._relationship import DataRelationship
from ._attribute import DataAttribute


T_co = TypeVar("T_co", covariant=True)  # covariant value type

Item = Tuple[str, Any]  # type: TypeAlias


class DataMeta(BaseDataMeta, BaseClassMeta):
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


class PrivateData(six.with_metaclass(DataMeta, BaseData, BasePrivateClass)):
    __slots__ = ("__mutable",)
    __kwargs__ = {"gen_init": True}

    def __hash__(self):
        # type: () -> int
        return hash(tuple(self))  # FIXME: generated

    def __eq__(self, other):
        return type(other) is type(self) and tuple(other) == tuple(self)  # FIXME: generated

    @runtime_final.final
    def __getitem__(self, name):
        # type: (str) -> Any
        if name not in type(self).__attributes__:
            error = "no attribute named {!r}".format(name)
            raise KeyError(error)
        return getattr(self, name)

    def __setattr__(self, name, value):
        if name in type(self).__attributes__:
            error = "{!r} attributes are read-only".format(type(self).__fullname__)
            raise AttributeError(error)
        return super(PrivateData, self).__setattr__(name, value)

    def __delattr__(self, name):
        if name in type(self).__attributes__:
            error = "{!r} attributes are read-only".format(type(self).__fullname__)
            raise AttributeError(error)
        return super(PrivateData, self).__delattr__(name)

    def _init(self, init_values):
        # type: (dict[str, Any]) -> None
        for name, value in six.iteritems(init_values):
            object.__setattr__(self, name, value)

    @overload
    def _update(self, __m, **kwargs):
        # type: (PD, SupportsKeysAndGetItem[str, Any], **Any) -> PD
        pass

    @overload
    def _update(self, __m, **kwargs):
        # type: (PD, Iterable[Item], **Any) -> PD
        pass

    @overload
    def _update(self, **kwargs):
        # type: (PD, **Any) -> PD
        pass

    @runtime_final.final
    def _update(self, *args, **kwargs):
        """
        Update attribute values.

        :return: Transformed.
        """
        updates = dict(*args, **kwargs)
        if not updates:
            return self

        cls = type(self)
        self_copy = copy.copy(self)

        def value_getter(name_):
            return getattr(self, name_, MISSING)

        updates = cls.__attributes__.get_update_values(updates, value_getter)
        if not updates:
            return self

        for name, value in six.iteritems(updates):
            if value is DELETED:
                object.__delattr__(self_copy, name)
            else:
                object.__setattr__(self_copy, name, value)

        return self_copy


PD = TypeVar("PD", bound=PrivateData)  # private data type


class Data(PrivateData, BaseInteractiveClass):
    __slots__ = ()
