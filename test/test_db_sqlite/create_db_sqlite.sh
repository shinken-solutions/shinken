#!/bin/sh
cd test_db_sqlite
if [ ! -f test_db_sqlite.sqlite ];then 
    sqlite3 test_db_sqlite.sqlite  < test_db_sqlite.sql
fi
