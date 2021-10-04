import csv
import sqlite3
import psycopg2


def csv_reader(table, file_obj, cursor, index_model):
    reader = csv.reader(file_obj)
    index = 0

    for row in reader:
        if index == 0:
            index = 1
            continue

        if index_model == 1:
            values = ",".join(["?" for i in range(0, len(row))])
            sql = f'insert into {table} values({values})'
            print(sql, row[1])
            cursor.execute(sql, row)


def main():
    con = psycopg2.connect(
        database="af",
        user="food",
        password="food",
        host="127.0.0.1",
        port="5432"
    )

    print("Database opened successfully")


if __name__ == '__main__':
    main()
