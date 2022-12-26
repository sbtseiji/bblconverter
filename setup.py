import setuptools

with open("README.md", "r") as fh:
  long_description = fh.read()

setuptools.setup(
  name = "bblconverter",
  version = "0.1.0",
  author="SHIBATA Seiji",
  description = "A tool to convert BibLaTeX bbl files to LaTeX bibitem, markdown, or docx files.",
  long_description=long_description,
  long_description_content_type="text/markdown",
  url="https://github.com/sbtseiji/bblconverter",
  packages=setuptools.find_packages(),
  classifiers = [
      "Programming Language :: Python :: 3",
      "License :: OSI Approved :: MIT License",
      "Operating System :: OS Independent",
  ],
  entry_points = {
    'console_scripts': ['bblconverter = bblconverter.bbl_converter:main']
  },
      python_requires='>=3.7',
)