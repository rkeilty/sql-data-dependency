from __future__ import print_function

import os
import shlex
import subprocess
import sys

from collections import defaultdict, namedtuple
from sqlalchemy import create_engine, inspect
from six import iteritems


class SqlDatabaseDependencyManager(object):

    def __init__(self, server=None, database=None, username=None, password=None, port=None):
        self._server = server
        self._database = database
        self._username = username
        self._password = password
        self._port = port

        # Make these global for now
        self.engine = create_engine('mysql://{username}:{password}@{server}:{port}/{database}'.format(
            username=self._username,
            password=self._password,
            server=self._server,
            port=self._port,
            database=self._database
        ))
        self.inspector = inspect(self.engine)

    def get_database_dependencies(self, table_column_roots, already_explored=defaultdict(lambda: [])):
        dependencies = defaultdict(lambda: [])

        for table, primary_keys in iteritems(table_column_roots):
            for primary_key in primary_keys:

                # Don't explore if we've already done it
                if primary_key in already_explored[table]:
                    continue

                # Add this to our "already explored" set
                already_explored[table].append(primary_key)
                row_depdencies = self.get_row_dependencies(table, primary_key, already_explored=already_explored)

                for row_dependency_table, row_dependency_primary_keys in iteritems(row_depdencies):
                    # Add to our final result set
                    current_row_dependency_primary_keys = dependencies[row_dependency_table]
                    dependencies[row_dependency_table] = \
                        current_row_dependency_primary_keys + \
                        list(set(row_dependency_primary_keys) - set(current_row_dependency_primary_keys))

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

        # Be really cheap here, if we can't coerce the PK into an integer, than cast it as a string
        try:
            int(primary_key)
        except:
            primary_key = '"{}"'.format(primary_key)

        table_results = \
            self.engine.execute('select {columns} from {table} where {primary_key_column}={primary_key}'.format(
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

        if table_result is None:
            print('No result for table PK "{}": {}'.format(table, primary_key))
            sys.exit(1)

        dependencies = defaultdict(lambda: [])
        for column, foreign_key in iteritems(column_foreign_key_map):
            if table_result[column] is not None:
                dependencies[foreign_key.table].append(table_result[column])

        # Iterate over each of those dependencies, recursively call this fn and add to return set
        downstream_dependencies = self.get_database_dependencies(dependencies, already_explored=already_explored)

        for downstream_dep_table, downstream_dep_keys in iteritems(downstream_dependencies):
            dependencies[downstream_dep_table].extend(downstream_dep_keys)
            dependencies[downstream_dep_table] = list(set(dependencies[downstream_dep_table]))

        # Finally, return it all
        return dependencies

    def mysqldump_statements(self, table_key_map, server, username, password, port, database):
        mysqldump_statements = []

        for table, primary_keys in iteritems(table_key_map):
            primary_key_column = self.inspector.get_pk_constraint(table)['constrained_columns'][0]

            mysqldump_where = '{primary_key_column} in ({primary_key})'.format(
                primary_key_column=primary_key_column,
                primary_key=','.join(
                    [str(pk) if not isinstance(pk, str) else '\'{}\''.format(pk) for pk in primary_keys]))

            mysqldump_statements.append(
                'mysqldump -h {server} -u {username} --port {port} --single-transaction '
                '{database} {table} --where="{where}"'.
                format(
                    username=username,
                    password=password,
                    server=server,
                    port=port,
                    database=database,
                    table=table,
                    where=mysqldump_where
                ))

        return mysqldump_statements

    def create_mysqldump(self, table_rows, dump_all_table_definitions=False):
        statements = self.mysqldump_statements(
            table_rows,
            self._server,
            self._username,
            self._password,
            self._port,
            self._database)

        try:
            # Make sure mysqldump is available on the PATH
            with open(os.devnull, 'w') as devnull:
                subprocess.check_call(['mysqldump', '--help'], stdout=devnull)
        except Exception:
            print('mysqldump not installed', file=sys.stderr)
            sys.exit(1)

        # We do this to prevent warnings when invoking our subprocess
        cmd_env = os.environ.copy()
        cmd_env['MYSQL_PWD'] = self._password
        dump = ''

        if dump_all_table_definitions:
            dump += subprocess.check_output(
                shlex.split(
                    'mysqldump -h {server} -u {username} --port {port} --single-transaction --no-data {database}'.
                    format(
                        server=self._server,
                        username=self._username,
                        port=self._port,
                        database=self._database)), env=cmd_env)
            dump += os.linesep

        for statement in statements:
            dump += subprocess.check_output(shlex.split(statement), env=cmd_env)
            dump += os.linesep

        return dump
