# -*- coding: utf-8 -*-
"""パーカッション"""
import sys
import time
import threading
import serial
import bluetooth
import pandas as pd
import config
from library import bt, head, serial_connect

PATH = "hand.csv"


class Lag:
    def __init__(self, period):
        self.__start_time = None
        self.__period = 0.01
        self.__loop_count = 0

    def get_lag(self,  send_time):
        self.__loop_count += 1
        if self.__start_time is None:
            self.__start_time = send_time
        if self.__start_time + self.__period*self.__loop_count - time.time() < 0:
            return 0
        return self.__start_time + self.__period*self.__loop_count - time.time()


def calculate_send_data(*args) -> int:
    """送信データを1Byteごとに分割"""
    castanets, shaker, tambourine, motion, color = args
    send_val = castanets*2**31+shaker*2**30+tambourine*2**29\
        + motion*2**27+color*2**24+0b111111111111111111111111
    return send_val


def generate_send_data(path: str) -> list:
    """送信するデータの配列とBPMを返す"""
    original_df = pd.read_csv(path)
    original_data = pd.DataFrame(index=None)
    for key in head.PERCUSSION:
        original_data[key] = original_df[key].fillna(0)

    return [calculate_send_data(*list(d[1:]))
            for d in original_data.itertuples()]


def setup() -> list:
    """セットアップ"""
    try:
        bt_sock = bt.BluetoothChild(1)
        bt_sock.connect()
        bpm = bt_sock.receive(8)
        maicon = serial_connect.Connection(
            dev="/dev/ttyACM0", rate=115200, data_size=config.BYTE_SIZE)
        bt_sock.send(1, 1)
        start_time = bt_sock.receive(64)/10000000
    except serial.SerialException:
        sys.exit("Setup Failed")
    except bluetooth.BluetoothError:
        sys.exit("Setup Failed")
    else:
        return [bt_sock, maicon, start_time, bpm]


def status_check(socket: bluetooth.BluetoothSocket) -> int:
    """ステータスのチェック"""
    while True:
        try:
            receive = socket.receive(1)
        except bluetooth.BluetoothError:
            print("BluetoothError")
            socket.send(1, 1)
            return
        else:
            return receive


def format_data(value):
    d1, d2, d3 = int((value & 2**31) / 2**31), int((value & 2 **
                                                    30) / 2**30), int((value & 2**29) / 2**29)
    m, c = int((value & 2**27) / 2**27), int((value & 2**24) / 2**24)
    return f"c:{d1}, s:{d2}, t:{d3}, m:{m}, c:{c}"


def main_connection(socket, maicon, start_time, bpm):
    """main"""
    generated_data = generate_send_data(f"../data/fixed/{PATH}")
    lag = Lag(60/bpm)
    try:

        if start_time <= 0:
            raise Exception("Failed")
        if start_time-time.time() > 0.2:
            time.sleep(start_time-time.time()-0.2)
        while start_time - time.time() > 0:
            time.sleep(0.001)

        if not maicon.is_aivable:
            return
        play_start = time.time()
        for sd in generated_data:
            send_time = time.time()
            time.sleep(config.PERCUSSION_DELAY)
            maicon.write(sd)
            print(f"{'{:.5f}'.format(time.time() - play_start)} {format_data(sd)}")
            time.sleep(lag.get_lag(send_time))

    except serial.SerialException:
        print("Process is Failed")
    except KeyboardInterrupt:
        print("Process is Failed")
    else:
        print("Connection Ended")
    finally:
        del maicon
        socket.send(1, 1)


def main():
    socket, maicon, start_time, bpm = setup()

    sub_thread = threading.Thread(
        target=main_connection, args=([socket, maicon, start_time, bpm]))
    main_thread = threading.Thread(
        target=status_check, args=([socket]))
    sub_thread.setDaemon(True)
    main_thread.start()
    sub_thread.start()
    try:
        main_thread.join()
        if sub_thread.is_alive():
            print("Process is Killed from master")
    except KeyboardInterrupt:
        socket.send(1, 1)
    sys.exit(0)


if __name__ == "__main__":
    main()
