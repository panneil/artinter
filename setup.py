from setuptools import setup, find_packages

setup(
    name="siliji_app",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pytesseract",
        "pyttsx3",
        "SpeechRecognition",
    ],
    entry_points={
        'console_scripts': [
            'siliji=siliji_app.main:main',
        ],
    },
) 