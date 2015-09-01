from setuptools import setup

setup(name='plcuppaal',
    version='0.1',
    description='Create Uppaal base templates from an xml PLC configuration file.',
    url='https://github.com/bencaldwell/plcuppaal',
    author='Ben Caldwell',
    author_email='benny.caldwell@gmail.com',
    license='GPL-2',
    packages=['plcuppaal'],
    install_requires=['pyuppaal'],
    zip_safe=False)
