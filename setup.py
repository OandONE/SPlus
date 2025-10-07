from setuptools import setup, find_packages

setup(
    name="PySPlus",
    version="0.5",
    author="seyyed mohamad hosein moosavi raja(01)",
    author_email="mohamadhosein159159@gmail.com",
    description="the library SPlus platform for bots.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/OandONE/SPlus",
    packages=find_packages(),
    python_requires='>=3.8',
    install_requires=["selenium==4.29.0","webdriver_manager==4.0.2","bs4==0.0.2"],
    license="MIT"
)
