"""List structures."""

import abc

import slotted
from basicco import runtime_final
from tippo import (
    Any,
    Iterable,
    Iterator,
    MutableSequence,
    Type,
    TypeVar,
    cast,
    overload,
)

from ._bases import (
    InteractiveProxyUniformStructure,
    InteractiveUniformStructure,
    MutableProxyUniformStructure,
    MutableUniformStructure,
    PrivateProxyUniformStructure,
    PrivateUniformStructure,
    ProxyUniformStructure,
    UniformStructure,
)
from ._utils import pre_move, resolve_continuous_slice, resolve_index

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)


class ListStructure(UniformStructure[T_co], slotted.SlottedSequence[T_co]):
    """List structure."""

    __slots__ = ()

    @abc.abstractmethod
    def __reversed__(self):
        # type: () -> Iterator[T_co]
        """
        Iterate over reversed values.

        :return: Reversed values iterator.
        """
        raise NotImplementedError()

    @overload
    def __getitem__(self, index):
        # type: (int) -> T_co
        pass

    @overload
    def __getitem__(self, index):
        # type: (slice) -> MutableSequence[T_co]
        pass

    @abc.abstractmethod
    def __getitem__(self, index):
        """
        Get value/values at index/from slice.

        :param index: Index/slice.
        :return: Value/values.
        """
        raise NotImplementedError()

    @classmethod
    @abc.abstractmethod
    def __construct__(cls, values):
        # type: (Type[LS], list[T_co]) -> LS
        """
        Construct an instance with deserialized values.

        :param values: Deserialized values.
        :return: Instance.
        """
        raise NotImplementedError()

    def serialize(self):
        # type: () -> list
        relationship = type(self).__relationship__
        return [relationship.serialize_value(v) for v in self]

    @classmethod
    def deserialize(cls, serialized):
        # type: (Type[LS], list) -> LS
        relationship = cls.__relationship__
        return cls.__construct__([relationship.deserialize_value(v) for v in serialized])

    @abc.abstractmethod
    def count(self, value):
        # type: (object) -> int
        """
        Count number of occurrences of a value.

        :param value: Value.
        :return: Number of occurrences.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def index(self, value, start=None, stop=None):
        # type: (Any, int | None, int | None) -> int
        """
        Get index of a value.

        :param value: Value.
        :param start: Start index.
        :param stop: Stop index.
        :return: Index of value.
        :raises ValueError: Provided stop but did not provide start.
        """
        raise NotImplementedError()

    @runtime_final.final
    def resolve_index(self, index, clamp=False):
        # type: (int, bool) -> int
        """
        Resolve index to a positive number.

        :param index: Input index.
        :param clamp: Whether to clamp between zero and the length.
        :return: Resolved index.
        :raises IndexError: Index out of range.
        """
        return resolve_index(len(self), index, clamp=clamp)

    @runtime_final.final
    def resolve_continuous_slice(self, slc):
        # type: (slice) -> tuple[int, int]
        """
        Resolve continuous slice according to length.

        :param slc: Continuous slice.
        :return: Index and stop.
        :raises IndexError: Slice is noncontinuous.
        """
        return resolve_continuous_slice(len(self), slc)

    @runtime_final.final
    def pre_move(self, item, target_index):
        # type: (slice | int, int) -> tuple[int, int, int, int] | None
        """
        Perform checks before moving values internally.

        :param item: Index/slice.
        :param target_index: Target index.
        :return: None or (index, stop, target index, post index).
        """
        return pre_move(len(self), item, target_index)


LS = TypeVar("LS", bound=ListStructure)


class PrivateListStructure(ListStructure[T], PrivateUniformStructure[T]):
    """Private list structure."""

    __slots__ = ()

    @runtime_final.final
    def _append(self, value):
        # type: (PLS, T) -> PLS
        """
        Append value at the end.

        :param value: Value.
        :return: Transformed.
        """
        return self._insert(len(self), value)

    @runtime_final.final
    def _extend(self, iterable):
        # type: (PLS, Iterable[T]) -> PLS
        """
        Extend at the end with iterable.

        :param iterable: Iterable.
        :return: Transformed.
        """
        return self._insert(len(self), *iterable)

    @runtime_final.final
    def _remove(self, value):
        # type: (PLS, T) -> PLS
        """
        Remove first occurrence of value.

        :param value: Value.
        :return: Transformed.
        :raises ValueError: Value is not present.
        """
        return self._delete(self.index(value))

    @runtime_final.final
    def _reverse(self):
        # type: (PLS) -> PLS
        """
        Reverse values.

        :return: Transformed.
        """
        return self._update(slice(0, len(self)), reversed(self))

    @abc.abstractmethod
    def _insert(self, index, *values):
        # type: (PLS, int, T) -> PLS
        """
        Insert value(s) at index.

        :param index: Index.
        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def _move(self, item, target_index):
        # type: (PLS, slice | int, int) -> PLS
        """
        Move values internally.

        :param item: Index/slice.
        :param target_index: Target index.
        :return: Transformed.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def _delete(self, item):
        # type: (PLS, slice | int) -> PLS
        """
        Delete values at index/slice.

        :param item: Index/slice.
        :return: Transformed.
        """
        raise NotImplementedError()

    @overload
    def _update(self, item, value):
        # type: (PLS, int, T) -> PLS
        pass

    @overload
    def _update(self, item, value):
        # type: (PLS, slice, Iterable[T]) -> PLS
        pass

    @abc.abstractmethod
    def _update(self, item, value):
        """
        Update value(s).

        :param item: Index/slice.
        :param value: Value(s).
        :return: Transformed.
        """
        raise NotImplementedError()


PLS = TypeVar("PLS", bound=PrivateListStructure)


# noinspection PyAbstractClass
class InteractiveListStructure(PrivateListStructure[T], InteractiveUniformStructure[T]):
    """Interactive list structure."""

    __slots__ = ()

    @runtime_final.final
    def append(self, value):
        # type: (ILS, T) -> ILS
        """
        Append value at the end.

        :param value: Value.
        :return: Transformed.
        """
        return self._append(value)

    @runtime_final.final
    def extend(self, iterable):
        # type: (ILS, Iterable[T]) -> ILS
        """
        Extend at the end with iterable.

        :param iterable: Iterable.
        :return: Transformed.
        """
        return self._extend(iterable)

    @runtime_final.final
    def remove(self, value):
        # type: (ILS, T) -> ILS
        """
        Remove first occurrence of value.

        :param value: Value.
        :return: Transformed.
        :raises ValueError: Value is not present.
        """
        return self._remove(value)

    @runtime_final.final
    def reverse(self):
        # type: (ILS) -> ILS
        """
        Reverse values.

        :return: Transformed.
        """
        return self._reverse()

    @runtime_final.final
    def insert(self, index, *values):
        # type: (ILS, int, T) -> ILS
        """
        Insert value(s) at index.

        :param index: Index.
        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        """
        return self._insert(index, *values)

    @runtime_final.final
    def move(self, item, target_index):
        # type: (ILS, slice | int, int) -> ILS
        """
        Move values internally.

        :param item: Index/slice.
        :param target_index: Target index.
        :return: Transformed.
        """
        return self._move(item, target_index)

    @runtime_final.final
    def delete(self, item):
        # type: (ILS, slice | int) -> ILS
        """
        Delete values at index/slice.

        :param item: Index/slice.
        :return: Transformed.
        """
        return self._delete(item)

    @overload
    def update(self, item, value):
        # type: (ILS, int, T) -> ILS
        pass

    @overload
    def update(self, item, value):
        # type: (ILS, slice, Iterable[T]) -> ILS
        pass

    @runtime_final.final
    def update(self, item, value):
        """
        Update value(s).

        :param item: Index/slice.
        :param value: Value(s).
        :return: Transformed.
        """
        return self._update(item, value)


ILS = TypeVar("ILS", bound=InteractiveListStructure)


# noinspection PyAbstractClass
class MutableListStructure(PrivateListStructure[T], MutableUniformStructure[T], slotted.SlottedMutableSequence[T]):
    """Mutable list structure."""

    __slots__ = ()

    @runtime_final.final
    def __iadd__(self, iterable):
        """
        In place addition.

        :param iterable: Another iterable.
        :return: Added list.
        """
        self._extend(iterable)
        return self

    @overload
    def __setitem__(self, index, value):
        # type: (int, T) -> None
        pass

    @overload
    def __setitem__(self, slc, values):
        # type: (slice, Iterable[T]) -> None
        pass

    @runtime_final.final
    def __setitem__(self, item, value):
        """
        Set value/values at index/slice.

        :param item: Index/slice.
        :param value: Value/values.
        :raises IndexError: Slice is noncontinuous.
        :raises ValueError: Values length does not fit in slice.
        """
        self._update(item, value)

    @overload
    def __delitem__(self, index):
        # type: (int) -> None
        pass

    @overload
    def __delitem__(self, slc):
        # type: (slice) -> None
        pass

    @runtime_final.final
    def __delitem__(self, item):
        # type: (slice | int) -> None
        """
        Delete value/values at index/slice.

        :param item: Index/slice.
        :raises IndexError: Slice is noncontinuous.
        """
        self._delete(item)

    @runtime_final.final
    def pop(self, index=-1):
        # type: (int) -> T
        """
        Pop value from index.

        :param index: Index.
        :return: Value.
        """
        value = self[index]
        del self[index]
        return value

    @runtime_final.final
    def insert(self, index, *values):
        # type: (int, T) -> None
        """
        Insert value(s) at index.

        :param index: Index.
        :param values: Value(s).
        :raises ValueError: No values provided.
        """
        self._insert(index, *values)

    @runtime_final.final
    def append(self, value):
        # type: (T) -> None
        """
        Append value at the end.

        :param value: Value.
        """
        self._append(value)

    @runtime_final.final
    def extend(self, iterable):
        # type: (Iterable[T]) -> None
        """
        Extend at the end with iterable.

        :param iterable: Iterable.
        """
        self._extend(iterable)

    @runtime_final.final
    def remove(self, value):
        # type: (T) -> None
        """
        Remove first occurrence of value.

        :param value: Value.
        :raises ValueError: Value is not present.
        """
        self._remove(value)

    @runtime_final.final
    def reverse(self):
        # type: () -> None
        """Reverse values."""
        self._reverse()

    @runtime_final.final
    def move(self, item, target_index):
        # type: (slice | int, int) -> None
        """
        Move values internally.

        :param item: Index/slice.
        :param target_index: Target index.
        """
        self._move(item, target_index)

    @runtime_final.final
    def delete(self, item):
        # type: (slice | int) -> None
        """
        Delete values at index/slice.

        :param item: Index/slice.
        """
        self._delete(item)

    @overload
    def update(self, item, value):
        # type: (int, T) -> None
        pass

    @overload
    def update(self, item, value):
        # type: (slice, Iterable[T]) -> None
        pass

    @runtime_final.final
    def update(self, item, value):
        """
        Update value(s).

        :param item: Index/slice.
        :param value: Value(s).
        :return: Transformed.
        """
        self._update(item, value)


# noinspection PyAbstractClass
class ProxyList(ListStructure[T_co], ProxyUniformStructure[T_co]):
    """Proxy list."""

    __slots__ = ()

    def __init__(self, wrapped):
        # type: (PrivateListStructure[T_co]) -> None
        """
        :param wrapped: List structure to be wrapped.
        """
        super(ProxyList, self).__init__(wrapped)

    @runtime_final.final
    def __reversed__(self):
        # type: () -> Iterator[T_co]
        """
        Iterate over reversed values.

        :return: Reversed values iterator.
        """
        return reversed(self._wrapped)

    @overload
    def __getitem__(self, index):
        # type: (int) -> T_co
        pass

    @overload
    def __getitem__(self, index):
        # type: (slice) -> MutableSequence[T_co]
        pass

    @runtime_final.final
    def __getitem__(self, index):
        """
        Get value/values at index/from slice.

        :param index: Index/slice.
        :return: Value/values.
        """
        return self._wrapped[index]

    @runtime_final.final
    def count(self, value):
        # type: (object) -> int
        """
        Count number of occurrences of a value.

        :param value: Value.
        :return: Number of occurrences.
        """
        return len(self._wrapped)

    @runtime_final.final
    def index(self, value, start=None, stop=None):
        # type: (Any, int | None, int | None) -> int
        """
        Get index of a value.

        :param value: Value.
        :param start: Start index.
        :param stop: Stop index.
        :return: Index of value.
        :raises ValueError: Provided stop but did not provide start.
        """
        return self._wrapped.index(value, start=start, stop=stop)

    @property
    def _wrapped(self):
        # type: () -> PrivateListStructure[T_co]
        """Wrapped list collection."""
        return cast(PrivateListStructure[T_co], super(ProxyList, self)._wrapped)


# noinspection PyAbstractClass
class PrivateProxyList(ProxyList[T], PrivateListStructure[T], PrivateProxyUniformStructure[T]):
    """Private proxy list."""

    __slots__ = ()

    @runtime_final.final
    def _insert(self, index, *values):
        # type: (PPL, int, T) -> PPL
        """
        Insert value(s) at index.

        :param index: Index.
        :param values: Value(s).
        :return: Transformed.
        :raises ValueError: No values provided.
        """
        return self._transform_wrapped(self._wrapped._insert(index, *values))

    @runtime_final.final
    def _move(self, item, target_index):
        # type: (PPL, slice | int, int) -> PPL
        """
        Move values internally.

        :param item: Index/slice.
        :param target_index: Target index.
        :return: Transformed.
        """
        return self._transform_wrapped(self._wrapped._move(item, target_index))

    @runtime_final.final
    def _delete(self, item):
        # type: (PPL, slice | int) -> PPL
        """
        Delete values at index/slice.

        :param item: Index/slice.
        :return: Transformed.
        """
        return self._transform_wrapped(self._wrapped._delete(item))

    @overload
    def _update(self, item, value):
        # type: (PPL, int, T) -> PPL
        pass

    @overload
    def _update(self, item, value):
        # type: (PPL, slice, Iterable[T]) -> PPL
        pass

    @runtime_final.final
    def _update(self, item, value):
        """
        Update value(s).

        :param item: Index/slice.
        :param value: Value(s).
        :return: Transformed.
        """
        return self._transform_wrapped(self._wrapped._update(item, value))  # noqa


PPL = TypeVar("PPL", bound=PrivateProxyList)


# noinspection PyAbstractClass
class InteractiveProxyList(PrivateProxyList[T], InteractiveListStructure[T], InteractiveProxyUniformStructure[T]):
    """Interactive proxy list."""

    __slots__ = ()


# noinspection PyAbstractClass
class MutableProxyList(PrivateProxyList[T], MutableListStructure[T], MutableProxyUniformStructure[T]):
    """Proxy mutable list."""

    __slots__ = ()

    def __init__(self, wrapped):
        # type: (MutableListStructure[T]) -> None
        """
        :param wrapped: Mutable list structure.
        """
        super(MutableProxyList, self).__init__(wrapped)

    @property
    def _wrapped(self):
        # type: () -> MutableListStructure[T]
        """Wrapped mutable list structure."""
        return cast(MutableListStructure[T], super(MutableProxyList, self)._wrapped)
