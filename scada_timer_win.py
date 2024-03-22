#!/usr/bin/env python
import configparser
import os
from stend_003 import *
import asyncio
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

import numpy as np

current_directory = os.getcwd()
print("Текущая директория:", current_directory)

# Создание экземпляра объекта ConfigParser
config = configparser.ConfigParser()
if os.path.isfile('config_timer.ini'):
    print("Файл config_timer.ini существует.")
else:
    print("Файл config_timer.ini не существует.")
    # Установка значений переменных
    config['DEFAULT'] = {
        'init_bar': '10',
        'min_bar': '10',
        'max_bar': '50',
        'iter_bar': '1',
        'step_bar': '2',
        'coef_bar': '0.1',
        'coefp_bar': '10',
        'coefi_bar': '0.1',
        'coefd_bar': '3',
        'delta_bar': '0.05',
        'min_sec': '5',
        'max_sec': '5'}
    config['AUTO'] = {
        'mon': 'COM26'  }

    # Сохранение значений в файле INI
    with open('config_timer.ini', 'w') as configfile:
        config.write(configfile)


ser = 0
mon = 0
stop_it        = False
btnStartHard   = None
btnStart       = None
btnStop        = None
btnUpSpeed     = None
btnDnSpeed     = None
init_bar_input = None
min_bar_input  = None
max_bar_input  = None
iter_bar_input = None
step_bar_input = None
my_window      = None
coef_bar_input = None
vent_checkbox  = 0
max_checkbox   = 0

bar_label = None
bar_speed = None

input_field, dropdown, items = None, None, []
numbs = []

config.read('config_timer.ini')
ser = init_ports()
mon = init_modbus(config.get('AUTO', 'mon'))
if ser == 0:
    print('Драйвер управления стендом не обнаружен. Программа остановлена.')
    exit()

def home_hardware_and_press(widget):
    global ser, mon, btnStartHard, btnStart, btnStop, btnUpSpeed, btnDnSpeed, bar_label
    #ser = init_ports()
    init_hardware(ser, mon, waiting=False)
    print('Ок')
    btnStartHard.enabled = True  # Для включения кнопки
    btnStart.enabled = True
    press_off(True)
    time.sleep(1)
    press_on(True)
    
def home_hardware(widget):
    global ser, mon, btnStartHard, btnStart, btnStop, btnUpSpeed, btnDnSpeed, bar_label
    #ser = init_ports()
    init_hardware(ser, mon, waiting=False)
    print('Ок')
    btnStartHard.enabled = True  # Для включения кнопки
    btnStart.enabled = True
    
def start_hardware(widget):
    print("Стартую!")
    global ser, mon, btnStartHard, btnStart, btnStop, btnUpSpeed, btnDnSpeed, bar_label
    global raw_pressure_min, raw_pressure_max
    
    btnStartHard.enabled = False
    btnUpSpeed.enabled = True
    btnDnSpeed.enabled = True
    raw_pressure_max = 0
    raw_pressure_min = 3
    asyncio.ensure_future(update_label(bar_label, mon))

def calculate_speed(widget):
    if int(widget.value) > 32000:
        widget.value = 32000
        print('widget.value = 32000')
    
def calculate_front(widget):
    print('Функция калькуляции фронтов отключена.')

def save_params(section = 'DEFAULT'):
    global ser, mon, stop_it, btnStartHard, btnStart, btnStop, init_bar_input, min_bar_input, delta_bar_input
    global max_bar_input, iter_bar_input, step_bar_input, coef_bar_input, coefp_bar_input, coefi_bar_input, coefd_bar_input
    global min_sec_input, max_sec_input
    global min_frn_input, max_frn_input
    
    config[section] = {
        'init_bar' : init_bar_input.value,
        'min_bar'  : min_bar_input.value,
        'max_bar'  : max_bar_input.value,
        'iter_bar' : iter_bar_input.value,
        'step_bar' : step_bar_input.value,
        'coef_bar' : coef_bar_input.value,
        'coefp_bar': coefp_bar_input.value,
        'coefi_bar': coefi_bar_input.value,
        'coefd_bar': coefd_bar_input.value,
        'delta_bar': delta_bar_input.value,
        'min_sec'  : min_sec_input.value,
        'max_sec'  : max_sec_input.value,
        'min_frn'  : min_frn_input.value,
        'max_frn'  : max_frn_input.value
    }

    # Сохранение значений в файле INI
    with open('config_timer.ini', 'w') as configfile:
        config.write(configfile)
    return True

def plus_program(widget):
    global ser, bar_speed
    ser.write(b'tone(55,1300,10)\n')
    time.sleep(.1)
    ser.write('f={}\n'.format(int(bar_speed.value)).encode())
    time.sleep(1)
    ser.write('f=0\n'.encode())

def minus_program(widget):
    global ser, bar_speed
    ser.write(b'tone(55,1300,10)\n')
    time.sleep(.1)
    ser.write('f=-{}\n'.format(int(bar_speed.value)).encode())
    time.sleep(1)
    ser.write('f=0\n'.encode())

def press_off(widget):
    global ser, mon, stop_it, btnStartHard, btnStart, btnStop, init_bar_input, min_bar_input
    ser.write(b'pinmode(56,1)\n')
    time.sleep(.1)
    ser.write(b'd56=1\n')
    
def press_on(widget):
    global ser, mon, stop_it, btnStartHard, btnStart, btnStop, init_bar_input, min_bar_input
    ser.write(b'pinmode(56,1)\n')
    time.sleep(.1)
    ser.write(b'd56=0\n')
    
def prepare_program(widget):
    global ser, mon, stop_it, btnStartHard, btnStart, btnStop, init_bar_input, min_bar_input, raw_pressure_max, raw_pressure_min
    global max_bar_input, iter_bar_input, step_bar_input, coef_bar_input
        
    save_params() #Сохранить параметры в конфигурационном файле.
    
    delta_raw = float(delta_bar_input.value)
    stop_it = False
    btnStart.enabled = True
    btnStop.enabled  = True
    
    coefficiens = float(coef_bar_input.value)

    raw_pressure_max = 0
    raw_pressure_min = 3
    time.sleep(.15)
    
    set_pressure_PID_timer_PWM(ser, mon, int(init_bar_input.value)/100, False, coefficiens,
        coefp_bar_input.value, coefi_bar_input.value, coefd_bar_input.value , delta_raw=delta_raw)  # Повышаем давление без контроля падения до 20% от лимита

    raw_pressure_min = raw_pressure_max
    time.sleep(0.1)
    ser.write('f=0\n'.encode())
    print("Программа приготовлена.")
    btnUpSpeed.enabled = True
    btnDnSpeed.enabled = True
    
def start_program(widget):
    print("Программа запущена.")
    global ser, mon, stop_it, btnStartHard, btnStart, btnStop, init_bar_input, min_bar_input, raw_pressure_max, raw_pressure_min, delta_bar_input
    global max_bar_input, iter_bar_input, step_bar_input, coef_bar_input, coefp_bar_input, coefi_bar_input, coefd_bar_input
    global min_sec_input, max_sec_input
    
    save_params() #Сохранить параметры в конфигурационном файле.
    
    delta_raw = float(delta_bar_input.value)
    stop_it = False
    btnStart.enabled = False  # Enable the "Start Program" button
    btnStop.enabled = True
    coefficiens = float(coef_bar_input.value)
    raw_pressure_max = 0
    raw_pressure_min = 3

    print("Программа продолжает работу")
    
    for _ in range(int(iter_bar_input.value)):
        for limit in range(int(min_bar_input.value), int(max_bar_input.value) + int(step_bar_input.value), int(step_bar_input.value)):
            pass
            if stop_it or not set_pressure_PID_timer_PWM(ser, mon, limit / 100, coefficiens,
                                coefp_bar_input.value, coefi_bar_input.value, coefd_bar_input.value,
                                delta_raw=delta_raw, timer=2):
                print("Сработал концевик. Остановка.")
                break
        
        set_pressure_PID_timer_PWM(ser, mon, int(max_bar_input.value) / 100, coefficiens,
                                coefp_bar_input.value, coefi_bar_input.value, coefd_bar_input.value,
                                delta_raw=delta_raw, timer=float(max_sec_input.value)) 
        
        for limit in range(int(max_bar_input.value), int(min_bar_input.value) - int(step_bar_input.value) , -int(step_bar_input.value)):
            pass
            if stop_it or not set_pressure_PID_timer_PWM(ser, mon, limit / 100, coefficiens,
                                coefp_bar_input.value, coefi_bar_input.value, coefd_bar_input.value,
                                delta_raw=delta_raw, up=False, timer=2):
                print("Сработал концевик. Остановка.")
                break
        
        set_pressure_PID_timer_PWM(ser, mon, int(min_bar_input.value) / 100, coefficiens,
                                coefp_bar_input.value, coefi_bar_input.value, coefd_bar_input.value,
                                delta_raw=delta_raw, timer=float(min_sec_input.value))
        
        if test_endstops(ser) == False:
            print("Сработал концевик. Остановка.")
            print("Программа остановлена.")
            ser.write(b'notone(49)\n')
            time.sleep(0.1)
            ser.write(b'notone(55)\n')
            time.sleep(0.1)
            ser.close()
            mon.serial.close()
            return

    ser.write('f=0\n'.encode())
    time.sleep(0.1)
    if not stop_it: 
        print("Уставка:", limit / 100, "\nДавление упало ниже 80% от уставки.")
        
    print("Программа остановлена.")
    btnStop.enabled = False

def wait_program(timer=1, up=True):
    global min_bar_input, max_bar_input, ser, mon, numbs
    min_bar = float(min_bar_input.value)
    max_bar = float(max_bar_input.value)
    
    start_time = time.time()  # Записываем текущее время
    ready = True
    speed_low = True
    speed_low2 = True
    # Управление стендом производим через частотный генератор, считывающий значения переменной f
    # Например, отправленная на стенд команда f=1000\n' будет означать, что следует установить частоту 1кГц
    # Затухание скорости происходит через переменную z.
    # Если поставить z = 1, то при каждом тике станка (~50мс) скорость f будет снижаться
    # ser.write('z=0\n'.encode())
    prev_avg = 0
    pred_avg = 0
    while True:
        test_endstops(ser, monitor = False)
        raw_pressure = get_pressure(mon)
        
        avg = calculate_moving_average(numbs)
        prev_avg = calculate_moving_average(numbs[:-15])
        pred_avg = avg + (avg - prev_avg)  # Предсказанное значение
        
        if up:
#             if ready and speed_low and max_bar / 100 < raw_pressure * 1.5 :  
#                 #ser.write('f=f/2\n'.encode())
#                 ser.write('z=f/1000\n'.encode())
#                 #ser.write('z=2\n'.encode())
#                 speed_low = False
# 
#             if ready and speed_low2 and max_bar / 100 < raw_pressure * 1.1 :  
#                 ser.write('z=f/100\n'.encode())
#                 speed_low2 = False

            if ready and speed_low and max_bar / 100 < pred_avg * 1.25 :  
                ser.write('f=f/2\n'.encode())
                speed_low = False

            if ready and speed_low2 and max_bar / 100 < pred_avg * 1.1 :  
                ser.write('f=f/2\n'.encode())
                #speed_low2 = False

            if ready and max_bar / 100 < raw_pressure :
                ser.write('f=0; z=0\n'.encode())
                ready = False
        else:
            if ready and min_bar / 100 > raw_pressure:
                ser.write('f=0;z=0\n'.encode())
                ready = False
                


        
        print(0, raw_pressure, min_bar/100, max_bar/100, up, avg, 0, pred_avg)
        numbs.append(raw_pressure)
        
        #prev_avg = avg

        if time.time() - start_time >= timer:  # Проверяем, прошло ли timer секунд
            ser.write(b'z=0\n')
            time.sleep(.01)
            print(numbs)
            break

def sleep_program(timer=1, up=True):
    global min_bar_input, max_bar_input, ser, mon, numbs
    min_bar = float(min_bar_input.value)
    max_bar = float(max_bar_input.value)
    start_time = time.time()  # Записываем текущее время
    
    while True:
        test_endstops(ser, monitor = False)
        raw_pressure = get_pressure(mon)
        
        avg = calculate_moving_average(numbs)
        prev_avg = calculate_moving_average(numbs[:-15])
        pred_avg = avg + (avg - prev_avg)  # Предсказанное значение

        print(0, raw_pressure, min_bar/100, max_bar/100, up, avg, 0, pred_avg)
        numbs.append(raw_pressure)
        
        if time.time() - start_time >= timer:  # Проверяем, прошло ли timer секунд
            print(numbs)
            break
        
        
def calculate_moving_average(numbs):
    window_size = 10
    if len(numbs) < window_size:
        return 0  # Если в массиве меньше 10 элементов, возвращаем None
    else:
        window = numbs[-window_size:]  # Берем последние 10 элементов массива
        moving_average = sum(window) / window_size  # Вычисляем среднее значение
        return moving_average



def freq_program(widget):
    stop_it = True
    global ser, mon, min_sec_input, max_sec_input, min_frn_input, max_frn_input, coef_bar_input
    global vent_checkbox, max_checkbox
    
    print("Программа стартует работу частотного генератора", vent_checkbox.value, max_checkbox.value)
    freq = int(coef_bar_input.value)
    
    # Управление стендом производим через частотный генератор, считывающий значения переменной f
    # Например, отправленная на стенд команда f=1000\n' будет означать, что следует установить частоту 1кГц
    for _ in range(int(iter_bar_input.value)):
        # Фронт повышения давления
        ser.write('f={};z=0\n'.format(int(freq)).encode())
        if max_checkbox.value:
            wait_program(float(max_frn_input.value))
        else:
            sleep_program(float(max_frn_input.value))
        
        # Плато повышенного давления
        ser.write('f=0;z=0\n'.encode())
        if max_checkbox.value:
            wait_program(float(max_sec_input.value))
        else:
            sleep_program(float(max_sec_input.value))
        
        # Фронт снижения давления
        ser.write('f={};z=0\n'.format(-1*freq).encode())
        wait_program(float(min_frn_input.value), up=False)
        #print('-'*60)

        if vent_checkbox.value:
            # Если есть флажок сброса, то сбрасываем
            ser.write(b'd56=1\n')
            time.sleep(.1)
        
        # Плато пониженного давления
        ser.write('\nf=0;z=0\n'.encode())
        wait_program(float(min_sec_input.value), up=False)
        
        if vent_checkbox.value:
            # Если есть флажок сброса, то закрываемся после сброса
            ser.write(b'd56=0\n')
            time.sleep(.1)
        
    print("Программа завершает работу частотного генератора")
    ser.write('f=0\n'.encode())
    
    start_time = time.time()  # Запоминаем текущее время


def stop_program(widget):
    global btnStop,stop_it
    btnStop.enabled = False  # Disable the "Stop Program" button
    stop_it = True

async def update_label(llabel, mmon):
    global mon, bar_label
    while True:
        try:
            value = get_pressure(mon)
            value = round(value,4)
            bar_label.text = f"Давление в системе: {value}"
            #print(value)
            await asyncio.sleep(1)  # Пауза в 1000 мс (1 секунда)
        except:
            pass
            #print('*')

def selection_handler(widget):
    selected_item = widget.value
    print("Выбран элемент:", selected_item)

def load_config(selection='DEFAULT'):
    global init_bar_input, min_bar_input, max_bar_input
    global iter_bar_input, coef_bar_input
    global min_sec_input, max_sec_input
    global min_frn_input, max_frn_input
    
    config.read('config_timer.ini')

    # Получение значений переменных
    init_bar_input.value = config.get(selection, 'init_bar')
    min_bar_input.value  = config.get(selection, 'min_bar')
    max_bar_input.value  = config.get(selection, 'max_bar')
    iter_bar_input.value = config.get(selection, 'iter_bar')
    coef_bar_input.value = config.get(selection, 'coef_bar')

    min_sec_input.value = float(config.get(selection, 'min_sec'))
    max_sec_input.value = float(config.get(selection, 'max_sec'))
    min_frn_input.value = float(config.get(selection, 'min_frn'))
    max_frn_input.value = float(config.get(selection, 'max_frn'))

def set_max(widget):
    global max_bar_input, max_checkbox
    max_bar_input.enabled= max_checkbox.value

    
def build(app):
    config.read('config_timer.ini')

    # Получение значений переменных
    init_bar = config.get('DEFAULT', 'init_bar')
    min_bar  = config.get('DEFAULT', 'min_bar')
    max_bar  = config.get('DEFAULT', 'max_bar')
    iter_bar = config.get('DEFAULT', 'iter_bar')
    step_bar = config.get('DEFAULT', 'step_bar')
    coef_bar = config.get('DEFAULT', 'coef_bar')
    coefp_bar = config.get('DEFAULT', 'coefp_bar')
    coefi_bar = config.get('DEFAULT', 'coefi_bar')
    coefd_bar = config.get('DEFAULT', 'coefd_bar')

    delta_bar = float(config.get('DEFAULT', 'delta_bar'))
    min_sec = float(config.get('DEFAULT', 'min_sec'))
    max_sec = float(config.get('DEFAULT', 'max_sec'))
    min_frn = float(config.get('DEFAULT', 'min_frn'))
    max_frn = float(config.get('DEFAULT', 'max_frn'))
    
    global btnStartHard, btnStart, btnStop, btnUpSpeed, btnDnSpeed, init_bar_input, min_bar_input, delta_bar_input
    global max_bar_input, iter_bar_input, step_bar_input, coef_bar_input, coefp_bar_input, coefi_bar_input, coefd_bar_input, bar_speed, bar_label
    global min_sec_input, max_sec_input
    global min_frn_input, max_frn_input
    global input_field, dropdown, items, vent_checkbox, max_checkbox

    global my_window
    btnStartHard = toga.Button('Инициализировать стенд', on_press=start_hardware)
    btnStartHard.style.height = 50
    btnHome = toga.Button('Установить начальную позицию штока', on_press=home_hardware_and_press)
    btnHome.style.height = 50
    btnPrepare = toga.Button('Установить начальное давление в системе', on_press=prepare_program, enabled=True)
       
    btnPrepare.style.height = 50
    btnStart = toga.Button('Start Program',  on_press=start_program, enabled=False)
    btnStart.style.height = 50
    btnStop = toga.Button('Stop  Program',  on_press=stop_program, enabled=False)
    btnStop.style.height = 50
    btnFreq = toga.Button('Запустить стенд',  on_press=freq_program)
    btnFreq.style.height = 50
    
    label = toga.Label('Нач. давление kPa:')
    label.style.width = 120
    init_bar_input = toga.TextInput(value=init_bar)
    init_bar_input.style.flex = 1
    init_bar_input.style.padding = 1
    init_bar_input.style.width = 50
    
    min_label = toga.Label('Мин.давление, kPa:')
    min_label.style.width = 120
    min_bar_input = toga.TextInput(value=min_bar, on_change=calculate_front)
    min_bar_input.style.flex = 1
    min_bar_input.style.padding = 1
    min_bar_input.style.width = 50
    #min_bar_input.enabled=False

    min_frn_label = toga.Label('Фронт, с:')
    #min_frn_label.enabled=False
    min_frn_input = toga.TextInput(value=min_frn)
    min_frn_input.style.flex = 1
    min_frn_input.style.padding = 1
    min_frn_input.style.width = 30
    #min_frn_input.enabled=False
    

    min_sec_label = toga.Label('Плато, с:')
    min_sec_input = toga.TextInput(value=min_sec)
    min_sec_input.style.flex = 1
    min_sec_input.style.padding = 1
    min_sec_input.style.width = 30

    max_label = toga.Label('Макс.давление, kPa:')
    max_label.style.width = 120
    max_bar_input = toga.TextInput(value=max_bar, on_change=calculate_front)
    max_bar_input.style.flex = 1
    max_bar_input.style.padding = 1
    max_bar_input.style.width = 50
    #max_bar_input.enabled=False
    
    max_frn_label = toga.Label('Фронт, с:')
    #max_frn_label.enabled=False
    max_frn_input = toga.TextInput(value=max_frn)
    max_frn_input.style.flex = 1
    max_frn_input.style.padding = 1
    max_frn_input.style.width = 30
    #max_frn_input.enabled=False
    
    vent_checkbox = toga.Switch(value = 0, text = "Сброс")
    max_checkbox = toga.Switch(value = 1, text = "Контроль", on_change=set_max)
    
    max_sec_label = toga.Label('Плато, с:')
    max_sec_input = toga.TextInput(value=max_sec)
    max_sec_input.style.flex = 1
    max_sec_input.style.padding = 1
    max_sec_input.style.width = 30
    
    iter_label = toga.Label('Число повторов:')
    iter_label.style.width = 120
    iter_bar_input = toga.TextInput(value=iter_bar)
    iter_bar_input.style.flex = 1
    iter_bar_input.style.padding = 1
    iter_bar_input.style.width = 30

    step_label = toga.Label('Приращение:')
    step_label.style.width = 120
    step_bar_input = toga.TextInput(value=step_bar, on_change=calculate_front)
    step_bar_input.style.flex = 1
    step_bar_input.style.padding = 1
    step_bar_input.style.width = 30
    
    coef_label = toga.Label('Скорость:')
    #coef_label.enabled=False
    coef_bar_input = toga.TextInput(value=coef_bar, on_change=calculate_speed)
    coef_bar_input.style.flex = 1
    coef_bar_input.style.padding = 1
    #coef_bar_input.enabled=False
    
    
    delta_label = toga.Label('Дельта:')
    delta_bar_input = toga.TextInput(value=delta_bar)
    delta_bar_input.style.flex = 1
    delta_bar_input.style.padding = 1
    delta_bar_input.style.width = 50
        
    coefp_label = toga.Label('Кp:')
    coefp_bar_input = toga.TextInput(value=coefp_bar)
    coefp_bar_input.style.flex = 1
    coefp_bar_input.style.padding = 1
    coefp_bar_input.style.width = 50
    
    coefi_label = toga.Label('Кi:')
    coefi_bar_input = toga.TextInput(value=coefi_bar)
    coefi_bar_input.style.flex = 1
    coefi_bar_input.style.padding = 1
    coefi_bar_input.style.width = 50
    
    coefd_label = toga.Label('Кd:')
    coefd_bar_input = toga.TextInput(value=coefd_bar)
    coefd_bar_input.style.flex = 1
    coefd_bar_input.style.padding = 1
    coefd_bar_input.style.width = 50
    
    bar_label =  toga.Label('Давление в системе: 0.0000')
    bar_label.style.width = 220

    box_label = toga.Box(children=[label, init_bar_input], style=Pack(direction=ROW, padding=1))
    box_min   = toga.Box(children=[min_label, min_bar_input, min_frn_label, min_frn_input, min_sec_label, min_sec_input, vent_checkbox], style=Pack(direction=ROW, padding=1))
    box_max   = toga.Box(children=[max_label, max_bar_input, max_frn_label, max_frn_input, max_sec_label, max_sec_input, max_checkbox], style=Pack(direction=ROW, padding=1))
    box_iter  = toga.Box(children=[iter_label, iter_bar_input], style=Pack(direction=ROW, padding=1))
    box_step  = toga.Box(children=[step_label, step_bar_input], style=Pack(direction=ROW, padding=1))
    box_coef  = toga.Box(children=[coef_label, coef_bar_input], style=Pack(direction=ROW, padding=1))
    box_coefp = toga.Box(children=[coefp_label, coefp_bar_input, coefi_label, coefi_bar_input, coefd_label, coefd_bar_input], style=Pack(direction=ROW, padding=1))
    box_bar   = toga.Box(children=[bar_label], style=Pack(direction=ROW, padding=1))
    
    items=['DEFAULT'] + [_ for _ in config.sections() if _ != 'AUTO']
    
    dropdown = toga.Selection(items=items, on_select=selection_handler)
    
    box = toga.Box(children=[btnStartHard, btnHome, btnPrepare, btnFreq,
                             box_label,
                             box_max,
                             box_min,
                             box_iter,
                             box_coef,
                             box_bar],
                   style=Pack(direction=COLUMN, padding=1))
    
    bar_speed_label = toga.Label('Скорость ручная:')
    bar_speed       = toga.TextInput(value=3000)
    bar_speed.style.flex = 1
    bar_speed.style.padding = 1
    bar_speed.style.width = 50
    
    btnUpSpeed  = toga.Button(' +  ',  on_press=plus_program)
    btnDnSpeed  = toga.Button(' -  ',  on_press=minus_program)
    btnOpen     = toga.Button('Cl.Open',  on_press=press_off)
    btnHomeMore = toga.Button('Home',  on_press=home_hardware)
    btnClose    = toga.Button('Cl.Close', on_press=press_on)
    
    box2 = toga.Box(style=Pack(direction=ROW, padding=1, height = 50))
    box2.add(bar_speed_label, bar_speed, btnUpSpeed, btnDnSpeed, btnOpen, btnHomeMore, btnClose)
    box2.style.height = 50
    
    box3 = toga.Box(style=Pack(direction=ROW, padding=1))
    
    input_field = toga.TextInput()
    add_button = toga.Button('Save', on_press=add_item)
    dropdown.style.width = 190
    
    box3.add(dropdown, input_field, add_button)
    box.add(box2, box3)
    #box.add(box2)
    app.main_window.size = (420, 480)
    my_window = app.main_window
    calculate_front(box)
    
    app.main_window.app.icon = current_directory + "/speedometr.png"
    return box

def on_close(widget):
    global ser, my_window
    global btnStartHard, btnStart, btnStop, init_bar_input, min_bar_input
    global max_bar_input, iter_bar_input, step_bar_input, coef_bar_input
    try:
        ser.write('f=0\n'.encode())
        print("Насос остановлен.")
        time.delay(.1)
        ser.close()
    except:
        print("Насос не доступен.")    
    print("Окно закрывается.")
    
    save_params()
    print("Параметры сохраняются.")
    #print(app.main_window.size)
    return True

def selection_handler(widget):
    selected_item = widget.value
    print("Выбран элемент:", selected_item)
    print(items, widget.items, widget._window.show() )
    load_config(selection=selected_item)
    widget.refresh()

def add_item(widget):
    global input_field, dropdown, items, config
    new_item = input_field.value
    try:
        print(config[new_item])
    except:
        print('Секция несуществует. Добавляем:', new_item)
        if new_item.strip() != '':
            config.add_section(new_item)
            items.append(new_item)
        else:
            new_item = dropdown.value
        with open('config_timer.ini', 'w') as configfile:
            config.write(configfile)
    save_params(new_item)
    dropdown.items = items
    dropdown.value = new_item
    input_field.value = ""
    print("Создан элемент:", new_item)
    
if __name__ == "__main__":
    app = toga.App('Управление РС по частоте', 'com.example.programstart', startup=build)
    app.on_exit = on_close
    app.main_loop()
