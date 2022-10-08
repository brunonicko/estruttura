import copy

import six

from basicco import mangling, runtime_final
from estruttura import DELETED, AttributeMap, StructureMeta, Structure, PrivateStructure, InteractiveStructure
from tippo import Any, TypeVar, Type, dataclass_transform

from ._bases import BaseDataMeta, BaseData
from ._relationship import DataRelationship
from ._attribute import DataAttribute
from ._utils import attribute as attribute_


T_co = TypeVar("T_co", covariant=True)  # covariant value type


@dataclass_transform(field_descriptors=(DataAttribute, attribute_))
class DataMeta(BaseDataMeta, StructureMeta):
    __attribute_type__ = DataAttribute  # type: Type[DataAttribute]
    __relationship_type__ = DataRelationship  # type: Type[DataRelationship]

    # noinspection PyUnusedLocal
    @staticmethod
    def __edit_dct__(this_attribute_map, attribute_map, name, bases, dct, **kwargs):
        # type: (AttributeMap, AttributeMap, str, tuple[Type, ...], dict[str, Any], **Any) -> dict[str, Any]

        # Convert attributes to slots.
        slots = list(dct.get("__slots__", ()))
        dct_copy = dict(dct)
        for attribute_name, attribute in six.iteritems(this_attribute_map):
            if attribute.constant:
                dct_copy[attribute_name] = attribute.default
            else:
                del dct_copy[attribute_name]
                slot_name = mangling.unmangle(attribute_name, name)
                slots.append(slot_name)
        dct_copy["__slots__"] = tuple(slots)

        return dct_copy


class ProtectedData(six.with_metaclass(DataMeta, Structure, BaseData)):
    """Protected data."""

    __slots__ = ()

    def __init_subclass__(
        cls,
        kw_only=None,  # type: bool | None
        gen_order=None,  # type: bool | None
        **kwargs
    ):
        # type: (...) -> None
        super(ProtectedData, cls).__init_subclass__(
            kw_only=kw_only,
            frozen=True,
            gen_init=True,
            gen_hash=True,
            gen_eq=True,
            gen_order=gen_order,
            gen_repr=True,
            **kwargs
        )

    @classmethod
    def __construct__(cls, values):
        # type: (Type[PRD], dict[str, Any]) -> PRD
        """
        Construct an instance with deserialized attribute values.

        :param values: Deserialized attribute values.
        :return: Instance.
        """
        self = cls.__new__(cls)
        for name, value in six.iteritems(values):
            object.__setattr__(self, name, value)
        return self

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


PRD = TypeVar("PRD", bound=ProtectedData)


class PrivateData(ProtectedData, PrivateStructure):
    """Private data."""

    __slots__ = ()

    @runtime_final.final
    def __update_state__(self, new_values, old_values):
        # type: (PD, dict[str, Any], dict[str, Any]) -> PD
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


PD = TypeVar("PD", bound=PrivateData)


class Data(PrivateData, InteractiveStructure):
    """Data."""

    __slots__ = ()
