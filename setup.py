# Copyright 2026 Lucas Foulkes
# Use of this source code is governed by an MIT-style license that can be found
# in the LICENSE file or at https://opensource.org/licenses/MIT.

from glob import glob
import os

from setuptools import find_packages, setup


package_name = 'robot'


setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
         ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml', 'LICENSE']),
        (os.path.join('share', package_name, 'config'),
         glob('config/*.yaml')),
        (os.path.join('share', package_name, 'launch'),
         glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'urdf'),
         glob('urdf/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Lucas Foulkes',
    maintainer_email='lucasfoulkes@gmail.com',
    description='Model, configuration, and bringup for the Ackermann robot.',
    license='MIT',
    entry_points={
        'console_scripts': [],
    },
)
