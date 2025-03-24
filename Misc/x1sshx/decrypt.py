import sys
from Crypto.Cipher import AES
from Crypto.Util import Counter


class Encrypt:
    def __init__(self, aes_key):
        if len(aes_key) != 16:
            raise ValueError("AES key must be 16 bytes long")
        self.aes_key = aes_key

    def segment(self, stream_num, offset, data):
        if stream_num == 0:
            raise ValueError("stream number must be nonzero")

        # 生成8字节大端表示的nonce
        nonce = stream_num.to_bytes(8, 'big')

        # 创建CTR模式的计数器，前8字节为nonce，后8字节从0开始计数（大端）
        counter = Counter.new(
            64, prefix=nonce, initial_value=0, little_endian=False)
        cipher = AES.new(self.aes_key, AES.MODE_CTR, counter=counter)

        # 跳过指定offset长度的密钥流
        cipher.encrypt(bytes(offset))

        # 加密/解密数据
        return cipher.encrypt(data)


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <offset> <data_hex>")
        sys.exit(1)

    try:
        offset = int(sys.argv[1])
        data_hex = sys.argv[2].strip()
        data = bytes.fromhex(data_hex)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # 初始化加密器（使用硬编码密钥）
    key = bytes.fromhex("c01acd129bb7e38eb37f931856960840")
    encryptor = Encrypt(key)

    # 计算stream_num (0x100000000 | 1)
    stream_num = (0x100000000 | 1)

    try:
        decrypted = encryptor.segment(stream_num, offset, data)
        print(f"Decrypted data: 0x{decrypted.hex()}")
    except Exception as e:
        print(f"Error during decryption: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
