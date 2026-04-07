"""GPG 密钥管理。

负责系统级的非对称加密密钥生成、文件存储以及挑战令牌的解密验证。
"""

import os
import logging
import pgpy
from pgpy.constants import (
    PubKeyAlgorithm,
    KeyFlags,
    HashAlgorithm,
    SymmetricKeyAlgorithm,
)

logger = logging.getLogger(__name__)


class GPGKeyManager:
    """内部辅助：负责 RSA 密钥对的持久化与解密逻辑。"""

    def __init__(self, key_file: str):
        self._key_file = key_file
        self.private_key = None
        self.public_key_armor = ""
        self._load_or_generate()

    def _load_or_generate(self):
        """从文件系统加载密钥，不存在或损坏则创建一个 2048 位 RSA 密钥。"""
        if os.path.exists(self._key_file):
            try:
                k, _ = pgpy.PGPKey.from_file(self._key_file)
                self.private_key, self.public_key_armor = k, str(k.pubkey)
                return
            except (ValueError, Exception):
                logger.warning("密钥文件损坏，将重新生成: %s", self._key_file)

        k = pgpy.PGPKey.new(PubKeyAlgorithm.RSAEncryptOrSign, 2048)
        u = pgpy.PGPUID.new("CIMS Server", comment="ClassIsland")
        k.add_uid(
            u,
            usage={KeyFlags.EncryptCommunications},
            hashes=[HashAlgorithm.SHA256],
            ciphers=[SymmetricKeyAlgorithm.AES256],
        )
        self.private_key, self.public_key_armor = k, str(k.pubkey)
        with open(self._key_file, "w") as f:
            f.write(str(k))

    def decrypt(self, encrypted: str) -> str:
        """解密客户端发回的加密挑战令牌。"""
        try:
            msg = pgpy.PGPMessage.from_blob(encrypted)
            raw = self.private_key.decrypt(msg).message
            return bytes(raw) if isinstance(raw, bytearray) else raw
        except Exception as e:
            logger.error("解密失败: %s", e)
            return None
