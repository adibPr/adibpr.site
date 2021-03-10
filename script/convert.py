import os
import sys
import argparse
import glob
from pathlib import Path

path_this = os.path.dirname(os.path.abspath(__file__))
sys.path.append(path_this)

from util import get_logger
from notebook import Notebook

logger = get_logger("convert")

def convert_file(arg):
    nb = Notebook(arg['input_file'])
    nb.export(arg['output_file'], img_to=arg['media_folder'])

def convert_folder(arg):
    # first, we need to somehow reconstruct the hierarchy of the input folder
    # to the output folder
    # the way we do that by get the input path, and then subtract it from the
    # actual notes path.
    tot_base_part = len(Path(arg['input_file']).parts)
    for note in glob.iglob(os.path.join(arg['input_file'], '**/*.ipynb'), recursive=True):
        logger.debug("Processing {}".format(note))
        # $note is also a path, but joined with the $input_file
        # get note but with strip base, only preserve the hierarchy
        # remeber: -1 since we do not want to include the file, only the 
        # folder hierarchy
        note_path_hierarchy = os.path.join(*Path(note).parts[tot_base_part:-1])
        note_fname = os.path.split(note)[-1]
        note_name, note_ext = os.path.splitext(note_fname)

        note_output = os.path.join(arg['output_file'], note_path_hierarchy, note_name + ".md")
        note_media_output = os.path.join(arg['media_folder'], note_path_hierarchy, note_name)

        logger.debug("Converting")
        nb  = Notebook(note)
        nb.export(note_output, img_to=note_media_output)

def get_argparser():
    parser = argparse.ArgumentParser(description="""
            A program to convert jupyter notebook to a markdown.
            If a folder is provided, then it will recursively convert it
        """)
    
    parser.add_argument(
            "-IF", "--input-file", help="input file/folder", 
            required=True,
            dest="input_file"
        )
    parser.add_argument(
            "-OF", "--output-file", 
            help="output (destination) file/folder", 
            dest="output_file",
            default=os.path.join(path_this, 'exported')
        )

    parser.add_argument("-MF", "--media-folder",
            help="folder for generated media (if any)",
            dest="media_folder",
            default=os.path.join(path_this, 'exported', 'media')
        )
        
    return parser

if __name__ == '__main__':
    parser = get_argparser()
    args = vars(parser.parse_args())

    logger.info("Your argument: ")
    logger.info(f"input_file      : {args['input_file']}")
    logger.info(f"output_folder   : {args['output_file']}")
    logger.info(f"media_folder    : {args['media_folder']}")

    convert_folder(args)

