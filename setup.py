from setuptools import setup, find_packages
from os import path
from pip._internal.req.req_file import parse_requirements
from pip._internal.download import PipSession

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

# Inject test requirements from requirements_test.txt into setup.py
requirements_test_file = parse_requirements(path.join('requirements', 'requirements_test.txt'), session=PipSession())
for req in requirements_test_file:
    tests_require.append(str(req.req))
    if req.link:
        dependency_links.append(str(req.link))


setup(
    name='wingmonkey',
    version='0.1.18',
    url='https://github.com/vikingco/wingmonkey',
    license='BSD',
    author='Jonas Steur',
    author_email='jonas.steur@unleashed.be',
    description='mailchimp api v3 client',
    long_description=open('README.md', 'r').read(),
    packages=find_packages('.'),
    include_package_data=True,
    install_requires=install_requires,
    tests_require=tests_require,
    dependency_links=dependency_links,
    classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Operating System :: OS Independent',
        'Environment :: Web Environment',
    ],
)
