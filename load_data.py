import os
import sqlite3
from itertools import product


methods = ["b3lyp", "cam", "m06hf"]
indo_methods = ["indo_" + x for x in ["default"] + methods]

OPTSETS = ["noopt"] + [os.path.join("opt", x) for x in methods]
STRUCTSETS = ['O', 'N', "rot"]
CALCSETS = methods + indo_methods


def build_datasets_table(optsets, structsets, calcsets):
    with sqlite3.connect("database.sqlite") as conn:
        conn.execute("DROP TABLE IF EXISTS datasets")
        string = """
        CREATE TABLE datasets
        (
            id integer primary key,
            optset varchar,
            structset varchar,
            calcset varchar
        )
        """
        conn.execute(string)

        data = list(product(optsets, structsets, calcsets))
        conn.executemany('INSERT INTO datasets(optset, structset, calcset)  VALUES (?,?,?)', data)
        conn.commit()


def build_names_table(names):
    with sqlite3.connect("database.sqlite") as conn:
        conn.execute("DROP TABLE IF EXISTS names")
        string = """
        CREATE TABLE names
        (
            id integer primary key,
            name varchar
        )
        """
        conn.execute(string)
        conn.commit()

        conn.executemany("INSERT INTO names(name) VALUES (?)", [[x] for x in names])
        conn.commit()


def build_data_table(data):
    with sqlite3.connect("database.sqlite") as conn:
        conn.execute("DROP TABLE IF EXISTS data")
        string = """
        CREATE TABLE data
        (
            id integer primary key,
            name varchar,
            homo float,
            lumo float,
            excitation float,
            dataset_id integer,
            FOREIGN KEY(dataset_id) REFERENCES datasets(id)
        )
        """
        conn.execute(string)
        conn.commit()

        string = """
        INSERT INTO data(name, homo, lumo, excitation, dataset_id)
        VALUES
        (
            ?,
            ?,
            ?,
            ?,
            (
                SELECT id FROM datasets
                WHERE optset=? and structset=? and calcset=?
            )
        )
        """
        conn.executemany(string, data)
        conn.commit()


def build_norm_name_data_table(data):
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
            (
                SELECT id FROM names
                WHERE name=?
            ),
            ?,
            ?,
            ?,
            (
                SELECT id FROM datasets
                WHERE optset=? and structset=? and calcset=?
            )
        )
        """
        conn.executemany(string, data)
        conn.commit()


def export_database(fill_null=False):
    names, data = load_data_for_db_insert(OPTSETS, STRUCTSETS, CALCSETS, fill_null=fill_null)

    build_datasets_table(OPTSETS, STRUCTSETS, CALCSETS)
    build_data_table(data)


def export_norm_name_database(fill_null=True):
    names, data = load_data_for_db_insert(OPTSETS, STRUCTSETS, CALCSETS, fill_null=fill_null)

    build_datasets_table(OPTSETS, STRUCTSETS, CALCSETS)
    build_names_table(names)
    build_norm_name_data_table(data)


def load_data_for_db_insert(optsets, structsets, calcsets, fill_null=True):
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
                            names[name][(optset, structset, calcset)] = payload
                        except KeyError:
                            names[name] = {(optset, structset, calcset): payload}

    data = []
    for optset in optsets:
        for structset in structsets:
            for calcset in calcsets:
                for name in names:
                    if fill_null:
                        temp = names[name].get((optset, structset, calcset), [None, None, None])
                    else:
                        if names[name].get((optset, structset, calcset)) is not None:
                            temp = names[name].get((optset, structset, calcset))
                        else:
                            continue
                    data.append([name] + temp + [optset, structset, calcset])
    return sorted(names), data


if __name__ == "__main__":
    export_database(fill_null=True)
    # export_norm_name_database(fill_null=True)