import pytest

from estruttura.examples import ImmutableDict, ImmutableList, relationship

json_relationship = relationship(types=(str, int, bool, float, None, "JSONDict", "JSONList"))


class JSONList(ImmutableList):
    relationship = json_relationship


class JSONDict(ImmutableDict):
    key_relationship = relationship(types=(str,))
    relationship = json_relationship


def test_json():
    example = {
        "glossary": {
            "__class__": "foo",
            "__state__": "bar",
            "title": "example glossary",
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

    assert isinstance(data["glossary"], JSONDict)
    assert isinstance(data["glossary"]["GlossDiv"]["GlossList"]["GlossEntry"]["GlossDef"]["GlossSeeAlso"], JSONList)


if __name__ == "__main__":
    pytest.main()
