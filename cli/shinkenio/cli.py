#!/usr/bin/env python

# Copyright (C) 2009-2012:
#    Gabes Jean, naparuba@gmail.com
#    Gerhard Lausser, Gerhard.Lausser@consol.de
#    Gregory Starck, g.starck@gmail.com
#    Hartmut Goebel, h.goebel@goebel-consult.de
#
# This file is part of Shinken.
#
# Shinken is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Shinken is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Shinken.  If not, see <http://www.gnu.org/licenses/>.


import pycurl
import os
import sys
import json
import tempfile
import tarfile
import urllib
import shutil
from StringIO import StringIO
from shinken.log import logger, cprint

# Will be populated by the shinken CLI command
CONFIG = None



############# ********************        PUBLISH           ****************###########

def read_package_json(fd):
    buf = fd.read()
    fd.close()
    buf = buf.decode('utf8', 'ignore')
    try:
        package_json = json.loads(buf)
    except ValueError, exp:
        logger.error("Bad package.json file : %s" % exp)
        sys.exit(2)
    if not package_json:
        logger.error("Bad package.json file")
        sys.exit(2)
    return package_json




def create_archive(to_pack):
    # First try to look if the directory we are trying to pack is valid
    to_pack = os.path.abspath(to_pack)
    if not os.path.exists(to_pack):
        logger.error("Error : the directory to pack is missing %s" % to_pack)
        sys.exit(2)
    logger.debug("Preparing to pack the directory %s" % to_pack)
    package_json_p = os.path.join(to_pack, 'package.json')
    if not os.path.exists(package_json_p):
        logger.error("Error : Missing file %s" % package_json_p)
        sys.exit(2)
    package_json = read_package_json(open(package_json_p))

    name = package_json.get('name', None)
    if not name:
        logger.error('Missing name entry in the package.json file. Cannot pack')
        sys.exit(2)


    # return True for files we want to exclude
    def tar_exclude_filter(f):
        # if the file start with .git, we bail out
        # Also ending with ~ (Thanks emacs...)
        if f.startswith('./.git'):
            return True
        if f.endswith('~'):
            return True
        return False

    # Now prepare a destination file
    tmp_dir  = tempfile.gettempdir()
    tmp_file = os.path.join(tmp_dir, name+'.tar.gz')
    tar = tarfile.open(tmp_file, "w:gz")
    os.chdir(to_pack)
    tar.add(".",arcname='.', exclude=tar_exclude_filter)
    tar.close()
    logger.debug("Saved file %s" % tmp_file)
    return tmp_file


def publish_archive(archive):
    # Now really publish it
    proxy = CONFIG['shinken.io']['proxy']
    api_key = CONFIG['shinken.io']['api_key']

    # Ok we will push the file with a 10s timeout
    c = pycurl.Curl()
    c.setopt(c.POST, 1)
    c.setopt(c.CONNECTTIMEOUT, 10)
    c.setopt(c.TIMEOUT, 10)
    if proxy:
        c.setopt(c.PROXY, proxy)
    c.setopt(c.URL, "http://shinken.io/push")
    c.setopt(c.HTTPPOST, [("api_key", api_key),
                          ("data",
                           (c.FORM_FILE, str(archive),
                            c.FORM_CONTENTTYPE, "application/x-gzip"))
                          ])
    response = StringIO()
    c.setopt(pycurl.WRITEFUNCTION, response.write)
    c.setopt(c.VERBOSE, 1)
    c.perform()
    r = c.getinfo(pycurl.HTTP_CODE)
    c.close()
    if r != 200:
        logger.error("There was a critical error : %s" % response.getvalue())
        sys.exit(2)
    else:
        ret  = json.loads(response.getvalue().replace('\\/', '/'))
        status = ret.get('status')
        text   = ret.get('text')
        if status == 200:
            logger.log(text)
        else:
            logger.error(text)


def do_publish(to_pack='.'):
    logger.debug("WILL CALL PUBLISH.py with %s" % to_pack)
    archive = create_archive(to_pack)
    publish_archive(archive)




################" *********************** SEARCH *************** ##################
def search(look_at):
    # Now really publish it
    proxy = CONFIG['shinken.io']['proxy']
    api_key = CONFIG['shinken.io']['api_key']

    # Ok we will push the file with a 10s timeout
    c = pycurl.Curl()
    c.setopt(c.POST, 0)
    c.setopt(c.CONNECTTIMEOUT, 10)
    c.setopt(c.TIMEOUT, 10)
    if proxy:
        c.setopt(c.PROXY, proxy)

    args = {'keywords':','.join(look_at)}
    c.setopt(c.URL, str('shinken.io/searchcli?'+urllib.urlencode(args)))
    response = StringIO()
    c.setopt(pycurl.WRITEFUNCTION, response.write)
    #c.setopt(c.VERBOSE, 1)
    c.perform()
    r = c.getinfo(pycurl.HTTP_CODE)
    c.close()
    if r != 200:
        logger.error("There was a critical error : %s" % response.getvalue())
        sys.exit(2)
    else:
        ret  = json.loads(response.getvalue().replace('\\/', '/'))
        status = ret.get('status')
        result   = ret.get('result')
        if status != 200:
            logger.log(result)
            return []
        return result



def print_search_matches(matches):
    if len(matches) == 0:
        logger.warning("No match founded in shinken.io")
        return
    for p in matches:
        name = p['name']
        user_id = p['user_id']
        keywords = p['keywords']
        description = p['description']
        cprint('%s ' %  name , 'green', end='')
        cprint('(%s) [%s] : %s' %  (user_id, ','.join(keywords), description))




def do_search(*look_at):
    logger.debug("CALL SEARCH WITH ARGS %s" % look_at)
    matches = search(look_at)
    print_search_matches(matches)





####################   ***************** INSTALL ************ ###################

def _copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            if not os.path.exists(d):
                os.mkdir(d)
            _copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)



def grab_package(pname):
    cprint('Grabbing : ' , end='')
    cprint('%s' %  pname, 'green')

    # Now really publish it
    proxy = CONFIG['shinken.io']['proxy']
    api_key = CONFIG['shinken.io']['api_key']

    # Ok we will push the file with a 10s timeout
    c = pycurl.Curl()
    c.setopt(c.POST, 0)
    c.setopt(c.CONNECTTIMEOUT, 10)
    c.setopt(c.TIMEOUT, 10)
    if proxy:
        c.setopt(c.PROXY, proxy)

    c.setopt(c.URL, str('shinken.io/grab/%s' % pname))
    response = StringIO()
    c.setopt(pycurl.WRITEFUNCTION, response.write)
    #c.setopt(c.VERBOSE, 1)
    c.perform()
    r = c.getinfo(pycurl.HTTP_CODE)
    c.close()
    if r != 200:
        logger.error("There was a critical error : %s" % response.getvalue())
        sys.exit(2)
    else:
        ret = response.getvalue()
        logger.debug("CURL result len : %d " % len(ret))
        return ret



def grab_local(d):
    # First try to look if the directory we are trying to pack is valid
    to_pack = os.path.abspath(d)
    if not os.path.exists(to_pack):
        err = "Error : the directory to install is missing %s" % to_pack
        logger.error(err)
        raise Exception(err)

    package_json_p = os.path.join(to_pack, 'package.json')
    if not os.path.exists(package_json_p):
        logger.error("Error : Missing file %s" % package_json_p)
        sys.exit(2)
    package_json = read_package_json(open(package_json_p))

    pname = package_json.get('name', None)
    if not pname:
        err = 'Missing name entry in the package.json file. Cannot install'
        logger.error(err)
        raise Exception(err)

    # return True for files we want to exclude
    def tar_exclude_filter(f):
        # if the file start with .git, we bail out
        # Also ending with ~ (Thanks emacs...)
        if f.startswith('./.git'):
            return True
        if f.endswith('~'):
            return True
        return False

    # Now prepare a destination file
    tmp_file  = tempfile.mktemp()
    tar = tarfile.open(tmp_file, "w:gz")
    os.chdir(to_pack)
    tar.add(".",arcname='.', exclude=tar_exclude_filter)
    tar.close()
    fd = open(tmp_file, 'rb')
    raw = fd.read()
    fd.close()

    return (pname, raw)



def install_package(pname, raw):
    logger.debug("Installing the package %s (size:%d)" % (pname, len(raw)))
    tmpdir = os.path.join(tempfile.gettempdir(), pname)
    logger.debug("Unpacking the package into %s" % tmpdir)

    if os.path.exists(tmpdir):
        logger.debug("Removing previous tmp dir %s" % tmpdir)
        shutil.rmtree(tmpdir)
    logger.debug("Creating temporary dir %s" % tmpdir)
    os.mkdir(tmpdir)

    # open a file with the content
    f = StringIO(raw)
    tar_file = tarfile.open(fileobj=f, mode="r")
    logger.debug("Tar file contents:")
    for i in tar_file.getmembers():
        path = i.name
        if path == '.':
            continue
        if not path.startswith('./') or '..' in path:
            logger.error("SECURITY: the path %s seems dangerous!" % path)
            return
        logger.debug("\t%s" % path)
    # Extract all in the tmpdir
    tar_file.extractall(tmpdir)
    tar_file.close()


    package_json_p = os.path.join(tmpdir, 'package.json')
    if not os.path.exists(package_json_p):
        logger.error("Error : bad archive : Missing file %s" % package_json_p)
        return None
    package_json = read_package_json(open(package_json_p))
    logger.debug("Package.json content %s " % package_json)

    modules_dir = CONFIG['paths']['modules']
    share_dir   = CONFIG['paths']['share']
    packs_dir   = CONFIG['paths']['packs']
    etc_dir     = CONFIG['paths']['etc']
    doc_dir     = CONFIG['paths']['doc']
    test_dir   = CONFIG['paths'].get('test', '/__DONOTEXISTS__')
    for d in (modules_dir, share_dir, packs_dir, doc_dir):
        if not os.path.exists(d):
            logger.error("The installation directory %s is missing!" % d)
            return

    p_share  = os.path.join(tmpdir, 'share')

    logger.debug("TMPDIR:%s modules_dir:%s pname:%s" %(tmpdir, modules_dir, pname))
    # Now install the package from $TMP$/module/* to $MODULES$/pname/*
    p_module = os.path.join(tmpdir, 'module')
    if os.path.exists(p_module):
        logger.info("Installing the module package data")
        mod_dest = os.path.join(modules_dir, pname)
        if os.path.exists(mod_dest):
            logger.info("Removing previous module install at %s" % mod_dest)

            shutil.rmtree(mod_dest)
        # shutil will do the create dir
        shutil.copytree(p_module, mod_dest)
        logger.info("Copy done in the module directory %s" % mod_dest)


    p_doc  = os.path.join(tmpdir, 'doc')
    logger.debug("TMPDIR:%s doc_dir:%s pname:%s" %(tmpdir, doc_dir, pname))
    # Now install the package from $TMP$/doc/* to $MODULES$/doc/source/89_packages/pname/*
    if os.path.exists(p_doc):
        logger.info("Installing the doc package data")
        doc_dest = os.path.join(doc_dir, 'source', '89_packages', pname)
        if os.path.exists(doc_dest):
            logger.info("Removing previous doc install at %s" % doc_dest)

            shutil.rmtree(doc_dest)
        # shutil will do the create dir
        shutil.copytree(p_doc, doc_dest)
        logger.info("Copy done in the doc directory %s" % doc_dest)


    # Now install the pack from $TMP$/pack/* to $PACKS$/pname/*
    p_pack = os.path.join(tmpdir, 'pack')
    if os.path.exists(p_pack):
        logger.info("Installing the pack package data")
        pack_dest = os.path.join(packs_dir, pname)
        if os.path.exists(pack_dest):
            logger.info("Removing previous pack install at %s" % pack_dest)
            shutil.rmtree(pack_dest)
        # shutil will do the create dir
        shutil.copytree(p_pack, pack_dest)
        logger.info("Copy done in the pack directory %s" % pack_dest)

    # Now install the etc from $TMP$/etc/* to $ETC$/etc/*
    p_etc = os.path.join(tmpdir, 'etc')
    if os.path.exists(p_etc):
        logger.info("Merging the etc package data into your etc directory")
        # We don't use shutils because it NEED etc_dir to be non existant...
        # Come one guys..... cp is not as terrible as this...
        _copytree(p_etc, etc_dir)
        logger.info("Copy done in the etc directory %s" % etc_dir)


    # Now install the tests from $TMP$/tests/* to $TESTS$/tests/*
    # if the last one is specified on the configuration file (optionnal)
    p_tests = os.path.join(tmpdir, 'test')
    if os.path.exists(p_tests) and os.path.exists(test_dir):
        logger.info("Merging the test package data into your test directory")
        # We don't use shutils because it NEED etc_dir to be non existant...
        # Come one guys..... cp is not as terrible as this...
        logger.debug("COPYING %s into %s" % (p_tests, test_dir))
        _copytree(p_tests, test_dir)
        logger.info("Copy done in the test directory %s" % test_dir)

    cprint('OK ', 'green', end='')
    cprint('%s' % pname)





def do_install(pname, local):
    raw = ''
    if local:
        pname, raw = grab_local(pname)

    if not local:
        raw = grab_package(pname)
    install_package(pname, raw)




exports = {
    do_publish : {
        'keywords': ['publish'],
        'args': [
            {'name' : 'to_pack', 'default':'.', 'description':'Package directory. Default to .'},

            ],
        'description': 'Publish a package on shinken.io. Valid api key required'
        },

    do_search  : {'keywords': ['search'], 'args': [],
                  'description': 'Search a package on shinken.io by looking at its keywords'
                  },
    do_install : {
        'keywords': ['install'],
        'args': [
            {'name' : 'pname', 'description':'Package to install'},
            {'name' : '--local', 'description':'Use a local directory instead of the shinken.io version', 'type': 'bool'},
            ],
        'description' : 'Grab and install a package from shinken.io'
        },

    }
