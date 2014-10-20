#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import os
from urllib import urlretrieve

input_folder = "pages/"
output_folder = "../source"

chapters = {'about': '01',
            'gettingstarted': '02',
            'configuringshinken': '03',
            'runningshinken': '04',
            'thebasics': '05',
            'advancedtopics': '06',
            'configobjects': '07',
            'securityandperformancetuning': '08',
            'integrationwithothersoftware': '09',
            'shinkenaddons': '10',
            'development': '11',
            }

external_links = {}
internal_links = {}
output = []

# Functions


def title1(text):
    length = len(text)
    output = "\n\n%s\n%s\n%s\n\n" % ("=" * length, text, "=" * length)
    write(output)

def title2(text):
    length = len(text)
    output = "\n\n%s\n%s\n\n" % (text, "=" * length)
    write(output)

def title3(text):
    length = len(text)
    output = "\n\n%s\n%s\n\n" % (text, "-" * length)
    write(output)

def title4(text):
    length = len(text)
    output = "\n\n%s\n%s\n\n" % (text, "~" * length)
    write(output)

def title5(text):
    length = len(text)
    output = "\n\n%s\n%s\n\n" % (text, "*" * length)
    write(output)

def external_link(links):
    for link in links.items():
        output = "\n.. _%s: %s" % link
        write(output)

def normal_text(text):
    output = text
    write(output)

def get_image(image_url, image_path):
    path = "/".join((output_folder, image_path))
    try:
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        urlretrieve(image_url, path)
    except Exception:
        import pdb;pdb.set_trace()

def get_lengths(lengths, row):
    if lengths is None:
        lengths = [len(cell) for cell in row]
    else:
        if len(lengths) > len(row):
            row = row + [''] * (len(lengths) - len(row))
        row_lengths = [len(cell) for cell in  row]
        lengths = map(lambda x: max([i for i in x]), zip(row_lengths, lengths))
    return lengths


# Main
for root, dirs, files in os.walk(input_folder):
    for filename in files:
        f = open(os.path.join(root, filename), 'r')
        # Set vars
        in_code = False
        in_note = False
        in_table = False
        in_tagcode = False
        nb_col = None
        external_links = {}
        internal_links = {}
        tables = []
        rows = []
        output = []

        # open file
        rst_filename = filename[:-3] + "rst"
        chapter = rst_filename.split("-", 1)
        if len(chapter) <= 1:
            chapter = "raws"
        elif not chapter[0] in chapters:
            chapter = "raws"
        else:
            chapter = chapter[0]
            chapter = chapters[chapter] + "_" + chapter
        if root.endswith('configobjects'):
            chapter = '07_configobjects'
        chapter_folder = os.path.join(output_folder, chapter)
        if not os.path.exists(chapter_folder):
            os.makedirs(chapter_folder)
        rst_file = os.path.join(chapter_folder, rst_filename)
        fw = open(rst_file, 'w')

        def write(text):
            fw.write(text)


        # Write the first line
        ref_target = ".. _%s:\n\n" % filename[:-4]
        write(ref_target)

        # parse line !
        for line in f:
            o_line = line
            # always strip line ???
#            line = line.strip('\n')
            # nagivations links
            #m = re.match("\|.*Prev.*Up.*Next.*\|", line.strip())
            m = re.match("\|.*Next.*\|", line.strip())
            if m:
                # we don't want it
                continue
            m = re.match("\|.*Chapter [0-9]*.*\|", line.strip())
            if m:
                # we don't want it
                continue
            m = re.match("\|.*Part .*\|", line.strip())
            if m:
                # we don't want it
                continue
            # Title 1
            m = re.match("===== ?Chapter [0-9]*\.(.*) ?=====", line)
            if m:
                # get datas
                title = m.groups()[0]
                # prepare datas
                attrs = {'text': title}
                data = {
                        'fnt': title1,
                        'attrs': attrs,
                        }
                # store datas
                output.append(data)
                # Disable in_code
                in_code = False
                # next line
                continue
            # Title 2
            m = re.match("====== ?(.*) ?======", line)
            if m:
                title = m.groups()[0]
                # prepare datas
                attrs = {'text': title}
                data = {
                        'fnt': title1,
                        'attrs': attrs,
                        }
                # store datas
                output.append(data)
                # Disable in_code
                in_code = False
                # next line
                continue
            # Title 2
            m = re.match("===== ?(.*) ?=====", line)
            if m:
                title = m.groups()[0]
                # prepare datas
                attrs = {'text': title}
                data = {
                        'fnt': title2,
                        'attrs': attrs,
                        }
                # store datas
                output.append(data)
                # Disable in_code
                in_code = False
                # next line
                continue
            # Title 3
            m = re.match("==== ?(.*) ?====", line)
            if m:
                title = m.groups()[0]
                # prepare datas
                attrs = {'text': title}
                data = {
                        'fnt': title3,
                        'attrs': attrs,
                        }
                # store datas
                output.append(data)
                # Disable in_code
                in_code = False
                # next line
                continue
            # Title 4
            m = re.match("=== ?(.*) ?===", line)
            if m:
                title = m.groups()[0]
                # prepare datas
                attrs = {'text': title}
                data = {
                        'fnt': title4,
                        'attrs': attrs,
                        }
                # store datas
                output.append(data)
                # Disable in_code
                in_code = False
                # next line
                continue
            # Title 5
            m = re.match("== ?(.*) ?==", line)
            if m:
                title = m.groups()[0]
                # prepare datas
                attrs = {'text': title}
                data = {
                        'fnt': title5,
                        'attrs': attrs,
                        }
                # store datas
                output.append(data)
                # Disable in_code
                in_code = False
                # next line
                continue

            # Normal line
            # Search external links
            m = re.search("\[\[https?://(.*?)\|(.*?)\]\]", line)
            if m:
                links = re.findall("\[\[(https?)://(.*?)\|(.*?)\]\]", line)
                for link in links:
                    line = re.sub("\[\[https?://(.*?)\|(.*?)\]\]", "`%s`_" % link[2], line, count=1, flags=0)
                    external_links[link[2]] = link[0] + "://" + link[1]

            m = re.search("\[\[https?://(.*?)\]\]", line)
            if m:
                links = re.findall("\[\[(https?)://(.*?)\]\]", line)
                for link in links:
                    line = re.sub("\[\[https?://(.*?)\]\]", "`%s`_" % link[1], line, count=1, flags=0)
                    external_links[link[1]] = link[0] + "://" + link[1]
            
            # Search internal links
            m = re.search("\[\[(.*?)\|(.*?)\]\]", line)
            if m:
                links = re.findall("\[\[(.*?)\|(.*?)\]\]", line)
                for link in links:
                    ref = link[0].split(":")[-1]
                    ref_text = link[1].strip()
                    line = re.sub("\[\[(.*?)\|(.*?)\]\]", ":ref:`%s <%s>`" % (ref_text, ref), line, count=1, flags=0)
                    if ref.startswith("configuringshinken/configobjects/"):
                        ref = ref.replace("configuringshinken/configobjects/", '')
                    internal_links[ref_text] = ref

            m = re.search("\[\[(.*?)\]\]", line)
            if m:
                links = re.findall("\[\[(.*?)\]\]", line)
                for link in links:
                    ref = link.split(":")[-1]
                    ref_text = ref
                    line = re.sub("\[\[(.*?)\]\]", ":ref:`%s` <%s>" % (ref_text, ref), line, count=1, flags=0)
                    if ref.startswith("configuringshinken/configobjects/"):
                        ref = ref.replace("configuringshinken/configobjects/", '')
                    internal_links[ref_text] = ref

            # Search image
            m = re.search("\{\{(.*?)\|(.*?)\}\}", line)
            if m:
                images = re.findall("\{\{(.*?)\|(.*?)\}\}", line)
                for image, text in images:
                    # TODO prepare image var
                    path = image.replace(":shinken:", "")
                    path = path.replace(":", "/")
                    img_filename = os.path.basename(path)
                    path = os.path.dirname(path)
                    # Download images
                    image_url = image.replace(":shinken:", "")
                    image_url = image_url.replace(":", "/")
                    image_url = "http://www.shinken-monitoring.org/wiki/_media/" + image_url
                    ##
#                    path = os.path.join("_static/images/", path)
                    path = "_static/images/" + path
                    image_path = os.path.join(path, img_filename)
#                    if not os.path.exists(path):
#                        os.makedirs(path)
                    get_image(image_url, image_path)
                    # TODO add \n after the image ???
                    image_rst_path = "/" + image_path
                    line = re.sub("\{\{(.*?)\}\}", "\n\n.. image:: %s\n   :scale: 90 %%\n\n" % image_rst_path, line, count=1, flags=0)

            m = re.search("\{\{(.*?)\}\}", line)
            if m:
                images = re.findall("\{\{(.*?)\}\}", line)
                for image in images:
                    # TODO prepare image var
                    path = image.replace(":shinken:", "")
                    path = path.replace(":", "/")
                    img_filename = os.path.basename(path)
                    path = os.path.dirname(path)
                    # Download images
                    image_url = image.replace(":shinken:", "")
                    image_url = image_url.replace(":", "/")
                    image_url = "http://www.shinken-monitoring.org/wiki/_media/" + image_url
                    ##
#                    path = os.path.join("_static/images/", path)
                    path = "_static/images/" + path
                    image_path = os.path.join(path, img_filename)
#                    if not os.path.exists(path):
#                        os.makedirs(path)
                    get_image(image_url, image_path)
                    # TODO add \n after the image ???
                    image_rst_path = "/" + image_path
                    line = re.sub("\{\{(.*?)\}\}", "\n\n.. image:: %s\n   :scale: 90 %%\n\n" % image_rst_path, line, count=1, flags=0)




            # Emphasis
            m = re.search("[^/](//[^/]*//)[^/]", line)
            if m:
                emphasis = re.findall("[^/](//[^/]*//)[^/]", line)
                for emph in emphasis:
                    new = "*%s*" % emph[2:-2]
                    line = line.replace(emph, new)



            # Code with tag
            m1 = re.search("<code>", line)
            m2 = re.search("</code>", line)
            if m2 and in_tagcode == True:
                # end code
                line = line.replace("</code>", "")
                in_tagcode = False
            elif m1 and in_tagcode == False:
                # start code
                line = line.replace("<code>", "\n::\n\n  ")
                in_tagcode = True



            # code with spaces
            m = re.search("^  *[-\*]", line)
            # end code
            if m and in_code == True and line.strip() != "::":
                # Code/list merged
                in_code = False
                line = re.sub("^ *", "", line)
                line = "\n" + line

            # end code
            if in_code == True and not re.search("^  *", line) and line.strip() != '':
                in_code = False
            m = re.search("^  *[^- \*]", line)

            # start code
            if m and in_code == False:
                in_code = True
                line = re.sub("^  ", "\n::\n\n  ", line)


            # if in code ....
            if in_code == True or in_tagcode == True:
                # In code
                if not line.startswith("  "):
                    line = "  " + line

            # if NOT in code...
            if in_code == False and in_tagcode == False:
                line = re.sub("\\\\", "\\\\", line)


            # Note
            m1 = re.search("<note>", line)
            m2 = re.search("<note warning>", line)
            m3 = re.search("<note tip>", line)
            m4 = re.search("<note important>", line)
            if m1:
                line = line.replace("<note>", ".. note::  ")
                in_note = True
            elif m2:
                line = line.replace("<note warning>", ".. warning::  ")
                in_note = True
            elif m3:
                line = line.replace("<note tip>", ".. tip::  ")
                in_note = True
            elif m4:
                line = line.replace("<note important>", ".. important::  ")
                in_note = True
            elif in_note == True:
                line = "   " + line

            m = re.search("</note>", line)
            if m:
                line = line.replace("</note>", "")
                in_note = False

            line = line.replace(u"”".encode('utf-8'), '"')
            line = line.replace(u"�".encode('utf-8'), '"')
            line = line.replace(u"′".encode('utf-8'), '"')
            line = line.replace(u"’".encode('utf-8'), '"')
            line = line.replace(u"‘".encode('utf-8'), '"')

#            if line.find("$HOSTACKAUTHORNAME$") != -1:
#                import pdb;pdb.set_trace()


            # table
            m1 = re.match(" *\^.*\^ *", line.strip())
            m2 = re.match(" *\|.*\| *", line.strip())
            if m1:
                # Table header
                in_table = True
                line = line.strip()[1:-1]
                cells = [c.strip() for c in line.split('^')]
                if nb_col is None:
                    nb_col = len(cells)
                rows.append(cells)
                # don't write this line
                continue 
            elif m2:
                in_table = True
                line = line.strip()[1:-1]
                cells = [c.strip() for c in line.split('|')]
                if nb_col is None:
                    nb_col = len(cells)
                rows.append(cells)
                # don't write this line
                continue
            elif m is None and in_table == True:
                in_table = False
                borders_len = reduce(get_lengths, rows, None)
                line = "\n\n" + " ".join(["=" * i for i in borders_len])
                for row in rows:
                    f_row = " ".join(['{:{fill}{align}%d}'] * nb_col)
                    f_row = f_row % tuple(borders_len)
                    if nb_col > len(row):
                        row = row + [''] * (nb_col - len(row))
                    f_row = f_row.format(*row, fill=" ", align="<")
                    line += "\n" + f_row
                line += "\n" + " ".join(["=" * i for i in borders_len]) + "\n\n"
                rows = []
                nb_col = None

            # prepare datas
            attrs = {'text': line}
            data = {
                    'fnt': normal_text,
                    'attrs': attrs,
                    }
            # store datas
            output.append(data)

        # write lines
        for data in output:
            data['fnt'](**data['attrs'])
        external_link(external_links)

        # close file
        fw.close()


# echo 
print "mv ../source/raws/about.rst ../source/01_about/"
print "mv ../source/raws/ch07.rst ../source/02_gettingstarted/"
print "mv ../source/raws/part-problemsandimpacts.rst ../source/06_advancedtopics/"

