from setuptools import setup

setup(name='clusto-sgext',
      version='0.1',
      packages=['sgext'],
      install_requires=[
        'clusto',
        'IPy',
        'boto',
        'kombu',
        'eventlet',
        'PyYAML',
      ], scripts=[
        'sgext/scripts/clusto-barker-consumer',
        'sgext/scripts/clusto-puppet-node2',
        'sgext/scripts/clusto-ec2-report',
      ])
