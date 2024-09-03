from setuptools import setup, find_packages


setup(
    author="Luke Campagnola",
    author_email="lukec@alleninstitute.org",
    description="Modern, pythonic API for NEURON.",
    install_requires=["numpy", "neuron"],
    license="MIT",
    name="pynrn",
    packages=find_packages(),
    url="https://github.com/campagnola/pynrn",
    version="1.0",
)
