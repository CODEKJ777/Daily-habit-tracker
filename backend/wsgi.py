#!/usr/bin/env python3
"""
WSGI entrypoint for production servers. Exposes `application`.
"""
import os
from app import create_app

application = create_app(os.getenv("FLASK_ENV"))
