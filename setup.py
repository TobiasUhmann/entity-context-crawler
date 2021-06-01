from distutils.core import setup

setup(
    entry_points={
        'console_scripts': [
            'ecc = entity_context_crawler.__main__:main'
        ]
    },
    install_requires=[
        'lxml',
        'spacy',
        'wikitextparser'
    ],
    name='entity-context-crawler',
    packages=[
        'entity_context_crawler',
        'entity_context_crawler.cmd',
        'entity_context_crawler.dao',
        'entity_context_crawler.util',
    ],
    version='2.0.0'
)
