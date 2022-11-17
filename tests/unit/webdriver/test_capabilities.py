from pytest_sosu.webdriver import Capabilities, SauceOptions


def test_to_dict():
    caps = Capabilities()
    caps_data = caps.to_dict()
    assert set(caps_data) == {"browserName", "browserVersion", "sauce:options"}
    assert set(caps_data["sauce:options"]) == {"seleniumVersion"}

    w3c_caps_data = caps.to_dict(w3c_mode=True)
    assert set(w3c_caps_data) == {"browserName", "browserVersion", "sauce:options"}
    assert set(w3c_caps_data["sauce:options"]) == {"seleniumVersion"}

    legacy_caps_data = caps.to_dict(w3c_mode=False)
    assert set(legacy_caps_data) == {"browserName", "version", "seleniumVersion"}


def test_to_dict_with_auto_include_selenium_version_param_disabled():
    caps = Capabilities()
    caps_data = caps.to_dict(auto_include_selenium_version=False)
    assert set(caps_data) == {"browserName", "browserVersion", "sauce:options"}
    assert set(caps_data["sauce:options"]) == set()

    w3c_caps_data = caps.to_dict(w3c_mode=True, auto_include_selenium_version=False)
    assert set(w3c_caps_data) == {"browserName", "browserVersion", "sauce:options"}
    assert set(w3c_caps_data["sauce:options"]) == set()

    legacy_caps_data = caps.to_dict(w3c_mode=False, auto_include_selenium_version=False)
    assert set(legacy_caps_data) == {"browserName", "version"}


def test_to_dict_with_auto_include_selenium_version_disabled():
    caps = Capabilities(sauce_options=SauceOptions(auto_include_selenium_version=False))
    caps_data = caps.to_dict()
    assert set(caps_data) == {"browserName", "browserVersion", "sauce:options"}
    assert set(caps_data["sauce:options"]) == set()

    w3c_caps_data = caps.to_dict(w3c_mode=True)
    assert set(w3c_caps_data) == {"browserName", "browserVersion", "sauce:options"}
    assert set(w3c_caps_data["sauce:options"]) == set()

    legacy_caps_data = caps.to_dict(w3c_mode=False)
    assert set(legacy_caps_data) == {"browserName", "version"}


def test_to_dict_with_w3c_mode_off_and_auto_include_selenium_version_disabled():
    caps = Capabilities(
        sauce_options=SauceOptions(auto_include_selenium_version=False), w3c_mode=False
    )
    caps_data = caps.to_dict()
    assert set(caps_data) == {"browserName", "version"}

    w3c_caps_data = caps.to_dict(w3c_mode=True)
    assert set(w3c_caps_data) == {"browserName", "browserVersion", "sauce:options"}
    assert set(w3c_caps_data["sauce:options"]) == set()

    legacy_caps_data = caps.to_dict(w3c_mode=False)
    assert set(legacy_caps_data) == {"browserName", "version"}
