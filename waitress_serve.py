"""
	Script to run that serves the project via WSGI using Waitress. This should be set up to run on boot by a Windows
	scheduled task
"""

from waitress import serve
from Waterspout.wsgi import application
from Waterspout.local_settings import SERVE_ADDRESS

serve(application, listen=SERVE_ADDRESS)  # serve the application! might not respond to termination signals
