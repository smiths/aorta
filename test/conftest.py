

def pytest_addoption(parser):
    """Add argument parser to pytest, we can pass parameters to pytest.
    """
    parser.addoption("--testCase", action="store", default=0)
    parser.addoption("--limit", action="store", default=0.05)
    parser.addoption("--qualifiedCoef", action="store", default=2.2)
    parser.addoption("--ffactor", action="store", default=3.5)


def pytest_generate_tests(metafunc):
    """Convert parser arguments to parameters
    """
    option_value = float(metafunc.config.option.limit)
    if 'limit' in metafunc.fixturenames and option_value is not None:
        metafunc.parametrize("limit", [option_value])

    option_value = float(metafunc.config.option.qualifiedCoef)
    if 'qualifiedCoef' in metafunc.fixturenames and option_value is not None:
        metafunc.parametrize("qualifiedCoef", [option_value])

    option_value = float(metafunc.config.option.ffactor)
    if 'ffactor' in metafunc.fixturenames and option_value is not None:
        metafunc.parametrize("ffactor", [option_value])

    option_value = int(metafunc.config.option.testCase)
    if 'testCase' in metafunc.fixturenames and option_value is not None:
        metafunc.parametrize("testCase", [option_value])
