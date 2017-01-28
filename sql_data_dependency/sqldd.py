from __future__ import print_function

import argparse
import json
import os
import shlex
import subprocess
import sys

from collections import defaultdict, namedtuple
from pprint import pprint
from sqlalchemy import create_engine, inspect


class SqlDatabaseDependencyManager(object):

    def __init__(self, app_args):
        self.app_args = app_args

        # Make these global for now
        self.engine = create_engine('mysql://{username}:{password}@{server}:{port}/{database}'.format(
            username=app_args.username,
            password=app_args.password,
            server=app_args.server,
            port=app_args.port,
            database=app_args.database
        ))
        self.inspector = inspect(self.engine)

    def get_database_dependencies(self, table_column_roots, already_explored=defaultdict(lambda: [])):
        dependencies = defaultdict(lambda: [])

        for table, primary_keys in table_column_roots.iteritems():
            for primary_key in primary_keys:

                # Don't explore if we've already done it
                if primary_key in already_explored[table]:
                    continue

                # Add this to our "already explored" set
                already_explored[table].append(primary_key)
                row_depdencies = self.get_row_dependencies(table, primary_key, already_explored=already_explored)

                for row_dependency_table, row_dependency_primary_keys in row_depdencies.iteritems():
                    # Add to our final result set
                    current_row_dependency_primary_keys = dependencies[row_dependency_table]
                    dependencies[row_dependency_table] = \
                        current_row_dependency_primary_keys + list(set(row_dependency_primary_keys) - set(current_row_dependency_primary_keys))

        return dependencies


    def get_row_dependencies(self, table, primary_key, already_explored=defaultdict(lambda: [])):
        # Does the table have any foreign keys, if not, there are no downstream dependencies so return right away.
        foreign_keys = self.inspector.get_foreign_keys(table)
        if not foreign_keys:
            return {}

        # Otherwise, get the value for all foreign keys in that row
        ForeignKey = namedtuple('ForeignKey', ['table', 'column'])

        column_foreign_key_map = {}
        for foreign_key in foreign_keys:
            # Dont handle compound keys right now
            if len(foreign_key['constrained_columns']) != 1 or len(foreign_key['referred_columns']) != 1:
                raise Exception('Too many columns referenced in foreign key')

            # Ensure the FK is a PK of the referenced table
            referenced_pk = self.inspector.get_pk_constraint(foreign_key['referred_table'])
            if set(referenced_pk['constrained_columns']) != set(foreign_key['referred_columns']):
                raise Exception('Primary key doesnt match foreign key constraint')

            # Create a mapping
            column_foreign_key_map[foreign_key['constrained_columns'][0]] = \
                ForeignKey(table=foreign_key['referred_table'], column=foreign_key['referred_columns'][0])

        # Each of those keys becomes a dependency now, so add to our return set
        primary_key_column = self.inspector.get_pk_constraint(table)['constrained_columns'][0]
        table_results = self.engine.execute('select {columns} from {table} where {primary_key_column}={primary_key}'.format(
            columns=','.join(column_foreign_key_map.keys()),
            table=table,
            primary_key_column=primary_key_column,
            primary_key=primary_key))

        table_result = None

        try:
            for row in table_results:
                table_result = row
                break
        finally:
            table_results.close()

        dependencies = defaultdict(lambda: [])
        for column, foreign_key in column_foreign_key_map.iteritems():
            if table_result[column] is not None:
                dependencies[foreign_key.table].append(table_result[column])

        # Iterate over each of those dependencies, recursively call this fn and add to return set
        downstream_dependencies = self.get_database_dependencies(dependencies, already_explored=already_explored)

        for downstream_dep_table, downstream_dep_keys in downstream_dependencies.iteritems():
            dependencies[downstream_dep_table].extend(downstream_dep_keys)
            dependencies[downstream_dep_table] = list(set(dependencies[downstream_dep_table]))

        # Finally, return it all
        return dependencies

    def mysqldump_statements(self, table_key_map, server, username, password, port, database):
        mysqldump_statements = []

        for table, primary_keys in table_key_map.iteritems():
            primary_key_column = self.inspector.get_pk_constraint(table)['constrained_columns'][0]

            mysqldump_where = '{primary_key_column} in ({primary_key})'.format(
                primary_key_column=primary_key_column,
                primary_key=','.join([str(pk) if not isinstance(pk, basestring) else '\'{}\''.format(pk) for pk in primary_keys]))

            mysqldump_statements.append('MYSQL_PWD={password} mysqldump -h {server} -u{username} --port={port} --single-transaction {database} {table} --where="{where}"'.format(
                username=username,
                password=password,
                server=server,
                port=port,
                database=database,
                table=table,
                where=mysqldump_where
            ))

        return mysqldump_statements

    def create_mysqldump(self, table_rows):
        # Dump MySQL if we can
        if self.app_args.mysqldump:
            statements = self.mysqldump_statements(
                table_rows,
                self.app_args.server,
                self.app_args.username,
                self.app_args.password,
                self.app_args.port,
                self.app_args.database)

            try:
                # Make sure mysqldump is available on the PATH
                with open(os.devnull, 'w') as devnull:
                    subprocess.check_call(['mysqldump', '--help'], stdout=devnull)
            except Exception:
                print('mysqldump not installed', file=sys.stderr)
                sys.exit(1)

            try:
                os.remove('dump.sql')
                with open('dump.sql', 'w+'):
                    pass
            except OSError:
                pass

            with open('dump.sql', 'a+') as dump_file:
                if self.app_args.mysqldump_table_defs:
                    subprocess.check_call(
                        'MYSQL_PWD={password} mysqldump -h {server} -u{username} --port={port} --single-transaction --no-data {database}'.format(
                            server=self.app_args.server,
                            username=self.app_args.username,
                            password=self.app_args.password,
                            port=self.app_args.port,
                            database=self.app_args.database
                        ), shell=True, stdout=dump_file)

                for statement in statements:
                    subprocess.check_call(statement, shell=True, stdout=dump_file)

            if self.app_args.mysqldump_gzip:

                try:
                    os.remove('dump.sql.gz')
                except OSError:
                    pass
                subprocess.check_call(['gzip', 'dump.sql'])


class SqlDataDependencyCommand(object):

    @classmethod
    def parse_args(cls):

        ######################################################
        # Parse the Args
        ######################################################
        parser = argparse.ArgumentParser(
            description='SQL Data Dependency Tool',
            epilog='One of either ([table][primary_key]) or [--json] is required.')

        # Primary key / table def args
        parser.add_argument('table', nargs='?', help='Table to analyze')
        parser.add_argument('primary_key', nargs='?', help='Primary key for row in table to analyze')
        parser.add_argument('--json', dest='json_file', help='File containing tables and rows to analyze')

        # Database specific args
        parser.add_argument('--server', default='127.0.0.1', help='Database server')
        parser.add_argument('--port', default=3306, help='Database port')
        parser.add_argument('--database', required=True, help='Database name')
        parser.add_argument('--username', default='root', help='Database username')
        parser.add_argument('--password', default='password', help='Database password')

        # MySQLDump related args
        parser.add_argument('--mysqldump', action='store_true', help='Generate a mysqldump file of all dependencies')
        parser.add_argument('--mysqldump_gzip', action='store_true', help='GZip the mysqldump output')
        parser.add_argument(
            '--mysqldump_table_defs', action='store_true',
            help='Dump _all_ table defs, even those without dependencies.  Useful for constructing skeleton DBs.')
        return parser.parse_args()

    @classmethod
    def process(cls):
        # Get the args
        args = cls.parse_args()

        sql_data_dependency_manager = SqlDatabaseDependencyManager(args)

        if args.json_file is not None:
            with open(args.json_file) as json_file:
                table_dependency_roots = json.load(json_file)

        else:
            if args.table is None or args.primary_key is None:
                raise Exception('Either a JSON file, or a single table/PK must be supplied.')
            table_dependency_roots = {args.table: [args.primary_key]}

        dependencies = sql_data_dependency_manager.get_database_dependencies(table_dependency_roots)

        # Combine with the given params
        for root_table, root_keys in table_dependency_roots.iteritems():
            dependencies[root_table].extend(root_keys)
            dependencies[root_table] = list(set(dependencies[root_table]))
            dependencies[root_table].sort()

        # If we need to do the MySQL dump, do it here
        sql_data_dependency_manager.create_mysqldump(dependencies)

        # Print all the goodies
        pprint(dict(dependencies))


if __name__ == '__main__':
    command = SqlDataDependencyCommand()
    command.process()
