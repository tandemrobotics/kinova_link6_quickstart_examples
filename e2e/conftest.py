def pytest_addoption(parser):
    parser.addoption('--robot-ip', default='192.168.1.10')
    parser.addoption('--robot-username', default='admin')
    parser.addoption('--robot-password', default='admin')
