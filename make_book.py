#!/usr/bin/env python3
"""Make a pdf for a kernel directory

Usage:
  make_book.py [--color] -t title -r release -c contents DIRECTORY

Options:
  -h --help     Show this help screen
  --color       Turn on color pdf output
  -t title      Title for the book
  -r release    String of the release date
  -c contents   String for the table of contents

"""

import contextlib
import os
import sys
import shutil
import tempfile
import subprocess

from docopt import docopt
from jinja2 import Environment, FileSystemLoader

# Define a temporary directory context manager
# taken from: http://stackoverflow.com/a/33288373
# the first is a general changing directory context
# the second expands that to create and cleanup a temp directory
@contextlib.contextmanager
def cd(newdir, cleanup=lambda: True):
    prevdir = os.getcwd()
    os.chdir(os.path.expanduser(newdir))
    try:
        yield
    finally:
        os.chdir(prevdir)
        cleanup()

@contextlib.contextmanager
def tempdir():
    dirpath = tempfile.mkdtemp()
    def cleanup():
        shutil.rmtree(dirpath)
    with cd(dirpath, cleanup):
        yield dirpath


def build_sections(parent_dir, color):
    '''
    Build a list of section dictionaries, based on the files under parent_dir

    Each dictionary has:
      filepath = path to the file
      title = title of the section, based on file name
      language = language to use for listing based on file name
      color = inherit the global color variable
      tex_file = the tex file name to use

    First four are used in render_section, the last is for tracking
    '''
    sections = []
    for (dirpath, dirnames, filenames) in os.walk(parent_dir):
        # extend our list with dictionaries for each file in filenames
        sections.extend([{'filepath':os.path.join(dirpath, f)} for f in sorted(filenames)])

    for section in sections:
        # this needs to be done per file
        # Determine language from filepath
        filename = os.path.basename(section['filepath'])
        if (filename == 'Makefile') or (filename == 'Kconfig'):
            section['language'] = 'make'
        elif filename.endswith('.c'):
            section['language'] = 'C'
        elif filename.endswith('.h'):
            section['language'] = 'C'
        elif filename.endswith('.S'):
            section['language'] = '{[x86masm]Assembler}'
        elif filename.endswith('.sh'):
            section['language'] = 'sh'
        else:
            # Make seems like a good general purpose
            section['language'] = 'make'

        # title is the relative path to the parent_dir
        relative_path = os.path.relpath(section['filepath'], parent_dir)

        # escape underscores for title only
        section['title'] = relative_path.replace('_','\_')

        # change example/test\_file.c to example_test_file_c.tex
        section['tex_file'] = relative_path.replace('.','_')
        section['tex_file'] = section['tex_file'].replace('/','_')
        section['tex_file'] = section['tex_file']

        section['color'] = color

    return sections

def render_section(section, template):
    '''
    Returns the rendered tex string.

    templates is the Jinja LaTeX template
    section has the keys to fill in the template
    '''
    rendered_tex = template.render(color=section['color'],
                                   language=section['language'],
                                   title=section['title'],
                                   filepath=section['filepath'])
    return rendered_tex


if __name__ == "__main__":
    arguments = docopt(__doc__, version='make_book 0.1')

    # Begin jinja environments
    # Courtesy of:
    # http://eosrei.net/articles/2015/11/latex-templates-python-and-jinja2-generate-pdfs
    # {{ var }} is replaced with \VAR{ var }
    # {{ for x in list }} is replaced with \BLOCK{ for x in list }
    # {# comment #} is replaced with \#{ comment }
    # Line statements and comments are defined, but not used
    script_dir = os.path.dirname(sys.argv[0])
    template_dir = os.path.join(script_dir, 'templates')
    latex_env = Environment(block_start_string = '\BLOCK{',
                            block_end_string = '}',
                            variable_start_string = '\VAR{',
                            variable_end_string = '}',
                            comment_start_string = '\#{',
                            comment_end_string = '}',
                            line_statement_prefix = '%%',
                            line_comment_prefix = '%#',
                            trim_blocks = True,
                            autoescape = False,
                            loader = FileSystemLoader(template_dir)
                           )

    section_template = latex_env.get_template('section.tex')
    book_template = latex_env.get_template('book_with_license.tex')
    gpl_template = latex_env.get_template('gplv2.tex')

    # Parse options from docopt dicionary
    color = arguments['--color']
    parent_path = arguments['DIRECTORY']
    parent_path = os.path.abspath(parent_path)
    book_title = arguments['-t'].replace('_','\_')
    kernel_releasedate = arguments['-r']
    kernel_contentsdir = arguments['-c'].replace('_','\_')

    # Populate the list of section dictionaries
    sections = build_sections(parent_path, color)

    # We want to generate all the tex files, in a tmp directory
    # so we're going to:
    # 1. create a temporary working directory
    # 2. render all the section templates
    # 3. render the book tex
    # 4. generate the pdf and clean up
    orig_work_dir = os.getcwd()
    with tempdir() as tmp:
        for section in sections:
            print('Rendering {}'.format(section['tex_file']))
            rendered_tex = render_section(section, section_template)
            with open(section['tex_file']+'.tex', 'w') as tex:
                tex.write(rendered_tex)
       
        # also need to include the GPLv2 license:
        rendered_tex = gpl_template.render()
        with open('gplv2.tex', 'w') as tex:
            tex.write(rendered_tex)

        # Section tex files are all created, now to create book:
        rendered_tex = book_template.render(title=book_title,
                                            releasedate=kernel_releasedate,
                                            contentsdir=kernel_contentsdir,
                                            sections=sections)
        with open('book.tex', 'w') as tex:
            tex.write(rendered_tex)

        pdflatex_cmd = ['pdflatex', 'book.tex']
        # pdflatex_cmd = ['ls','-l']
        print('Initial render')
        p = subprocess.run(pdflatex_cmd, 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)

        # Table of Contents isn't populated unless rendered twice
        print('Final render')
        p = subprocess.run(pdflatex_cmd, 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)

        # move the pdf output to the original working directory
        tmp_pdf = os.path.join(tmp, 'book.pdf')
        final_pdf = os.path.join(orig_work_dir, 'book.pdf')
        shutil.move(tmp_pdf,final_pdf)

    print(final_pdf)
