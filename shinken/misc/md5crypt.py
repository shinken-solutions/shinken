#########################################################
# md5crypt.py
#
# 0423.2000 by michal wallace http://www.sabren.com/
# based on perl's Crypt::PasswdMD5 by Luis Munoz (lem@cantv.net)
# based on /usr/src/libcrypt/crypt.c from FreeBSD 2.2.5-RELEASE
#
# MANY THANKS TO
#
#  Carey Evans - http://home.clear.net.nz/pages/c.evans/
#  Dennis Marti - http://users.starpower.net/marti1/
#
#  For the patches that got this thing working!
#
#########################################################
"""md5crypt.py - Provides interoperable MD5-based crypt() function

SYNOPSIS

import md5crypt.py

cryptedpassword = md5crypt.md5crypt(password, salt);

DESCRIPTION

unix_md5_crypt() provides a crypt()-compatible interface to the
rather new MD5-based crypt() function found in modern operating systems.
It's based on the implementation found on FreeBSD 2.2.[56]-RELEASE and
contains the following license in it:

 "THE BEER-WARE LICENSE" (Revision 42):
 <phk@login.dknet.dk> wrote this file.  As long as you retain this notice you
 can do whatever you want with this stuff. If we meet some day, and you think
 this stuff is worth it, you can buy me a beer in return.   Poul-Henning Kamp

apache_md5_crypt() provides a function compatible with Apache's
.htpasswd files. This was contributed by Bryan Hart <bryan@eai.com>.

"""

MAGIC = '$1$'  # Magic string
ITOA64 = "./0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

from hashlib import md5


def to64(v, n):
    ret = ''
    while n - 1 >= 0:
        n = n - 1
        ret = ret + ITOA64[v & 0x3f]
        v = v >> 6
    return ret


def apache_md5_crypt(pw, salt):
    # change the Magic string to match the one used by Apache
    return unix_md5_crypt(pw, salt, '$apr1$')


def unix_md5_crypt(pw, salt, magic=None):

    if magic is None:
        magic = MAGIC

    # Take care of the magic string if present
    if salt[:len(magic)] == magic:
        salt = salt[len(magic):]

    # salt can have up to 8 characters:
    import string
    salt = string.split(salt, '$', 1)[0]
    salt = salt[:8]

    ctx = pw + magic + salt

    final = md5(pw + salt + pw).digest()

    for pl in range(len(pw), 0, -16):
        if pl > 16:
            ctx = ctx + final[:16]
        else:
            ctx = ctx + final[:pl]
    # Now the 'weird' xform (??)

    i = len(pw)
    while i:
        if i & 1:
            ctx = ctx + chr(0)  # if ($i & 1) { $ctx->add(pack("C", 0)); }
        else:
            ctx = ctx + pw[0]
        i = i >> 1

    final = md5(ctx).digest()

    # The following is supposed to make
    # things run slower.

    # my question: WTF???

    for i in range(1000):
        ctx1 = ''
        if i & 1:
            ctx1 = ctx1 + pw
        else:
            ctx1 = ctx1 + final[:16]

        if i % 3:
            ctx1 = ctx1 + salt

        if i % 7:
            ctx1 = ctx1 + pw

        if i & 1:
            ctx1 = ctx1 + final[:16]
        else:
            ctx1 = ctx1 + pw

        final = md5(ctx1).digest()
    # Final xform

    passwd = ''

    passwd = passwd + to64((int(ord(final[0])) << 16)
                           | (int(ord(final[6])) << 8)
                           | (int(ord(final[12]))), 4)

    passwd = passwd + to64((int(ord(final[1])) << 16)
                           | (int(ord(final[7])) << 8)
                           | (int(ord(final[13]))), 4)

    passwd = passwd + to64((int(ord(final[2])) << 16)
                           | (int(ord(final[8])) << 8)
                           | (int(ord(final[14]))), 4)

    passwd = passwd + to64((int(ord(final[3])) << 16)
                           | (int(ord(final[9])) << 8)
                           | (int(ord(final[15]))), 4)

    passwd = passwd + to64((int(ord(final[4])) << 16)
                           | (int(ord(final[10])) << 8)
                           | (int(ord(final[5]))), 4)

    passwd = passwd + to64((int(ord(final[11]))), 2)

    return magic + salt + '$' + passwd

# assign a wrapper function:
md5crypt = unix_md5_crypt

if __name__ == "__main__":
    print unix_md5_crypt("cat", "hat")
