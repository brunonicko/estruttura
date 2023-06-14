from basicco import SlottedBase, abstract
from slotted import SlottedCollection
from tippo import Iterator, Self, TypeVar

__all__ = [
    "Structure",
    "ImmutableStructure",
    "MutableStructure",
    "CollectionStructure",
]


T = TypeVar("T")


class Structure(SlottedBase):
    """Base Structure."""

    __slots__ = ()

    @abstract
    def __hash__(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        """
        raise NotImplementedError()

    @abstract
    def __eq__(self, other):
        # type: (object) -> bool
        """
        Compare for equality.

        :param other: Another object.
        :return: True if equal.
        """
        raise NotImplementedError()


class ImmutableStructure(Structure):
    """Base Immutable Structure."""

    __slots__ = ()


class MutableStructure(Structure):
    """Base Mutable Structure."""

    __slots__ = ()
    __hash__ = None  # type: ignore


class CollectionStructure(Structure, SlottedCollection[T]):
    """Base Collection Structure."""

    __slots__ = ()

    @abstract
    def __contains__(self, content):
        # type: (object) -> bool
        """
        Whether has content.

        :param content: Content.
        :return: True if has content.
        """
        raise NotImplementedError()

    @abstract
    def __iter__(self):
        # type: () -> Iterator[T]
        """
        Iterate over content.

        :return: Content iterator.
        """
        raise NotImplementedError()

    @abstract
    def __len__(self):
        # type: () -> int
        """
        Get length.

        :return: Length.
        """
        raise NotImplementedError()


class ImmutableCollectionStructure(ImmutableStructure, CollectionStructure[T]):
    """Base Immutable Collection Structure."""

    __slots__ = ()

    @abstract
    def clear(self):
        # type: () -> Self
        """
        Clear contents.

        :return: Transformed.
        """
        raise NotImplementedError()


class MutableCollectionStructure(MutableStructure, CollectionStructure[T]):
    """Base Mutable Collection Structure."""

    __slots__ = ()
    __hash__ = None  # type: ignore

    @abstract
    def clear(self):
        # type: () -> None
        """Clear contents."""
        raise NotImplementedError()
