# from cryptography.fernet import Fernet
# import json

# secrets = {
    
#     "default": {
#         "DB_NAME": "postgres",
#         "DB_USER": "postgres",
#         "DB_PASS": "1234",
#         "DB_HOST": "localhost",
#         "DB_PORT": "5432"
#     },
#     "voting_app": {
#         "DB_NAME": "voting_app",
#         "DB_USER": "postgres",
#         "DB_PASS": "1234",
#         "DB_HOST": "localhost",
#         "DB_PORT": "5432"
#     }
# }

# import os
# key = os.environ["CONNECTION_KEY"].encode()
# f = Fernet(key)

# token = f.encrypt(json.dumps(secrets).encode())

# with open("database/db_secrets.enc", "wb") as fh:
#     fh.write(token)

# # from cryptography.fernet import Fernet

# # key = Fernet.generate_key()
# # print(key.decode())