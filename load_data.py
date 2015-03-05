import os
import sqlite3
from itertools import product


def export_database():
    conn = sqlite3.connect("database.sqlite")

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
    methods = ["b3lyp","cam","m06hf"]
    indo_methods = ["indo_"+x for x in ["default"] + methods]

    optsets = ["noopt"] + [os.path.join("opt", x) for x in methods]
    structsets = ['O','N',"rot"]
    calcsets = methods + indo_methods
    data = list(product(optsets, structsets, calcsets))
    conn.executemany('INSERT INTO datasets(optset, structset, calcset)  VALUES (?,?,?)', data)
    conn.commit()

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
    data = load_data(optsets, structsets, calcsets)
    conn.executemany(string, data)
    conn.commit()



def load_data(optsets, structsets, calcsets):
    data = []

    for optset in optsets:
        for structset in structsets:
            for calcset in calcsets:
                path = os.path.join(optset, structset, calcset+".txt")
                if not os.path.exists(path):
                    print path
                    continue
                with open(path, 'r') as f:
                    for line in f:
                        name, homo, lumo, gap = line.strip().split()

                        payload = [name, float(homo), float(lumo), float(gap), optset, structset, calcset]
                        data.append(payload)
    return data


# export_database()
