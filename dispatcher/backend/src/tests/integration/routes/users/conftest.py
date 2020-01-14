import datetime

import pytest
from bson import ObjectId

from common.roles import ROLES


@pytest.fixture(scope="module")
def working_private_key():
    yield """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAuBGJjT33bHGmHDE13tDcUqUvuam1Tvlg2jC7fyS2w5qKyc8w
WBSLcbK+Yb8SnJEN44FHXKCKs6cH44PPDYcXpz5i5arGkH5CNiI5jsQ8Gh+M7NSC
huPgU8mOhBaxJ1oDvbyTCTzlcwXb97lFDlC705xO2Vqam/trUUApOhlBfQKGo5gM
05bvj4w+d5EasEboCvxCq6iI4OTW/8uReMRly0296LbFKfohQd0yeucgfReAv0OE
eUq6/0dwlgUL6DCx1I8mux6aaBFubJfHvpxGKcClQlbsiYkb/TbqJgbodmR+37X2
PM8ZFcr+lG1TV8BU7090FW8DOqUIFcf5yZs3mwIDAQABAoIBABaakLm3klrO2gc8
Q9FI9MVxY5r5LDq2hR5GPcAvUgJTSBfgSZ+HZlhgCuEWBcMUTRBTH+BQFrhZGq7l
0Ndob48qKhrqDdhQqPDc4xSVJIxQs42hyyWldjbT2Zx+7OJYO31hWu0XfVXSsmCJ
b+GCKI6j80rdxX7CMTuZFXb9Av3GzAc3L3TQMtJ4+Rva+C2YHckHSh2LQ7pbjuFf
MCQ2kEkEFpJnOW8zVPz/lkbSiZymg+PpIwbI0iloZVeV9vbm196gfmS+2q0XOpBI
AcjbNCPQDM33KnUdsv3NLg8HQlbUP5LDpsekL1gRVjJ/ypd2l59UbfI9GiYMYJRc
JVnIfIECgYEA8OgMk2GSSnlD1IGSYmfP5oKOMd5Ih31xxvh6F2Qi2+fE0WvmE9ut
9Z5D88MhtZ3kRXheTXHOzI5wLCeJr3s0PUgHXPsYP3Dw2abnEuueQyJk/LU0MGum
xh2j18U0Tj07GhvH2ByRKEl5QvFK9f8rKJW5JLswDrpg/NKnrGbz3x8CgYEAw5na
Jhr/0kxda9fWYoH3aE29XHtDdsa3efyxHFOG7iojqBUPbOcVlHizmyRnwe1yUt2j
VxhpUyQpwaII5OxK30Dwuc5c5QTO6AAjJ09FXCApwxRjnK4qWRH0aYdVW68HFy60
z+XfkDevbyxb99W+75jSc8jYQ0mZ2FgY3j8YpAUCgYAjFwnN5eZzJpq0t3LlFo33
24huxxv1cFZETykpgxJ4yZenkXnf5p2+KyFmvkOIusjnPZMu4KbosM6x/8hUYTPI
wVchOgncI81RRrhdzygsSzQ+gv5pFyUhsmuNIFJwGwci1G0Vk4OpRJp/H7p1foeA
z9459XIYkxlRejWmLRDUrQKBgQCz8Z8J/T6ptg0fwDF+8DeuIg55vQBEje2O8NPy
zjjMc8HXyIAnXLOyohQBPs2hT5Mj/rhc0J1cmmE7vJhYGbWLi0+qb9lv6yt5rV6p
tDiH1yL0T5aQNn3I8Uabqp/xN6TbQ+GdfMleAIyJRxLYfjAodbvuPrANvvEkYW+H
Th6aDQKBgQC3iLEkoFdGNOUrH8VxJKR9YDOIWQ413IRR4p7aRwz3qezw7FmLhqNK
DZ3RC9/1xkWuaA94v0RnYNoGs5IImYCc9Irf+vtudw/dzs2vIA8N1vlLRYMtjUPk
nRWOIhuCIVxmalSW0B2wFNRk5tYCvYieDfOqLWEtMLzuN3AZktVRHg==
-----END RSA PRIVATE KEY-----\n"""


@pytest.fixture(scope="module")
def not_working_private_key():
    yield """-----BEGIN RSA PRIVATE KEY-----
MIIEpgIBAAKCAQEAzcn8aFBjbg3d2MC9lkFZI4u9qbeqxbe86FoxeYrwXrVzchws
F3ywS/x0Ggd9b5fb4Px3m8WHi0YwkbPGzJHwkG6TPHoG+4fcBFY+7S56fowaV9Iw
6qfe821Nih0bAfRCnEVTXJw2jyLpMBeBEwCMiOMOiphFi8/MRvut9QkyIP+qks0D
5gnaqY2ypIqz/2WAXYIOjoFP7nM7Lxr6kSY/0JC1m40L3jzzfXjV4k1EHdfC6q8z
xtRW2mVLS1Xgc5gSr8r7DfQQZTmQlnp2GwZ093AxHmCqgCt/6kw4zLKvE8PMz4Yd
oVQgyDhgGIGgXL6UcD+XI5J1dmFa2znU/8v5/QIDAQABAoIBAQDD1pT+MIJvGYMl
40aI12edDD9SZBeAUXrVJAAxSqe1ebiDv4u2TlL3/SgAHWCh8kKtuZWaCEEVqZZP
Emb+B2SIDrLPutEqTgBzoCACV1j7VRk8uisTJO5nen1wEoLBOVKqpM7QM1k4nmCM
A9Ix4zPakTolawPEKdydMKY7qqSqAO22JvyxZCvLS0+fCdWYrQTrGANEnabbeDNq
euSgs8w3t+URDDsXR/uyKVGq21nOtw975PqOY54InZni/eMev8RAtEB/gtgOUw98
C98QTxSUwwkporuk9jX6vyUjMvw4Fpcuk2vqZnbMPWM0fC+nbXh/J4RJc8j+Jrlz
DTO/WlQBAoGBAP1SH20X4PDYyEmMOvX75oU+ZeKk/D1/IXPdGC0szmHSxQKPwgRA
Ns2ZFPl5wH0BhIxx7G+UOl66JEGqgymRq2Pz09p+GwzuJiSPfT7HKCe3/UyvUugL
x9kmW/fgjZQKcE/9j8Ic3zZSr25MZbXlDhEh70fH1cd4EEhS7QLidc9pAoGBAM/3
KzaOtuniJVED+qyqTI16JdUapAX8IT/jWyNxo/8s7uoLdZpR9chlOSgdO7dOsakP
3Cfxl0qQLoHPfGSKTXmJKfRY7hBl9G65P9SRi2Zzf2EISiic5ycnzwXOOsfYx+6M
LBodRaAJ4H2+DqHypPRYjxS09LCtmof7/doTS9d1AoGBALWIxXaTdyKB5741HQes
dj0kQzVRUGXtlhaG6c1t35Rgy8gTJ1GOhvd9bXd+lb+/d7KB7ZLkYZQCxvq76/S9
LFqboEViu5XfkDwBDBsR86fLBV2QAtTBpHzsLVoMdMkTVfss1Xmg4SD3zjo3y2e3
dwY2EFibT4r7coexzaGUkiKJAoGBAMhzhGp82t/Kw484V6mQKGOBpe+nUwwVvvK2
sUUTpzAxXkOnMf7CGzbCInqA2utP5bx/9gNmQR50pO8oT80U5aJMzGyiPyz9KMKE
unqoowXoM5ISjHBi9AbwvwHoiw3P7L4IzAWLy217t69bvvzoRYjjx139IZEedEG4
aTGGweZ1AoGBAIUGMaVsZ6z6wRptbZ+1dRNhMMCPAF6w8xweeHbBdvh/uH4gRXEC
7XbgvLh8A95Z5kIiGAZKpXpwkBzvN6rwla+jYW6L/8VK0XlBaqY3Hg9YsYQXo7UM
RhJMRUmh/D3kxUFO/wtSDGfo/HR/1iEraoddi+sA6+R56vA8ziJC51xw
-----END RSA PRIVATE KEY-----\n"""


@pytest.fixture(scope="module")
def make_user(database):
    user_ids = []

    def _make_user(username: str = "some-user", role: str = None) -> dict:
        document = {
            "_id": ObjectId(),
            "username": username,
            "password_hash": "pbkdf2:sha256:150000$dEqsZI8W$2d2bbcbadab59281528ecbb27d26ac628472a0b2f0a5e1828edbeeae683dd40f",
            "ssh_keys": [
                {
                    "name": "pytest",
                    "fingerprint": "a4a7cfd26a11ec519b63d4d12f34ecf2",
                    "key": "AAAAB3NzaC1yc2EAAAADAQABAAABAQC4EYmNPfdscaYcMTXe0NxSpS+5qbVO+WDaMLt/JLbDmorJzzBYFItxsr5hvxKckQ3jgUdcoIqzpwfjg88NhxenPmLlqsaQfkI2IjmOxDwaH4zs1IKG4+BTyY6EFrEnWgO9vJMJPOVzBdv3uUUOULvTnE7ZWpqb+2tRQCk6GUF9AoajmAzTlu+PjD53kRqwRugK/EKrqIjg5Nb/y5F4xGXLTb3otsUp+iFB3TJ65yB9F4C/Q4R5Srr/R3CWBQvoMLHUjya7HppoEW5sl8e+nEYpwKVCVuyJiRv9NuomBuh2ZH7ftfY8zxkVyv6UbVNXwFTvT3QVbwM6pQgVx/nJmzeb",
                    "type": "RSA",
                    "added": datetime.datetime(2019, 1, 1),
                    "last_used": datetime.datetime(2019, 1, 1),
                    "pkcs8_key": "-----BEGIN PUBLIC KEY-----\n"
                    "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAuBGJjT33bHGmHDE13tDc\n"
                    "UqUvuam1Tvlg2jC7fyS2w5qKyc8wWBSLcbK+Yb8SnJEN44FHXKCKs6cH44PPDYcX\n"
                    "pz5i5arGkH5CNiI5jsQ8Gh+M7NSChuPgU8mOhBaxJ1oDvbyTCTzlcwXb97lFDlC7\n"
                    "05xO2Vqam/trUUApOhlBfQKGo5gM05bvj4w+d5EasEboCvxCq6iI4OTW/8uReMRl\n"
                    "y0296LbFKfohQd0yeucgfReAv0OEeUq6/0dwlgUL6DCx1I8mux6aaBFubJfHvpxG\n"
                    "KcClQlbsiYkb/TbqJgbodmR+37X2PM8ZFcr+lG1TV8BU7090FW8DOqUIFcf5yZs3\n"
                    "mwIDAQAB\n"
                    "-----END PUBLIC KEY-----\n",
                }
            ],
        }
        if role:
            document["scope"] = ROLES.get(role)
        user_id = database.users.insert_one(document).inserted_id
        user_ids.append(user_id)
        return document

    yield _make_user

    database.users.delete_many({"_id": {"$in": user_ids}})


@pytest.fixture(scope="module")
def user(make_user):
    return make_user()


@pytest.fixture(scope="module")
def users(make_user):
    users = []
    for index in range(5):
        username = "user_{}".format(index)
        user = make_user(username)
        users.append(user)
    return users
