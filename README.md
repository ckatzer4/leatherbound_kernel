# leatherbound_kernel
Python and LaTeX tools to create the PDFs for a leatherbound book of the Linux kernel source code.

## -- Where to get source code --
The Linux public archive: https://www.kernel.org/pub/linux/kernel/

##-- Project setup details --
_This is how I have my development environment setup._
Linux source downloaded to $projectroot/linux-\*.\*.\*/

Virtual environment setup in $projectroot/venv/

LaTeX Jinja templates are found in $projectroot/templates/

Python script for finding files and string processing is `make_chapter.py` and `make_book.py`

Output pdfs are created in the current working directory.

Full installation instrucutions still being worked on.

## -- Dependencies --
### Python Dependencies
_I have these in a python virtualenvionment_
* python3
* docopt (pip install docopt)
* Jinja2 (pip install Jinja2)

### LaTeX Dependencies
My font of choice was PT Mono, of the ParaType family.
This project makes use of the following LaTeX packages:
* listings
* fancyhdr
* paratype

Of these, paratype is likely the most difficult to obtain. 
OpenSUSE provides a package (zypper install texlive-paratype), but [CTAN](http://www.ctan.org/tex-archive/fonts/paratype/tex) also provides a similar package. The CTAN package can be installed by downloading all the files to /usr/share/texmf/tex/latex/paratype/ , or to the proper location for your operating system.


If the TeX paratype package is too difficult to obtain, a different font could be used by changing the LaTeX templates under $projectroot/templates/

## -- Process --
Download and unpack the kernel of choice from public archive.
Run the `make_book.py` command to process the unpacked directory:
`./make_book.py --color -t 'Linux 2.6.0' -r 'Released December 17, 2003' -c 'linux-2.6.0/kernel/' linux-2.6.0/kernel/`

The script will locate all files in the target directory and process the file name to create and render .tex files in a temporary directory. PDF output files are copied to the current working directory.
