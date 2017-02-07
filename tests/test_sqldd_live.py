import pytest

from sql_data_dependency.sqldd import SqlDatabaseDependencyManager
from sqlalchemy import create_engine


live = pytest.mark.skipif(
    not pytest.config.getoption("--runlivedb"),
    reason="need --runlivedb option to run"
)


@live
def test_simple_dump():
    # This test assumes a database call sqldd_db, user of root/password
    engine = create_engine('mysql://root:password@127.0.0.1:3306/sqldd_db')
    with open('tests/test_sqldd.sql', 'r') as sql_file:
        sql_commands = sql_file.read()
        engine.execute(sql_commands)

    # Given this, invoke the manager
    manager = SqlDatabaseDependencyManager(
        server='127.0.0.1', database='sqldd_db', username='root', password='password', port=3306)

    row_deps = manager.get_row_dependencies('A', 53)
    assert sorted(row_deps.keys()) == ['D', 'M']
    assert sorted(row_deps['D']) == [1, 2, 20]
    assert sorted(row_deps['M']) == [48]
