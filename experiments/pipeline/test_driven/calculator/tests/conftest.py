import os
import pytest

@pytest.fixture(scope="session", autouse=True)
def setup_display():
    """Set up a virtual display for tkinter tests using Xvfb."""
    # Start Xvfb in the background
    os.environ['DISPLAY'] = ':99'
    os.system('Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &')
    yield
    # Cleanup is optional - Xvfb will be killed when process ends
