#!/usr/bin/env python3
"""Make a pdf for a kernel directory

Usage:
  make_book.py [--color] [--volumes num] -t title -r release_date -c contents_directory DIRECTORY

Options:
  -h --help          Show this help screen
  --color            Turn on color pdf output
  --volumes num      Split into 'num' pdfs (default: 1)
  -t title           Title for the book
  -r release         String of the release date
  -c contents        String for the table of contents

"""

import contextlib
import os
import sys
import shutil
import tempfile
import subprocess
import re
from collections import OrderedDict

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


def create_volume(vol_info):
    '''
    Creates the tex file named 'vol_info['tex']' with vol_info['sections'].
    Section tex files are also created.

    After this is done, we just need to compile pdf with 'pdflatex tex_file' 

    Assumes:
      section_template, gpl_template, and book_template are the correct 
        Jinja2 templates
    '''
    for section in vol_info['sections']:
        # print('Rendering {}'.format(section['tex_file']))
        rendered_tex = render_section(section, section_template)
        with open(section['tex_file']+'.tex', 'w') as tex:
            tex.write(rendered_tex)
       
    # also need to include the GPLv2 license:
    rendered_tex = gpl_template.render()
    with open('gplv2.tex', 'w') as tex:
        tex.write(rendered_tex)

    # Section tex files are all created, now to create book:
    rendered_tex = book_template.render(title=vol_info['title'],
                                        releasedate=vol_info['releasedate'],
                                        contentsdir=vol_info['contentsdir'],
                                        sections=vol_info['sections'])
    with open(vol_info['tex_file'], 'w') as tex:
        tex.write(rendered_tex)


def create_toc(vol_info):
    '''
    Render the document twice
     1st - initial render gets relative page numbers for sections
     2nd - second render adds the length of the table of contents
    '''

    pdflatex_cmd = ['pdflatex', vol_info['tex_file']]

    print('Initial render for '+vol_info['tex_file'])
    p = subprocess.run(pdflatex_cmd, 
                       stdout=subprocess.DEVNULL, 
                       stderr=subprocess.DEVNULL)

    print('Rendering table of contents')
    p = subprocess.run(pdflatex_cmd, 
                       stdout=subprocess.DEVNULL, 
                       stderr=subprocess.DEVNULL)

    vol_info['toc'] = vol_info['tex_file'].replace('.tex','.toc')


def create_pdf(vol_info):
    '''
    Render the final document (technically the third time)
     3rd - third render gets correct page numbers for sections
    '''
    pdflatex_cmd = ['pdflatex', vol_info['tex_file']]

    print('Final render')
    p = subprocess.run(pdflatex_cmd, 
                       stdout=subprocess.DEVNULL, 
                       stderr=subprocess.DEVNULL)

    # populate the pdf_file key with the generated file
    vol_info['pdf_file'] = vol_info['tex_file'].replace('.tex', '.pdf')


def copy_pdf(vol_info, tmp_dir, target_dir):
    # move the pdf output to the original working directory
    pdf_name = vol_info['pdf_file']
    tmp_pdf = os.path.join(tmp_dir, pdf_name)
    final_pdf = os.path.join(target_dir, pdf_name)
    shutil.move(tmp_pdf, final_pdf)
    print(final_pdf)


def split_volumes(book_info, number_volumes):
    '''
    Split the original book into the desired number of volumes (number_volumes).

    Returns a list of dictionaries with the following keys:
      title - title for a new volume (e.g. Linux 2.6.0 Volume 2)
      tex_file - the .tex file for the new volume
      releasedate - release date of the original book
      contentsdir - the contents directory of the original book
      sections - a list of section dictionaries
    '''
    # if there's no need to split, just return the original for final compiling
    if number_volumes < 2:
        return [book_info]

    # Create a dictionary of page numbers for all sections
    # The chapter and license lines are ignored for now
    section_page_regex = '\\contentsline \{section\}\{(.*)\}\{([0-9]+)\}'
    page_to_section = OrderedDict()
    section_count = 0
    with open(book_info['toc'], 'r') as fh:
        for line in fh:
            if '{chapter}' in line:
                continue
            elif 'LICENSE' in line:
                continue
            else:
                groups = re.search(section_page_regex, line)
                if groups:
                    # sections in the list are the same order of the toc
                    # so we can just keep count and link them in the dict
                    page = groups.group(2)
                    page_to_section[int(page)] = book_info['sections'][section_count]
                    section_count += 1

    # "last" isn't quite right, but close enough for our puposes
    last_page_number = max(page_to_section.keys())

    # Use last_page_number to identify where to split
    split_point = int(last_page_number)//number_volumes

    # initialize list of volumes
    volumes = [ { 'sections':[] } for x in range(number_volumes) ]

    # populate the section list for new volumes
    for (page, section) in page_to_section.items():
        volume_index = page//split_point
        # volume_index should never be more than number_volumes:
        volume_index = min(volume_index, number_volumes-1)
        volumes[volume_index]['sections'].append(section)

    for (index, volume) in enumerate(volumes):
        # Add the remaining keys for our new volumes
        volume['title'] = '{title} Volume {i}'.format(title=book_info['title'],
                                                          i=index)
        volume['tex_file'] = 'vol{i}.tex'.format(i=index)
        volume['releasedate'] = book_info['releasedate']
        volume['contentsdir'] = book_info['contentsdir']

        # Now to create .tex and .toc from dictionary
        create_volume(volume)
        create_toc(volume)

    return volumes


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
    try:
        number_volumes = int(arguments['--volumes'])
    except TypeError:
        number_volumes = 1

    book_info = {}
    book_info['tex_file'] = 'book.tex'
    book_info['title'] = arguments['-t'].replace('_','\_')
    book_info['releasedate'] = arguments['-r']
    book_info['contentsdir'] = arguments['-c'].replace('_','\_')

    # Populate the list of section dictionaries
    book_info['sections'] = build_sections(parent_path, color)

    # We want to generate all the tex files, in a tmp directory
    # so we're going to:
    # 1. create a temporary working directory
    # 2. render all the section templates and the full book.tex
    # 3. render table of contents for tex
    # 4. use table of contents to split into volumes if necessary
    # 5. for each vol*.tex, generate the final pdf and clean-up
    orig_work_dir = os.getcwd()
    with tempdir() as tmp:
        # create_volume populates the .tex file for the full book
        create_volume(book_info)

        # create_toc populates the .toc file
        create_toc(book_info)

        # create volumes based on initial renders
        volumes = split_volumes(book_info, number_volumes)

        # for each volume, create a pdf and copy back to original directory
        for volume in volumes:
            create_pdf(volume)
            copy_pdf(volume, tmp, orig_work_dir)

