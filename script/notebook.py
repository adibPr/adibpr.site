#!/usr/bin/env python

import os
import sys
import subprocess
import json
import re
import shutil
import shlex # for shell quote
import argparse
from pathlib import Path

path_this = os.path.dirname (os.path.abspath (__file__))
sys.path.append(path_this)
from util import get_logger

logger = get_logger ('notebook')

class Notebook(object):

    def __init__ (self, path):
        logger.info("Processing {}".format(path))
        self.path = path
        self.fname = os.path.basename (path)
        self.basepath = os.path.dirname (path)
    
    def check_valid (self):
        logger.debug("File extension check")
        assert self.path.endswith ('.ipynb'), "It does not have ipynb extension"
        with open (self.path, 'r') as f_:
            note = json.load (f_)

            logger.debug("First cell check")
            assert note['cells'][0]['cell_type'] == 'raw' , "first cell is not raw"
            first_cell = note['cells'][0]['source']
            assert first_cell[0].strip () == "---" and first_cell[-1].strip () == "---",\
                    "No --- the in first and last line"

            logger.debug("Metadata check")
            metadata_str = first_cell[1:-1]
            metadata = {}
            for line in metadata_str:
                line_splitted = line.strip ().split (':')
                if line_splitted:
                    metadata[line_splitted[0].strip ()] = " ".join (line_splitted[1:]).strip () # in case the title has :

            assert set (["author", "title"]) - set (metadata.keys ()) == set (),\
                    "No author and title is provided"

            logger.debug ("Metadata info: ")
            for key in metadata:
                logger.debug ("\t{}: {}".format (key, metadata[key]))
            if 'draft' not in metadata or metadata['draft'].lower () != 'false':
                raise ValueError ("Notes is in draft")

    def export (self, post_to, img_to=None):
        """
        Save/convert this note into markdown format that are ready to be displayed (in format of Markdown)
        @post_to: path, if $post_to is a folder, then the *folder* we want to put our markdown. The 
            final path will be $post_to/{{fname}}.md
            if the $post_to is a file (with .md extension), then it will be exported into that fname.
        @img_to: path. If the note has user generated chart, the image will be moved to here.
            Default is {{notebook folder}}/img 
        #@res_prefix: path. The prefix of all image url. For ex: image !a.jpg will be converted into {{res_prefix}}/a.jpg
        """

        self.check_valid ()

        # check whether $post_to is folder or a path to file
        # if it's a folder, then use default naming
        if post_to.endswith ('.md'):
            post_to_base, post_to_file = os.path.split(post_to)
        else:
            post_to_base = post_to
            post_to_file = self.fname[:-6] + ".md"
            post_to = os.path.join(post_to_base, post_to_file)

        path_md = os.path.join(self.basepath, self.fname[:-6] + ".md")

        logger.debug("Base export: {}".format(post_to))
        logger.debug("\tfname: {}".format(post_to_file))

        logger.debug("Convert to markdown")
        cmd = ["jupyter-nbconvert {} --to markdown".format (shlex.quote (self.path))]
        subprocess.run (cmd, shell=True)

        # replace all image url with it's prefix
        # FIXME: change into replace url with it's google drive counterpart
        # Notebook.replace_url (path_md, res_prefix)

        # move the markdown to its destination
        Path(post_to_base).mkdir(parents=True, exist_ok=True)
        shutil.move (path_md, post_to)

        # and the files, if any
        img_files = path_md.rstrip (".md") + "_files"
        if os.path.exists (img_files):
            logger.debug("Moving image files")
            if img_to is None:
                img_to = os.path.join (self.post_to_base, "media")

            # recreate img_to
            Path(img_to).mkdir(parents=True, exist_ok=True)

            # using shell copy because python copy can't overwrite
            cmd = ['cp -rf {}/* {}'.format (shlex.quote (img_files), shlex.quote (img_to))]
            subprocess.run (cmd, shell=True)

            # remove the files then
            shutil.rmtree (img_files)

        logger.debug("Done")

    @staticmethod
    def replace_url (path_md, res_prefix):
        """
        This is the case if you have an asset that you put into a local directory,
        and you want it in the site. But since we are planning on using google drive,
        we are not sure about this feature.
        """
        assert path_md.endswith ('.md'), '{} is not a md file (from its extension)'.format (path_md)

        with open (path_md, 'r') as f_:
            this_file = path_md[:-2] # from aa.md to aa
            md_content = "\n".join (f_.read ().splitlines ())
            # change here, check if its start with http, otherwise assume its local
            # and change to it's public link respectively
            img_links = re.findall (r'\!\[.*?\]\((.*?)\)', md_content, flags=re.I)
            for link in set (img_links): # to prevent the same img being replaced twice
                # check for web links
                if "http" in link or "www" in link:
                    continue 

                new_link = os.path.join (res_prefix, link)
                logger.debug ("Convert link :{} -> {}".format (link, new_link))
                # be careful if you want to replace the same content
                md_content = re.sub (re.escape (link), new_link, md_content)

        # write it
        with open (path_md, 'w') as f_:
            f_.write (md_content)
