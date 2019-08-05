from re import search
from setuptools import setup, find_packages

with open('gqlask/__init__.py') as f:
    version = search('__version__ = (.*)', f.read()).group(1).strip('"\'')

with open('README.md') as f:
    long_description = f.read()

with open('requirements.txt') as f:
    requirements = []
    for item in f:
        if item:
            requirements.append(item.strip())


setup(
    name='gqlask',
    version=version,
    description='graphql tool',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/lonsdale8734/gqlask',
    author='zhangbao',
    author_email='lonsdale8734@gmail.com',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    keywords='python graphql',
    packages=find_packages(exclude=['tests*']),
    python_requires='>=3.6',
    install_requires=requirements,
)
