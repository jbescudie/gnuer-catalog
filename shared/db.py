"""DB module.


Copyright 2023 Jean-Baptiste Escudié


This program is Free Software. You can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or (at
your option) any later version.
"""
import sqlite3
import os
import typing


def session(schemas: typing.Sequence):
    '''opens a sqlite3 connection with in memory as main + specified attached schemas.

    *schemas*: sequence of schema names to be attached. Corresponding URIs will be looked up from env variables matching the pattern <SCHEMA>_SQLITE_URI.
    
    :returns: an instantiated sqlite3.Connection
    '''

    conn = sqlite3.connect(":memory:",uri=True)
    schema_to_uri = schemas_uris_from_env()
    attach_stmts = tuple(
        f'''ATTACH "{schema_to_uri[schema]}" as "{schema}" ; '''
        for schema in schemas
    )
    script = '\n'.join(attach_stmts)
    conn.executescript(script)

    return conn


def schemas_uris_from_env() -> typing.Mapping:
    '''returns a mapping[schemas,URI] from enviroment variables matching the pattern <SCHEMA>_SQLITE_URI'''
    suffix="_SQLITE_URI"
    return {
        k[:-len(suffix)]:v
        for k,v in os.environ.items()
        if k.endswith(suffix)
    }



def test_can_open_default_session():
    schemas = ("DATA","META")
    connection = session(schemas)
    connection.close()
    
    
