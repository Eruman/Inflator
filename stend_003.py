#!/usr/bin/env python

import minimalmodbus
import serial, time
from serial.tools import list_ports

limit = 0.05
raw_pressure_max = limit
raw_pressure_min = limit
stop_it = False

def print_data(prefix, raw_pressure, raw_pressure_max = 0, raw_pressure_min = 0, limit = 0, control_signal = 0, delta_raw = 0.05):
    #if raw_pressure >= 0:
    #delta_raw = raw_pressure_max *.05
    print(prefix, round(raw_pressure,4), round(raw_pressure_max,4), round(raw_pressure_min,4), round(limit,4), round(control_signal,2), round(limit - delta_raw,4), round(limit + delta_raw,4))
    #else:
    #    print(prefix, 0, round(raw_pressure_max,2), round(raw_pressure_min,2), round(limit,2), round(control_signal,2))
    
def init_ports():
    available_ports = list_ports.comports()
    print(f'Доступные порты: {[x.device for x in available_ports]}')
    print()
    '''
    Подключение устройств по СОМ-портам.

    '''
    #Получаем список портов
    ports = list(list_ports.comports())
    ser = 0
    #Получаем список портов и ищем нужное устройство
    for p in ports:
        print(str(p).split(' - ')[1])
        if str(p).split(' - ')[1][:16] == 'USB-SERIAL CH340':
            print(str(p).split(' - ')[0], ' имеется!')
            name2 = str(p).split(' - ')[0]
            #Подключаемся к нужному устройству
            ser = serial.Serial(
                port=name2, baudrate=115200, bytesize=8, timeout=3, stopbits=serial.STOPBITS_ONE
                )  # open serial port
            time.sleep(1)
            
    print()
    return(ser)



def init_hardware(ser, mon, waiting=True):
    #print(ser, mon, waiting)
    print('\nЖмите ENTER для старта калибровки.', end="")
    #После первого включения измеритель ждет любого входного символа
    #ser.write(b'f=-2000;tone(55,1300,100)\n')
    ser.write(b'tone(55,1300,10);f=1000\n')
    time.sleep(1.0)
    ser.write(b'tone(55,1300,10)\n')
    if waiting:
        input()
    else:
        time.sleep(.1)
    
    time.sleep(.5)
    #Активируем приводы
    #ser.write(b'tone(55,1300);down\n')
    ser.write(b'f=-3000\n')
    
    #if test_endstops_down(ser):
    #ser.write(b'down\n')
    #time.sleep(1)

    # Функции станка
    # function go {pinmode(2,0); pinmode(3,0); while(1){print(d2),;print"--",;print(d3);};};
    # function retract {i=2000;while(i--){d49=!d49;}};
    # function down {d48=0;retract;tone(49,s);};
    # function up {d48=1;retract;tone(49,60000);};
    # function check_a0 {if(a0==0){up;};if(a0==1023){down;};};
    # function startup {print"Check JOY started every 500 ms..."; s = 5000; run check_a0,500;};
    # function stop_press {notone(49)};
    # function upslow {d48=1;retract;tone(49,5000);};
    
    # pinmode(56,1) // настроить порт управления реле
    # d56=1 // включить реле
    # d56=0 // отключить реле
   
    #ser.write(b'up\n')
    ser.write(b'pinmode(56,1)\n')
    time.sleep(.2)
    ser.write(b'd56=1\n')
    time.sleep(.2)
    #ser.write(b'upslow\n')
    time.sleep(.2)
    while test_endstops(ser):
        #print('**')
        pass
    print('После возвращения в исходное состояние сброс разрежения.')
    #print('После возвращения в исходное состояние жмите ENTER для сброса разрежения.', end="")
    #input()    
#     time.sleep(1)
#     ser.write(b'd56=1\n')
#     time.sleep(3)
    ser.write(b'd56=0\n')
    print('Жмите ENTER для старта протокола.', end="")
    if waiting:
        input()
    else:
        time.sleep(.1)
    #ser.write(b'notone(55)\n')
    #    print('Стартовали...\n')
    time.sleep(1)

def init_modbus(mod_bus_device = 'COM26') :
    instrument = minimalmodbus.Instrument(mod_bus_device, 1)

    #print(instrument.serial.port)
    #instrument.serial.baudrate = 9600
    instrument.serial.baudrate = 9600
    instrument.serial.bytesize = 8
    instrument.serial.stopbits = 1
    instrument.serial.timeout  = 0.05
    #instrument.address         # this is the slave address number
    instrument.mode = minimalmodbus.MODE_RTU   # rtu or ascii mode
    return instrument

def get_pressure(instrument):
    try:
        raw_pressure = instrument.read_register(11, 3) * 100    # Чтение значения давления из регистра датчика
    except:
        raw_pressure = 0
        print("Error bar-meter")
    #print(f"Pressure: {pressure:.2f} бар")                    # Вывод значения давления в бар с точностью до 2 знаков после запятой
    if raw_pressure > 6500:
        #raw_pressure = -1000
        raw_pressure = 0
    return raw_pressure / 100 / 1.012 # коэффициент есть усредненное отклонение по 12 измерениям поверенного прибора

def test_endstops_down(ser):
    if ser.in_waiting != 0:
        data1 = []
        print("#", end="")
        while ser.in_waiting > 0:
            #Читаем префикс-байт и байт данных
            char = ser.read()
            data1.append(char)
            #print(char.decode(), end="")
        inp = b''
        inp = inp.join(data1)
        if inp[:3] == b'+\r\n':
            print('****************************************', inp.decode())
            return False
        if inp[:1] == b'+':
            print('----------------------------------------', inp.decode())
            return False
        if inp != b'\r\n> ':
            #print(inp.decode())
            pass
    return True

def test_endstops_up(ser):
    if ser.in_waiting != 0:
        data1 = []
        print("#", end="")
        while ser.in_waiting > 0:
            #Читаем префикс-байт и байт данных
            char = ser.read()
            data1.append(char)
            #print(char.decode(), end="")
        inp = b''
        inp = inp.join(data1)
        if inp[:3] == b'-\r\n':
            print('****************************************', inp.decode())
            return False
        if inp[:1] == b'-':
            print('----------------------------------------', inp.decode())
            return False
        if inp != b'\r\n> ':
            #print(inp.decode())
            pass
    return True

def test_endstops(ser, monitor=False):
    if ser.in_waiting != 0:
        data1 = []
        if monitor:
            print(".", end="")
        while ser.in_waiting > 0:
            #Читаем префикс-байт и байт данных
            char = ser.read()
            data1.append(char)
            #print(char.decode(), end="")
        inp = b''
        inp = inp.join(data1)
        if inp[:3] == b'+\r\n' or inp[:3] == b'-\r\n':
            print('****************************************', inp.decode())
            return False
        if inp[:1] == b'+' or inp[:1] == b'-':
            print('----------------------------------------', inp.decode())
            return False
        if inp != b'\r\n> ':
            if monitor: print(inp.decode())
            pass
    return True

#   set_pressure_PID_timer_PWM
def set_pressure_PID_timer_PWM(ser, mon, limit, control = True, coefficiens = 1,
                     Kp = 0.5,
                     Ki = 0.1,
                     Kd = 0.25,
                     delta_raw = 0.05,
                     up = True,
                     timer = 3):
    #         raw_pressure_max = limit
    #         raw_pressure_min = limit
    Kp, Ki, Kd = float(Kp), float(Ki), float(Kd)
#     print(Kp, Ki, Kd)
#     print(type(Kp), type(Ki), type(Kd))
    global raw_pressure_min, raw_pressure_max
    global stop_it
    # d48=0 // направление движения штока - вниз
    # d48=1 // направление движения штока - вверх
    #ser.write(b'd48=0\n')
    #cmd = 'd48=0;tone(49,{});\n'.format(int(50)).encode()
    cmd = b'\n'
    _cmd = b''
    
    # Define the PID controller parameters
#     Kp = 0.5  # Пропорциональный рост
#     Ki = 0.1  # Интегральный рост
#     Kd = 0.25  # Производный рост (Дифференциальный)

    # Initialize the variables
    previous_error = 0
    integral = 0
    #stop_it = False
    
    start_time = time.time()  # Записываем текущее время
    
    while True:
        pass
        if stop_it:
            break
        
        raw_pressure = get_pressure(mon)
                
        if cmd != _cmd:
            ser.write(cmd)
            _cmd = cmd
           
            #await asyncio.sleep(.035)
            time.sleep(.035)
        
        if test_endstops(ser) == False:
            return False
        
        print_data(0, raw_pressure, raw_pressure_max, raw_pressure_min, limit, delta_raw=delta_raw)

        if raw_pressure > 0 and raw_pressure < raw_pressure_min:
            raw_pressure_min = raw_pressure

        if raw_pressure > raw_pressure_max:
            raw_pressure_max = raw_pressure
        # *-*************************************************

        # Вычисляем ошибку между текущим давлением и заданным пределом
        error = limit - raw_pressure
        # Вычисляем пропорциональный прирост давления
        proportional = Kp * error
        # Вычисляем интегральный прирост давления
        integral += Ki * error
        # Вычисляем производный прирост давления
        derivative = Kd * (error - previous_error)
        # Вычисляем модуль суммарного прироста давления
        #control_signal = abs(proportional + integral + derivative)
        control_signal = (proportional + integral + derivative)
        # Запоминаем предыдущую ошибку
        previous_error = error
        
        #print(control_signal)
        
        if time.time() - start_time >= timer:  # Проверяем, прошло ли timer секунд
            return True
        
        if control_signal > 32000:
            control_signal = 32000
        if control_signal < -32000:
            control_signal = -32000
        
        # Управление стендом производим через частотный генератор, считывающий значения переменной f
        # Например, отправленная на стенд команда f=1000\n' будет означать, что следует установить частоту 1кГц
        if up and raw_pressure < limit: #Снизу вверх до середины
            cmd = 'f={}\n'.format(int(10*control_signal)).encode()
            print('#Снизу вверх до середины')
            continue
        
        if raw_pressure < limit - delta_raw: #Вверх без корридора
            cmd = 'f={}\n'.format(int(10*control_signal)).encode()
            print('#Вверх без корридора')
            continue

        if up and raw_pressure > limit and raw_pressure < limit + delta_raw: #Снизу вверх от середины стоим
            cmd = b'f=f/2\n'
            print('#Снизу вверх от середины стоим')
            continue

        if not up and raw_pressure <= limit and raw_pressure > limit - delta_raw: #Сверху вниз от середины стоим
            cmd = b'f=f/2\n'
            print('#Сверху вниз от середины стоим')
            continue
       
        if not up and raw_pressure > limit: #Сверху вниз до середины
            cmd = 'f={}\n'.format(int(10*control_signal)).encode()
            print('#Сверху вниз до середины')
            continue
        
        if raw_pressure > limit + delta_raw: #Вниз без корридора
            cmd = 'f={}\n'.format(int(10*control_signal)).encode()
            print('#Вниз без корридора')
            continue

