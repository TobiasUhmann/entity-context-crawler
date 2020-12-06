from datetime import datetime


def log(msg: str = None):
    if msg:
        print('{} | {}'.format(datetime.now().strftime("%H:%M:%S"), msg))
    else:
        print()


def log_start(msg: str):
    print('{} | {}'.format(datetime.now().strftime("%H:%M:%S"), msg), end='')


def log_end(msg: str):
    print(msg)
