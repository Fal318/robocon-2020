# -*- coding: utf-8 -*-
"""送信側のプログラム"""
import sys
import time
import threading
import pandas as pd
import bluetooth as bt
import address as ad
from library import key
from library import bt_connect
from library import program_number

csv_data = pd.read_csv("../data/csv/merged.csv", header=0)


args = sys.argv
is_debug = False
if len(args) > 1 and args[1] == "-d":
    is_debug = True


TARGET: int = 2
PERIOD: float = 0.09

"""
TARGET:接続する台数
PERIOD:実行周期(sec)
id:
    0:ウクレレ
    1:パーカッション
"""


def csv_to_senddata(id_num: int) -> list:
    """CSVから送信用データに変換する"""
    program_nums: list = None
    if id_num == 0:
        program_nums = program_number.UKULELE
    if id_num == 1:
        program_nums = program_number.PERCUSSION
    if program_nums is None:
        return None
    arrs = [[] for _ in range(len(program_nums))]

    for (i, program_num) in enumerate(program_nums):
        for sound in csv_data[str(program_num)]:
            arrs[i].append(str(sound))
    if id_num == 0:
        return [[key.chord_to_value(a) if a != "nan" else 1 for a in arr]for arr in arrs]
    if id_num == 1:
        ret_arr = [[1 for _ in range(len(arrs[0]))]]
        for (i, arr) in enumerate(arrs):
            for (j, element) in enumerate(arr):
                if element != "nan":
                    ret_arr[0][j] += 2**i
        return ret_arr
    return None


class Connection:
    """通信を定周期で行うためのクラス"""

    def __init__(self, proc_id: int):
        self.sending_data: list = csv_to_senddata(proc_id)  # 送るデータ
        self.rcv_data: list = []  # 受け取ったデータ
        self.sendtime: float = None  # 最後に送信をした時間
        self.proc_id: int = proc_id  # プロセスを識別するID

        try:
            # 通信用のインスタンスを生成
            self.ras = bt_connect.Connect("ras{0}".format(
                self.proc_id), ad.CLIENT[proc_id], 1, is_debug)

            if self.ras.connectbluetooth(self.ras.bdaddr, self.ras.port):
                self.aivable = True
                print("Connect")
            else:
                self.aivable = False
                print("Connection Failed")
        except IndexError:
            self.aivable = False

    def is_aivable(self) -> bool:
        """プロセスが有効かどうかを返す関数"""
        return self.aivable

    def sender(self, data: int):
        """データ(整数値)を送信する関数"""
        self.sendtime = time.time()
        self.ras.sock.send((data).to_bytes(1, "little"))
        print("target={0} send:{1}".format(self.proc_id, data))

    def receiveer(self):
        """データを受信する関数"""
        self.rcv_data.append(int.from_bytes(
            self.ras.sock.recv(1024), "little"))
        print("host:{0} recv:{1}".format(self.proc_id, self.rcv_data[-1]))

    def main_process(self, period: int):
        """メインプロセス"""
        try:
            for send in self.sending_data[0]:
                self.sender(send)
                time.sleep(period - (time.time() - self.sendtime))
        except KeyboardInterrupt:
            self.sender(0)
            print("Connection Killed")
        except ValueError:
            self.sender(0)
            print("周期が早すぎます")
        except bt.BluetoothError:
            print("Connection Killed")
        else:
            self.sender(0)

    def __del__(self):
        self.ras.disconnect()


def main() -> int:
    """メイン"""
    if len(ad.CLIENT) < TARGET:
        print("len(address) < TARGET")
        return 1
    rass, threads = [], []
    for i in range(TARGET):
        ras = Connection(i)
        if ras.is_aivable():
            rass.append(ras)
            thread = threading.Thread(
                target=ras.main_process, args=([PERIOD]))
            threads.append(thread)

    for thread in threads:
        thread.start()

    for ras in rass:
        del ras
    return 0


if __name__ == "__main__":
    main()
