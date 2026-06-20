import touzi_agent


def test_package_has_version():
    assert isinstance(touzi_agent.__version__, str)
    assert touzi_agent.__version__ != ""
