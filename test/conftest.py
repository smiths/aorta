

def pytest_addoption(parser):
    """Add argument parser to pytest. We can pass parameters to pytest.
    """
    parser.addoption("--testCase", action="store", default="001-43681283")
    parser.addoption("--limit", action="store", default=0.05)


def pytest_generate_tests(metafunc):
    """Convert parser arguments to parameters
    """
    option_value = float(metafunc.config.option.limit)
    if 'limit' in metafunc.fixturenames and option_value is not None:
        metafunc.parametrize("limit", [option_value])

    option_value = metafunc.config.option.testCase
    if 'testCase' in metafunc.fixturenames and option_value is not None:
        metafunc.parametrize("testCase", [option_value])
