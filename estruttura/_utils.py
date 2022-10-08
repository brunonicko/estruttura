"""Utility functions."""

from tippo import Any, Callable, Type, TypeVar, cast

from ._attribute import Attribute, AttributeMap
from ._bases import UniformStructure, UniformStructureMeta
from ._relationship import Relationship
from ._structure import Structure, StructureMeta

T = TypeVar("T")


def get_relationship(uniform_structure):
    # type: (Type[UniformStructure] | UniformStructure) -> Relationship
    return uniform_structure.__relationship__


def get_relationship_type(uniform_structure):
    # type: (Type[UniformStructure] | UniformStructure) -> Type[Relationship]
    if not isinstance(uniform_structure, UniformStructureMeta):
        uniform_structure = cast(Type[UniformStructure], type(uniform_structure))
    return uniform_structure.__relationship_type__


def get_attributes(structure):
    # type: (Type[Structure] | Structure) -> AttributeMap
    if not isinstance(structure, StructureMeta):
        structure = cast(Type[Structure], type(structure))
    return structure.__attributes__


def get_attribute_type(structure):
    # type: (Type[Structure] | Structure) -> Type[Attribute]
    if not isinstance(structure, StructureMeta):
        structure = cast(Type[Structure], type(structure))
    return structure.__attribute_type__


def to_items(structure):
    # type: (Structure) -> list[tuple[str, Any]]
    return [(n, structure[n]) for n in structure if hasattr(structure, n)]


def getter(attribute, dependencies):
    # type: (T, tuple) -> Callable[[Callable[[Any], T]], None]

    def decorator(func):
        # type: (Callable[[Any], T]) -> None
        if func.__name__ != "_":
            error = "delegate function {!r} needs to be named '_'".format(func.__name__)
            raise NameError(error)
        cast(Attribute, attribute).getter(*dependencies)(func)

    return decorator


def setter(attribute):
    # type: (Any) -> Callable[[Callable[[Any, Any], None]], None]

    def decorator(func):
        # type: (Callable[[Any, Any], None]) -> None
        if func.__name__ != "_":
            error = "delegate function {!r} needs to be named '_'".format(func.__name__)
            raise NameError(error)
        cast(Attribute, attribute).setter(func)

    return decorator


def deleter(attribute):
    # type: (Any) -> Callable[[Callable[[Any], None]], None]

    def decorator(func):
        # type: (Callable[[Any], None]) -> None
        if func.__name__ != "_":
            error = "delegate function {!r} needs to be named '_'".format(func.__name__)
            raise NameError(error)
        cast(Attribute, attribute).deleter(func)

    return decorator


def resolve_index(length, index, clamp=False):
    # type: (int, int, bool) -> int
    """
    Resolve index to a positive number.

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
    Resolve continuous slice according to length.

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
    # type: (int, slice | int, int) -> tuple[int, int, int, int] | None
    """
    Perform checks before moving values internally.

    :param length: Length of the list.
    :param item: Index/slice.
    :param target_index: Target index.
    :return: None or (index, stop, target index, post index).
    """

    # Resolve slice/index.
    if isinstance(item, slice):
        index, stop = resolve_continuous_slice(length, item)
        if index == stop:
            return None
    else:
        index = resolve_index(length, item)
        stop = index + 1

    # Calculate target index and post index.
    target_index = resolve_index(length, target_index, clamp=True)
    if index <= target_index <= stop:
        return None
    elif target_index > stop:
        post_index = target_index - (stop - index)
    else:
        post_index = target_index

    return index, stop, target_index, post_index


# TODO: make_base
# TODO: make_class
# TODO: make_dict, make_list, make_set
# TODO: is_class
