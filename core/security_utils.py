"""
Utilidades de seguridad compartidas, como el contexto de hashing de contraseñas.
"""

from passlib.context import CryptContext

# Contexto de contraseñas para hashing (bcrypt es el recomendado)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Podrían añadirse aquí otras funciones de seguridad compartidas en el futuro
# ej: def verify_password(plain_password, hashed_password):
#         return pwd_context.verify(plain_password, hashed_password)
#     def get_password_hash(password):
#         return pwd_context.hash(password) 