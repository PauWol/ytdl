from setuptools import setup, find_packages

setup(
    name="ytdl",
    version="1.0.0",
    description="CLI YouTube song & playlist downloader with metadata and thumbnail embedding",
    author="Your Name",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "yt-dlp>=2024.1.0",
        "click>=8.1.7",
        "rich>=13.7.0",
        "mutagen>=1.47.0",
        "requests>=2.31.0",
    ],
    entry_points={
        "console_scripts": [
            "ytdl=ytdl.cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
