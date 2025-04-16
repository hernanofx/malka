from setuptools import setup, find_packages

setup(
    name="projectAron",
    version="1.0",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "projectAron": ["*.json", "templates/*", "static/*"],
    },
    data_files=[
        ('projectAron', ['projectAron/credenciales.json']),
    ],
)
