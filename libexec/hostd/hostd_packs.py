import optparse
import time
import sys
import os
import zipfile
import shutil

from pymongo.connection import Connection

VERSION = '0.1'
TMP_PATH = '/tmp/pack_analysing'

def do_list(table):
    search = table.find()
    for s in search:
        print "Pack: %s state:%s user:%s" % (s.get('_id'), s.get('state'), s.get('user'))


def check_tmp():
    if os.path.exists(TMP_PATH):
        shutil.rmtree(TMP_PATH)
    os.mkdir(TMP_PATH)


def validate_pack(table, pack):
    u = table.find_one({'_id' : pack})
    if not u:
        print 'ERROR : cannot find pack %s' % pack
        sys.exit(2)
    u['state'] = 'validated'
    table.save(u)
    print "OK : pack %s is validated" % pack



def refuse_pack(table, pack, comment):
    u = table.find_one({'_id' : pack})
    if not u:
        print 'ERROR : cannot find pack %s' % pack
        sys.exit(2)
    u['state'] = 'refused'
    u['moderation_comment'] = comment
    table.save(u)
    print "OK : pack %s is refused" % pack


def delete_pack(table, pack):
    u = table.find_one({'_id' : pack})
    if not u:
        print 'ERROR : cannot find pack %s' % pack
        sys.exit(2)
    table.remove({'_id' : pack})
    print "OK : pack %s is removed" % pack



def analyse_pack(table, pack):
    print "Analysing pack"
    if not zipfile.is_zipfile(pack):
        print "ERROR : the pack %s is not a zip file!" % pack
        sys.exit(2)

    check_tmp()
    print "UNFLATING PACK INTO", TMP_PATH
    f = zipfile.ZipFile(pack)
    f.extractall(TMP_PATH)
    

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
    parser.add_option('--validate', dest='do_validate', action='store_true',
                      help='validate a user')
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

    if opts.do_validate:
        mode = 'validate'
        if not pack:
            print "ERROR : no pack filled"
            sys.exit(2)
        validate_pack(table, pack)

    if opts.do_refuse:
        mode = 'refuse'
        if not pack:
            print "ERROR : no pack filled"
            sys.exit(2)
        refuse_pack(table, pack, comment)

    if opts.do_delete:
        mode = 'delete'
        if not pack:
            print "ERROR : no pack filled"
            sys.exit(2)
        delete_pack(table, pack)

    if opts.do_analyse:
        mode = 'delete'
        if not pack:
            print "ERROR : no pack filled"
            sys.exit(2)
        analyse_pack(table, pack)

