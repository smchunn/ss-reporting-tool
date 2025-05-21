import concurrent.futures, threading
import logging


def threader(func, tables, threadcount):
    if logging.getLogger().getEffectiveLevel() == logging.DEBUG:
        for table in tables:
            func(table)
    elif len(tables) == 1:
        func(tables[0])
    else:
        with concurrent.futures.ThreadPoolExecutor(threadcount) as executor:
            futures = [executor.submit(func, table) for table in tables]

            for x, _ in enumerate(concurrent.futures.as_completed(futures)):
                print(f"thread no. {x} returned")


def scheduler(count, interval, func, *args, **kwargs):
    def wrapper():
        nonlocal count
        if count > 0:
            func(args, kwargs)
            count -= 1
            if count > 0:
                threading.Timer(interval, wrapper).start()

    wrapper()
def log(msg):
    pass

