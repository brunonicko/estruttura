import six
import pyrsistent
from basicco import recursive_repr, custom_repr
from tippo import Any, TypeVar, Iterable, Mapping, Iterator, Union, overload
from pyrsistent.typing import PMap

from estruttura import SupportsKeysAndGetItem, BasePrivateDict, BaseInteractiveDict

from ._bases import BasePrivateDataCollection, BaseDataCollection


KT = TypeVar("KT")  # key type
VT = TypeVar("VT")  # value type


class PrivateDataDict(BasePrivateDataCollection[PMap[KT, VT], KT], BasePrivateDict[KT, VT]):
    """Private dictionary data."""

    __slots__ = ()

    @staticmethod
    def _init_internal(initial):
        # type: (Union[Iterable[tuple[KT, VT]], Mapping[KT, VT]]) -> PMap[KT, VT]
        """
        Initialize internal state.

        :param initial: Initial values.
        """
        return pyrsistent.pmap(initial)

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
        if len(args) == 1 and not kwargs:
            initial = args[0]
        else:
            initial = dict(*args, **kwargs)
        super(PrivateDataDict, self).__init__(initial)

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

    @recursive_repr.recursive_repr
    def __repr__(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        """
        return custom_repr.mapping_repr(
            self._internal,
            prefix="{}({{".format(type(self).__fullname__),
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

    def _clear(self):
        # type: (PDD) -> PDD
        """
        Clear.

        :return: Transformed.
        """
        return self._make(pyrsistent.pmap())

    def _discard(self, key):
        # type: (PDD, KT) -> PDD
        """
        Discard key if it exists.

        :param key: Key.
        :return: Transformed.
        """
        return self._make(self._internal.discard(key))

    def _remove(self, key):
        # type: (PDD, KT) -> PDD
        """
        Delete existing key.

        :param key: Key.
        :return: Transformed.
        :raises KeyError: Key is not present.
        """
        return self._make(self._internal.remove(key))

    def _set(self, key, value):
        # type: (PDD, KT, VT) -> PDD
        """
        Set value for key.

        :param key: Key.
        :param value: Value.
        :return: Transformed.
        """
        return self._make(self._internal.set(key, value))

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
        return self._make(self._internal.update(dict(*args, **kwargs)))

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


PDD = TypeVar("PDD", bound=PrivateDataDict)


class DataDict(PrivateDataDict[KT, VT], BaseDataCollection[PMap[KT, VT], KT], BaseInteractiveDict[KT, VT]):
    """Dictionary data."""

    __slots__ = ()
