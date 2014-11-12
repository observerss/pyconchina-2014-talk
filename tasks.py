#!/usr/bin/env python
# -*- coding: utf-8 -*-
from invoke import task
from IPython.nbconvert.exporters import SlidesExporter
from IPython.config import Config

from IPython.nbformat import current as nbformat


@task
def dist():
    import os
    import shutil
    if not os.path.exists('dist'):
        os.mkdir("dist")
    _build(outfile="dist/talk.html",
           #reveal_prefix="https://cdn.jsdelivr.net/reveal.js/2.5.0",
           reveal_prefix="http://cdn.bootcss.com/reveal.js/2.5",
           template_file="templates/slides_reveal")
    try:
        shutil.copytree('images', 'dist/images')
        shutil.copyfile('custom.css', 'dist/custom.css')
    except:
        pass


@task
def build():
    _build()


def _build(infile=None, outfile=None,
           reveal_prefix='reveal.js',
           template_file='templates/slides_reveal_local'):
    if infile is None:
        infile = "talk.ipynb" # load the name of your slideshow
    if outfile is None:
        outfile = "talk.slides.html"

    print('building {} to {}'.format(infile, outfile))

    notebook = open(infile).read()
    notebook_json = nbformat.reads_json(notebook)

    # This is the config object I talked before:
    # After the 'url_prefix', you can set the location of your
    # local reveal.js library, i.e. if the reveal.js is located
    # in the same directory as your talk.slides.html, then
    # set 'url_prefix':'reveal.js'.

    c = Config({
                'RevealHelpPreprocessor':{
                    'enabled':True,
                    'url_prefix':reveal_prefix,
                    },
                })

    exportHtml = SlidesExporter(config=c,
                                template_file=template_file)
    (body,resources) = exportHtml.from_notebook_node(notebook_json)

    # table -> bootstrap table
    body = body.replace('<table>',
                        '<table class="table table-striped">')

    # for all code blocks after "show me the code", no "input_hidden"
    show = body.find('数据预处理-训练集与特征')
    body = body[:show] + body[show:].replace('input_hidden', 'input')

    open(outfile, 'w').write(body)
