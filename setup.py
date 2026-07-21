from setuptools import setup, find_packages

setup(
    name="claude2agy",
    version="1.0.0",
    description="Tool to convert Claude Code (.jsonl) chat sessions into native Antigravity CLI sessions",
    author="Antigravity Pair Programmer",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "claude2agy=claude2agy.cli:main",
        ],
    },
    python_requires=">=3.8",
)
