# leatherbound_kernel
Python and LaTeX tools to create the PDFs for a leatherbound book of the Linux kernel source code.

## -- Where to get Linux source code --
The Linux public archive: https://www.kernel.org/pub/linux/kernel/

##-- Project setup details --
This is how I have my development environment setup.

* Copy the master branch from GitHub

* Download the Linux source to $projectroot/linux-\*.\*.\*/

* Setup a virtual environment in $projectroot/venv/

* Use `make_chapter.py` and `make_book.py` to create PDFs.

## -- Dependencies --
### Python Dependencies
I have these in a python virtualenvionment:
* python3
* docopt (pip install docopt)
* Jinja2 (pip install Jinja2)

### LaTeX Dependencies
This project makes use of the following LaTeX packages:
* listings
* fancyhdr
* paratype

Of these, the paratype package is likely the most difficult to obtain. 

OpenSUSE provides a package (`zypper install texlive-paratype`), but [CTAN](http://www.ctan.org/tex-archive/fonts/paratype/tex) also provides a similar package. The CTAN package can be installed by downloading all the files to /usr/share/texmf/tex/latex/paratype/ , or to the proper location for your operating system.


If the TeX paratype package is too difficult to obtain, a different font could be used by changing the LaTeX templates under $projectroot/templates/

## -- Examples --
I've done most of my development with Linux 2.6.0, since the linux-2.6.0/kernel directory is still small enough to fit within a single book.

To create a single chapter of a .c file:
`./make_chapter.py --color linux-2.6.0/kernel/fork.c`

If the the .c file falls into a different child directory, use:
`./make_chapter.py --color -p linux-2.6.0/kernel linux-2.6.0/kernel/power/poweroff.c`

To make a book of the entire directory, you'll have to also specify a title (-t), a release date (-r), and the directory for the table of contents (-c):
`./make_book.py -t 'Linux 2.6.0' -r 'Released December 17, 2003' -c 'linux-2.6.0/kernel/' linux-2.6.0/kernel/`


## -- Details --
`make_chapter.py` and `make_book.py` will create a temporary working directory, and then use Jinja2 to render `.tex` files from the templates in the `templates/` directory. 

`pdflatex` is then called from within the script to generate the pdf, which is copied back to the original working directory.

