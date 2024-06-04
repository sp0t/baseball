from passlib.hash import sha256_crypt
password = sha256_crypt.encrypt("^DMnN%Vsge5r")
print(password)