import setuptools

with open('README.md', 'r') as rm:
    long_description = rm

setuptools.setup(
    name='mangobocado',
    version='0.0.1',
    author='Leonardo Guercio',
    author_email='lpguercio@gmail.com',
    description='A small model wrapper for motor',
    long_description=long_description,
    url='https://github.com/mountolive/mango'
    packages=setuptools.find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3.7',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
