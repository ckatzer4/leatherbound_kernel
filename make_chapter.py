#!/usr/bin/env python3
"""Make a pdf for a sincle C file

Usage:
  make_chapter.py [--color] [-p PARENTDIR] FILE

Options:
  -h --help     Show this help screen
  --color       Turn on color pdf output
  -p PARENTDIR  Base directory

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


if __name__ == "__main__":
    arguments = docopt(__doc__, version='make_chapter 0.1')

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

    chapter_template = latex_env.get_template('base.tex')

    # Parse options from docopt dicionary
    color = arguments['--color']
    filepath = arguments['FILE']
    filepath = os.path.abspath(filepath)
    filename = os.path.basename(filepath)

    # Determine language from filepath
    if (filename == 'Makefile') or (filename == 'Kconfig'):
        language = 'make'
    elif filename.endswith('.c'):
        language = 'C'
    elif filename.endswith('.h'):
        language = 'C'
    elif filename.endswith('.S'):
        language = '{[x86masm]Assembler}'
    elif filename.endswith('.sh'):
        language = 'sh'
    else:
        # Make seems like a good general purpose
        language = 'make'

    # title is basename, or the relative path if parent is given
    if arguments['-p']:
        parent_dir = arguments['-p']
        parent_dir = os.path.abspath(parent_dir)
        title = os.path.relpath(filepath, parent_dir)
    else:
        title = os.path.basename(filepath)

    outfile_base = title

    # escape underscores for title only
    title = title.replace('_','\_')

    # I only want to render a pdf output, then print the name of the prd
    # so we're going to:
    # 1. create a temporary working directory
    # 2. run pdflatex in that directory
    # 3. copy the pdf out of the temp directory
    # 4. clean up
    orig_work_dir = os.getcwd()
    with tempdir() as tmp:
        rendered_tex = chapter_template.render(color=color, 
                                               language=language,
                                               title=title, 
                                               filepath=filepath)

        # outfile_base changes example/test\_file.c to example_test_file.c
        outfile_base = outfile_base.replace('.','_')
        outfile_base = outfile_base.replace('/','_')

        # define some file names
        tex_file = '{}.tex'.format(outfile_base)
        pdf_file = '{}.pdf'.format(outfile_base)
        tmp_pdf = os.path.join(tmp, pdf_file)
        final_pdf = os.path.join(orig_work_dir, pdf_file)
        tmp_tex = os.path.join(tmp, tex_file)
        final_tex = os.path.join(orig_work_dir, tex_file)

        with open(tex_file, 'w') as tex:
            tex.write(rendered_tex)
        
        # tex file is written, now run pdflatex
        pdflatex_cmd = ['pdflatex', '"{}"'.format(tex_file)]
        # pdflatex_cmd = ['ls','-l']
        p = subprocess.run(pdflatex_cmd, 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)

        # move the pdf output to the original working directory
        shutil.move(tmp_pdf,final_pdf)
        shutil.move(tmp_tex,final_tex)

    print(pdf_file)
