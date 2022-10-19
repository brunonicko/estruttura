import pyrsistent
import six
from basicco.abstract_class import abstract
from basicco.recursive_repr import recursive_repr
from basicco.safe_repr import safe_repr
from basicco.custom_repr import mapping_repr
from basicco.explicit_hash import set_to_none
from tippo import Any, overload, Iterator, Iterable, SupportsKeysAndGetItem, TypeVar, Type, Mapping, cast
from pyrsistent.typing import PMap

from ..base import BaseClass, BaseImmutableClass, BaseMutableClass
from ..constants import DELETED


_PMAP_TYPE = type(pyrsistent.pmap())  # type: Type[PMap]


class ClassState(BaseClass):
    __slots__ = ()

    @overload
    def __init__(self, __m, **kwargs):
        # type: (SupportsKeysAndGetItem[str, Any], **Any) -> None
        pass

    @overload
    def __init__(self, __m, **kwargs):
        # type: (Iterable[tuple[str, Any]], **Any) -> None
        pass

    @overload
    def __init__(self, **kwargs):
        # type: (**Any) -> None
        pass

    @abstract
    def __init__(self, *args, **kwargs):
        raise NotImplementedError()

    def __dir__(self):
        members = super(ClassState, self).__dir__()
        members.extend((list(zip(*self)) or [[], []])[0])
        return sorted(members)

    def __getattr__(self, name):
        # type: (str) -> Any
        try:
            return self._internal[name]
        except KeyError:
            pass
        return self.__getattribute__(name)

    def __getitem__(self, name):
        # type: (str) -> Any
        """
        Get value for attribute.

        :param name: Attribute name.
        :return: Attribute value.
        :raises KeyError: Attribute does not exist or has no value.
        """
        return self._internal[name]

    def __contains__(self, name):
        # type: (object) -> bool
        """
        Get whether there's a value for attribute.

        :param name: Attribute name.
        :return: True if has value.
        """
        return name in self._internal

    def __iter__(self):
        # type: () -> Iterator[tuple[str, Any]]
        """
        Iterate over attribute items (name, value).

        :return: Attribute item iterator.
        """
        for name, value in six.iteritems(self._internal):
            yield name, value

    def __len__(self):
        # type: () -> int
        """
        Get count of attributes with values.

        :return: Number of attributes with values.
        """
        return len(self._internal)

    @safe_repr
    @recursive_repr
    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        """
        return mapping_repr(
            self._internal,
            prefix="{}(".format(type(self).__qualname__),
            suffix=")",
            template="{key}={value}",
            key_repr=str,
            sorting=True,
            sort_key=lambda p: p[0]
        )

    @property
    @abstract
    def _internal(self):
        # type: () -> Mapping[str, Any]
        """Internal mapping."""
        raise NotImplementedError()


class ImmutableClassState(ClassState, BaseImmutableClass):
    __slots__ = ("__internal",)

    @overload
    def __init__(self, __m, **kwargs):
        # type: (SupportsKeysAndGetItem[str, Any], **Any) -> None
        pass

    @overload
    def __init__(self, __m, **kwargs):
        # type: (Iterable[tuple[str, Any]], **Any) -> None
        pass

    @overload
    def __init__(self, **kwargs):
        # type: (**Any) -> None
        pass

    def __init__(self, *args, **kwargs):
        if len(args) == 1 and not kwargs and type(args[0]) is _PMAP_TYPE:
            internal = cast(PMap[str, Any], args[0])
        else:
            internal = pyrsistent.pmap(dict(*args, **kwargs))
        self.__internal = internal  # type: PMap[str, Any]

    def __hash__(self):
        # type: () -> int
        return hash(self._internal)

    def __eq__(self, other):
        # type: (object) -> bool
        return type(self) is type(other) and self._internal == cast(ImmutableClassState, other)._internal

    @overload
    def _update(self, __m, **kwargs):
        # type: (ICS, SupportsKeysAndGetItem[str, Any], **Any) -> ICS
        pass

    @overload
    def _update(self, __m, **kwargs):
        # type: (ICS, Iterable[tuple[str, Any]], **Any) -> ICS
        pass

    @overload
    def _update(self, **kwargs):
        # type: (ICS, **Any) -> ICS
        pass

    def _update(self, *args, **kwargs):
        """
        Update attribute values.

        Same parameters as :meth:`dict.update`.
        :return: Transformed.
        """
        updates = dict(*args, **kwargs)
        deletes = set()
        for key, value in list(updates.items()):
            if value is DELETED:
                del updates[key]
                deletes.add(key)

        internal = self._internal.update(updates)
        if deletes:
            evolver = internal.evolver()
            for key in deletes:
                del evolver[key]
            internal = evolver.persistent()

        return type(self)(internal)

    @property
    def _internal(self):
        # type: () -> PMap[str, Any]
        return self.__internal


ICS = TypeVar("ICS", bound=ImmutableClassState)


class MutableClassState(ClassState, BaseMutableClass):
    __slots__ = ("__internal",)

    @overload
    def __init__(self, __m, **kwargs):
        # type: (SupportsKeysAndGetItem[str, Any], **Any) -> None
        pass

    @overload
    def __init__(self, __m, **kwargs):
        # type: (Iterable[tuple[str, Any]], **Any) -> None
        pass

    @overload
    def __init__(self, **kwargs):
        # type: (**Any) -> None
        pass

    def __init__(self, *args, **kwargs):
        self.__internal = dict(*args, **kwargs)  # type: dict[str, Any]

    @set_to_none
    def __hash__(self):
        error = "{!r} object is not hashable".format(type(self).__name__)
        raise TypeError(error)

    def __eq__(self, other):
        # type: (object) -> bool
        return type(self) is type(other) and self._internal == cast(MutableClassState, other)._internal

    def __setattr__(self, name, value):
        # type: (str, Any) -> None
        if not hasattr(type(self), name):
            try:
                self._update({name: value})
            except KeyError:
                error = "could not set attribute {!r}".format(name)
                exc = AttributeError(error)
                six.raise_from(exc, None)
                raise exc
        else:
            super(MutableClassState, self).__setattr__(name, value)

    def __delattr__(self, name):
        # type: (str) -> None
        if not hasattr(type(self), name):
            try:
                self._update({name: DELETED})
            except KeyError:
                if name in self:
                    error = "could not delete attribute {!r}".format(name)
                else:
                    error = "no value to delete for attribute {!r}".format(name)
                exc = AttributeError(error)
                six.raise_from(exc, None)
                raise exc
        else:
            super(MutableClassState, self).__delattr__(name)

    @overload
    def _update(self, __m, **kwargs):
        # type: (MCS, SupportsKeysAndGetItem[str, Any], **Any) -> MCS
        pass

    @overload
    def _update(self, __m, **kwargs):
        # type: (MCS, Iterable[tuple[str, Any]], **Any) -> MCS
        pass

    @overload
    def _update(self, **kwargs):
        # type: (MCS, **Any) -> MCS
        pass

    def _update(self, *args, **kwargs):
        """
        Update keys and values.

        Same parameters as :meth:`dict.update`.
        :return: Transformed.
        """
        updates = dict(*args, **kwargs)
        deletes = set()
        for key, value in list(updates.items()):
            if value is DELETED:
                del updates[key]
                deletes.add(key)

        self._internal.update(updates)
        for key in deletes:
            del self._internal[key]

        return self

    @property
    def _internal(self):
        # type: () -> dict[str, Any]
        return self.__internal


MCS = TypeVar("MCS", bound=MutableClassState)
