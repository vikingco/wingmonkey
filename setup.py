from setuptools import setup, find_packages
from os import path
from pip.req import parse_requirements
from pip.download import PipSession

# Lists of requirements and dependency links which are needed during runtime, testing and setup
install_requires = []
tests_require = []
dependency_links = []

# Inject requirements from requirements.txt into setup.py
requirements_file = parse_requirements(path.join('requirements', 'requirements.txt'), session=PipSession())
for req in requirements_file:
    install_requires.append(str(req.req))
    if req.link:
        dependency_links.append(str(req.link))

setup(
    name='wingmonkey',
    version='0.1.0-beta',
    packages=find_packages('.'),
    include_package_data=True,
    install_requires=install_requires,
    url='https://github.com/vikingco/wingmonkey',
    license='MIT',
    author='Jonas Steur',
    author_email='jonas.steur@unleashed.be',
    description='mailchimp api v3 client',
    dependency_links=dependency_links,
    classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Operating System :: OS Independent',
        'Environment :: Web Environment',
    ],
)
