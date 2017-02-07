import pytest
import subprocess

from sql_data_dependency.sqldd import SqlDatabaseDependencyManager


live = pytest.mark.skipif(
    not pytest.config.getoption("--runlivedb"),
    reason="need --runlivedb option to run"
)


@live
def test_simple_dump():
    # This test assumes a database call sqldd_db, user of root/password
    subprocess.check_call('mysql -uroot -ppassword -h127.0.0.1 -P3306 sqldd_db < tests/test_sqldd.sql', shell=True)

    # Given this, invoke the manager
    manager = SqlDatabaseDependencyManager(
        server='127.0.0.1', database='sqldd_db', username='root', password='password', port=3306)

    row_deps = manager.get_row_dependencies('A', 53)
    assert sorted(row_deps.keys()) == ['D', 'M']
    assert sorted(row_deps['D']) == [1, 2, 20]
    assert sorted(row_deps['M']) == [48]
