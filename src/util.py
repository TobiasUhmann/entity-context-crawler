from datetime import datetime


def log(msg: str):
    print('{} | {}'.format(datetime.now().strftime("%H:%M:%S"), msg))
