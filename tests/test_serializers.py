from enum import Enum

import pytest

from estruttura._relationship import Relationship
from estruttura.exceptions import SerializationError
from estruttura.serializers import EnumSerializer


class Result(Enum):
    Ok = 1
    Error = 2


def test_enum_serializer():
    rel = Relationship(types=(Result,), serializer=EnumSerializer())
    assert rel.serialize_value(Result.Ok) == 1
    assert rel.serialize_value(Result.Error) == 2
    assert rel.deserialize_value(1) is Result.Ok
    assert rel.deserialize_value(2) is Result.Error

    rel = Relationship(types=(Result,), serializer=EnumSerializer(by_name=True))
    assert rel.serialize_value(Result.Ok) == "Ok"
    assert rel.serialize_value(Result.Error) == "Error"
    assert rel.deserialize_value("Ok") is Result.Ok
    assert rel.deserialize_value("Error") is Result.Error

    with pytest.raises(SerializationError):
        rel.serialize_value("foo")  # type: ignore


if __name__ == "__main__":
    pytest.main()
