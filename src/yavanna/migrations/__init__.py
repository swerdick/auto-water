"""Versioned SQL migrations, applied by ``yavanna.migrate``.

Files are named ``NNN_description.up.sql`` / ``NNN_description.down.sql`` and are
loaded as package resources, so they ship inside the container image.
"""
