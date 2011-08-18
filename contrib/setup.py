from setuptools import setup

setup(name='clusto-sgext',
      version='0.1',
      packages=['sgext'],
      install_requires=[
        'clusto',
        'IPy',
        'boto',
      ])
