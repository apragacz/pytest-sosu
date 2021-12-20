from pytest_sosu.webdriver import Capabilities


def test_to_dict():
    caps = Capabilities()
    caps_data = caps.to_dict()
    assert "browserName" in caps_data
    assert "browserVersion" in caps_data
    assert "sauce:options" in caps_data

    legacy_caps_data = caps.to_dict(w3c=False)
    assert "browserName" in legacy_caps_data
    assert "version" in legacy_caps_data
    assert "sauce:options" not in legacy_caps_data
