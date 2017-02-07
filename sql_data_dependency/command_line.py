from __future__ import print_function

import argparse
import json
import sys

from six import iteritems
from sql_data_dependency.sqldd import SqlDatabaseDependencyManager


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

        # Output args
        parser.add_argument('--pretty', action='store_true', help='Pretty print the output')

        # Sqldump related args
        parser.add_argument('--sqldump', action='store_true', help='Generate a sql dump file of all dependencies')
        parser.add_argument(
            '--sqldump_table_defs', action='store_true', default=False,
            help='Dump _all_ table defs, even those without dependencies.  Useful for constructing skeleton DBs.')
        args = parser.parse_args()

        # By default, interpret as an integer if possible
        try:
            args.primary_key = int(args.primary_key)
        except:
            pass

        return args

    @classmethod
    def process(cls):
        # Get the args
        args = cls.parse_args()

        sql_data_dependency_manager = SqlDatabaseDependencyManager(
            server=args.server,
            database=args.database,
            username=args.username,
            password=args.password,
            port=args.port
        )

        if args.json_file is not None:
            with open(args.json_file) as json_file:
                table_dependency_roots = json.load(json_file)

        else:
            if args.table is None or args.primary_key is None:
                raise Exception('Either a JSON file, or a single table/PK must be supplied.')
            table_dependency_roots = {args.table: [args.primary_key]}

        dependencies = sql_data_dependency_manager.get_database_dependencies(table_dependency_roots)
        print(dependencies)
        # Combine with the given params
        for root_table, root_keys in iteritems(table_dependency_roots):
            dependencies[root_table].extend(root_keys)
            dependencies[root_table] = list(set(dependencies[root_table]))
            dependencies[root_table].sort()

        # If we need to do the MySQL dump, do it here
        if args.sqldump:
            dump = sql_data_dependency_manager.create_mysqldump(
                dependencies, dump_all_table_definitions=args.sqldump_table_defs)
            print(dump, file=sys.stdout)
        else:
            # Print all the goodies
            if args.pretty:
                map(lambda v: v.sort(), dependencies.values())
                json_dependencies = json.dumps(dict(dependencies), indent=4, sort_keys=True)
            else:
                json_dependencies = json.dumps(dict(dependencies))

            print(json_dependencies)


def main():
    command = SqlDataDependencyCommand()
    command.process()
