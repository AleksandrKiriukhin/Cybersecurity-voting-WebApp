import random
import math
from utils.primes import generujLiczbePierwsza, lcm, funkcjaL

def generujKlucze (bits = 16):

    print(f" \n ------------ Generacja kluczy zaczela sie! ------------ \n")

    p = generujLiczbePierwsza( bits)
    q = generujLiczbePierwsza( bits)

    print(f"Wygenerowane p = {p}")
    print(f"Wygenerowane q = {q}")

    while p == q:

        q = generujLiczbePierwsza( bits)

    n = p * q

    print(f"Wyliczone n = {n}")

    g= n+ 1

    print(f"Wyliczone g = {g}")

    lmbda = lcm (p-1, q-1)

    print(f"Wyliczona lambda = {lmbda}")

    mi = pow (funkcjaL (pow (g, lmbda, n * n), n), -1, n)

    print(f"Wyliczone mi = {mi}")

    print(f"\n ------------ Generacja kluczy zakonczyla sie! ------------ \n")

    print(f"n = {n}, g = {g}, lambda = {lmbda}, mi = {mi}")

    return {'n': n, 'g': g, 'lambda': lmbda, 'mi': mi}

def losoweR( n ):

    print(f" \n ------------ Generacja losowego r zaczela sie! ------------ \n")

    while True:
        r = random.randint( 1, n - 1)

        if math.gcd( r , n) == 1:

            print(f"Wygenerowane losowe r = {r}")

            print(f" \n ------------ Generacja losowego r zakonczyla sie! ------------ \n")

            return r

def szyfruj ( m, r, n, g):

    print(f" \n ------------ Szyfrowanie glosu zaczelo sie! ------------ \n")

    math.gcd( r, n) == 1

    c = ( pow ( g, m , n * n) * pow ( r, n, n * n)) % ( n * n)

    print(f"Zaszyfrowany glos wyglada tak = {c}")

    print(f" \n ------------ Szyfrowanie glosu zakonczylo sie! ------------ \n")

    return c

def deszsyfruj ( c, lmbda, mi, n):

    print(f"{c}")

    print(f"c = {c}")
    print(f"lmbda = {lmbda}")
    print(f"mi = {mi}")
    print(f"n = {n}")

    print(f" \n ------------ Deszyfrowanie glosu zaczelo sie! ------------ \n")

    p = ( funkcjaL ( pow ( c, lmbda, n * n), n) * mi ) % ( n)

    print(f"Deszyfrowany glos wyglada tak = {p}")

    print(f" \n ------------ Deszyfrowanie glosu zakonczylo sie! ------------ \n")

    return p