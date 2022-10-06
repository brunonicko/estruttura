import six
import pyrsistent
from basicco import recursive_repr, custom_repr, safe_repr
from tippo import Any, TypeVar, Iterable, Mapping, Iterator, Union, SupportsKeysAndGetItem, overload
from pyrsistent.typing import PMap

from estruttura import DELETED, DictStructure, PrivateDictStructure, InteractiveDictStructure, get_relationship

from ._bases import UniformData, PrivateUniformData, InteractiveUniformData


KT = TypeVar("KT")  # key type
VT = TypeVar("VT")  # value type


class ProtectedDataDict(UniformData[PMap[KT, VT], KT], DictStructure[KT, VT]):
    """Protected data dictionary."""

    __slots__ = ()

    @staticmethod
    def _init_internal(initial):
        # type: (Union[Iterable[tuple[KT, VT]], Mapping[KT, VT]]) -> PMap[KT, VT]
        """
        Initialize internal state.

        :param initial: Initial values.
        """
        return pyrsistent.pmap(initial or ())

    @overload
    def __init__(self, __m, **kwargs):
        # type: (SupportsKeysAndGetItem[KT, VT], **VT) -> None
        pass

    @overload
    def __init__(self, __m, **kwargs):
        # type: (Iterable[tuple[KT, VT]], **VT) -> None
        pass

    @overload
    def __init__(self, **kwargs):
        # type: (**VT) -> None
        pass

    def __init__(self, *args, **kwargs):
        initial = dict(*args, **kwargs)
        rel = get_relationship(self)
        for key, value in six.iteritems(initial):
            if value is DELETED:
                error = "{!r}; DELETED is not a valid initial value".format(key)
                raise ValueError(error)
            if rel is not None:
                try:
                    value = rel.process(value)
                except Exception as e:
                    exc = type(e)("{!r}; {}".format(key, e))
                    six.raise_from(exc, None)
                    raise exc
            initial[key] = value
        super(ProtectedDataDict, self).__init__(initial)

    def __contains__(self, key):
        # type: (Any) -> bool
        """
        Get whether key is present.

        :param key: Key.
        :return: True if contains.
        """
        return key in self._internal

    def __iter__(self):
        # type: () -> Iterator[KT]
        """
        Iterate over keys.

        :return: Keys iterator.
        """
        for key in six.iterkeys(self._internal):
            yield key

    def __len__(self):
        # type: () -> int
        """
        Get key count.

        :return: Key count.
        """
        return len(self._internal)

    @safe_repr.safe_repr
    @recursive_repr.recursive_repr
    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        """
        return custom_repr.mapping_repr(
            self._internal,
            prefix="{}({{".format(type(self).__qualname__),
            suffix="})",
            sorting=True,
            sort_key=lambda i: hash(i[0]),
        )

    def __getitem__(self, key):
        # type: (KT) -> VT
        """
        Get value for key.

        :param key: Key.
        :return: Value.
        :raises KeyError: Key is not present.
        """
        return self._internal[key]

    def get(self, key, fallback=None):
        # type: (KT, Any) -> Union[VT, Any]
        """
        Get value for key, return fallback value if key is not present.

        :param key: Key.
        :param fallback: Fallback value.
        :return: Value or fallback value.
        """
        return self._internal.get(key, fallback)

    def iteritems(self):
        # type: () -> Iterator[tuple[KT, VT]]
        """
        Iterate over items.

        :return: Items iterator.
        """
        for key, value in six.iteritems(self._internal):
            yield key, value

    def iterkeys(self):
        # type: () -> Iterator[KT]
        """
        Iterate over keys.

        :return: Keys iterator.
        """
        for key in six.iterkeys(self._internal):
            yield key

    def itervalues(self):
        # type: () -> Iterator[VT]
        """
        Iterate over values.

        :return: Values iterator.
        """
        for value in six.itervalues(self._internal):
            yield value


class PrivateDataDict(ProtectedDataDict[KT, VT], PrivateUniformData[PMap[KT, VT], KT], PrivateDictStructure[KT, VT]):
    """Private data dictionary."""

    __slots__ = ()

    @overload
    def _update(self, __m, **kwargs):
        # type: (PDD, SupportsKeysAndGetItem[KT, VT], **VT) -> PDD
        pass

    @overload
    def _update(self, __m, **kwargs):
        # type: (PDD, Iterable[tuple[KT, VT]], **VT) -> PDD
        pass

    @overload
    def _update(self, **kwargs):
        # type: (PDD, **VT) -> PDD
        pass

    def _update(self, *args, **kwargs):
        """
        Update keys and values.
        Same parameters as :meth:`dict.update`.

        :return: Transformed.
        """
        if not args and not kwargs:
            return self

        updates = dict(*args, **kwargs)
        deletes = set()
        rel = get_relationship(self)
        for key, value in six.iteritems(updates):
            if value is DELETED:
                deletes.add(key)
                continue
            if rel is not None:
                try:
                    value = rel.process(value)
                except Exception as e:
                    exc = type(e)("{!r}; {}".format(key, e))
                    six.raise_from(exc, None)
                    raise exc
            updates[key] = value

        internal = self._internal
        if updates:
            internal = internal.update(updates)
        if deletes:
            internal = internal.transform([lambda k: k in deletes], pyrsistent.discard)

        return self._make(internal)


PDD = TypeVar("PDD", bound=PrivateDataDict)


class DataDict(PrivateDataDict[KT, VT], InteractiveUniformData[PMap[KT, VT], KT], InteractiveDictStructure[KT, VT]):
    """Data dictionary."""

    __slots__ = ()
