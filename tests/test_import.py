import pytest


def test_import_bases():
    import estruttura.bases

    for member_name in estruttura.bases.__all__:
        getattr(estruttura.bases, member_name)


if __name__ == "__main__":
    pytest.main()
