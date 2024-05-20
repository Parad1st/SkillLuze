import ctypes
import cv2
import json
import math
import mss
import numpy as np
import os
import sys
import time
import torch
import uuid
import win32api

from termcolor import colored


PUL = ctypes.POINTER(ctypes.c_ulong)
class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort),
                ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong),
                ("wParamL", ctypes.c_short),
                ("wParamH", ctypes.c_ushort)]

class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.c_ulong),
                ("dwFlags", ctypes.c_ulong),
                ("time", ctypes.c_ulong),
                ("dwExtraInfo", PUL)]

class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput),
                ("mi", MouseInput),
                ("hi", HardwareInput)]

class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong),
                ("ii", Input_I)]

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class Aimbot:
    extra = ctypes.c_ulong(0)
    ii_ = Input_I()
    screen = mss.mss()
    pixel_increment = 1 #контролирует, сколько пикселей перемещается мышью за каждое относительное движение
    with open("lib/config/config.json") as f:
        sens_config = json.load(f)
    aimbot_status = colored("ENABLED", 'green')

    def __init__(self, box_constant = 416, collect_data = False, mouse_delay = 0.0001, debug = False):
        #контролирует начальную ширину и высоту центрированного прямоугольника окна оверлея.
        self.box_constant = box_constant #управляет размером области обнаружения (равной ширине и высоте)

        print("[INFO] Loading the neural network model (YOLOv5)")
        self.model = torch.hub.load('ultralytics/yolov5', 'custom', path='lib/best.pt', force_reload = True)
        if torch.cuda.is_available():
            print(colored("CUDA ACCELERATION [ENABLED]", "green"))
        else:
            print(colored("[!] CUDA ACCELERATION IS UNAVAILABLE", "red"))
            print(colored("[!] Check your PyTorch installation, otherwise performance will be poor.\n[!] Also try updating your Nvidia drivers.", "red"))

        self.model.conf = 0.45 # базовый порог достоверности (или базовое обнаружение (0-1)
        self.model.iou = 0.45 # NMS IoU (0-1)
        self.collect_data = collect_data
        self.mouse_delay = mouse_delay
        self.debug = debug

        print("\n[INFO] PRESS 'F1' TO TOGGLE AIMBOT\n[INFO] PRESS 'F2' TO QUIT\n[INFO] Hold the right mouse button for the aimbot to work")

    def update_status_aimbot():
        if Aimbot.aimbot_status == colored("ENABLED", 'green'):
            Aimbot.aimbot_status = colored("DISABLED", 'red')
        else:
            Aimbot.aimbot_status = colored("ENABLED", 'green')
        sys.stdout.write("\033[K")
        print(f"[!] AIMBOT IS [{Aimbot.aimbot_status}]", end = "\r")

    def left_click():
        ctypes.windll.user32.mouse_event(0x0002) #левая мышь вниз
        Aimbot.sleep(0.0001)
        ctypes.windll.user32.mouse_event(0x0004) #левая мышь вверх

    def sleep(duration, get_now = time.perf_counter):
        if duration == 0: return
        now = get_now()
        end = now + duration
        while now < end:
            now = get_now()

    def is_aimbot_enabled():
        return True if Aimbot.aimbot_status == colored("ENABLED", 'green') else False

    def is_targeted():
        return True if win32api.GetKeyState(0x02) in (-127, -128) else False

    def is_target_locked(x, y):
        #plus/minus 5 pixel threshold
        threshold = 5
        return True if 960 - threshold <= x <= 960 + threshold and 540 - threshold <= y <= 540 + threshold else False

    def move_crosshair(self, x, y):
        if Aimbot.is_targeted():
            scale = Aimbot.sens_config["targeting_scale"]
        else:
            return #TODO

        if self.debug: start_time = time.perf_counter()
        for rel_x, rel_y in Aimbot.interpolate_coordinates_from_center((x, y), scale):
            Aimbot.ii_.mi = MouseInput(rel_x, rel_y, 0, 0x0001, 0, ctypes.pointer(Aimbot.extra))
            input_obj = Input(ctypes.c_ulong(0), Aimbot.ii_)
            ctypes.windll.user32.SendInput(1, ctypes.byref(input_obj), ctypes.sizeof(input_obj))
            if not self.debug: Aimbot.sleep(self.mouse_delay) #time.sleep недостаточно точен
        if self.debug: #remove this later
            print(f"TIME: {time.perf_counter() - start_time}")
            print("DEBUG: SLEEPING FOR 1 SECOND")
            time.sleep(1)

    #generator выдает кортежи пикселей для относительного перемещения
    def interpolate_coordinates_from_center(absolute_coordinates, scale):
        diff_x = (absolute_coordinates[0] - 960) * scale/Aimbot.pixel_increment
        diff_y = (absolute_coordinates[1] - 540) * scale/Aimbot.pixel_increment
        length = int(math.dist((0,0), (diff_x, diff_y)))
        if length == 0: return
        unit_x = (diff_x/length) * Aimbot.pixel_increment
        unit_y = (diff_y/length) * Aimbot.pixel_increment
        x = y = sum_x = sum_y = 0
        for k in range(0, length):
            sum_x += x
            sum_y += y
            x, y = round(unit_x * k - sum_x), round(unit_y * k - sum_y)
            yield x, y
            

    def start(self):
        print("[INFO] The screen is being captured!")
        Aimbot.update_status_aimbot()
        half_screen_width = ctypes.windll.user32.GetSystemMetrics(0)/2 #это всегда должно быть 960
        half_screen_height = ctypes.windll.user32.GetSystemMetrics(1)/2 #это всегда должно быть 540
        detection_box = {'left': int(half_screen_width - self.box_constant//2), #координата x1 (для верхнего левого угла коробки)
                          'top': int(half_screen_height - self.box_constant//2), #координата y1 (для верхнего левого угла поля)
                          'width': int(self.box_constant),  #ширина коробки
                          'height': int(self.box_constant)} #высота коробки
        if self.collect_data:
            collect_pause = 0

        while True:
            start_time = time.perf_counter()
            frame = np.array(Aimbot.screen.grab(detection_box))
            if self.collect_data: orig_frame = np.copy((frame))
            results = self.model(frame)

            if len(results.xyxy[0]) != 0: #игрок обнаружен
                least_crosshair_dist = closest_detection = player_in_frame = False
                for *box, conf, cls in results.xyxy[0]: #перебрать каждого обнаруженного игрока
                    x1y1 = [int(x.item()) for x in box[:2]]
                    x2y2 = [int(x.item()) for x in box[2:]]
                    x1, y1, x2, y2, conf = *x1y1, *x2y2, conf.item()
                    height = y2 - y1
                    relative_head_X, relative_head_Y = int((x1 + x2)/2), int((y1 + y2)/2 - height/2.7) #смещение, чтобы примерно аппроксимировать голову, используя соотношение высоты
                    own_player = x1 < 15 or (x1 < self.box_constant/5 and y2 > self.box_constant/1.2) #помогает гарантировать, что ваш собственный игрок не будет считаться действительным обнаружением

                    #вычислить расстояние между каждым обнаружением и перекрестием в (self.box_constant/2, self.box_constant/2)
                    crosshair_dist = math.dist((relative_head_X, relative_head_Y), (self.box_constant/2, self.box_constant/2))

                    if not least_crosshair_dist: least_crosshair_dist = crosshair_dist #инициализировать переменную наименьшего расстояния перекрестия в первой итерации

                    if crosshair_dist <= least_crosshair_dist and not own_player:
                        least_crosshair_dist = crosshair_dist
                        closest_detection = {"x1y1": x1y1, "x2y2": x2y2, "relative_head_X": relative_head_X, "relative_head_Y": relative_head_Y, "conf": conf}

                    if not own_player:
                        cv2.rectangle(frame, x1y1, x2y2, (244, 113, 115), 2) #нарисовать ограничивающие рамки для всех обнаружений игрока (кроме собственного)
                        cv2.putText(frame, f"{int(conf * 100)}%", x1y1, cv2.FONT_HERSHEY_DUPLEX, 0.5, (244, 113, 116), 2) #нарисуйте метки доверия на ограничивающих рамках
                    else:
                        own_player = False
                        if not player_in_frame:
                            player_in_frame = True

                if closest_detection: #если действительное обнаружение существует
                    cv2.circle(frame, (closest_detection["relative_head_X"], closest_detection["relative_head_Y"]), 5, (115, 244, 113), -1) #нарисуй круг на голове

                    #провести линию от перекрестия к голове
                    cv2.line(frame, (closest_detection["relative_head_X"], closest_detection["relative_head_Y"]), (self.box_constant//2, self.box_constant//2), (244, 242, 113), 2)

                    absolute_head_X, absolute_head_Y = closest_detection["relative_head_X"] + detection_box['left'], closest_detection["relative_head_Y"] + detection_box['top']

                    x1, y1 = closest_detection["x1y1"]
                    if Aimbot.is_target_locked(absolute_head_X, absolute_head_Y):
                        cv2.putText(frame, "LOCKED", (x1 + 40, y1), cv2.FONT_HERSHEY_DUPLEX, 0.5, (115, 244, 113), 2) #рисует метки достоверности на ограничивающих рамках
                    else:
                        cv2.putText(frame, "TARGETING", (x1 + 40, y1), cv2.FONT_HERSHEY_DUPLEX, 0.5, (115, 113, 244), 2) #рисует метки доверия на ограничивающих рамках

                    if Aimbot.is_aimbot_enabled():
                        Aimbot.move_crosshair(self, absolute_head_X, absolute_head_Y)

            if self.collect_data and time.perf_counter() - collect_pause > 1 and Aimbot.is_targeted() and Aimbot.is_aimbot_enabled() and not player_in_frame: #скриншоты можно делать только раз в 1 секунду
                cv2.imwrite(f"lib/data/{str(uuid.uuid4())}.jpg", orig_frame)
                collect_pause = time.perf_counter()
            
            cv2.putText(frame, f"FPS {int(1/(time.perf_counter() - start_time))}", (5, 30), cv2.FONT_HERSHEY_DUPLEX, 1, (113, 116, 244), 2)
            cv2.imshow("[Overlay] SkillLuze", frame)
            if cv2.waitKey(1) & 0xFF == ord('0'):
                break

    def clean_up():
        print("\n[!] YOU CLICK TO F2. EXIT...")
        Aimbot.screen.close()
        os._exit(0)

if __name__ == "__main__": print("Бро, ты чето не то открыл! Please, open Start.bat file!")
