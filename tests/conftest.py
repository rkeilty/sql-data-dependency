def pytest_addoption(parser):
    parser.addoption("--runlivedb", action="store_true", help="run live tests")
