from setuptools import setup, find_packages

setup(
    name="claude2agy",
    version="1.2.0",
    description="Bi-directional converter between Claude Code (.jsonl) and Antigravity CLI (agy) sessions",
    author="Antigravity Pair Programmer",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "claude2agy=claude2agy.cli:main",
            "agy2claude=claude2agy.cli:main",
        ],
    },
    python_requires=">=3.8",
)
