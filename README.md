# leatherbound_kernel
Python and LaTeX tools to create the PDFs for a leatherbound book of the Linux kernel source code.

## Details
`make_chapter.py` and `make_book.py` will create a temporary working directory, and then use Jinja2 to render `.tex` files from the templates in the `templates/` directory. 

`pdflatex` is then called from within the script to generate the pdf, which is copied back to the original working directory.

## Options and Usage
    $ ./make_book.py
    Make a pdf for a kernel directory
    
    Usage:
      make_book.py [--color] [--volumes num] [--keep_tex] -t title -r release_date -c contents_directory DIRECTORY
    
    Options:
      -h --help          Show this help screen
      --color            Turn on color pdf output
      --volumes num      Split into 'num' pdfs (default: 1)
      --keep_tex         Preserve the tex file(s)
      -t title           Title for the book
      -r release         String of the release date
      -c contents        String for the table of contents

### Examples
To create a single chapter of a .c file:
`./make_chapter.py --color linux-2.6.0/kernel/fork.c`

If the the .c file falls into a different child directory, use:
`./make_chapter.py --color -p linux-2.6.0/kernel linux-2.6.0/kernel/power/poweroff.c`

To make a book of the entire directory, you'll have to also specify a title (-t), a release date (-r), and the directory for the table of contents (-c):
`./make_book.py -t 'Linux 2.6.0' -r 'Released December 17, 2003' -c 'linux-2.6.0/kernel/' linux-2.6.0/kernel/`

## Install Instructions
* Copy the master branch from GitHub

* Download Linux source to $projectroot/linux-\*.\*.\*/

* Setup a virtual environment in $projectroot/venv/

* Use `make_chapter.py` and `make_book.py` to create PDFs.

## Dependencies
### OS Dependencies
* texlive (`pdflatex` command)
* pyton 3.4+

### Python Dependencies
* docopt (pip install docopt)
* Jinja2 (pip install Jinja2)

### LaTeX Dependencies
This project makes use of the following LaTeX packages:
* listings
* fancyhdr
* paratype

Of these, the paratype package is likely the most difficult to obtain. 

OpenSUSE and Fedora provide a `texlive-paratype` package in their repos, but [CTAN](http://www.ctan.org/tex-archive/fonts/paratype) also provides a similar package. The CTAN package can be installed by downloading all the files to /usr/share/texmf/tex/latex/paratype/ , or to the proper location for your operating system.

If the TeX paratype package is too difficult to obtain, a different font could be used by changing the LaTeX templates under $projectroot/templates/

## Where to get Linux source code
The Linux public archive: https://www.kernel.org/pub/linux/kernel/

