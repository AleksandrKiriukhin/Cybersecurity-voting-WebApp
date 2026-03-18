from encryption.paillier import generujKlucze
from voting.candidates import kandydaci
from voting.vote_manager import zeroweGlosy, dodajGlos, wyniki
from ui.app import run
from database.db_creation import init_db
from database.db_static_data import static_data

if __name__=="__main__":
    
    init_db()
    static_data()

    # run()
    

# keys = generujKlucze(bits=16)
# n,g,lmbda,mu = keys['n'], keys['g'], keys['lambda'], keys['mi']

# candidates = kandydaci()

# encrypted_votes = zeroweGlosy(candidates, n, g)

# while True:
#     print("\nKandydaci: ")
#     for i, name in enumerate(candidates):
#         print (f"{i+1}. {name}")
#     print ("Wybierz kandydata 1 lub 2, lub q zeby zakoczyc")
#     choice = input("\n")

#     if choice.lower() == 'q':
#         break

#     try:
#         idx = int(choice) - 1
#         if idx < 0 or idx >= len(candidates):
#             print("Nieprawidlowy wybor")
#             continue
#     except ValueError:
#         print("Nieprawidlowy wybor")
#         continue

#     selected = candidates[idx]

#     dodajGlos(selected, candidates, encrypted_votes, n, g)
    
#     print (f"Twoj glos na {selected} zostal zaszyfrowany")

# print ("\n Wyniki: ")
# results = wyniki(candidates, encrypted_votes, lmbda, mu, n)
# for name, count in results.items():
#     print(f"{name}: {count} glos(y)")

# if __name__=="__main__":
#     run()