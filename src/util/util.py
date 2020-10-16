from datetime import datetime


def log(msg: str = None):
    if msg:
        print('{} | {}'.format(datetime.now().strftime("%H:%M:%S"), msg))
    else:
        print()
