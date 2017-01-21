#!/usr/bin/env python3
"""Make a pdf for a single C file

Usage:
  make_chapter.py [--color] [-p PARENTDIR] [--keep_tex] FILE

Options:
  -h --help     Show this help screen
  --color       Turn on color pdf output
  --keep_tex    Preserve the tex file
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


def create_chapter(info):
    '''
    Creates the tex file named 'info['tex']' with info['sections'].

    After this is done, we just need to compile pdf with 'pdflatex tex_file' 

    Assumes:
      chapter_template are the correct 
        Jinja2 templates
    '''
    # Section tex files are all created, now to create book:
    rendered_tex = chapter_template.render(color=info['color'],
                                           language=info['language'],
                                           title=info['title'],
                                           filepath=info['filepath'])
    with open(info['tex_file'], 'w') as tex:
        tex.write(rendered_tex)


def create_pdf(info):
    '''
    Render the final document
    '''
    pdflatex_cmd = ['pdflatex', info['tex_file']]

    print('Final render')
    p = subprocess.run(pdflatex_cmd, 
                       stdout=subprocess.DEVNULL, 
                       stderr=subprocess.DEVNULL)

    # populate the pdf_file key with the generated file
    info['pdf_file'] = info['tex_file'].replace('.tex', '.pdf')


def copy_pdf(info, tmp_dir, target_dir):
    # move the pdf output to the original working directory
    pdf_name = info['pdf_file']
    tmp_pdf = os.path.join(tmp_dir, pdf_name)
    final_pdf = os.path.join(target_dir, pdf_name)
    shutil.move(tmp_pdf, final_pdf)
    print(final_pdf)


def copy_tex(info, tmp_dir, target_dir):
    # move the tex output to the original working directory
    tex_name = info['tex_file']
    tmp_tex = os.path.join(tmp_dir, tex_name)
    final_tex = os.path.join(target_dir, tex_name)
    shutil.move(tmp_tex, final_tex)
    print(final_tex)


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
    info = {}
    info['color'] = arguments['--color']
    keep_tex = arguments['--keep_tex']
    info['filepath'] = arguments['FILE']
    info['filepath'] = os.path.abspath(info['filepath'])
    filename = os.path.basename(info['filepath'])

    # Determine language from filepath
    if (filename == 'Makefile') or (filename == 'Kconfig'):
        info['language'] = 'make'
    elif filename.endswith('.c'):
        info['language'] = 'C'
    elif filename.endswith('.h'):
        info['language'] = 'C'
    elif filename.endswith('.S'):
        info['language'] = '{[x86masm]Assembler}'
    elif filename.endswith('.sh'):
        info['language'] = 'sh'
    else:
        # Make seems like a good general purpose
        info['language'] = 'make'

    # title is basename, or the relative path if parent is given
    if arguments['-p']:
        parent_dir = arguments['-p']
        parent_dir = os.path.abspath(parent_dir)
        rel_path = os.path.relpath(info['filepath'], parent_dir)
    else:
        rel_path = os.path.basename(info['filepath'])

    info['title'] = rel_path.replace('_','\_')

    info['tex_file'] = rel_path.replace('.','_').replace('/','_') + '.tex'

    # We want to generate all the tex files, in a tmp directory
    # so we're going to:
    # 1. create a temporary working directory
    # 2. render the tex
    # 3. render the pdf
    # 4. copy files back
    orig_work_dir = os.getcwd()
    with tempdir() as tmp:
        # create_chapter creates the .tex file for the chapter
        create_chapter(info)

        # create the pdf and copy back to original directory
        create_pdf(info)
        copy_pdf(info, tmp, orig_work_dir)
        if keep_tex:
            copy_tex(info, tmp, orig_work_dir)

