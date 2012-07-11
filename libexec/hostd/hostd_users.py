import optparse
import time
import sys
import os

from pymongo.connection import Connection

VERSION = '0.1'


def do_list(table):
    search = table.find()
    for s in search:
        print "User: %s validated:%s email:%s" % (s.get('username'), s.get('validated'), s.get('email'))


def validate_user(table, username):
    u = table.find_one({'username': username})
    if not u:
        print 'ERROR: cannot find user %s' % username
        sys.exit(2)
    u['validate'] = True
    table.save(u)
    print "OK: user %s is validated" % username


def delete_user(table, username):
    u = table.find_one({'username': username})
    if not u:
        print 'ERROR: cannot find user %s' % username
        sys.exit(2)
    table.remove({'username': username})
    print "OK: user %s is deleted"


if __name__ == '__main__':

    parser = optparse.OptionParser(
        """%prog [options] [-H server] [-d database]""",
        version="%prog " + VERSION)
    parser.add_option('-H', '--host',
                      dest="host", help=('Mongodb host'))
    parser.add_option('-d', '--database', dest="database",
                      help="""Mongodb database""")
    parser.add_option('-l', '--list', dest='do_list', action='store_true',
                      help='List users')
    parser.add_option('--validate', dest='do_validate', action='store_true',
                      help='validate a user')
    parser.add_option('--delete', dest='do_delete', action='store_true',
                      help='delete a user')
    parser.add_option('-u', '--user', dest='username',
                      help='Username')

    opts, args = parser.parse_args()

    host = opts.host or 'localhost'
    database = opts.database or 'hostd'

    con = Connection(host)
    db = getattr(con, database)
    print "Connexion OK", db
    table = getattr(db, 'users')
    print "Table", table

    username = ''
    mode = 'list'

    if opts.username:
        username = opts.username

    if opts.do_list:
        mode = 'list'
        do_list(table)

    if opts.do_validate:
        mode = 'validate'
        if not username:
            print "ERROR: no user filled"
            sys.exit(2)
        validate_user(table, username)

    if opts.do_delete:
        if not username:
            print "ERROR: no user filled"
            sys.exit(2)
        delete_user(table, username)
