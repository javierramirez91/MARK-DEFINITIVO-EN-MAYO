"""
Sistema de cifrado mejorado para el asistente Mark.
Implementa cifrado de extremo a extremo para todas las conversaciones.
"""
import logging
import os
import base64
import json
import traceback
from typing import Dict, Any, Optional, Union, Tuple
from datetime import datetime, timedelta

# Configurar logging con más detalle
logger = logging.getLogger("mark.encryption")

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.primitives.serialization import (
        load_pem_private_key,
        load_pem_public_key,
        Encoding,
        PrivateFormat,
        PublicFormat,
        NoEncryption
    )
    CRYPTO_AVAILABLE = True
except ImportError as e:
    logger.error(f"No se pudieron importar las dependencias de criptografía: {e}")
    CRYPTO_AVAILABLE = False

class E2EEncryption:
    """
    Sistema de cifrado de extremo a extremo para conversaciones.
    Utiliza cifrado asimétrico para el intercambio de claves y
    cifrado simétrico para el contenido de los mensajes.
    """
    
    def __init__(self, key_directory: Optional[str] = None, key_rotation_days: int = 90):
        """
        Inicializar el sistema de cifrado
        
        Args:
            key_directory: Directorio para almacenar las claves (opcional)
            key_rotation_days: Días entre rotaciones de claves (por defecto: 90)
        """
        # Usar el directorio proporcionado o el predeterminado
        self.key_directory = key_directory or os.path.join(os.path.dirname(__file__), "../../keys")
        os.makedirs(self.key_directory, exist_ok=True)
        
        # Configuración de rotación de claves
        self.key_rotation_days = key_rotation_days
        
        # Inicializar componentes
        self.private_key = None
        self.public_key = None
        self.user_keys = {}
        self.user_keys_file = os.path.join(self.key_directory, "user_keys.json")
        
        # Verificar si existen las claves, si no, generarlas
        if not os.path.exists(os.path.join(self.key_directory, "private_key.pem")):
            logger.info("No se encontraron claves RSA, generando nuevas claves...")
            self._generate_key_pair()
        
        # Cargar claves
        self.private_key = self._load_private_key()
        self.public_key = self._load_public_key()
        
        # Cargar claves de usuarios
        self.user_keys = self._load_user_keys()
        
        # Verificar si es necesario rotar claves
        self.check_key_rotation()
        
        logger.info("Sistema de cifrado E2E inicializado correctamente")
    
    def _generate_key_pair(self) -> bool:
        """
        Genera un nuevo par de claves RSA
        
        Returns:
            bool: True si se generaron correctamente, False en caso contrario
        """
        if not CRYPTO_AVAILABLE:
            logger.error("No se pueden generar claves: cryptography no está disponible")
            return False
        
        try:
            # Generar clave privada RSA con tamaño de clave más seguro
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=4096  # Aumentado de 2048 a 4096 bits para mayor seguridad
            )
            
            # Obtener clave pública
            public_key = private_key.public_key()
            
            # Guardar clave privada con permisos restrictivos
            private_pem = private_key.private_bytes(
                encoding=Encoding.PEM,
                format=PrivateFormat.PKCS8,
                encryption_algorithm=NoEncryption()
            )
            private_key_path = os.path.join(self.key_directory, "private_key.pem")
            with open(private_key_path, "wb") as f:
                f.write(private_pem)
            
            # Establecer permisos restrictivos en sistemas Unix
            if os.name == 'posix':
                os.chmod(private_key_path, 0o600)  # Solo lectura/escritura para el propietario
            
            # Guardar clave pública
            public_pem = public_key.public_bytes(
                encoding=Encoding.PEM,
                format=PublicFormat.SubjectPublicKeyInfo
            )
            with open(os.path.join(self.key_directory, "public_key.pem"), "wb") as f:
                f.write(public_pem)
                
            logger.info("Par de claves RSA generado correctamente (4096 bits)")
            return True
        except Exception as e:
            logger.error(f"Error al generar par de claves: {e}")
            logger.debug(traceback.format_exc())
            return False
    
    def _load_private_key(self):
        """
        Carga la clave privada desde el archivo
        
        Returns:
            La clave privada cargada o None si hubo un error
        """
        if not CRYPTO_AVAILABLE:
            logger.warning("No se puede cargar la clave privada: cryptography no está disponible")
            return None
        
        try:
            private_key_path = os.path.join(self.key_directory, "private_key.pem")
            if not os.path.exists(private_key_path):
                logger.error(f"No se encontró el archivo de clave privada en {private_key_path}")
                return None
            
            with open(private_key_path, "rb") as f:
                private_key_data = f.read()
            
            # Verificar que los datos parecen una clave PEM válida
            if not private_key_data.startswith(b'-----BEGIN PRIVATE KEY-----'):
                logger.error("El archivo de clave privada no tiene el formato esperado")
                return None
            
            return load_pem_private_key(private_key_data, password=None)
        except Exception as e:
            logger.error(f"Error al cargar clave privada: {e}")
            logger.debug(traceback.format_exc())
            return None
    
    def _load_public_key(self):
        """
        Carga la clave pública desde el archivo
        
        Returns:
            La clave pública cargada o None si hubo un error
        """
        if not CRYPTO_AVAILABLE:
            logger.warning("No se puede cargar la clave pública: cryptography no está disponible")
            return None
        
        try:
            public_key_path = os.path.join(self.key_directory, "public_key.pem")
            if not os.path.exists(public_key_path):
                logger.error(f"No se encontró el archivo de clave pública en {public_key_path}")
                return None
            
            with open(public_key_path, "rb") as f:
                public_key_data = f.read()
            
            # Verificar que los datos parecen una clave PEM válida
            if not public_key_data.startswith(b'-----BEGIN PUBLIC KEY-----'):
                logger.error("El archivo de clave pública no tiene el formato esperado")
                return None
            
            return load_pem_public_key(public_key_data)
        except Exception as e:
            logger.error(f"Error al cargar clave pública: {e}")
            logger.debug(traceback.format_exc())
            return None
    
    def _load_user_keys(self) -> Dict[str, Dict[str, Any]]:
        """
        Carga las claves de los usuarios desde el archivo
        
        Returns:
            Diccionario con las claves de los usuarios o un diccionario vacío si hubo un error
        """
        if os.path.exists(self.user_keys_file):
            try:
                with open(self.user_keys_file, "r") as f:
                    data = json.load(f)
                
                # Validar la estructura de los datos
                for user_id, user_data in data.items():
                    required_fields = ["public_key", "symmetric_key", "encrypted_symmetric_key", 
                                      "created_at", "last_rotation"]
                    if not all(field in user_data for field in required_fields):
                        logger.warning(f"Datos de usuario {user_id} incompletos, se omitirán")
                        continue
                        
                    # Validar fechas
                    try:
                        datetime.fromisoformat(user_data["created_at"])
                        datetime.fromisoformat(user_data["last_rotation"])
                    except ValueError:
                        logger.warning(f"Fechas inválidas para el usuario {user_id}, se corregirán")
                        # Corregir fechas inválidas
                        current_time = datetime.now().isoformat()
                        data[user_id]["created_at"] = current_time
                        data[user_id]["last_rotation"] = current_time
                
                logger.info(f"Claves de usuario cargadas correctamente: {len(data)} usuarios")
                return data
            except json.JSONDecodeError:
                logger.error("El archivo de claves de usuario está corrupto")
                # Hacer una copia de seguridad del archivo corrupto
                backup_file = f"{self.user_keys_file}.bak.{int(datetime.now().timestamp())}"
                try:
                    os.rename(self.user_keys_file, backup_file)
                    logger.info(f"Se ha creado una copia de seguridad del archivo corrupto: {backup_file}")
                except Exception as e:
                    logger.error(f"No se pudo crear copia de seguridad: {e}")
            except Exception as e:
                logger.error(f"Error al cargar claves de usuarios: {e}")
                logger.debug(traceback.format_exc())
        else:
            logger.info("No existe archivo de claves de usuario, se creará uno nuevo")
        
        return {}
    
    def _save_user_keys(self) -> bool:
        """
        Guarda las claves de los usuarios en el archivo
        
        Returns:
            True si se guardaron correctamente, False en caso contrario
        """
        try:
            # Crear una copia de seguridad antes de guardar
            if os.path.exists(self.user_keys_file):
                backup_file = f"{self.user_keys_file}.bak"
                try:
                    with open(self.user_keys_file, "r") as src, open(backup_file, "w") as dst:
                        dst.write(src.read())
                    logger.debug(f"Copia de seguridad creada: {backup_file}")
                except Exception as e:
                    logger.warning(f"No se pudo crear copia de seguridad: {e}")
            
            # Guardar el archivo
            with open(self.user_keys_file, "w") as f:
                json.dump(self.user_keys, f, indent=2)
            
            # Establecer permisos restrictivos en sistemas Unix
            if os.name == 'posix':
                os.chmod(self.user_keys_file, 0o600)  # Solo lectura/escritura para el propietario
            
            logger.debug(f"Claves de usuario guardadas correctamente: {len(self.user_keys)} usuarios")
            return True
        except Exception as e:
            logger.error(f"Error al guardar claves de usuarios: {e}")
            logger.debug(traceback.format_exc())
            return False
    
    def generate_symmetric_key(self) -> bytes:
        """Genera una nueva clave simétrica aleatoria"""
        return os.urandom(32)  # 256 bits
    
    def encrypt_symmetric_key(self, symmetric_key: bytes, public_key=None) -> str:
        """
        Cifra una clave simétrica con la clave pública RSA
        
        Args:
            symmetric_key: Clave simétrica a cifrar
            public_key: Clave pública a usar (si es None, usa la del sistema)
            
        Returns:
            Clave simétrica cifrada en formato base64
        """
        if not CRYPTO_AVAILABLE:
            return ""
        
        try:
            key_to_use = public_key if public_key else self.public_key
            encrypted_key = key_to_use.encrypt(
                symmetric_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return base64.b64encode(encrypted_key).decode('utf-8')
        except Exception as e:
            logger.error(f"Error al cifrar clave simétrica: {e}")
            return ""
    
    def decrypt_symmetric_key(self, encrypted_key: str, private_key=None) -> Optional[bytes]:
        """
        Descifra una clave simétrica con la clave privada RSA
        
        Args:
            encrypted_key: Clave simétrica cifrada en formato base64
            private_key: Clave privada a usar (si es None, usa la del sistema)
            
        Returns:
            Clave simétrica descifrada
        """
        if not CRYPTO_AVAILABLE:
            return None
        
        try:
            key_to_use = private_key if private_key else self.private_key
            encrypted_key_bytes = base64.b64decode(encrypted_key)
            return key_to_use.decrypt(
                encrypted_key_bytes,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
        except Exception as e:
            logger.error(f"Error al descifrar clave simétrica: {e}")
            return None
    
    def encrypt_message(self, message: str, symmetric_key: bytes) -> str:
        """
        Cifra un mensaje con una clave simétrica usando AES-GCM
        
        Args:
            message: Mensaje a cifrar
            symmetric_key: Clave simétrica para el cifrado
            
        Returns:
            Mensaje cifrado en formato base64 o el mensaje original si ocurre un error
        """
        if not CRYPTO_AVAILABLE:
            logger.warning("No se puede cifrar el mensaje: cryptography no está disponible")
            return message
        
        if not message:
            return message
        
        if not symmetric_key or len(symmetric_key) != 32:
            logger.error(f"Clave simétrica inválida para cifrado (longitud: {len(symmetric_key) if symmetric_key else 0})")
            return message
        
        try:
            # Generar nonce aleatorio
            nonce = os.urandom(12)
            
            # Crear cifrador
            aesgcm = AESGCM(symmetric_key)
            
            # Añadir metadatos como datos asociados autenticados (AAD)
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "version": "1.0"
            }
            aad = json.dumps(metadata).encode('utf-8')
            
            # Cifrar mensaje con AAD
            ciphertext = aesgcm.encrypt(nonce, message.encode('utf-8'), aad)
            
            # Combinar nonce, longitud de AAD, AAD y texto cifrado
            aad_length = len(aad).to_bytes(2, byteorder='big')
            combined = nonce + aad_length + aad + ciphertext
            
            # Codificar en base64
            encrypted = base64.b64encode(combined).decode('utf-8')
            
            return encrypted
        except Exception as e:
            logger.error(f"Error al cifrar mensaje: {e}")
            logger.debug(traceback.format_exc())
            return message
    
    def decrypt_message(self, encrypted_message: str, symmetric_key: bytes) -> str:
        """
        Descifra un mensaje con una clave simétrica usando AES-GCM
        
        Args:
            encrypted_message: Mensaje cifrado en formato base64
            symmetric_key: Clave simétrica para el descifrado
            
        Returns:
            Mensaje descifrado o el mensaje cifrado original si ocurre un error
        """
        if not CRYPTO_AVAILABLE:
            logger.warning("No se puede descifrar el mensaje: cryptography no está disponible")
            return encrypted_message
        
        if not encrypted_message:
            return encrypted_message
        
        if not symmetric_key or len(symmetric_key) != 32:
            logger.error(f"Clave simétrica inválida para descifrado (longitud: {len(symmetric_key) if symmetric_key else 0})")
            return encrypted_message
        
        try:
            # Decodificar mensaje cifrado
            combined = base64.b64decode(encrypted_message)
            
            # Verificar longitud mínima (nonce + longitud AAD)
            if len(combined) < 14:  # 12 bytes de nonce + 2 bytes de longitud AAD
                logger.error("Mensaje cifrado demasiado corto")
                return encrypted_message
            
            # Extraer componentes
            nonce = combined[:12]
            aad_length = int.from_bytes(combined[12:14], byteorder='big')
            
            # Verificar que el mensaje tiene suficiente longitud
            if len(combined) < 14 + aad_length:
                logger.error("Mensaje cifrado corrupto (AAD incompleto)")
                return encrypted_message
            
            aad = combined[14:14+aad_length]
            ciphertext = combined[14+aad_length:]
            
            # Crear descifrador
            aesgcm = AESGCM(symmetric_key)
            
            # Descifrar mensaje con AAD
            try:
                plaintext = aesgcm.decrypt(nonce, ciphertext, aad)
                return plaintext.decode('utf-8')
            except Exception as e:
                # Si falla con AAD, intentar sin AAD (compatibilidad con versiones anteriores)
                logger.warning(f"Error al descifrar con AAD, intentando sin AAD: {e}")
                plaintext = aesgcm.decrypt(nonce, ciphertext, None)
                return plaintext.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Error al descifrar mensaje: {e}")
            logger.debug(traceback.format_exc())
            return encrypted_message
    
    def register_user_key(self, user_id: str, public_key_pem: str) -> bool:
        """
        Registra la clave pública de un usuario
        
        Args:
            user_id: ID del usuario
            public_key_pem: Clave pública en formato PEM
            
        Returns:
            True si se registró correctamente, False en caso contrario
        """
        if not CRYPTO_AVAILABLE:
            return False
        
        try:
            # Cargar clave pública
            public_key = load_pem_public_key(public_key_pem.encode('utf-8'))
            
            # Generar clave simétrica para este usuario
            symmetric_key = self.generate_symmetric_key()
            
            # Cifrar clave simétrica con la clave pública del usuario
            encrypted_key = self.encrypt_symmetric_key(symmetric_key, public_key)
            
            # Guardar información del usuario
            self.user_keys[user_id] = {
                "public_key": public_key_pem,
                "symmetric_key": base64.b64encode(symmetric_key).decode('utf-8'),
                "encrypted_symmetric_key": encrypted_key,
                "created_at": datetime.now().isoformat(),
                "last_rotation": datetime.now().isoformat()
            }
            
            # Guardar cambios
            self._save_user_keys()
            
            return True
        except Exception as e:
            logger.error(f"Error al registrar clave de usuario: {e}")
            return False
    
    def rotate_user_key(self, user_id: str) -> bool:
        """
        Rota la clave simétrica de un usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            True si se rotó correctamente, False en caso contrario
        """
        if not CRYPTO_AVAILABLE:
            logger.warning("No se pueden rotar claves: cryptography no está disponible")
            return False
        
        if user_id not in self.user_keys:
            logger.error(f"No se encontró el usuario {user_id} para rotación de clave")
            return False
        
        try:
            # Guardar la clave anterior para mantener acceso a mensajes antiguos
            old_key = self.user_keys[user_id]["symmetric_key"]
            
            # Cargar clave pública del usuario
            public_key_pem = self.user_keys[user_id]["public_key"]
            public_key = load_pem_public_key(public_key_pem.encode('utf-8'))
            
            # Generar nueva clave simétrica
            new_symmetric_key = self.generate_symmetric_key()
            
            # Cifrar nueva clave simétrica
            encrypted_key = self.encrypt_symmetric_key(new_symmetric_key, public_key)
            
            # Actualizar información del usuario
            if "previous_keys" not in self.user_keys[user_id]:
                self.user_keys[user_id]["previous_keys"] = []
            
            # Guardar la clave anterior con su fecha de uso
            self.user_keys[user_id]["previous_keys"].append({
                "key": old_key,
                "start_date": self.user_keys[user_id].get("last_rotation", datetime.now().isoformat()),
                "end_date": datetime.now().isoformat()
            })
            
            # Limitar el historial de claves (mantener máximo 5 claves anteriores)
            if len(self.user_keys[user_id]["previous_keys"]) > 5:
                self.user_keys[user_id]["previous_keys"] = self.user_keys[user_id]["previous_keys"][-5:]
            
            # Actualizar la clave actual
            self.user_keys[user_id]["symmetric_key"] = base64.b64encode(new_symmetric_key).decode('utf-8')
            self.user_keys[user_id]["encrypted_symmetric_key"] = encrypted_key
            self.user_keys[user_id]["last_rotation"] = datetime.now().isoformat()
            
            # Guardar cambios
            if not self._save_user_keys():
                logger.error("No se pudieron guardar las claves después de la rotación")
                return False
            
            logger.info(f"Clave rotada correctamente para el usuario {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error al rotar clave de usuario {user_id}: {e}")
            logger.debug(traceback.format_exc())
            return False
    
    def check_key_rotation(self) -> None:
        """Verifica si es necesario rotar las claves de los usuarios"""
        if not CRYPTO_AVAILABLE:
            return
        
        try:
            current_time = datetime.now()
            rotated_count = 0
            
            for user_id, user_data in list(self.user_keys.items()):
                try:
                    last_rotation = datetime.fromisoformat(user_data["last_rotation"])
                    days_since_rotation = (current_time - last_rotation).days
                    
                    # Registrar información sobre la antigüedad de las claves
                    if days_since_rotation > self.key_rotation_days * 0.8:  # Advertencia al 80% del tiempo
                        logger.warning(f"Clave del usuario {user_id} próxima a expirar: {days_since_rotation} días")
                    
                    if days_since_rotation > self.key_rotation_days:
                        logger.info(f"Rotando clave para usuario {user_id} (antigüedad: {days_since_rotation} días)")
                        if self.rotate_user_key(user_id):
                            rotated_count += 1
                except (ValueError, KeyError) as e:
                    logger.error(f"Error al procesar rotación para usuario {user_id}: {e}")
                    # Corregir datos corruptos
                    user_data["last_rotation"] = current_time.isoformat()
            
            if rotated_count > 0:
                logger.info(f"Se rotaron {rotated_count} claves de usuario")
        except Exception as e:
            logger.error(f"Error al verificar rotación de claves: {e}")
            logger.debug(traceback.format_exc())
    
    def encrypt_conversation(self, user_id: str, conversation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cifra una conversación completa para un usuario
        
        Args:
            user_id: ID del usuario
            conversation: Conversación a cifrar
            
        Returns:
            Conversación cifrada o la conversación original si ocurre un error
        """
        if not CRYPTO_AVAILABLE:
            logger.warning("No se puede cifrar la conversación: cryptography no está disponible")
            return conversation
        
        if not conversation:
            return conversation
        
        if user_id not in self.user_keys:
            logger.error(f"No se encontró el usuario {user_id} para cifrado de conversación")
            return conversation
        
        try:
            # Obtener clave simétrica del usuario
            symmetric_key = base64.b64decode(self.user_keys[user_id]["symmetric_key"])
            
            # Crear una copia profunda para no modificar el original
            encrypted_conversation = json.loads(json.dumps(conversation))
            
            # Añadir metadatos de cifrado
            encrypted_conversation["_encryption"] = {
                "encrypted": True,
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "version": "1.0"
            }
            
            # Cifrar mensajes
            if "messages" in encrypted_conversation:
                for i, message in enumerate(encrypted_conversation["messages"]):
                    # Cifrar el contenido del mensaje
                    if "content" in message and isinstance(message["content"], str):
                        encrypted_conversation["messages"][i]["content"] = self.encrypt_message(
                            message["content"], symmetric_key
                        )
                    
                    # Cifrar metadatos sensibles si existen
                    for sensitive_field in ["name", "email", "phone", "personal_info"]:
                        if sensitive_field in message and isinstance(message[sensitive_field], str):
                            encrypted_conversation["messages"][i][sensitive_field] = self.encrypt_message(
                                message[sensitive_field], symmetric_key
                            )
            
            return encrypted_conversation
        except Exception as e:
            logger.error(f"Error al cifrar conversación para usuario {user_id}: {e}")
            logger.debug(traceback.format_exc())
            return conversation
    
    def decrypt_conversation(self, user_id: str, encrypted_conversation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Descifra una conversación completa para un usuario
        
        Args:
            user_id: ID del usuario
            encrypted_conversation: Conversación cifrada
            
        Returns:
            Conversación descifrada o la conversación cifrada original si ocurre un error
        """
        if not CRYPTO_AVAILABLE:
            logger.warning("No se puede descifrar la conversación: cryptography no está disponible")
            return encrypted_conversation
        
        if not encrypted_conversation:
            return encrypted_conversation
        
        # Verificar si la conversación está cifrada
        if not encrypted_conversation.get("_encryption", {}).get("encrypted", False):
            logger.debug("La conversación no está cifrada, se devuelve sin cambios")
            return encrypted_conversation
        
        if user_id not in self.user_keys:
            logger.error(f"No se encontró el usuario {user_id} para descifrado de conversación")
            return encrypted_conversation
        
        try:
            # Obtener clave simétrica del usuario
            symmetric_key = base64.b64decode(self.user_keys[user_id]["symmetric_key"])
            
            # Crear una copia profunda para no modificar el original
            decrypted_conversation = json.loads(json.dumps(encrypted_conversation))
            
            # Descifrar mensajes
            if "messages" in decrypted_conversation:
                for i, message in enumerate(decrypted_conversation["messages"]):
                    # Descifrar el contenido del mensaje
                    if "content" in message and isinstance(message["content"], str):
                        decrypted_conversation["messages"][i]["content"] = self.decrypt_message(
                            message["content"], symmetric_key
                        )
                    
                    # Descifrar metadatos sensibles si existen
                    for sensitive_field in ["name", "email", "phone", "personal_info"]:
                        if sensitive_field in message and isinstance(message[sensitive_field], str):
                            decrypted_conversation["messages"][i][sensitive_field] = self.decrypt_message(
                                message[sensitive_field], symmetric_key
                            )
            
            # Si la conversación no se pudo descifrar con la clave actual, intentar con claves anteriores
            if "previous_keys" in self.user_keys[user_id] and self._is_conversation_still_encrypted(decrypted_conversation):
                logger.info(f"Intentando descifrar con claves anteriores para usuario {user_id}")
                for key_data in reversed(self.user_keys[user_id]["previous_keys"]):
                    try:
                        old_key = base64.b64decode(key_data["key"])
                        temp_decrypted = self._try_decrypt_with_key(encrypted_conversation, old_key)
                        if not self._is_conversation_still_encrypted(temp_decrypted):
                            logger.info(f"Conversación descifrada con clave anterior (fecha: {key_data['end_date']})")
                            return temp_decrypted
                    except Exception as e:
                        logger.warning(f"Error al intentar descifrar con clave anterior: {e}")
            
            # Marcar como descifrado
            if "_encryption" in decrypted_conversation:
                decrypted_conversation["_encryption"]["decrypted"] = True
                decrypted_conversation["_encryption"]["decryption_timestamp"] = datetime.now().isoformat()
            
            return decrypted_conversation
        except Exception as e:
            logger.error(f"Error al descifrar conversación para usuario {user_id}: {e}")
            logger.debug(traceback.format_exc())
            return encrypted_conversation
    
    def _is_conversation_still_encrypted(self, conversation: Dict[str, Any]) -> bool:
        """
        Verifica si una conversación sigue cifrada después de un intento de descifrado
        
        Args:
            conversation: Conversación a verificar
            
        Returns:
            True si la conversación parece seguir cifrada, False en caso contrario
        """
        if "messages" not in conversation or not conversation["messages"]:
            return False
        
        # Tomar una muestra de mensajes para verificar
        sample_messages = conversation["messages"][:min(5, len(conversation["messages"]))]
        
        for message in sample_messages:
            if "content" in message and isinstance(message["content"], str):
                content = message["content"]
                # Verificar si el contenido parece estar en base64 (posiblemente cifrado)
                if len(content) > 20 and all(c in base64.b64encode(b'').decode('ascii') for c in content):
                    try:
                        # Intentar decodificar como base64
                        decoded = base64.b64decode(content)
                        # Si se puede decodificar y parece binario, probablemente sigue cifrado
                        if len(decoded) > 12 and not all(32 <= b <= 126 for b in decoded[:20]):
                            return True
                    except:
                        pass
        
        return False
    
    def _try_decrypt_with_key(self, encrypted_conversation: Dict[str, Any], key: bytes) -> Dict[str, Any]:
        """
        Intenta descifrar una conversación con una clave específica
        
        Args:
            encrypted_conversation: Conversación cifrada
            key: Clave simétrica para intentar el descifrado
            
        Returns:
            Conversación descifrada o la conversación original si falla
        """
        try:
            # Crear una copia profunda para no modificar el original
            decrypted_conversation = json.loads(json.dumps(encrypted_conversation))
            
            # Descifrar mensajes
            if "messages" in decrypted_conversation:
                for i, message in enumerate(decrypted_conversation["messages"]):
                    # Descifrar el contenido del mensaje
                    if "content" in message and isinstance(message["content"], str):
                        try:
                            decrypted_conversation["messages"][i]["content"] = self.decrypt_message(
                                message["content"], key
                            )
                        except:
                            # Ignorar errores individuales al descifrar mensajes
                            pass
                    
                    # Descifrar metadatos sensibles si existen
                    for sensitive_field in ["name", "email", "phone", "personal_info"]:
                        if sensitive_field in message and isinstance(message[sensitive_field], str):
                            try:
                                decrypted_conversation["messages"][i][sensitive_field] = self.decrypt_message(
                                    message[sensitive_field], key
                                )
                            except:
                                # Ignorar errores individuales al descifrar campos
                                pass
            
            return decrypted_conversation
        except Exception as e:
            logger.error(f"Error al intentar descifrar con clave alternativa: {e}")
            return encrypted_conversation

    def verify_encryption_system(self) -> Dict[str, Any]:
        """
        Verifica la integridad del sistema de cifrado
        
        Returns:
            Diccionario con el resultado de la verificación
        """
        result = {
            "status": "ok",
            "crypto_available": CRYPTO_AVAILABLE,
            "issues": [],
            "recommendations": []
        }
        
        if not CRYPTO_AVAILABLE:
            result["status"] = "error"
            result["issues"].append("Las dependencias de criptografía no están disponibles")
            result["recommendations"].append("Instalar cryptography: pip install cryptography")
            return result
        
        # Verificar claves RSA
        if not self.private_key:
            result["status"] = "error"
            result["issues"].append("No se pudo cargar la clave privada RSA")
            result["recommendations"].append("Generar nuevas claves RSA")
        
        if not self.public_key:
            result["status"] = "error"
            result["issues"].append("No se pudo cargar la clave pública RSA")
            result["recommendations"].append("Generar nuevas claves RSA")
        
        # Verificar permisos de archivos en sistemas Unix
        if os.name == 'posix':
            private_key_path = os.path.join(self.key_directory, "private_key.pem")
            if os.path.exists(private_key_path):
                permissions = oct(os.stat(private_key_path).st_mode & 0o777)
                if permissions != '0o600':
                    result["status"] = "warning"
                    result["issues"].append(f"Permisos inseguros en clave privada: {permissions}")
                    result["recommendations"].append("Establecer permisos 600 en clave privada: chmod 600 private_key.pem")
        
        # Verificar claves de usuario
        if not self.user_keys:
            result["status"] = "warning"
            result["issues"].append("No hay claves de usuario registradas")
        else:
            # Verificar rotación de claves
            current_time = datetime.now()
            for user_id, user_data in self.user_keys.items():
                try:
                    last_rotation = datetime.fromisoformat(user_data["last_rotation"])
                    days_since_rotation = (current_time - last_rotation).days
                    
                    if days_since_rotation > self.key_rotation_days:
                        result["status"] = "warning"
                        result["issues"].append(f"Clave del usuario {user_id} expirada: {days_since_rotation} días")
                        result["recommendations"].append(f"Rotar clave del usuario {user_id}")
                except (ValueError, KeyError):
                    result["status"] = "warning"
                    result["issues"].append(f"Datos de rotación inválidos para usuario {user_id}")
                    result["recommendations"].append(f"Corregir datos de usuario {user_id}")
        
        # Realizar prueba de cifrado/descifrado
        try:
            test_message = f"Test message {datetime.now().isoformat()}"
            test_key = self.generate_symmetric_key()
            encrypted = self.encrypt_message(test_message, test_key)
            decrypted = self.decrypt_message(encrypted, test_key)
            
            if decrypted != test_message:
                result["status"] = "error"
                result["issues"].append("La prueba de cifrado/descifrado falló")
                result["recommendations"].append("Verificar la implementación de cifrado")
        except Exception as e:
            result["status"] = "error"
            result["issues"].append(f"Error en prueba de cifrado: {e}")
        
        # Añadir información adicional
        result["key_directory"] = self.key_directory
        result["key_rotation_days"] = self.key_rotation_days
        result["user_count"] = len(self.user_keys)
        
        return result

# Instancia global del sistema de cifrado
encryption_service = E2EEncryption() if CRYPTO_AVAILABLE else None 