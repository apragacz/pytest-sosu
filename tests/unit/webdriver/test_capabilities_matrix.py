from pytest_sosu.webdriver import Browser, Capabilities, CapabilitiesMatrix, Platform


def test_iter_capabilities():
    linux = Platform("Linux")
    win_10 = Platform("Windows", 10)
    chrome_97 = Browser("chrome", 97)
    ff_96 = Browser("firefox", 96)
    caps_matrix = CapabilitiesMatrix(
        platforms=[linux, win_10],
        browsers=[chrome_97, ff_96],
    )
    assert set(caps_matrix.iter_capabilities()) == {
        Capabilities(platform=linux, browser=chrome_97),
        Capabilities(platform=linux, browser=ff_96),
        Capabilities(platform=win_10, browser=chrome_97),
        Capabilities(platform=win_10, browser=ff_96),
    }
