import os
from .common import *

if 'DOCKER' in os.environ:
    print("Using Docker settings file")
    from .docker import *
