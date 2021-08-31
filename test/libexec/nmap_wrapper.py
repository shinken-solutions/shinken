#!/usr/bin/env python

s = """
srv1::os=windows
srv1::osversion=2003
srv1::macvendor=Hewlett Packard
srv1::openports=135,139,445,80
srv2::os=windows
srv2::osversion=7
srv2::macvendor=VMware
srv2::openports=80,135,139,445
"""
print(s)
