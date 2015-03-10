import os
import sqlite3
from itertools import product


methods = ["b3lyp", "cam", "m06hf"]
indo_methods = ["indo_" + x for x in ["default"] + methods]

OPTSETS = ["noopt"] + [os.path.join("opt", x) for x in methods]
STRUCTSETS = ['O', 'N', "rot"]
CALCSETS = methods + indo_methods


def build_datasets_table(optsets, calcsets):
    with sqlite3.connect("database.sqlite") as conn:
        conn.execute("DROP TABLE IF EXISTS datasets")
        string = """
        CREATE TABLE datasets
        (
            id integer primary key,
            optset varchar,
            calcset varchar
        )
        """
        conn.execute(string)

        data = list(product(optsets, calcsets))
        conn.executemany('INSERT INTO datasets(optset, calcset)  VALUES (?,?)', data)
        conn.commit()


def build_names_table(names):
    with sqlite3.connect("database.sqlite") as conn:
        conn.execute("DROP TABLE IF EXISTS names")
        string = """
        CREATE TABLE names
        (
            id integer primary key,
            name varchar,
            structset varchar
        )
        """
        conn.execute(string)
        conn.commit()

        conn.executemany("INSERT INTO names(name, structset) VALUES (?, ?)", names)
        conn.commit()


def build_data_table(data):
    with sqlite3.connect("database.sqlite") as conn:
        conn.execute("DROP TABLE IF EXISTS data")
        string = """
        CREATE TABLE data
        (
            id integer primary key,
            name_id integer,
            homo float,
            lumo float,
            excitation float,
            dataset_id integer,
            FOREIGN KEY(name_id) REFERENCES names(id),
            FOREIGN KEY(dataset_id) REFERENCES datasets(id)
        )
        """
        conn.execute(string)
        conn.commit()

        string = """
        INSERT INTO data(name_id, homo, lumo, excitation, dataset_id)
        VALUES
        (
            ?,
            ?,
            ?,
            ?,
            (
                SELECT id FROM datasets
                WHERE optset=? and calcset=?
            )
        )
        """
        conn.executemany(string, data)
        conn.commit()


def export_database(fill_null=False):
    names, data = load_data_for_db_insert(OPTSETS, STRUCTSETS, CALCSETS, fill_null=fill_null)

    build_datasets_table(OPTSETS, CALCSETS)
    build_names_table(names)
    build_data_table(data)


def load_data_for_db_insert(optsets, structsets, calcsets, fill_null=False):
    names = {}
    for optset in optsets:
        for structset in structsets:
            for calcset in calcsets:
                path = os.path.join(optset, structset, calcset+".txt")
                if not os.path.exists(path):
                    continue

                with open(path, 'r') as f:
                    for line in f:
                        name, homo, lumo, gap = line.strip().split()

                        payload = [float(homo), float(lumo), float(gap)]
                        try:
                            names[(name, structset)][(optset, calcset)] = payload
                        except KeyError:
                            names[(name, structset)] = {(optset, calcset): payload}

    sorted_names = sorted(names.keys())
    data = []
    for i, (name, structset) in enumerate(sorted_names):
        for optset in optsets:
            for calcset in calcsets:
                if names[(name, structset)].get((optset, calcset)) is None and not fill_null:
                    continue

                if fill_null:
                    temp = names[(name, structset)].get((optset, calcset), [None, None, None])
                else:
                    temp = names[(name, structset)].get((optset, calcset))
                data.append([i+1] + temp + [optset, calcset])
    return sorted_names, data


def load_data_from_db(prop=None, optsets=None, structsets=None, calcsets=None):
    if prop not in ['homo', 'lumo', 'excitation']:
        return ValueError("Invalid property: %s" % prop)
    if not all(x in OPTSETS for x in optsets):
        return ValueError("Invalid optsets: %s" % (optsets, ))
    if not all(x in STRUCTSETS for x in structsets):
        return ValueError("Invalid structsets: %s" % (structsets, ))
    if not all(x in CALCSETS for x in calcsets):
        return ValueError("Invalid calcsets: %s" % (calcsets, ))

    where_cond1 = "structset in %s" % (tuple(structsets), )
    where_cond2 = "optset in %s and calcset in %s" % (tuple(optsets), tuple(calcsets))
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
                data.append((name, [float(x) if x else None for x in values.split(',')]))
            except:
                pass

    columns = [x for x in conn.execute("SELECT optset, calcset FROM datasets WHERE %s" % (where_cond2, ))]
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


if __name__ == "__main__":
    export_database(fill_null=False)
    p, col = load_data_from_db(prop="homo", optsets=OPTSETS, structsets=['O'], calcsets=['b3lyp'])
    missing = get_missing_data()