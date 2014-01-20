#!/usr/bin/python

from StringIO import StringIO
import os

import requests
from lxml import etree

#application_name = "shinken"
application_name = ""
url = "http://www.shinken-monitoring.org/wiki"
sitemap_url = url + "/start?do=index"
sitemap_ajax_url = url + "/lib/exe/ajax.php"
parser = etree.HTMLParser()

raw_res = requests.get(sitemap_url)

res = StringIO(raw_res.content)
tree = etree.parse(res, parser)

index = tree.find("//div[@id='index__tree']")


def parse_level(level, root=""):
    items = level.findall(".//li")
#    import pdb;pdb.set_trace()
    for item in items:
        title = item.find("./div//strong")
        if not title is None:
            new_root = root + ":" + title.text
            print "Browse namespace : %s" % new_root
            data = {'call': 'index',
                    'idx' : new_root,
                    }
            raw_ajax_res = requests.post(sitemap_ajax_url, data=data)
            ajax_res = StringIO(raw_ajax_res.content)
            ajax_parser = etree.HTMLParser()
            ajax_tree = etree.parse(ajax_res, ajax_parser)
#            print raw_ajax_res.content
            parse_level(ajax_tree, new_root)
#            http://www.shinken-monitoring.org/wiki/lib/exe/ajax.php
#            print title.getparent().getparent()
        else:
#            import pdb;pdb.set_trace()
            page_name = item.find("./div//a").text
            page_url = url + "/" + root + ":" + page_name + "?do=export_raw"
            page_raw_res = requests.get(page_url)
#            tmp_root = root.replace(":", "/")
            tmp_root = root
            if tmp_root.startswith(":"):
                tmp_root = tmp_root[1:]
            try:
                os.makedirs(os.path.join('pages', application_name, tmp_root).replace(":", "/"))
            except OSError, e:
                #print e
                pass
            file_name = os.path.join('pages', application_name, tmp_root, page_name + ".txt")
            file_name = file_name.replace(":", "/")
            replace_dict = find_media(page_raw_res.content)
            # Change links
            modified_page_raw = page_raw_res.content
            modified_page_raw = modified_page_raw.replace("official:official_", "official:")
            modified_page_raw = modified_page_raw.replace("official_", "official:")
            modified_page_raw = modified_page_raw.replace("/official/", ":%s:official:" % application_name)
            modified_page_raw = modified_page_raw.replace("[[official:", "[[%s:official:" % application_name)
            modified_page_raw = modified_page_raw.replace("[[:", "[[:%s:" % application_name)
#            modified_page_raw = modified_page_raw.replace(":green_dot.16x16.png", ":shinken:green_dot.16x16.png")
#            modified_page_raw = modified_page_raw.replace(":red_dot.16x16.png", ":shinken:red_dot.16x16.png")
#            modified_page_raw = modified_page_raw.replace(":orange_dot.16x16.png", ":shinken:orange_dot.16x16.png")
            # Change media links
#            modified_page_raw = modified_page_raw.replace("{{:official:images:", "{{%s:official:" % application_name)
            for k, v in replace_dict.items():
                #print k, v
#                if v.find("images/") != -1 or k.find("images/"):
#                    import pdb;pdb.set_trace()
                modified_page_raw = modified_page_raw.replace(k, v.replace("/", ":"))
            modified_page_raw = modified_page_raw.replace(":images/", ":images/:")

# DISABLE: add :shinken:
#            modified_page_raw = modified_page_raw.replace("{{ :", "{{ :shinken:")
#            modified_page_raw = modified_page_raw.replace(":shinken:shinken:", ":shinken:")


#            if replace_dict:
#                import pdb;pdb.set_trace()
#            modified_page_raw = modified_page_raw.replace("{{:official:", "{{/%s/official/" % application_name)
#            if modified_page_raw.find("{{/") != -1:
#                import pdb;pdb.set_trace()
            f = open(file_name, "w")
            print "    Writing file : %s" % file_name
            f.write(modified_page_raw)
            f.close()

def find_media(raw_data):
    medias = raw_data.split("{{")
    replace_dict = {}
    if len(medias) > 1:
        for m in medias[1:]:
            media = m.split("}}")[0]
            if media.startswith("http"):
                continue
#            if media.find(".png") == -1:
#                import pdb;pdb.set_trace()
            media = media.split("png")[0] + "png"
            media = media.replace(":", "/")
            media = media.strip()
            if not media.endswith("png"):
                continue
            media_url = url + "/_media" + media

# DISABLE: add :shinken:
            #replace_dict[media] = ":shinken:" + media.replace("/", ":")
            replace_dict[media] = media.replace("/", ":")


            print "        Get media : %s - %s" % (media, media_url)
            media_folder = 'media/' + application_name + "/" + os.path.dirname(media)
            try:
                os.makedirs(media_folder)
            except OSError, e:
                #print e
                pass 
            media_res = requests.get(media_url)
            media_file = os.path.join(media_folder, os.path.basename(media))
            print "        Writing media : %s" % media_file
#            print media_res.content
            f = open(media_file, "w")
            f.write(media_res.content)
            f.close()
    return replace_dict




           
parse_level(index)

lonely_pages = [
    ("http://www.shinken-monitoring.org/wiki/official/start?do=export_raw&do=export_raw", "official"),
    ("http://www.shinken-monitoring.org/wiki/packs/start?do=export_raw&do=export_raw", "packs"),
]

for p, tmp_root in lonely_pages:
    page_name = "start"
    page_raw_res = requests.get(p)
    try:
        os.makedirs(os.path.join('pages', application_name, tmp_root).replace(":", "/"))
    except OSError, e:
        #print e
        pass
    file_name = os.path.join('pages', application_name, tmp_root, page_name + ".txt")
    file_name = file_name.replace(":", "/")
   #print file_name
    replace_dict = find_media(page_raw_res.content)
    # Change links
    modified_page_raw = page_raw_res.content
    modified_page_raw = modified_page_raw.replace("official:official_", "official:")
    modified_page_raw = modified_page_raw.replace("official_", "official:")
    modified_page_raw = modified_page_raw.replace("/official/", ":%s:official:" % application_name)
    modified_page_raw = modified_page_raw.replace("[[official:", "[[%s:official:" % application_name)
    modified_page_raw = modified_page_raw.replace("[[:", "[[:%s:" % application_name)
    # Change media links
    for k, v in replace_dict.items():
     #   print k, v
        modified_page_raw = modified_page_raw.replace(k, v.replace("/", ":"))
    modified_page_raw = modified_page_raw.replace(":images/", ":images/:")

# DISABLE: add :shinken:
    modified_page_raw = modified_page_raw.replace("{{ :", "{{ :shinken:")
    modified_page_raw = modified_page_raw.replace(":shinken:shinken:", ":shinken:")

    f = open(file_name, "w")
    print "    Writing file : %s" % file_name
    f.write(modified_page_raw)
    f.close()



# for i in `grep -R "^| "|grep Prev|cut -d ":" -f 1|uniq`; do  sed -i 's/^| .*Prev.*//' $i; done
# for i in `grep -R "^| "|grep Next|cut -d ":" -f 1|uniq`; do  sed -i 's/^| .*Next.*//' $i; done
# for i in `grep -R "^| "|grep About|cut -d ":" -f 1|uniq`; do sed -i 's/^| .*About.*//' $i; done
# for i in `grep -R "^| "|grep Home|cut -d ":" -f 1|uniq` ; do sed -i 's/^| .*Home.*//' $i; done
# for i in `grep -R "===== Cha" . -l`; do sed -i 's/^===== C\(.*\)=====$/====== C\1======/' $i; done

