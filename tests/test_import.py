import pytest


def test_import():
    import estruttura

    for member_name in estruttura.__all__:
        getattr(estruttura, member_name)

    import datta

    for member_name in datta.__all__:
        getattr(datta, member_name)


if __name__ == "__main__":
    pytest.main()
