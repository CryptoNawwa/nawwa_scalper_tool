import setuptools

with open('./requirements.txt') as f:
    required = f.read().splitlines()
with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="nawwa_scalper_tool",
    version="0.0.1",
    author="CryptoNawwa",
    description="Crypto scalping tool",
    url = 'https://github.com/CryptoNawwa/nawwa_scalper_tool',
    install_requires=required,
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages()
)