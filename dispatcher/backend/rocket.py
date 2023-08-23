from multiprocessing import Pool

import requests


def f(x):
    return requests.get("http://127.0.0.1:80").status_code


if __name__ == "__main__":
    with Pool(200) as p:
        print(p.map(f, range(200)))
    with Pool(2) as p:
        print(p.map(f, range(2)))
