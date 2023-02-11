

def pytest_addoption(parser):
    """Add argument parser to pytest, we can pass parameters to pytest.
    """
    parser.addoption("--limit", action="store", default=0.05)
    parser.addoption("--qsf", action="store", default=2.2)
    parser.addoption("--ffactor", action="store", default=3.5)


def pytest_generate_tests(metafunc):
    """Convert parser arguments to parameters
    """
    option_value = float(metafunc.config.option.limit)
    if 'limit' in metafunc.fixturenames and option_value is not None:
        metafunc.parametrize("limit", [option_value])

    option_value = float(metafunc.config.option.qsf)
    if 'qsf' in metafunc.fixturenames and option_value is not None:
        metafunc.parametrize("qsf", [option_value])

    option_value = float(metafunc.config.option.ffactor)
    if 'ffactor' in metafunc.fixturenames and option_value is not None:
        metafunc.parametrize("ffactor", [option_value])
