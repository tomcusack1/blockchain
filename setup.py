from distutils.core import setup
import setuptools


setup(name='blkchn',
      version='0.0.6',
      author='Tom Cusack-Huang',
      author_email='tom@cusack-huang.com',
      packages=['blkchn'],
      license='MIT',
      url='https://github.com/tomcusack1/blkchn',
      download_url='https://github.com/tomcusack1/blkchn/archive/v0.0.4.tar.gz',
      description='Blockchain data structure',
      install_requires=['flask', 'requests'])
