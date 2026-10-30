from setuptools import find_packages, setup

setup(
	name="imprest_book",
	version="0.0.1",
	description="Imprest Book — MD-approved disbursement requests for ERPNext",
	author="Bright Godwin",
	author_email="brightgodwin9@gmail.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=[],
)
