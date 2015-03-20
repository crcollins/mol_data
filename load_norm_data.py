import sqlite3

import matplotlib.pyplot as plt

from utils import OPTSETS, STRUCTSETS, CALCSETS, PROPS, input_check


def load_data_from_db(prop=None, optsets=None, structsets=None, calcsets=None):
    input_check(
        prop=prop, optsets=optsets, structsets=structsets, calcsets=calcsets)

    where_cond1 = "structset in %s" % (tuple(structsets), )
    where_cond2 = "optset in %s and calcset in %s" % (
        tuple(optsets), tuple(calcsets))
    where_cond1 = where_cond1.replace(",)", ")")
    where_cond2 = where_cond2.replace(",)", ")")

    # The double nested selects are to fix an issue where the empty data points were
    # getting joined together into the last empty data point.
    string = """
    SELECT a.name, group_concat(a.prop)
    FROM (
    SELECT d.name_id, d.name, IFNULL(data.{prop}, '') as prop
    FROM (
        SELECT names.id as name_id, names.name, ds.id as ds_id
        FROM (SELECT id, name FROM names WHERE {where1}) as names
        CROSS JOIN (SELECT id FROM datasets WHERE {where2}) as ds
        ) as d
    LEFT JOIN data
        ON d.name_id = data.name_id and d.ds_id = data.dataset_id
    ) as a
    GROUP BY a.name_id;
    """.format(prop=prop, where1=where_cond1, where2=where_cond2)

    data = []
    with sqlite3.connect("database.sqlite") as conn:
        for name, values in conn.execute(string):
            try:
                data.append(
                    (name, [float(x) if x else None for x in values.split(',')]))
            except:
                pass

    string = "SELECT optset, calcset FROM datasets WHERE %s" % (where_cond2, )
    columns = [x for x in conn.execute(string)]
    return data, columns


def get_missing_data(have_geom=False):
    if have_geom:
        addon = """
        AND (d.name || d.optset) IN (
            SELECT DISTINCT (n.name || ds.optset) FROM data
            INNER JOIN names as n
                ON data.name_id = n.id
            INNER JOIN datasets as ds
                ON data.dataset_id = ds.id
            )
        """
    else:
        addon = ""

    string = """
    SELECT d.name, d.optset, d.calcset
    FROM (
        SELECT names.id as name_id, names.name, ds.id as ds_id, ds.optset, ds.calcset
        FROM (SELECT id, name FROM names) as names
        CROSS JOIN (SELECT id, optset, calcset FROM datasets) as ds
        ) as d
    LEFT JOIN data
        ON d.name_id = data.name_id and d.ds_id = data.dataset_id
    WHERE
        data.homo IS NULL
        %s
    ;
    """ % addon

    with sqlite3.connect("database.sqlite") as conn:
        return [x for x in conn.execute(string)]


def compare_optimizations(prop=None, optsets=None, structsets=None, calcsets=None):
    data = []
    for x in optsets:
        p, _ = load_data_from_db(
            prop=prop, optsets=[x], structsets=structsets, calcsets=calcsets)
        names, numbers = zip(*p)
        data.append(sum(numbers, []))
    return data, optsets


def compare_methods(prop=None, optsets=None, structsets=None, calcsets=None):
    data = []
    for x in calcsets:
        p, _ = load_data_from_db(
            prop=prop, optsets=optsets, structsets=structsets, calcsets=[x])
        names, numbers = zip(*p)
        data.append(sum(numbers, []))
    return data, calcsets


def plot_data(data, labels, title=''):
    print [len([y for y in x if y is not None]) for x in data]
    for x, label in zip(data, labels):
        plt.plot(data[1], x, '.', label=label, alpha=.1)
    plt.title(title)
    plt.legend(loc='best')
    plt.show()

if __name__ == "__main__":
    from build_database import export_database

    try:
        p, col = load_data_from_db(prop="homo", optsets=['b3lyp'], structsets=['O'], calcsets=['b3lyp'])
    except sqlite3.OperationalError:
        export_database()

    for prop in PROPS:
        data, labels = compare_optimizations(prop=prop, optsets=OPTSETS, structsets=['O'], calcsets=CALCSETS)
        plot_data(data, labels)

    missing = get_missing_data(have_geom=False)
    print len(missing)