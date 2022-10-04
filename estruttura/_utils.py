from tippo import Any, Type

from ._class import Attribute, AttributeMap, ClassStructure
from ._relationship import Relationship
from ._structures import UniformStructure, UniformStructureMeta


def relationship(structure):
    # type: (Type[UniformStructure] | UniformStructure) -> Relationship | None
    return structure.__relationship__


def relationship_type(structure):
    # type: (Type[UniformStructure] | UniformStructure) -> Type[Relationship]
    if not isinstance(structure, UniformStructureMeta):
        structure = type(structure)
    return structure.__relationship_type__


def attributes(cls):
    # type: (Type[ClassStructure] | ClassStructure) -> AttributeMap
    return cls.__attributes__


def attribute_type(cls):
    # type: (Type[ClassStructure] | ClassStructure) -> Type[Attribute]
    return cls.__attribute_type__


def to_items(obj):
    # type: (ClassStructure) -> list[tuple[str, Any]]
    return [(n, obj[n]) for n in obj if hasattr(obj, n)]


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
