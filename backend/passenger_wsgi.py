import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from main import app
from a2wsgi import ASGIMiddleware

application = ASGIMiddleware(app)
