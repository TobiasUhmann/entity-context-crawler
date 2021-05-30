from distutils.core import setup

setup(
    name='entity-context-crawler',
    version='0.2.0',
    packages=['src'],
    entry_points={
        'console_scripts': [
            'ecc = src.__main__:main'
        ]
    }
)
