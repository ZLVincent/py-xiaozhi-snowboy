#!/usr/bin/python
# -*- coding: UTF-8 -*-
import json
import time
import requests
import paho.mqtt.client as mqtt
import threading
import pyaudio
import opuslib  # windwos平台需要将opus.dll 拷贝到C:\Windows\System32
import socket
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from os import urandom
from common import logging, utils
import os
import wave

logger = logging.getLogger(__name__)

OTA_VERSION_URL = 'https://api.tenclass.net/xiaozhi/ota/'
MAC_ADDR = 'cd:69:f9:9d:b9:ba'
#MAC_ADDR = 'cd:68:f8:8d:b8:ba'
# {"mqtt":{"endpoint":"post-cn-apg3xckag01.mqtt.aliyuncs.com","client_id":"GID_test@@@cc_ba_97_20_b4_bc",
# "username":"Signature|LTAI5tF8J3CrdWmRiuTjxHbF|post-cn-apg3xckag01","password":"0mrkMFELXKyelhuYy2FpGDeCigU=",
# "publish_topic":"device-server","subscribe_topic":"devices"},"firmware":{"version":"0.9.9","url":""}}
mqtt_info = {}
aes_opus_info = {"type": "hello", "version": 3, "transport": "udp",
                 "udp": {"server": "120.24.160.13", "port": 8884, "encryption": "aes-128-ctr",
                         "key": "263094c3aa28cb42f3965a1020cb21a7", "nonce": "01000000ccba9720b4bc268100000000"},
                 "audio_params": {"format": "opus", "sample_rate": 24000, "channels": 1, "frame_duration": 60},
                 "session_id": "b23ebfe9"}

iot_msg = {"session_id": "635aa42d", "type": "iot",
           "descriptors": [{"name": "Speaker", "description": "当前 AI 机器人的扬声器",
                            "properties": {"volume": {"description": "当前音量值", "type": "number"}},
                            "methods": {"SetVolume": {"description": "设置音量",
                                                      "parameters": {
                                                          "volume": {"description": "0到100之间的整数", "type": "number"}
                                                      }
                                                      }
                                        }
                            },
                           {"name": "Lamp", "description": "一个测试用的灯",
                            "properties": {"power": {"description": "灯是否打开", "type": "boolean"}},
                            "methods": {"TurnOn": {"description": "打开灯", "parameters": {}},
                                        "TurnOff": {"description": "关闭灯", "parameters": {}}
                                        }
                            }
                           ]
           }
iot_status_msg = {"session_id": "635aa42d", "type": "iot", "states": [
    {"name": "Speaker", "state": {"volume": 50}}, {"name": "Lamp", "state": {"power": False}}]}
goodbye_msg = {"session_id": "b23ebfe9", "type": "goodbye"}
local_sequence = 0
listen_state = None
audio = None
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# udp_socket.setblocking(False)
conn_state = False
recv_audio_thread = threading.Thread()
# 创建停止标志
stop_event = threading.Event()
mqttc = None

TOP_DIR = os.path.dirname(os.path.abspath(__file__))
DETECT_DING = os.path.join(TOP_DIR, "snowboy/resources/ding.wav")

def get_ota_version():
    global mqtt_info
    header = {
        'Device-Id': MAC_ADDR,
        'Content-Type': 'application/json'
    }
    post_data = {"flash_size": 16777216, "minimum_free_heap_size": 8318916, "mac_address": f"{MAC_ADDR}",
                 "chip_model_name": "esp32s3", "chip_info": {"model": 9, "cores": 2, "revision": 2, "features": 18},
                 "application": {"name": "xiaozhi", "version": "0.9.9", "compile_time": "Jan 22 2025T20:40:23Z",
                                 "idf_version": "v5.3.2-dirty",
                                 "elf_sha256": "22986216df095587c42f8aeb06b239781c68ad8df80321e260556da7fcf5f522"},
                 "partition_table": [{"label": "nvs", "type": 1, "subtype": 2, "address": 36864, "size": 16384},
                                     {"label": "otadata", "type": 1, "subtype": 0, "address": 53248, "size": 8192},
                                     {"label": "phy_init", "type": 1, "subtype": 1, "address": 61440, "size": 4096},
                                     {"label": "model", "type": 1, "subtype": 130, "address": 65536, "size": 983040},
                                     {"label": "storage", "type": 1, "subtype": 130, "address": 1048576,
                                      "size": 1048576},
                                     {"label": "factory", "type": 0, "subtype": 0, "address": 2097152, "size": 4194304},
                                     {"label": "ota_0", "type": 0, "subtype": 16, "address": 6291456, "size": 4194304},
                                     {"label": "ota_1", "type": 0, "subtype": 17, "address": 10485760,
                                      "size": 4194304}],
                 "ota": {"label": "factory"},
                 "board": {"type": "bread-compact-wifi", "ssid": "mzy", "rssi": -58, "channel": 6,
                           "ip": "192.168.124.38", "mac": f"{MAC_ADDR}"}}

    response = requests.post(OTA_VERSION_URL, headers=header, data=json.dumps(post_data))
    logger.info('=========================')
    logger.info(response.text)
    logger.info(f"get version: {response}")
    mqtt_info = response.json()['mqtt']

def aes_ctr_encrypt(key, nonce, plaintext):
    cipher = Cipher(algorithms.AES(key), modes.CTR(nonce), backend=default_backend())
    encryptor = cipher.encryptor()
    return encryptor.update(plaintext) + encryptor.finalize()

def aes_ctr_decrypt(key, nonce, ciphertext):
    cipher = Cipher(algorithms.AES(key), modes.CTR(nonce), backend=default_backend())
    decryptor = cipher.decryptor()
    plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    return plaintext

def send_audio(audio_stream=None):
    global aes_opus_info, udp_socket, local_sequence
    key = aes_opus_info['udp']['key']
    nonce = aes_opus_info['udp']['nonce']
    server_ip = aes_opus_info['udp']['server']
    server_port = aes_opus_info['udp']['port']
    logger.info(f"{server_ip} : {server_port}")
    # 初始化Opus编码器
    encoder = opuslib.Encoder(16000, 1, opuslib.APPLICATION_AUDIO)
    try:
        # 编码音频数据
        frame_size = len(audio_stream) // 2
        encoded_data = encoder.encode(audio_stream, frame_size)
        # 打印音频数据
        # print(f"Encoded data: {len(encoded_data)}")
        # nonce插入data.size local_sequence_
        local_sequence += 1
        new_nonce = nonce[0:4] + format(len(encoded_data), '04x') + nonce[8:24] + format(local_sequence, '08x')
        # 加密数据，添加nonce
        encrypt_encoded_data = aes_ctr_encrypt(bytes.fromhex(key), bytes.fromhex(new_nonce), bytes(encoded_data))
        data = bytes.fromhex(new_nonce) + encrypt_encoded_data
        sent = udp_socket.sendto(data, (server_ip, server_port))
        logger.info(sent)
        EndListen()
    except Exception as e:
        logger.critical(f"send audio err: {e}")

def recv_audio():
    global aes_opus_info, udp_socket, audio
    key = aes_opus_info['udp']['key']
    nonce = aes_opus_info['udp']['nonce']
    sample_rate = aes_opus_info['audio_params']['sample_rate']
    frame_duration = aes_opus_info['audio_params']['frame_duration']
    frame_num = int(frame_duration / (1000 / sample_rate))
    logger.info(f"recv audio: sample_rate -> {sample_rate}, frame_duration -> {frame_duration}, frame_num -> {frame_num}")
    # 初始化Opus编码器
    decoder = opuslib.Decoder(sample_rate, 1)
    try:
        spk = audio.open(format=pyaudio.paInt16, channels=1, rate=sample_rate, output=True, frames_per_buffer=frame_num)
        while not stop_event.is_set():
            data, server = udp_socket.recvfrom(4096)
            logger.info(f"Received from server {server}: {len(data)}")
            if len(data) == 0:
                continue
            encrypt_encoded_data = data
            # 解密数据,分离nonce
            split_encrypt_encoded_data_nonce = encrypt_encoded_data[:16]
            # 十六进制格式打印nonce
            # print(f"split_encrypt_encoded_data_nonce: {split_encrypt_encoded_data_nonce.hex()}")
            split_encrypt_encoded_data = encrypt_encoded_data[16:]
            decrypt_data = aes_ctr_decrypt(bytes.fromhex(key),
                                           split_encrypt_encoded_data_nonce,
                                           split_encrypt_encoded_data)
            # 解码播放音频数据
            spk.write(decoder.decode(decrypt_data, frame_num))
        logger.info("recv_audio task exit")
    # except BlockingIOError:
    #     # 无数据时短暂休眠以减少CPU占用
    #     time.sleep(0.1)
    except Exception as e:
        logger.critical(f"recv audio err: {e}")
    finally:
        spk.stop_stream()
        spk.close()

def on_message(client, userdata, message):
    global aes_opus_info, udp_socket, tts_state, recv_audio_thread
    msg = json.loads(message.payload)
    logger.info(f"recv msg: {msg}")
    if udp_socket:
        logger.info("udp_socket exit")
    if aes_opus_info:
        logger.info(aes_opus_info['session_id'])
    if msg['type'] == 'hello':
        aes_opus_info = msg
        udp_socket.connect((msg['udp']['server'], msg['udp']['port']))
        # 发送 iot msg
        # iot_msg['session_id'] = msg['session_id']
        # push_mqtt_msg(iot_msg)
        # print(f"send iot message: {iot_msg}")
        # 发送 iot status消息
        # iot_status_msg['session_id'] = msg['session_id']
        # print(f"send iot status message: {iot_status_msg}")
        # push_mqtt_msg(iot_status_msg)
        # 检查recv_audio_thread线程是否启动
        if not recv_audio_thread.is_alive():
            # 启动一个线程，用于接收音频数据
            recv_audio_thread = threading.Thread(target=recv_audio)
            recv_audio_thread.start()
        else:
            logger.info("recv_audio_thread is alive")
        StartListen()
    elif msg['type'] == 'goodbye' and udp_socket and msg['session_id'] == aes_opus_info['session_id']:
        logger.info(f"recv good bye msg")
        stopRun()

def on_connect(client, userdata, flags, rs, pr):
    # subscribe_topic = mqtt_info['subscribe_topic'].split("/")[0] + '/p2p/GID_test@@@' + MAC_ADDR.replace(':', '_')
    # logger.info(f"subscribe topic: {subscribe_topic}")
    # 订阅主题
    # client.subscribe(subscribe_topic)
    logger.info("connect to mqtt server")

def push_mqtt_msg(message):
    global mqtt_info, mqttc
    mqttc.publish(mqtt_info['publish_topic'], json.dumps(message))

def play_audio_file(fname=DETECT_DING):
    """Simple callback function to play a wave file. By default it plays
    a Ding sound.

    :param str fname: wave file name
    :return: None
    """
    ding_wav = wave.open(fname, "rb")
    ding_data = ding_wav.readframes(ding_wav.getnframes())
    audio = pyaudio.PyAudio()
    stream_out = audio.open(
        format=audio.get_format_from_width(ding_wav.getsampwidth()),
        channels=ding_wav.getnchannels(),
        rate=ding_wav.getframerate(),
        input=False,
        output=True,
    )
    stream_out.start_stream()
    stream_out.write(ding_data)
    time.sleep(0.2)
    stream_out.stop_stream()
    stream_out.close()
    audio.terminate()

def sayHello():
    # 发送hello消息,建立udp连接
    hello_msg = {"type": "hello", "version": 3, "transport": "udp",
                 "audio_params": {"format": "opus", "sample_rate": 16000, "channels": 1, "frame_duration": 60}}
    push_mqtt_msg(hello_msg)
    logger.info(f"send hello message: {hello_msg}")

def StartListen():
    play_audio_file(DETECT_DING)
    msg = {"session_id": aes_opus_info['session_id'], "type": "listen", "state": "start", "mode": "manual"}
    push_mqtt_msg(msg)
    logger.info(f"send start listen message: {msg}")

def EndListen():
    msg = {"session_id": aes_opus_info['session_id'], "type": "listen", "state": "stop"}
    push_mqtt_msg(msg)
    logger.info(f"send stop listen message: {msg}")

def run():
    global mqtt_info, mqttc, audio
    audio = pyaudio.PyAudio()
    # 获取mqtt与版本信息
    get_ota_version()
    # 创建客户端实例
    mqttc = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2, client_id=mqtt_info['client_id'])
    mqttc.username_pw_set(username=mqtt_info['username'], password=mqtt_info['password'])
    mqttc.tls_set(ca_certs=None, certfile=None, keyfile=None, cert_reqs=mqtt.ssl.CERT_REQUIRED,
                  tls_version=mqtt.ssl.PROTOCOL_TLS, ciphers=None)
    mqttc.on_connect = on_connect
    mqttc.on_message = on_message
    mqttc.connect(host=mqtt_info['endpoint'], port=8883)
    mqttc.loop_start()
    # say hello
    sayHello()

def stopRun():
    global stop_event, udp_socket, mqttc
    # 通知线程停止
    stop_event.set()
    # 等待线程退出
    #recv_audio_thread.join()
    # socket
    udp_socket.shutdown(socket.SHUT_RDWR)
    udp_socket.close()
    udp_socket = None
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # mqtt
    mqttc.disconnect()
    mqttc.loop_stop()
    mqttc = None
    utils.setRecordable(True)
    logger.info("xiaozhi stoped")