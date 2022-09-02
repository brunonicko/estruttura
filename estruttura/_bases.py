_SERIALIZED_CLASS_KEY = "__class__"
_ESCAPED_SERIALIZED_CLASS_KEY = "\\__class__"
_SERIALIZED_VALUE_KEY = "__state__"


T = TypeVar("T")  # Any type.


def _escape_serialized_class(dct):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Escape serialized '__class__' key.

    :param dct: Serialized dictionary.
    :return: Escaped serialized dictionary.
    """
    if _SERIALIZED_CLASS_KEY in dct:
        dct = dct.copy()
        dct[_ESCAPED_SERIALIZED_CLASS_KEY] = dct.pop(_SERIALIZED_CLASS_KEY)
    return dct


def _unescape_serialized_class(dct):
    # type: (Dict[str, Any]) -> Dict[str, Any]
    """
    Unescape serialized '__class__' key.

    :param dct: Serialized dictionary.
    :return: Unescaped serialized dictionary.
    """
    if _ESCAPED_SERIALIZED_CLASS_KEY in dct:
        dct = dct.copy()
        dct[_SERIALIZED_CLASS_KEY] = dct.pop(_ESCAPED_SERIALIZED_CLASS_KEY)
    return dct


class BaseStructureMeta(BaseMeta):
    """
    Metaclass for :class:`objetto.bases.BaseStructure`.

    Inherits from:
      - :class:`objetto.bases.BaseMeta`

    Inherited by:
      - :class:`objetto.bases.BaseAuxiliaryStructureMeta`
      - :class:`objetto.bases.BaseAttributeStructureMeta`
      - :class:`objetto.bases.BaseDataMeta`
      - :class:`objetto.bases.BaseObjectMeta`

    Features:
      - Support for `unique descriptors <objetto.objects.unique_descriptor>`_.
      - Defines serializable structure type.
    """

    __unique_descriptor_name = WeakKeyDictionary(
        {}
    )  # type: MutableMapping[BaseStructureMeta, Optional[str]]
    __unique_descriptor = WeakKeyDictionary(
        {}
    )  # type: MutableMapping[BaseStructureMeta, Optional[UniqueDescriptor]]

    def __init__(cls, name, bases, dct):
        # type: (str, Tuple[Type, ...], Dict[str, Any]) -> None
        super(BaseStructureMeta, cls).__init__(name, bases, dct)

        # Find unique descriptors.
        unique_descriptors = {}
        for base in reversed(getmro(cls)):
            base_is_base_structure = isinstance(base, BaseStructureMeta)
            for member_name, member in iteritems(base.__dict__):

                # Found unique descriptor.
                if type(member) is UniqueDescriptor:

                    # Valid declaration.
                    if base_is_base_structure:
                        unique_descriptors[member_name] = member

                    # Invalid.
                    else:
                        error = (
                            "unique descriptor '{}' can't be declared in base '{}', "
                            "which is not a subclass of '{}'"
                        ).format(member_name, base.__name__, BaseStructure.__name__)
                        raise TypeError(error)

                # Was overridden.
                elif member_name in unique_descriptors:
                    del unique_descriptors[member_name]

        # Multiple unique descriptors.
        if len(unique_descriptors) > 1:
            error = "class '{}' has multiple unique descriptors at {}".format(
                cls.__name__, ", ".join("'{}'".format(n) for n in unique_descriptors)
            )
            raise TypeError(error)

        # Store unique descriptor.
        unique_descriptor_name = None  # type: Optional[str]
        unique_descriptor_ = None  # type: Optional[UniqueDescriptor]
        if unique_descriptors:
            unique_descriptor_name, unique_descriptor_ = next(
                iteritems(unique_descriptors)
            )
        type(cls).__unique_descriptor_name[cls] = unique_descriptor_name
        type(cls).__unique_descriptor[cls] = unique_descriptor_

    @property
    @final
    def _unique_descriptor_name(cls):
        # type: () -> Optional[str]
        """
        Unique descriptor name or `None`.

        :rtype: str or None
        """
        return type(cls).__unique_descriptor_name[cls]

    @property
    @final
    def _unique_descriptor(cls):
        # type: () -> Optional[UniqueDescriptor]
        """
        Unique descriptor or `None`.

        :rtype: objetto.objects.UniqueDescriptor or objetto.data.UniqueDescriptor or \
None
        """
        return type(cls).__unique_descriptor[cls]

    @property
    @abstractmethod
    def _serializable_structure_types(cls):
        # type: () -> Tuple[Type[BaseStructure], ...]
        """
        Serializable structure types.

        :rtype: tuple[type[objetto.bases.BaseStructure]]
        """
        raise NotImplementedError()

    @property
    def _relationship_type(cls):
        # type: () -> Type[BaseRelationship]
        """
        Relationship type.

        :rtype: type[objetto.bases.BaseRelationship]
        """
        return BaseRelationship


# noinspection PyTypeChecker
_BS = TypeVar("_BS", bound="BaseStructure")


class BaseStructure(
    with_metaclass(BaseStructureMeta, BaseHashable, BaseProtectedCollection[T])
):
    """
    Base structure.

    Metaclass:
      - :class:`objetto.bases.BaseStructureMeta`

    Inherits from:
      - :class:`objetto.bases.BaseHashable`
      - :class:`objetto.bases.BaseProtectedCollection`

    Inherited By:
      - :class:`objetto.bases.BaseInteractiveStructure`
      - :class:`objetto.bases.BaseMutableStructure`
      - :class:`objetto.bases.BaseAuxiliaryStructure`
      - :class:`objetto.bases.BaseData`
      - :class:`objetto.bases.BaseObject`

    Features:
      - Is hashable.
      - Is a protected collection.
      - Has state.
      - Unique hash based on ID if unique descriptor is defined.
      - Holds values at locations.
      - Has a relationship for each location.
      - Serializes/deserializes values and itself.
    """

    __slots__ = ()

    @final
    def __hash__(self):
        # type: () -> int
        """
        Get hash.

        :return: Hash.
        :rtype: int
        """
        cls = type(self)
        if cls._unique_descriptor:
            return hash(id(self))
        else:
            return self._hash()

    @final
    def __eq__(self, other):
        # type: (Any) -> bool
        """
        Compare with another object for equality/identity.

        :param other: Another object.

        :return: True if equal or the exact same object.
        :rtype: bool
        """
        if self is other:
            return True
        if not isinstance(other, collections_abc.Hashable):
            return self._eq(other)
        cls = type(self)
        if cls._unique_descriptor:
            return False
        elif isinstance(other, BaseStructure) and type(other)._unique_descriptor:
            return False
        else:
            return self._eq(other)

    @staticmethod
    @final
    def __deserialize_value(
        serialized,  # type: Any
        location,  # type: Any
        relationship,  # type: BaseRelationship
        serializable_structure_types,  # type: Tuple[Type[BaseStructure], ...]
        class_name,  # type: str
        override_serialized=MISSING,  # type: Any
        **kwargs  # type: Any
    ):
        # type: (...) -> Any
        """
        Deserialize value for location with built-in serializer.

        :param serialized: Serialized value.
        :param location: Location.
        :param relationship: Relationship.
        :param serializable_structure_types: Serializable structure types.
        :param override_serialized: Override serialized value.
        :param kwargs: Keyword arguments to be passed to the deserializers.
        :return: Deserialized value.
        :raises TypeError: Can't deserialize value due to ambiguous types.
        """

        # Override serialized.
        if override_serialized is not MISSING:
            serialized = override_serialized

        # Possible serialized structure.
        if type(serialized) in (dict, list):

            # Serialized in a dictionary.
            if type(serialized) is dict:

                # Serialized structure with path to its class.
                if _SERIALIZED_CLASS_KEY in serialized:
                    serialized_class = import_path(
                        serialized[_SERIALIZED_CLASS_KEY]
                    )  # type: Type[BaseStructure]
                    serialized_value = serialized[_SERIALIZED_VALUE_KEY]
                    if type(serialized_value) is dict:
                        serialized_value = _unescape_serialized_class(serialized_value)
                    return serialized_class.deserialize(serialized_value, **kwargs)

                # Unescape keys.
                serialized = _unescape_serialized_class(serialized)

            # Single, non-ambiguous structure type.
            single_structure_type = relationship.get_single_exact_type(
                serializable_structure_types
            )  # type: Optional[Type[BaseStructure]]
            if single_structure_type is not None:
                return single_structure_type.deserialize(serialized, **kwargs)

            # Complex type (dict or list).
            single_complex_type = relationship.get_single_exact_type(
                (dict, list)
            )  # type: Optional[Union[Type[Dict], Type[List]]]
            if single_complex_type is None:
                error = (
                    "can't deserialize '{}' object as a value of '{}' since "
                    "relationship{} defines none or ambiguous types"
                ).format(
                    type(serialized).__name__,
                    class_name,
                    " at location {}".format(location) if location is not None else "",
                )
                raise TypeError(error)

        # Return type-check deserialized value.
        return relationship.fabricate_value(serialized, factory=False)

    @staticmethod
    @final
    def __serialize_value(
        value,  # type: Any
        relationship,  # type: BaseRelationship
        serializable_structure_types,  # type: Tuple[Type[BaseStructure], ...]
        override_value=MISSING,  # type: Any
        **kwargs  # type: Any
    ):
        # type: (...) -> Any
        """
        Serialize value for location with built-in serializer.

        :param value: Value.
        :param relationship: Relationship.
        :param serializable_structure_types: Serializable structure types.
        :param override_value: Override value.
        :param kwargs: Keyword arguments to be passed to the serializers.
        :return: Serialized value.
        """

        # Override value.
        if override_value is not MISSING:
            value = override_value

        # Structure type.
        if isinstance(value, serializable_structure_types):
            serialized_value = value.serialize(**kwargs)

            # Escape keys.
            if type(serialized_value) is dict:
                serialized_value = _escape_serialized_class(serialized_value)

            # Ambiguous type, serialize with class path.
            single_structure_type = relationship.get_single_exact_type(
                serializable_structure_types
            )  # type: Optional[Type[BaseStructure]]
            if single_structure_type is None:
                return {
                    _SERIALIZED_CLASS_KEY: get_path(type(value)),
                    _SERIALIZED_VALUE_KEY: serialized_value,
                }

            return serialized_value

        # Escape keys.
        if type(value) is dict:
            value = _escape_serialized_class(value)

        return value

    # @abstractmethod (commented out due to a PyCharm bug)
    def _hash(self):
        # type: () -> int
        """
        **Abstract**

        Get hash.

        :return: Hash.
        :rtype: int

        :raises RuntimeError: Abstract method not implemented by subclasses.
        """
        # raise NotImplementedError
        raise RuntimeError()

    # @abstractmethod (commented out due to a PyCharm bug)
    def _eq(self, other):
        # type: (Any) -> bool
        """
        **Abstract**

        Compare with another object for equality.

        :param other: Another object.

        :return: True if equal.
        :rtype: bool

        :raises RuntimeError: Abstract method not implemented by subclasses.
        """
        # raise NotImplementedError
        raise RuntimeError()

    @classmethod
    @abstractmethod
    def _get_relationship(cls, location):
        # type: (Any) -> BaseRelationship
        """
        Get relationship at location.

        :param location: Location.
        :type location: collections.abc.Hashable

        :return: Relationship.
        :rtype: objetto.bases.BaseRelationship

        :raises KeyError: Invalid location.
        """
        raise NotImplementedError()

    @classmethod
    @final
    def deserialize_value(cls, serialized, location=None, **kwargs):
        # type: (Any, Any, Any) -> Any
        """
        Deserialize value for location.

        :param serialized: Serialized value.

        :param location: Location.
        :type location: collections.abc.Hashable

        :param kwargs: Keyword arguments to be passed to the deserializers.

        :return: Deserialized value.

        :raises objetto.exceptions.SerializationError: Can't deserialize value.
        :raises ValueError: Keyword arguments contain reserved keys.
        """

        # Get relationship.
        relationship = cls._get_relationship(location)
        if not relationship.serialized:
            error = (
                "can't deserialize '{}' object as a value of '{}' since the "
                "relationship{} does not allow for serialization/deserialization"
            ).format(
                type(serialized).__name__,
                cls.__fullname__,
                " at location {}".format(location) if location is not None else "",
            )
            raise SerializationError(error)

        # Built-in deserializer.
        deserializer = lambda override_serialized=MISSING: cls.__deserialize_value(
            serialized,
            location,
            relationship,
            cls._serializable_structure_types,
            cls.__fullname__,
            override_serialized=override_serialized,
            **kwargs
        )
        if relationship.deserializer is None:
            return deserializer()

        # Check kwargs for reserved keys.
        if "super" in kwargs:
            error = "can't pass reserved keyword argument 'super' to deserializers"
            raise ValueError(error)
        if "owner" in kwargs:
            error = "can't pass reserved keyword argument 'owner' to deserializers"
            raise ValueError(error)

        # Custom deserializer.
        kwargs = dict(kwargs)
        kwargs["super"] = deserializer
        kwargs["owner"] = cls
        if type(serialized) is dict:
            serialized = _unescape_serialized_class(serialized)
        value = run_factory(
            relationship.deserializer, args=(serialized,), kwargs=kwargs
        )
        return relationship.fabricate_value(value, factory=False)

    @final
    def serialize_value(self, value, location=None, **kwargs):
        # type: (Any, Any, Any) -> Any
        """
        Serialize value for location.

        :param value: Value.

        :param location: Location.
        :type location: collections.abc.Hashable

        :param kwargs: Keyword arguments to be passed to the serializers.

        :return: Serialized value.

        :raises objetto.exceptions.SerializationError: Can't serialize value.
        :raises ValueError: Keyword arguments contain reserved keys.
        """

        # Get relationship.
        cls = type(self)
        relationship = cls._get_relationship(location)
        if not relationship.serialized:
            error = (
                "can't serialize '{}' value contained in a '{}' object since the "
                "relationship{} does not allow for serialization/deserialization"
            ).format(
                type(value).__name__,
                cls.__fullname__,
                " at location {}".format(location) if location is not None else "",
            )
            raise SerializationError(error)

        # Built-in serializer
        serializer = lambda override_value=MISSING: self.__serialize_value(
            value,
            relationship,
            cls._serializable_structure_types,
            override_value=override_value,
            **kwargs
        )
        if relationship.serializer is None:
            return serializer()

        # Check kwargs for reserved keys.
        if "super" in kwargs:
            error = "can't pass reserved keyword argument 'super' to serializers"
            raise ValueError(error)
        if "owner" in kwargs:
            error = "can't pass reserved keyword argument 'owner' to deserializers"
            raise ValueError(error)
        if "instance" in kwargs:
            error = "can't pass reserved keyword argument 'instance' to deserializers"
            raise ValueError(error)

        # Custom serializer.
        kwargs = dict(kwargs)
        kwargs["super"] = serializer
        kwargs["owner"] = cls
        kwargs["instance"] = self
        serialized_value = run_factory(
            relationship.serializer, args=(value,), kwargs=kwargs
        )
        if type(serialized_value) is dict:
            serialized_value = _escape_serialized_class(serialized_value)
        return serialized_value

    @classmethod
    @abstractmethod
    def deserialize(cls, serialized, **kwargs):
        # type: (Type[_BS], Any, Any) -> _BS
        """
        Deserialize.

        :param serialized: Serialized.

        :param kwargs: Keyword arguments to be passed to the deserializers.

        :return: Deserialized.
        :rtype: objetto.bases.BaseStructure

        :raises objetto.exceptions.SerializationError: Can't deserialize.
        """
        raise NotImplementedError()

    @abstractmethod
    def serialize(self, **kwargs):
        # type: (Any) -> Any
        """
        Serialize.

        :param kwargs: Keyword arguments to be passed to the serializers.

        :return: Serialized.

        :raises objetto.exceptions.SerializationError: Can't serialize.
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def _state(self):
        # type: () -> BaseState
        """
        State.

        :rtype: objetto.bases.BaseState
        """
        raise NotImplementedError()


# noinspection PyAbstractClass
class BaseInteractiveStructure(BaseStructure[T], BaseInteractiveCollection[T]):
    """
    Base interactive structure.

    Inherits from:
      - :class:`objetto.bases.BaseStructure`
      - :class:`objetto.bases.BaseInteractiveCollection`

    Inherited By:
      - :class:`objetto.bases.BaseInteractiveAuxiliaryStructure`
      - :class:`objetto.bases.BaseInteractiveData`

    Features:
      - Is an interactive collection/structure.
    """

    __slots__ = ()


# noinspection PyAbstractClass
class BaseMutableStructure(BaseStructure[T], BaseMutableCollection[T]):
    """
    Base mutable structure.

    Inherits from:
      - :class:`objetto.bases.BaseStructure`
      - :class:`objetto.bases.BaseMutableCollection`

    Inherited By:
      - :class:`objetto.bases.BaseMutableAuxiliaryStructure`
      - :class:`objetto.bases.BaseMutableObject`

    Features:
      - Is a mutable collection/structure.
    """

    __slots__ = ()


class BaseAuxiliaryStructureMeta(BaseStructureMeta):
    """
    Metaclass for :class:`objetto.bases.BaseAuxiliaryStructure`.

    Inherits from:
      - :class:`objetto.bases.BaseStructureMeta`

    Inherited by:
      - :class:`objetto.bases.BaseAuxiliaryDataMeta`
      - :class:`objetto.bases.BaseAuxiliaryObjectMeta`
      - :class:`objetto.bases.BaseDictStructureMeta`
      - :class:`objetto.bases.BaseListStructureMeta`
      - :class:`objetto.bases.BaseSetStructureMeta`

    Features:
      - Defines a base auxiliary type.
      - Enforces correct type for :attr:`objetto.bases.BaseAuxiliaryStructure.\
_relationship`.
    """

    def __init__(cls, name, bases, dct):
        super(BaseAuxiliaryStructureMeta, cls).__init__(name, bases, dct)

        # Check relationship type.
        relationship = getattr(cls, "_relationship")
        relationship_type = cls._relationship_type
        assert_is_instance(relationship, relationship_type, subtypes=False)

    @property
    @abstractmethod
    def _base_auxiliary_type(cls):
        # type: () -> Type[BaseAuxiliaryStructure]
        """
        Base auxiliary structure type.

        :rtype: type[objetto.bases.BaseAuxiliaryStructure]
        """
        raise NotImplementedError()


# noinspection PyAbstractClass
class BaseAuxiliaryStructure(
    with_metaclass(BaseAuxiliaryStructureMeta, BaseStructure[T])
):
    """
    Structure with a single relationship for all locations.

    Inherits from:
      - :class:`objetto.bases.BaseStructure`

    Inherited By:
      - :class:`objetto.bases.BaseInteractiveAuxiliaryStructure`
      - :class:`objetto.bases.BaseMutableAuxiliaryStructure`
      - :class:`objetto.bases.BaseDictStructure`
      - :class:`objetto.bases.BaseListStructure`
      - :class:`objetto.bases.BaseSetStructure`
      - :class:`objetto.bases.BaseAuxiliaryData`
      - :class:`objetto.bases.BaseAuxiliaryObject`
    """

    __slots__ = ()

    _relationship = BaseRelationship()
    """
    **Class Attribute**

    Relationship for all locations.

    :type: objetto.bases.BaseRelationship
    """

    def find_with_attributes(self, **attributes):
        # type: (Any) -> Any
        """
        Find first value that matches unique attribute values.

        :param attributes: Attributes to match.

        :return: Value that has matching attributes.

        :raises ValueError: No attributes provided or no match found.
        """
        return self._state.find_with_attributes(**attributes)

    @classmethod
    @final
    def _get_relationship(cls, location=None):
        # type: (Any) -> BaseRelationship
        """
        Get relationship.

        :param location: Location.
        :type location: collections.abc.Hashable

        :return: Relationship.
        :rtype: objetto.bases.BaseRelationship
        """
        return cast("BaseRelationship", cls._relationship)


# noinspection PyAbstractClass
class BaseInteractiveAuxiliaryStructure(
    BaseAuxiliaryStructure[T],
    BaseInteractiveStructure[T],
):
    """
    Base interactive auxiliary structure.

    Inherits from:
      - :class:`objetto.bases.BaseAuxiliaryStructure`
      - :class:`objetto.bases.BaseInteractiveStructure`

    Inherited By:
      - :class:`objetto.bases.BaseInteractiveAuxiliaryData`
      - :class:`objetto.bases.BaseInteractiveDictStructure`
      - :class:`objetto.bases.BaseInteractiveListStructure`
      - :class:`objetto.bases.BaseInteractiveSetStructure`
    """

    __slots__ = ()


# noinspection PyAbstractClass
class BaseMutableAuxiliaryStructure(
    BaseAuxiliaryStructure[T],
    BaseMutableStructure[T],
):
    """
    Base mutable auxiliary structure.

    Inherits from:
      - :class:`objetto.bases.BaseAuxiliaryStructure`
      - :class:`objetto.bases.BaseMutableStructure`

    Inherited By:
      - :class:`objetto.bases.BaseMutableAuxiliaryObject`
      - :class:`objetto.bases.BaseMutableDictStructure`
      - :class:`objetto.bases.BaseMutableListStructure`
      - :class:`objetto.bases.BaseMutableSetStructure`
    """

    __slots__ = ()