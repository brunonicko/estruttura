import pytest
from tippo import Iterable, Mapping

from estruttura import Relationship
from estruttura.examples import ImmutableDict, ImmutableList


def json_converter(value):
    """JSON value converter."""
    if isinstance(value, Mapping):
        if not isinstance(value, JSONDict):
            value = JSONDict(value)
    elif isinstance(value, Iterable):
        if not isinstance(value, JSONList):
            value = JSONList(value)
    return value


json_relationship = Relationship(
    types=(str, int, bool, float, None, "JSONDict", "JSONList"),
    converter=json_converter,
    extra_paths=(__name__,),
)


class JSONList(ImmutableList):
    """JSON list."""

    relationship = json_relationship


class JSONDict(ImmutableDict):
    """JSON dictionary."""

    key_relationship = Relationship(types=(str,), extra_paths=(__name__,))
    relationship = json_relationship


def test_json():
    example = {
        "glossary": {
            "__class__": "foo",
            "__state__": "bar",
            "title": "example glossary",
            "version": 1,
            "approx": 2.2,
            "schema": True,
            "something": None,
            "GlossDiv": {
                "title": "S",
                "GlossList": {
                    "GlossEntry": {
                        "ID": "SGML",
                        "SortAs": "SGML",
                        "GlossTerm": "Standard Generalized Markup Language",
                        "Acronym": "SGML",
                        "Abbrev": "ISO 8879:1986",
                        "GlossDef": {
                            "para": "A meta-markup language, used to create markup languages such as DocBook.",
                            "GlossSeeAlso": ["GML", "XML"],
                        },
                        "GlossSee": "markup",
                    }
                },
            },
        },
    }
    data = JSONDict.deserialize(example)
    assert data.serialize() == example
    assert JSONDict(data) == data

    assert isinstance(data["glossary"], JSONDict)
    assert isinstance(data["glossary"]["GlossDiv"]["GlossList"]["GlossEntry"]["GlossDef"]["GlossSeeAlso"], JSONList)


if __name__ == "__main__":
    pytest.main()
