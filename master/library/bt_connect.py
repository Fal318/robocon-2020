# -*- coding: utf-8 -*-
"""BT通信ライブラリ"""
import time
import bluetooth as bt


class Connect:
    """BT"""

    def __init__(self, name: str, addr: str, port: int):
        self.__name = name
        self.__bdaddr = addr
        self.__port = port
        self.__sock = bt.BluetoothSocket(bt.RFCOMM)

    @property
    def name(self):
        """名前"""
        return

    @name.getter
    def name(self) -> str:
        """getter"""
        return self.__name

    @name.setter
    def name(self, name: str):
        """setter"""
        self.__name = name

    @property
    def bdaddr(self):
        """bdaddr"""
        return

    @bdaddr.getter
    def bdaddr(self) -> str:
        """getter"""
        return self.__bdaddr

    @bdaddr.setter
    def bdaddr(self, value):
        """setter"""
        self.__bdaddr = value

    @property
    def port(self):
        """port"""
        return

    @port.getter
    def port(self) -> int:
        """getter"""
        return self.__port

    @port.setter
    def port(self, value: int):
        """setter"""
        self.__port = value

    @property
    def sock(self):
        """sock"""
        return

    @sock.getter
    def sock(self) -> bt.BluetoothSocket:
        """getter"""
        return self.__sock

    @sock.setter
    def sock(self, value: int):
        """setter"""
        self.__sock = value

    def reconnect(self):
        """再接続"""
        self.__sock = bt.BluetoothSocket(bt.RFCOMM)

    def connectbluetooth(self) -> bool:
        """接続"""

        while True:
            try:
                if isinstance(self.__sock, bt.BluetoothSocket):
                    self.__sock.connect((self.__bdaddr, self.__port))
                    time.sleep(1)
            except bt.BluetoothError:
                self.reconnect()
                time.sleep(0.25)
            except KeyboardInterrupt:
                break
            else:
                return True
        return False

    def set_timeout(self, timeout: int):
        """タイムアウトの設定"""
        self.__sock.settimeout(timeout)

    def disconnect(self):
        """切断"""
        self.__sock.close()


if __name__ == '__main__':
    pass
