import os
from collections import OrderedDict
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), "requirements.txt")) as f:
    dependencies = f.read().strip().split("\n")

setup(
    name="BIKprotect",
    version="0.13.3",
    description="BIKprotect, a GPT-empowered penetration testing tool",
    long_description="""
    BIKprotect is a penetration testing tool empowered by ChatGPT.
    It is designed to automate the penetration testing process. It
    is prototyped initially on top of ChatGPT and operate in an
    interactive mode to guide penetration testers in both overall
    progress and specific operations.
    """,
    author="Gelei Deng",
    author_email="gelei.deng@ntu.edu.sg",
    maintainer="Gelei Deng",
    maintainer_email="gelei.deng@ntu.edu.sg",
    url="https://github.com/GreyDGL/BIKprotect",
    project_urls=OrderedDict(
        (
            ("Code", "https://github.com/GreyDGL/BIKprotect"),
            ("Issue tracker", "https://github.com/GreyDGL/BIKprotect/issues"),
        )
    ),
    license="MIT License",
    packages=["BIKprotect"] + find_packages(),
    # packages=find_packages(),
    # scripts=['BIKprotect/main.py'],
    install_requires=dependencies,
    entry_points={
        "console_scripts": [
            "BIKprotect=BIKprotect.main:main",
            "BIKprotect-cookie=BIKprotect.extract_cookie:main",
            "BIKprotect-connection=BIKprotect.test_connection:main",
        ]
    },
)
