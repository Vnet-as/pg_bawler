# -*- coding: utf-8 -*-
import setuptools

setuptools.setup(
    name='pg_bawler',
    version='0.1.0',
    author='Michal Kuffa',
    author_email='michal.kuffa@gmail.com',
    description='Notify/listen python helpers for postgresql.',
    long_description=open('README.rst').read(),
    packages=setuptools.find_packages(),
    install_requires=[],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
)
