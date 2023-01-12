"""List structures."""

import six
import slotted
from basicco import custom_repr
from basicco.abstract_class import abstract
from basicco.runtime_final import final
from tippo import Any, Callable, Iterable, MutableSequence, Type, TypeVar, overload

from ._bases import (
    BaseCollectionStructure,
    BaseImmutableCollectionStructure,
    BaseMutableCollectionStructure,
    BaseUserCollectionStructure,
    BaseUserImmutableCollectionStructure,
    BaseUserMutableCollectionStructure,
)
from .exceptions import ProcessingError

T = TypeVar("T")


class ListStructure(BaseCollectionStructure[T], slotted.SlottedSequence[T]):
    """List structure."""

    __slots__ = ()

    def __init__(self, initial=()):  # noqa
        # type: (Iterable[T]) -> None
        """
        :param initial: Initial values.
        """
        if self.relationship.will_process:
            try:
                initial_values = tuple(self.relationship.process_value(v, i) for i, v in enumerate(initial))
            except ProcessingError as e:
                exc = type(e)(e)
                six.raise_from(exc, None)
                raise exc
        else:
            initial_values = tuple(initial)
        self._do_init(initial_values)
        self.__post_init__()

    @overload
    def __getitem__(self, item):
        # type: (int) -> T
        pass

    @overload
    def __getitem__(self, item):
        # type: (slice) -> MutableSequence[T]
        pass

    @abstract
    def __getitem__(self, item):
        """
        Get value/values at index/slice.

        :param item: Index/slice.
        :return: Value/values.
        """
        raise NotImplementedError()

    @final
    def _eq(self, other):
        # type: (object) -> bool
        """
        Compare for equality.

        :param other: Another object.
        :return: True if equal.
        """
        if other is self:
            return True
        elif isinstance(other, list):
            return list(self) == other
        else:
            return isinstance(other, type(self)) and type(self) is type(other) and list(self) == list(other)

    def _repr(self):
        # type: () -> str
        """
        Get representation.

        :return: Representation.
        """
        return custom_repr.iterable_repr(self, prefix="{}([".format(type(self).__qualname__), suffix="])")

    @abstract
    def _do_init(self, initial_values):
        # type: (tuple[T, ...]) -> None
        """
        Initialize values (internal).

        :param initial_values: New values.
        """
        raise NotImplementedError()

    @classmethod
    @abstract
    def _do_deserialize(cls, values):
        # type: (Type[LS], tuple[T, ...]) -> LS
        """
        Deserialize (internal).

        :param values: Deserialized values.
        :return: List structure.
        :raises SerializationError: Error while deserializing.
        """
        raise NotImplementedError()

    def serialize(self):
        # type: () -> list[Any]
        """
        Serialize.

        :return: Serialized list.
        :raises SerializationError: Error while serializing.
        """
        return [type(self).relationship.serialize_value(v) for v in self]

    @classmethod
    def deserialize(cls, serialized):
        # type: (Type[LS], Iterable[Any]) -> LS
        """
        Deserialize.

        :param serialized: Serialized iterable.
        :return: List structure.
        :raises SerializationError: Error while deserializing.
        """
        values = tuple(cls.relationship.deserialize_value(s) for s in serialized)
        self = cls._do_deserialize(values)
        self.__post_deserialize__()
        return self

    @abstract
    def count(self, value):
        # type: (object) -> int
        """
        Count number of occurrences of a value.

        :param value: Value.
        :return: Number of occurrences.
        """
        raise NotImplementedError()

    @abstract
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

    @final
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

    @final
    def resolve_continuous_slice(self, slc):
        # type: (slice) -> tuple[int, int]
        """
        Resolve continuous slice according to length.

        :param slc: Continuous slice.
        :return: Index and stop.
        :raises IndexError: Slice is noncontinuous.
        """
        return resolve_continuous_slice(len(self), slc)

    @final
    def pre_move(self, item, target_index):
        # type: (slice | int, int) -> tuple[int, int, int, int, int] | None
        """
        Perform checks before moving values internally and get move indexes.

        :param item: Index/slice.
        :param target_index: Target index.
        :return: None or (target index, index, stop, post index, post_stop).
        """
        return pre_move(len(self), item, target_index)


LS = TypeVar("LS", bound=ListStructure)  # list structure self type


# noinspection PyAbstractClass
class UserListStructure(ListStructure[T], BaseUserCollectionStructure[T]):
    """User list structure."""

    __slots__ = ()

    @final
    def _append(self, value):
        # type: (ULS, T) -> ULS
        """
        Append value at the end.

        :param value: Value.
        :return: Transformed (immutable) or self (mutable).
        """
        return self._insert(len(self), value)

    @final
    def _extend(self, iterable):
        # type: (ULS, Iterable[T]) -> ULS
        """
        Extend at the end with iterable.

        :param iterable: Iterable.
        :return: Transformed (immutable) or self (mutable).
        """
        return self._insert(len(self), *iterable)

    @final
    def _remove(self, value):
        # type: (ULS, T) -> ULS
        """
        Remove first occurrence of value.

        :param value: Value.
        :return: Transformed (immutable) or self (mutable).
        :raises ValueError: Value is not present.
        """
        return self._delete(self.index(value))

    @final
    def _reverse(self):
        # type: (ULS) -> ULS
        """
        Reverse values.

        :return: Transformed (immutable) or self (mutable).
        """
        return self._update(slice(0, len(self)), reversed(self))

    @final
    def _sort(self, key=None):
        # type: (ULS, Callable[[T], Any] | None) -> ULS
        """
        Sort values.

        :param key: Sorting key function.
        :return: Transformed (immutable) or self (mutable).
        """
        return self._update(slice(0, len(self)), sorted(self, key=key))

    @abstract
    def _do_insert(self, index, new_values):
        # type: (int, tuple[T, ...]) -> None
        """
        Insert value(s) at index (internal).

        :param index: Index.
        :param new_values: New values.
        """
        raise NotImplementedError()

    @final
    def _insert(self, index, *values):
        # type: (ULS, int, T) -> ULS
        """
        Insert value(s) at index.

        :param index: Index.
        :param values: Value(s).
        :return: Transformed (immutable) or self (mutable).
        """
        if not values:
            return self
        index = self.resolve_index(index, clamp=True)
        if self.relationship.will_process:
            try:
                values = tuple(self.relationship.process_value(v, i) for i, v in enumerate(values))
            except ProcessingError as e:
                exc = type(e)(e)
                six.raise_from(exc, None)
                raise exc
        with self.__change_context__() as _self:
            _self._do_insert(index, values)
            return _self

    @abstract
    def _do_move(self, target_index, index, stop, post_index, post_stop, values):
        # type: (int, int, int, int, int, tuple[T, ...]) -> None
        """
        Move values internally (internal).

        :param target_index: Target index.
        :param index: Index (pre-move).
        :param index: Stop (pre-move).
        :param post_index: Post index (post-move).
        :param post_index: Post stop (post-move).
        :param values: Values being moved.
        """
        raise NotImplementedError()

    @final
    def _move(self, item, target_index):
        # type: (ULS, slice | int, int) -> ULS
        """
        Move values internally.

        :param item: Index/slice.
        :param target_index: Target index.
        :return: Transformed (immutable) or self (mutable).
        """
        result = self.pre_move(item, target_index)
        if result is None:
            return self
        target_index, index, stop, post_index, post_stop = result
        values = tuple(self[index:stop])
        with self.__change_context__() as _self:
            _self._do_move(target_index, index, stop, post_index, post_stop, values)
            return _self

    @abstract
    def _do_delete(self, index, stop, old_values):
        # type: (int, int, tuple[T, ...]) -> None
        """
        Delete values at index/slice (internal).

        :param index: Index.
        :param index: Stop.
        :param old_values: Values being deleted.
        """
        raise NotImplementedError()

    @final
    def _delete(self, item):
        # type: (ULS, slice | int) -> ULS
        """
        Delete values at index/slice.

        :param item: Index/slice.
        :return: Transformed (immutable) or self (mutable).
        """
        if isinstance(item, slice):
            index, stop = self.resolve_continuous_slice(item)
            if index == stop:
                return self
        else:
            index = self.resolve_index(item)
            stop = index + 1

        values = tuple(self[index:stop])
        if not values:
            return self

        with self.__change_context__() as _self:
            _self._do_delete(index, stop, values)
            return _self

    @final
    def _set(self, index, value):
        # type: (ULS, int, T) -> ULS
        """
        Set value at index.

        :param index: Index.
        :param value: Value.
        :return: Transformed (immutable) or self (mutable).
        :raises IndexError: Invalid index.
        """
        index = self.resolve_index(index)
        return self._update(index, value)

    @abstract
    def _do_update(self, index, stop, old_values, new_values):
        # type: (int, int, tuple[T, ...], tuple[T, ...]) -> None
        """
        Update value(s) (internal).

        :param index: Index.
        :param stop: Stop.
        :param old_values: Old values.
        :param new_values: New values.
        """
        raise NotImplementedError()

    @overload
    def _update(self, item, value):
        # type: (ULS, int, T) -> ULS
        pass

    @overload
    def _update(self, item, value):
        # type: (ULS, slice, Iterable[T]) -> ULS
        pass

    @final
    def _update(self, item, value):
        """
        Update value(s).

        :param item: Index/slice.
        :param value: Value(s).
        :return: Transformed (immutable) or self (mutable).
        :raises IndexError: Range length mismatch.
        """
        if isinstance(item, slice):
            index, stop = self.resolve_continuous_slice(item)
            if index == stop:
                return self._insert(index, *value)
            new_values = tuple(value)
            if stop - index != len(new_values):
                error = "range length ({}) and values length ({}) do not match".format(stop - index, len(new_values))
                raise IndexError(error)
        else:
            index = self.resolve_index(item)
            stop = index + 1
            new_values = (value,)

        if not new_values:
            return self
        old_values = tuple(self[index:stop])

        if self.relationship.will_process:
            try:
                if isinstance(item, slice):
                    new_values = tuple(self.relationship.process_value(v, i) for i, v in enumerate(new_values))
                else:
                    new_values = tuple(self.relationship.process_value(v) for v in new_values)
            except ProcessingError as e:
                exc = type(e)(e)
                six.raise_from(exc, None)
                raise exc

        with self.__change_context__() as _self:
            _self._do_update(index, stop, old_values, new_values)
            return _self


ULS = TypeVar("ULS", bound=UserListStructure)  # user list structure self type


# noinspection PyAbstractClass
class ImmutableListStructure(ListStructure[T], BaseImmutableCollectionStructure[T]):
    """Immutable list structure."""

    __slots__ = ()

    @final
    def _hash(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        """
        return hash(tuple(self))


ILS = TypeVar("ILS", bound=ImmutableListStructure)  # immutable list structure self type


# noinspection PyAbstractClass
class UserImmutableListStructure(
    ImmutableListStructure[T],
    UserListStructure[T],
    BaseUserImmutableCollectionStructure[T],
):
    """User immutable list structure."""

    __slots__ = ()

    @final
    def append(self, value):
        # type: (UILS, T) -> UILS
        """
        Append value at the end.

        :param value: Value.
        :return: Transformed.
        """
        return self._append(value)

    @final
    def extend(self, iterable):
        # type: (UILS, Iterable[T]) -> UILS
        """
        Extend at the end with iterable.

        :param iterable: Iterable.
        :return: Transformed.
        """
        return self._extend(iterable)

    @final
    def remove(self, value):
        # type: (UILS, T) -> UILS
        """
        Remove first occurrence of value.

        :param value: Value.
        :return: Transformed.
        :raises ValueError: Value is not present.
        """
        return self._remove(value)

    @final
    def reverse(self):
        # type: (UILS) -> UILS
        """
        Reverse values.

        :return: Transformed.
        """
        return self._reverse()

    @final
    def sort(self, key=None):
        # type: (UILS, Callable[[T], Any] | None) -> UILS
        """
        Sort values.

        :param key: Sorting key function.
        :return: Transformed (immutable) or self (mutable).
        """
        return self._sort(key=key)  # noqa

    @final
    def insert(self, index, *values):
        # type: (UILS, int, T) -> UILS
        """
        Insert value(s) at index.

        :param index: Index.
        :param values: Value(s).
        :return: Transformed.
        """
        return self._insert(index, *values)

    @final
    def move(self, item, target_index):
        # type: (UILS, slice | int, int) -> UILS
        """
        Move values internally.

        :param item: Index/slice.
        :param target_index: Target index.
        :return: Transformed.
        """
        return self._move(item, target_index)

    @final
    def delete(self, item):
        # type: (UILS, slice | int) -> UILS
        """
        Delete values at index/slice.

        :param item: Index/slice.
        :return: Transformed.
        """
        return self._delete(item)

    @final
    def set(self, index, value):
        # type: (UILS, int, T) -> UILS
        """
        Set value at index.

        :param index: Index.
        :param value: Value.
        :return: Transformed.
        :raises IndexError: Invalid index.
        """
        return self._set(index, value)

    @overload
    def update(self, item, value):
        # type: (UILS, int, T) -> UILS
        pass

    @overload
    def update(self, item, value):
        # type: (UILS, slice, Iterable[T]) -> UILS
        pass

    @final
    def update(self, item, value):
        """
        Update value(s).

        :param item: Index/slice.
        :param value: Value(s).
        :return: Transformed.
        """
        return self._update(item, value)


UILS = TypeVar("UILS", bound=UserImmutableListStructure)  # user immutable list structure self type


# noinspection PyAbstractClass
class MutableListStructure(
    ListStructure[T],
    BaseMutableCollectionStructure[T],
):
    """Mutable list structure."""

    __slots__ = ()


MLS = TypeVar("MLS", bound=MutableListStructure)  # mutable list structure self type


# noinspection PyAbstractClass
class UserMutableListStructure(
    MutableListStructure[T],
    UserListStructure[T],
    BaseUserMutableCollectionStructure[T],
    slotted.SlottedMutableSequence[T],
):
    """User mutable list structure."""

    __slots__ = ()

    @final
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

    @final
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

    @final
    def __delitem__(self, item):
        # type: (slice | int) -> None
        """
        Delete value/values at index/slice.

        :param item: Index/slice.
        :raises IndexError: Slice is noncontinuous.
        """
        self._delete(item)

    @final
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

    @final
    def insert(self, index, *values):
        # type: (int, T) -> None
        """
        Insert value(s) at index.

        :param index: Index.
        :param values: Value(s).
        """
        self._insert(index, *values)

    @final
    def append(self, value):
        # type: (T) -> None
        """
        Append value at the end.

        :param value: Value.
        """
        self._append(value)

    @final
    def extend(self, iterable):
        # type: (Iterable[T]) -> None
        """
        Extend at the end with iterable.

        :param iterable: Iterable.
        """
        self._extend(iterable)

    @final
    def remove(self, value):
        # type: (T) -> None
        """
        Remove first occurrence of value.

        :param value: Value.
        :raises ValueError: Value is not present.
        """
        self._remove(value)

    @final
    def reverse(self):
        # type: () -> None
        """Reverse values."""
        self._reverse()

    @final
    def sort(self, key=None):
        # type: (Callable[[T], Any] | None) -> None
        """
        Sort values.

        :param key: Sorting key function.
        """
        self._sort(key=key)

    @final
    def move(self, item, target_index):
        # type: (slice | int, int) -> None
        """
        Move values internally.

        :param item: Index/slice.
        :param target_index: Target index.
        """
        self._move(item, target_index)

    @final
    def delete(self, item):
        # type: (slice | int) -> None
        """
        Delete values at index/slice.

        :param item: Index/slice.
        """
        self._delete(item)

    @final
    def set(self, index, value):
        # type: (int, T) -> None
        """
        Set value at index.

        :param index: Index.
        :param value: Value.
        :return: Transformed.
        :raises IndexError: Invalid index.
        """
        self._set(index, value)

    @overload
    def update(self, item, value):
        # type: (int, T) -> None
        pass

    @overload
    def update(self, item, value):
        # type: (slice, Iterable[T]) -> None
        pass

    @final
    def update(self, item, value):
        """
        Update value(s).

        :param item: Index/slice.
        :param value: Value(s).
        :return: Transformed.
        """
        self._update(item, value)


UMLS = TypeVar("UMLS", bound=UserMutableListStructure)  # user mutable list structure self type


def resolve_index(length, index, clamp=False):
    # type: (int, int, bool) -> int
    """
    Resolve list index to a positive number.

    :param length: Length of the list.
    :param index: Input index.
    :param clamp: Whether to clamp between zero and the length.
    :return: Resolved index.
    :raises IndexError: Index out of range.
    """
    if index < 0:
        index += length
    if clamp:
        if index < 0:
            index = 0
        elif index > length:
            index = length
    elif index < 0 or index >= length:
        error = "index out of range"
        raise IndexError(error)
    return index


def resolve_continuous_slice(length, slc):
    # type: (int, slice) -> tuple[int, int]
    """
    Resolve continuous list slice according to length.

    :param length: Length of the list.
    :param slc: Continuous slice.
    :return: Index and stop.
    :raises IndexError: Slice is noncontinuous.
    """
    index, stop, step = slc.indices(length)
    if step != 1 or stop < index:
        error = "slice {} is noncontinuous".format(slc)
        raise IndexError(error)
    return index, stop


def pre_move(length, item, target_index):
    # type: (int, slice | int, int) -> tuple[int, int, int, int, int] | None
    """
    Perform checks before moving list values internally and get move indexes.

    :param length: Length of the list.
    :param item: Index/slice.
    :param target_index: Target index.
    :return: None or (target index, index, stop, post index, post stop).
    """

    # Resolve slice/index.
    if isinstance(item, slice):
        index, stop = resolve_continuous_slice(length, item)
        if index == stop:
            return None
    else:
        index = resolve_index(length, item)
        stop = index + 1

    # Calculate target index, post index, and post stop.
    target_index = resolve_index(length, target_index, clamp=True)
    if index <= target_index <= stop:
        return None
    elif target_index > stop:
        post_index = target_index - (stop - index)
    else:
        post_index = target_index
    post_stop = post_index + (stop - index)

    return target_index, index, stop, post_index, post_stop
