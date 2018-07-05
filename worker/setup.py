from setuptools import setup, find_packages


setup(
    name='zimfarm-worker',
    version='0.1',
    description='Zimfarm worker, a celery node that generate zim files and upload them to zimfarm warehouse.',
    url='https://github.com/openzim/zimfarm',
    author='The Kiwix Organization',
    author_email='chris@kiwix.org',
    license='GPLv3',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.6'
    ],
    keywords=['zimfarm', 'zim', 'celery'],
    packages=find_packages(exclude=['*.pyc']),
    install_requires=[
        'celery>=4.2',
        'docker>=3.4'
    ],
    python_requires='~=3.6',
    entry_points={
        'console_scripts': [
            'zimfarm-worker=zimfarmworker.main:main',
        ],
    },
)