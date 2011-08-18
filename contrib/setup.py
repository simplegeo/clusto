from setuptools import setup

setup(name='clusto-sgext',
      version='0.1',
      packages=['sgext'],
      install_requires=[
        'clusto',
        'IPy',
        'paramiko',
        'boto',
      ],
      entry_points={
        'console_scripts': [
            'sg-shell = sgext.commands.shell:main',
        ]
      })
