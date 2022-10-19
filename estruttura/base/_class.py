import six

from tippo import Any, TypeVar, Iterator, Iterable, SupportsKeysAndGetItem, Tuple, overload
from basicco.explicit_hash import set_to_none
from basicco.abstract_class import abstract
from basicco.runtime_final import final

from ..constants import DELETED
from ._base import BaseMeta, BaseCollection, BaseImmutableMeta, BaseImmutable, BaseMutableMeta, BaseMutable


class BaseClassMeta(BaseMeta):
    pass


# noinspection PyAbstractClass
class BaseClass(six.with_metaclass(BaseClassMeta, BaseCollection[Tuple[str, Any]])):
    __slots__ = ()

    def __bool__(self):
        # type: () -> bool
        """
        Cast as True by default.

        :return: True.
        """
        return True

    @abstract
    def __getitem__(self, name):
        # type: (str) -> Any
        """
        Get value for attribute.

        :param name: Attribute name.
        :return: Attribute value.
        :raises KeyError: Attribute does not exist or has no value.
        """
        raise NotImplementedError()

    @abstract
    def __contains__(self, name):
        # type: (object) -> bool
        """
        Get whether there's a value for attribute.

        :param name: Attribute name.
        :return: True if has value.
        """
        raise NotImplementedError()

    @abstract
    def __iter__(self):
        # type: () -> Iterator[tuple[str, Any]]
        """
        Iterate over attribute items (name, value).

        :return: Attribute item iterator.
        """
        raise NotImplementedError()

    @abstract
    def __len__(self):
        # type: () -> int
        """
        Get count of attributes with values.

        :return: Number of attributes with values.
        """
        raise NotImplementedError()

    @final
    def _discard(self, name):
        # type: (BC, str) -> BC
        """
        Discard attribute value if it's set.

        :param name: Attribute name.
        :return: Transformed.
        """
        try:
            return self._delete(name)
        except KeyError:
            return self

    @final
    def _delete(self, name):
        # type: (BC, str) -> BC
        """
        Delete existing attribute value.

        :param name: Attribute name.
        :return: Transformed.
        :raises KeyError: Key is not present.
        """
        return self._update({name: DELETED})

    @final
    def _set(self, name, value):
        # type: (BC, str, Any) -> BC
        """
        Set value for attribute.

        :param name: Attribute name.
        :param value: Value.
        :return: Transformed.
        """
        return self._update({name: value})

    @overload
    def _update(self, __m, **kwargs):
        # type: (BC, SupportsKeysAndGetItem[str, Any], **Any) -> BC
        pass

    @overload
    def _update(self, __m, **kwargs):
        # type: (BC, Iterable[tuple[str, Any]], **Any) -> BC
        pass

    @overload
    def _update(self, **kwargs):
        # type: (BC, **Any) -> BC
        pass

    @abstract
    def _update(self, *args, **kwargs):
        """
        Update attribute values.

        Same parameters as :meth:`dict.update`.
        :return: Transformed.
        """
        raise NotImplementedError()


BC = TypeVar("BC", bound=BaseClass)  # base class self type


class BaseImmutableClassMeta(BaseClassMeta, BaseImmutableMeta):
    pass


# noinspection PyAbstractClass
class BaseImmutableClass(six.with_metaclass(BaseImmutableClassMeta, BaseClass, BaseImmutable)):
    __slots__ = ()

    @final
    def discard(self, name):
        # type: (BIC, str) -> BIC
        """
        Discard attribute value if it's set.

        :param name: Attribute name.
        :return: Transformed.
        """
        return self._discard(name)

    @final
    def delete(self, name):
        # type: (BIC, str) -> BIC
        """
        Delete existing attribute value.

        :param name: Attribute name.
        :return: Transformed.
        :raises KeyError: Key is not present.
        """
        return self._delete(name)

    @final
    def set(self, name, value):
        # type: (BIC, str, Any) -> BIC
        """
        Set value for attribute.

        :param name: Attribute name.
        :param value: Value.
        :return: Transformed.
        """
        return self._set(name, value)

    @overload
    def update(self, __m, **kwargs):
        # type: (BIC, SupportsKeysAndGetItem[str, Any], **Any) -> BIC
        pass

    @overload
    def update(self, __m, **kwargs):
        # type: (BIC, Iterable[tuple[str, Any]], **Any) -> BIC
        pass

    @overload
    def update(self, **kwargs):
        # type: (BIC, **Any) -> BIC
        pass

    @final
    def update(self, *args, **kwargs):
        """
        Update attribute values.

        Same parameters as :meth:`dict.update`.
        :return: Transformed.
        """
        return self._update(*args, **kwargs)


BIC = TypeVar("BIC", bound=BaseImmutableClass)  # base immutable class self type


class BaseMutableClassMeta(BaseClassMeta, BaseMutableMeta):
    pass


# noinspection PyAbstractClass
class BaseMutableClass(six.with_metaclass(BaseMutableClassMeta, BaseClass, BaseMutable)):
    __slots__ = ()

    @set_to_none
    def __hash__(self):
        error = "{!r} object is not hashable".format(type(self).__name__)
        raise TypeError(error)

    @final
    def __setitem__(self, name, value):
        # type: (str, Any) -> None
        """
        Set attribute value.

        :param name: Attribute name.
        :param value: Attribute value.
        """
        self._update({name: value})

    @final
    def __delitem__(self, name):
        # type: (str) -> None
        """
        Delete attribute value.

        :param name: Attribute name.
        """
        self._update({name: DELETED})

    @final
    def discard(self, name):
        # type: (str) -> None
        """
        Discard attribute value if it's set.

        :param name: Attribute name.
        :return: Transformed.
        """
        self._discard(name)

    @final
    def delete(self, name):
        # type: (str) -> None
        """
        Delete existing attribute value.

        :param name: Attribute name.
        :return: Transformed.
        :raises KeyError: Key is not present.
        """
        self._delete(name)

    @final
    def set(self, name, value):
        # type: (str, Any) -> None
        """
        Set value for attribute.

        :param name: Attribute name.
        :param value: Value.
        :return: Transformed.
        """
        self._set(name, value)

    @overload
    def update(self, __m, **kwargs):
        # type: (SupportsKeysAndGetItem[str, Any], **Any) -> None
        pass

    @overload
    def update(self, __m, **kwargs):
        # type: (Iterable[tuple[str, Any]], **Any) -> None
        pass

    @overload
    def update(self, **kwargs):
        # type: (**Any) -> None
        pass

    @final
    def update(self, *args, **kwargs):
        """
        Update attribute values.

        Same parameters as :meth:`dict.update`.
        :return: Transformed.
        """
        self._update(*args, **kwargs)
