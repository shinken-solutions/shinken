#!/usr/bin/env python2

# Author: Thibault Cohen <thibault.cohen@savoirfairelinux.com>
# Inspired from http://docutils.sourceforge.net/tools/rst2man.py

import locale
import os
try:
    locale.setlocale(locale.LC_ALL, '')
except:
    pass

from docutils.core import publish_file
from docutils.writers import manpage


output_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), "manpages")
source_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), "sources")

for current_folder, subfolders, files in os.walk(source_folder):
    for rst_file in files:
        if rst_file.endswith(".rst"):
            input_file = os.path.join(current_folder, rst_file)
            output_file = os.path.join(output_folder, os.path.splitext(rst_file)[0] + ".8")
            publish_file(source_path=input_file,
                         destination_path=output_file,
                         writer=manpage.Writer()
                         )
