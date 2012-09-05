import optparse
import time
import sys
import os
import zipfile
import shutil
import glob


try:
    import shinken
    from shinken.bin import VERSION
except ImportError:
    # If importing shinken fails, try to load from current directory
    # or parent directory to support running without installation.
    # Submodules will then be loaded from there, too.
    import imp
    imp.load_module('shinken', *imp.find_module('shinken', [os.path.realpath("."), os.path.realpath(".."), os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), "..")]))
    from shinken.bin import VERSION

from shinken.objects.pack import Pack, Packs

from shinken.log import logger, DEBUG
from shinken.objects.config import Config

logger.setLevel(DEBUG)


class Dummy():
    def __init__(self):
        pass

    def add(self, obj):
        pass

logger.load_obj(Dummy())

from pymongo.connection import Connection

VERSION = '0.1'
TMP_PATH = '/tmp/pack_analysing'
PACKS_HOME = '/opt/packs'


def do_list(table):
    search = table.find()
    for s in search:
        print "Id:%s Name:%s state:%s user:%s filepath:%s path:%s" % (s.get('_id'), s.get('pack_name'), s.get('state'), s.get('user'), s.get('filepath'), s.get('path'))


def check_tmp():
    if os.path.exists(TMP_PATH):
        shutil.rmtree(TMP_PATH)
    os.mkdir(TMP_PATH)


def refuse_pack(table, pack, comment):
    u = table.find_one({'_id': pack})
    if not u:
        print 'ERROR: cannot find pack %s' % pack
        sys.exit(2)
    u['state'] = 'refused'
    u['moderation_comment'] = comment
    table.save(u)
    print "OK: pack %s is refused" % pack


def delete_pack(table, pack):
    u = table.find_one({'_id': pack})
    if not u:
        print 'ERROR: cannot find pack %s' % pack
        sys.exit(2)
    table.remove({'_id': pack})
    print "OK: pack %s is removed" % pack


def analyse_pack(table, pack):
    p = table.find_one({'_id': pack})
    filepath = p['filepath']
    print "Analysing pack"
    if not zipfile.is_zipfile(filepath):
        print "ERROR: the pack %s is not a zip file!" % filepath
        sys.exit(2)

    check_tmp()
    path = os.path.join(TMP_PATH, pack)
    print "UNFLATING PACK INTO", path
    f = zipfile.ZipFile(filepath)
    f.extractall(path)

    packs = Packs({})
    packs.load_file(path)
    packs = [i for i in packs]
    if len(packs) > 1:
        print "ERROR: the pack %s got too much .pack file in it!" % pack
        p['moderation_comment'] = "ERROR: no valid .pack in the pack"
        p['state'] = 'refused'
        table.save(p)
        sys.exit(2)

    if len(packs) == 0:
        print "ERROR: no valid .pack in the pack %s" % pack
        p['state'] = 'refused'
        p['moderation_comment'] = "ERROR: no valid .pack in the pack"
        table.save(p)
        sys.exit(2)

    # Now we move the pack to it's final directory
    dest_path = os.path.join(PACKS_HOME, pack)
    print "Will copy the tree in the pack tree", dest_path
    if os.path.exists(dest_path):
        shutil.rmtree(dest_path)
    shutil.copytree(path, dest_path)

    pck = packs.pop()
    print "We read pack", pck.__dict__
    # Now we can update the db pack entry
    p['pack_name'] = pck.pack_name
    p['description'] = pck.description
    p['macros'] = pck.macros
    p['path'] = pck.path
    p['templates'] = pck.templates
    if p['path'] == '/':
        p['path'] = '/uncategorized'
    p['doc_link'] = pck.doc_link
    if p['state'] == 'pending':
        p['state'] = 'ok'
    print "We want to save the object", p
    table.save(p)




if __name__ == '__main__':

    parser = optparse.OptionParser(
        """%prog [options] [-H server] [-d database]""",
        version="%prog " + VERSION)
    parser.add_option('-H', '--host',
                      dest="host", help=('Mongodb host'))
    parser.add_option('-d', '--database', dest="database",
                      help="""Mongodb database""")
    parser.add_option('-l', '--list', dest='do_list', action='store_true',
                      help='List packs')
    parser.add_option('--refuse', dest='do_refuse', action='store_true',
                      help='refuse a pack')
    parser.add_option('--delete', dest='do_delete', action='store_true',
                      help='Delete a pack')
    parser.add_option('-p', '--pack', dest='pack',
                      help='Pack')
    parser.add_option('-c', '--comment', dest='comment',
                      help='Set a comment')
    parser.add_option('--analyse', dest='do_analyse', action='store_true',
                      help='Analyse a pack')

    opts, args = parser.parse_args()

    host = opts.host or 'localhost'
    database = opts.database or 'hostd'

    con = Connection(host)
    db = getattr(con, database)
    print "Connexion OK", db
    table = getattr(db, 'packs')
    print "Table", table

    pack = ''
    mode = 'list'
    comment = opts.comment or ''

    if opts.pack:
        pack = opts.pack

    if opts.do_list:
        mode = 'list'
        do_list(table)

    if opts.do_refuse:
        mode = 'refuse'
        if not pack:
            print "ERROR: no pack filled"
            sys.exit(2)
        refuse_pack(table, pack, comment)

    if opts.do_delete:
        mode = 'delete'
        if not pack:
            print "ERROR: no pack filled"
            sys.exit(2)
        delete_pack(table, pack)

    if opts.do_analyse:
        mode = 'delete'
        if not pack:
            print "ERROR: no pack filled"
            sys.exit(2)
        analyse_pack(table, pack)
