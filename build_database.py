import os
import sqlite3
from itertools import product

from utils import OPTSETS, STRUCTSETS, CALCSETS, PROPS

def build_datasets_table(optsets, calcsets):
    with sqlite3.connect("database.sqlite") as conn:
        conn.execute("DROP TABLE IF EXISTS datasets")
        string = """
        CREATE TABLE datasets
        (
            id integer primary key,
            optset varchar,
            calcset varchar,
            parameters varchar
        )
        """
        conn.execute(string)

        data = list(product(optsets, calcsets))
        string = "INSERT INTO datasets(optset, calcset)  VALUES (?,?)"
        conn.executemany(string, data)
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

        string = "INSERT INTO names(name, structset) VALUES (?, ?)"
        conn.executemany(string, names)
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
    names, data = load_data_for_db_insert(OPTSETS, STRUCTSETS, CALCSETS,
                                          fill_null=fill_null)

    build_datasets_table(OPTSETS, CALCSETS)
    build_names_table(names)
    build_data_table(data)


def load_data_for_db_insert(optsets, structsets, calcsets, fill_null=False):
    names = {}
    for optset in optsets:
        for structset in structsets:
            for calcset in calcsets:
                path = os.path.join(optset, structset, calcset + ".txt")
                if not os.path.exists(path):
                    continue

                with open(path, 'r') as f:
                    for line in f:
                        name, homo, lumo, gap = line.strip().split()

                        payload = [float(homo), float(lumo), float(gap)]
                        try:
                            names[(name, structset)][
                                (optset, calcset)] = payload
                        except KeyError:
                            names[(name, structset)] = {
                                (optset, calcset): payload}

    sorted_names = sorted(names.keys())
    data = []
    for i, (name, structset) in enumerate(sorted_names):
        for optset in optsets:
            for calcset in calcsets:
                if names[(name, structset)].get((optset, calcset)) is None and not fill_null:
                    continue

                if fill_null:
                    temp = names[(name, structset)].get(
                        (optset, calcset), [None, None, None])
                else:
                    temp = names[(name, structset)].get((optset, calcset))
                data.append([i + 1] + temp + [optset, calcset])
    return sorted_names, data



if __name__ == "__main__":
    export_database(fill_null=False)
