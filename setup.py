from setuptools import setup

with open('README.rst', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='fac-cli',

    version=__import__('fac').__version__,

    description='Command-line mod manager for Factorio (install, update...).',
    long_description=long_description,

    url='https://github.com/mickael9/fac',

    author='Mickaël Thomas',
    author_email='mickael9@gmail.com',

    license='MIT',

    classifiers=[
        'Development Status :: 3 - Alpha',

        'Environment :: Console',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.5',
        'Topic :: Games/Entertainment',
    ],

    keywords='factorio mod manager updater installer',

    packages=['fac', 'fac.commands'],

    data_files=[('share/zsh/site-functions', ['zsh/_fac'])],

    install_requires=['requests', 'appdirs', 'packaging'],

    entry_points={
        'console_scripts': [
            'fac=fac.main:main',
        ],
    },
)
