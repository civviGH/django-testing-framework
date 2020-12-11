import os, sys

try:
    from .local import *
except ImportError:
    from .development import *