from setuptools import setup, find_packages

setup(
    name="popolo-name-resolver",
    version='0.2',
    description='Resolve names to people in Popolo data',
    long_description='',
    author='mySociety',
    author_email='hakim@mysociety.org',
    url='https://github.com/mysociety/popolo-name-resolver',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Django >= 1.8',
        'mysociety-django-popolo >= 0.0.5',
        'django-model-utils == 2.3.1',
        'django-haystack >= 2, < 3',
        'PyYAML',
        'django-nose',
        'psycopg2',
        'elasticsearch == 0.4.5',
    ],
    classifiers=[
        'Framework :: Django',
    ],
)
