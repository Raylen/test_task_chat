__author__ = 'Kael'

from setuptools import setup

requires = [
    'pyramid',
    'webtest',
    'pyramid_jinja2',
    'autobahn'
]

setup(name='tutorial',
      install_requires=requires,
      entry_points="""\
      [paste.app_factory]
      main = tutorial:main
      """,
)