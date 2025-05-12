from setuptools import setup, find_packages
import os

setup(
    name="nl2sql",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        # Core dependencies
        "pandas>=1.3.0",
        "matplotlib>=3.5.0",
        "numpy>=1.20.0",
        "openai>=1.0.0",
        "cryptography>=36.0.0",
        "sqlalchemy>=1.4.0",
        "pymysql>=1.0.0",
        "mysql-connector-python>=8.0.0",
        
        # Visualization dependencies
        "seaborn>=0.11.0",
        "scipy>=1.7.0",
        
        # Testing and utilities
        "colorama>=0.4.4",
    ],
    # tkinter is part of the standard library, not an external dependency
    entry_points={
        'console_scripts': [
            'nl2sql=nl2sql-app:main',
        ],
    },
    author="Phee Teik Wei",
    author_email="your.email@example.com",
    description="Natural Language to SQL Query System",
    keywords="nlp, sql, database, ai, visualization, business intelligence",
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Business/Finance",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Database :: Front-Ends",
        "Topic :: Scientific/Engineering :: Visualization",
    ],
    include_package_data=True,
    package_data={
        'nl2sql': ['*.png', '*.ico', '*.md'],
    },
    long_description=open('README.md').read() if os.path.exists('README.md') else 'Natural Language to SQL Query System with AI-driven Visualizations',
    long_description_content_type="text/markdown",
)
