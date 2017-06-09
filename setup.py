import os
import re
from setuptools import setup

# Allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

def read(fname):
    """
    Read text file. Return content.
    """
    try:
        return open(os.path.join(os.path.dirname(__file__), fname)).read()
    except IOError:
        return


def requires(fname):
    """
    Read requirements file. Return list.
    """
    dirname = os.path.dirname(os.path.abspath(fname))
    filename = os.path.basename(fname)
    lines = None
    requirements = []
    try:
        with open(os.path.join(dirname, filename)) as f:
            lines = f.read().splitlines()
    except IOError:
        return []

    for line in lines:
        if line.startswith('-r'):
            included_file = re.search("^-r (.*)$", line).group(1)
            # Call self recursively to follow includes--i.e. "-r file.txt"
            lines += requires(os.path.join(dirname, included_file))
        elif line.startswith('#'):
            pass
        else:
            requirements.append(line)
    return requirements


def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join(package, '__init__.py')).read()
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)


def get_packages(directories, exclude=None):
    """
    Return root packages and all sub-packages except those packages contained
    in optional exclude list.
    """
    packages = []
    exclude = exclude if exclude else []
    for directory in directories:
        packages += [re.sub('/', '.', dirpath)
            for dirpath, dirnames, filenames in os.walk(directory)
            if (os.path.exists(os.path.join(dirpath, '__init__.py')) and
                dirpath.split('/').pop() not in exclude)]
    return packages


def get_package_data(directories):
    """
    Return all files under the root packages that are not in a package
    themselves.
    """
    package_data = {}
    for directory in directories:
        walk = [(dirpath.replace(directory + os.sep, '', 1), filenames)
            for dirpath, dirnames, filenames in os.walk(directory)
            if not os.path.exists(os.path.join(dirpath, '__init__.py'))]
        filepaths = []
        for base, filenames in walk:
            filepaths.extend([os.path.join(base, filename)
                              for filename in filenames])
        package_data[directory] = filepaths
    return package_data


#version = get_version('pdf_form_filler')
install_requires = 'requirements/install.txt'
tests_require = 'requirements/test.txt'
if os.getenv('PDF_FORM_FILLER_DEV', None):
    install_requires = 'requirements/test.txt'

install_requires_list = requires(install_requires)
tests_require_list = requires(tests_require)

package_directories = []

setup(
    name='pdf_form_filler',
    version='1',
    url='http://www.eigenholser.com',
    license='MIT',
    description='PDF Form Filler',
    long_description=read('README.rst'),
    author='@eigenholser',
    author_email='eigenholser@noreply.github.com',
    packages=get_packages(package_directories, exclude=["tests"]),
    package_data=get_package_data(package_directories),
    entry_points={
        'console_scripts': [
            'filler = filler:main',
        ]
    },
    install_requires=install_requires_list,
    setup_requires=['pytest-runner'],
    tests_require=tests_require_list,
    zip_safe=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: CLI',
        'Intended Audience :: People',
        'License :: MIT',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Other/Nonlisted Topic',
    ]
)

