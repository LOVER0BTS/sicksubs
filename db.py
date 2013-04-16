import os
import sys
import sqlite3
import bierdopje
from ep import Ep


def initialize(path):
    '''
    This method initializes the next database at the given path. It also sets up
    the tables and returns the created db connection.
    '''
    path = os.path.expandvars(os.path.expanduser(path))
    # create the database dir if necessary
    if not os.path.exists(os.path.dirname(path)):
        try:
            os.makedirs(os.path.dirname(path))
        except:
            print(sys.argv[0] + ' : Could not create database directory "{0}"!'.format(path))

    # then open a connection and setup the tables
    conn = sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES)

    with conn:
        c = conn.cursor()
        #test to see if the shows table exists
        test = c.execute(u'''SELECT name FROM sqlite_master
                WHERE type="table"
                AND name="eps"''').fetchall()
        if not test:
            c.execute(u'''CREATE TABLE eps(timestamp timestamp, interm_loc, final_loc, tvdbid)''')
            c.execute(u'''CREATE UNIQUE INDEX unique_eps ON eps(interm_loc)''')

        #test to see if the tvr_shows table exists
        test = c.execute(u'''SELECT name FROM sqlite_master
                WHERE type="table"
                AND name="sids"''').fetchall()
        if not test:
            c.execute(u'''CREATE TABLE sids(tvdbid, sid)''')
            c.execute(u'''CREATE UNIQUE INDEX unique_sids ON sids(tvdbid)''')

    return conn


def add_ep(conn, when, interm_loc, final_loc, tvdbid):
    with conn:
        c = conn.cursor()
        c.execute(u'''INSERT OR REPLACE INTO eps VALUES (?, ?, ?, ?)''', (when, interm_loc, final_loc, tvdbid))


def get_sid(conn, tvdbid):
    with conn:
        c = conn.cursor()
        c.execute(u'''SELECT sid FROM sids WHERE tvdbid = ?''', (tvdbid,))
        result = c.fetchone()
        if not result:
            # not in db, we have to get it from bierdopje
            sid = bierdopje.get_show_id(tvdbid)
            if sid:
                c.execute(u'''INSERT INTO sids VALUES (?, ?)''', (tvdbid, sid))
            result = sid
        else:
            result = result[0]
        return result


def get_all_eps(conn):
    with conn:
        c = conn.cursor()
        c.execute(u'''SELECT * FROM eps''')
        rows = c.fetchall()
        if rows:
            result = []
            for row in rows:
                try:
                    result.append(Ep(conn, row))
                except:
                    print(u'Could not create Ep for "{}"'.format(row))

            return result
        else:
            return []


def remove_downloaded(conn, downloaded):
    with conn:
        c = conn.cursor()
        tvdbids = [(x.tvdbid,) for x in downloaded if x.result]
        c.executemany(u'''DELETE FROM eps WHERE tvdbid = ?''', tvdbids)
        return True


def remove_single(conn, ep):
    with conn:
        c = conn.cursor()
        tvdbid = ep.tvdbid
        c.execute(u'''DELETE FROM eps WHERE tvdbid = ?''', (tvdbid,))
        return True
