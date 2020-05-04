from threading import Thread  # QOLFAC: quality of life functions and classes, V:1.1
from time import sleep, time as t
from sqlite3 import connect, OperationalError


class NotList(Exception):
    pass


def is_empty(data):
    if isinstance(data, (tuple, list, dict)):
        if len(data) == 0:
            return True
        else:
            return False
    else:
        raise NotList


def tuple_convert(data_in):
    if isinstance(data_in, (tuple, list)):
        return data_in
    else:
        return data_in,


def function_handler(function, args: tuple = ()):
    args = tuple_convert(args)
    if args == ():
        function()
    else:
        function(*args)


def thread_run(function, args, daemonic=True):
    func = Thread(target=function, name=str(function), args=args)
    func.setDaemon(daemonic)
    func.start()


def quote_escape(str_in: str):
    str_out = ""
    for char in str_in:
        str_out += char
        if char == "\"":
            str_out += "\""
        elif char == "'":
            str_out += "'"
    return str_out


def zero(num):
    return 0 if num < 0 else num


def up_limit(num, lim):
    return num if lim > num else lim


def get_milli_time():
    return int(round(t() * 1000))


class StopWatch:
    def __init__(self):
        self.__time = 0
        self.__initial = 0
        self.__running = False

    def start(self):
        if not self.__running:
            self.__running = True
            self.__initial = get_milli_time()

    def stop(self):
        if self.__running:
            self.__time = (get_milli_time() - self.__initial) + self.__time
            self.__running = False

    def reset(self):
        if not self.__running:
            self.__time = 0
            self.__initial = 0

    def get_time(self, time_prefix="m"):
        if self.__running:
            time = (get_milli_time() - self.__initial) + self.__time
        else:
            time = self.__time
        return prefix_conversion("m", time_prefix, time)


def exec_time(func, args: tuple = None):
    stopper = StopWatch()
    stopper.start()
    if args is None:
        res = func()
    else:
        res = func(*args)
    stopper.stop()
    return res, stopper.get_time()


def prefix_conversion(current: str, required: str, data):
    p_map = {"y": -24, "z": -21, "a": -18, "f": -15, "p": -12, "n": -9, "u": -6, "m": -3, "c": -2, "d": -1,
             "b": 0, "D": 1, "H": 2, "K": 3, "M": 6, "G": 9, "T": 12, "P": 15, "E": 18, "Z": 21, "Y": 24}
    return data * (10 ** (p_map[current] - p_map[required]))


class Timer:
    def __init__(self, time, finish_com, com_args=None):
        self.original_time = time
        self.__time = self.original_time
        self.finish_command = finish_com
        self.com_args = com_args
        self.t_thread = Thread(target=self.__t_thread, name="Timer Thread (%s)" % self.original_time)
        self.t_thread.setDaemon(True)
        self.paused = False
        self.__abort = False

    def start(self):
        self.__time = self.original_time
        self.t_thread.start()

    def get_original_time(self):
        return self.original_time

    def pause(self):
        self.paused = True

    def unpause(self):
        self.paused = False

    def abort(self):
        if self.__time != 0:
            self.__abort = True
            self.__time = 0

    def change_by(self, amount):
        time = self.__time + amount
        if time < 0:
            time = 0
        self.__time = time

    def set(self, amount):
        if amount < 0:
            amount = 0
        self.__time = amount

    def get_time(self):
        return self.__time

    def __t_thread(self):
        while self.__time > 0:
            if not self.paused:
                sleep(1)
                if self.__time > 0:
                    self.__time -= 1
        if not self.__abort:
            if self.com_args is None:
                self.finish_command()
            else:
                self.finish_command(*tuple_convert(self.com_args))
        else:
            self.__abort = False


# noinspection SqlResolve
class DataBaseAccess:
    def __init__(self, db_name, load_data=False):
        self.database_name = db_name
        self.tables = {}
        column_info = {}
        if load_data:
            tables = self.sql("SELECT name FROM sqlite_master WHERE type='table'")
            for i in tables:
                table_info = self.__get_table_info(i[0])
                if table_info is not None:
                    for j in range(len(table_info)):
                        column_info[str(table_info[j][1])] = {"column_id": table_info[j][0],
                                                              "data_type": table_info[j][2],
                                                              "not_null": table_info[j][3],
                                                              "default_value": table_info[j][4],
                                                              "is_primary": table_info[j][5]}
                    self.tables[str(i[0])] = column_info
                    column_info = {}

    def sql(self, sql: str, sale: bool = False):  # SALE: selective automatic list escaping
        try:
            with connect(self.database_name) as db:
                cursor = db.cursor()
                cursor.execute(sql)
                if "select" in sql.lower():
                    data = cursor.fetchall()
                    while sale:
                        if len(data) == 1 and isinstance(data, list):
                            data = data[0]
                        else:
                            break
                    return data
                db.commit()
        except OperationalError as ex:
            print("Database error:", ex)

    def __get_table_info(self, table):
        return self.sql(f"PRAGMA table_info({table});")


if __name__ == '__main__':
    pass
