"""
db.py -  Database utilities
"""
import datetime
import os
import re
import json
import logging
from django.db import connection, transaction

from django.conf import settings


class Db:
    def __init__(self, dbconf=None):
        if dbconf is None:
            dbconf = "default"
        self.dbconf = dbconf
        self.parms = settings.DATABASES[dbconf]
        self.conn = None

    def connectMaybe(self):
        if self.conn is not None:
            return
        return connection

    def getNewConnection(self):
        return connection

    def escape_string(self, s):
        return connection.ops.quote_name(s)

    def execute(self, qry, args, connection=None):
        cursor = None
        if connection is None:
            self.connectMaybe()
            cursor = self.conn.cursor()
        else:
            cursor = connection.cursor()
        # replace placeholder if in postgres mode
        if self.parms["ENGINE"] == "django.db.backends.postgresql_psycopg2":
            qry = qry.replace("?", "%s")
        if settings.DEBUG_QUERY:
            logging.info("[execute] " + qry % args)
        cursor.execute(qry, args)
        return cursor

    def doTransaction(self, qry, args):
        connection = self.getNewConnection()
        cursor = self.execute(qry, args, connection)
        transaction.commit_unless_managed()

    # same as getRows but returns the results in a dict index by the 1st val
    def getIndexedRows(self, qry, args):
        rows = self.getRows(qry, args)
        x = None if rows is None else {}
        for row in rows:
            if row[0] in x:
                x[row[0]].append(row)
            else:
                x[row[0]] = [row]
        return x

    def getVal(self, qry, args):
        connection = self.getNewConnection()
        cursor = self.execute(qry, args, connection)
        row = cursor.fetchone()
        cursor.close()
        if row is None:
            return None
        return row[0]

    def getRow(self, qry, args):
        connection = self.getNewConnection()
        cursor = self.execute(qry, args, connection)
        row = cursor.fetchone()
        cursor.close()
        return row

    def getRows(self, qry, args):
        if settings.DEBUG_QUERY:
            debug_query = qry.replace("?", "%s")
            logging.info("[getRows] " + debug_query % args)
        connection = self.getNewConnection()
        cursor = self.execute(qry, args, connection)
        rows = cursor.fetchall()
        cursor.close()
        return rows

    def getRowsByName(self, c, names, container):
        # c: a database cursor, on which a sql query has bveen carried out
        # names: A mapping: id_desired -> SQL fieldname (SQL fieldname can be None if we want same as id_desired)

        # build dict:
        d = {}
        for i in range(0, len(c.description)):
            d[c.description[i][0]] = i
        rows = c.fetchall()
        for r in rows:
            a = {}
            for n in names:
                sqlfield = n if names[n] is None else names[n]
                a[n] = r[d[sqlfield]]
            container.append(a)
        return d, rows
