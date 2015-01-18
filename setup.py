# -*- coding: utf-8 -*-
import codecs
from os import path

from setuptools import setup

with open('README.rst', 'rt') as f:
    long_description = f.read()

setup(
    name='saltobserver',
    version='0.9.3',
    description='A simple webapp for presenting data as offered by SaltStack\'s Redis Returner',
    long_description=long_description,
    url='https://github.com/analogbyte/saltobserver',
    author='Daniel Nägele',
    author_email='saltobserver@danieln.de',
    license='MIT',
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Framework :: Flask',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],
    keywords='saltstack redis returner salt states',
    packages=['saltobserver'],
    package_data={
        'saltobserver': [
            'templates/*.html',
            'static/style.css',
        ]
    },
    install_requires=['flask', 'flask_sockets', 'gunicorn', 'redis', 'gevent', 'gevent-websocket'],
    scripts=['scripts/run_saltobserver'],
)
