#include "bitlash.h"
/* посмотреть еще немного про прерывания: https://alexgyver.ru/lessons/interrupts/

*/

// Объявление прерывания
void interruptHandler0() {
  //digitalWrite(48, LOW); // DOWN DIR
  //digitalWrite(49, !digitalRead(49)); // DOWN DIR
  noTone(49); // Отключаем STP
}

void interruptHandler1() {
  //digitalWrite(48, HIGH); // UP DIR
  //digitalWrite(49, !digitalRead(49)); // DOWN DIR
  noTone(49); // Отключаем STP
}

numvar func_tone(void) {
  if (getarg(0) == 2) tone(getarg(1), getarg(2));
  else tone(getarg(1), getarg(2), getarg(3));
  return 0;
}


numvar func_notone(void) {
  noTone(getarg(1));
  return 0;
}


void setup() {
  // Настройка прерывания
  pinMode(48, OUTPUT); // Активируем DIR
  pinMode(49, OUTPUT); // Активируем STP
  pinMode(55, OUTPUT); // Активируем Buzzer
  attachInterrupt(digitalPinToInterrupt(2), interruptHandler0, CHANGE);
  attachInterrupt(digitalPinToInterrupt(3), interruptHandler1, CHANGE);
  initBitlash(115200);
  addBitlashFunction("tone", (bitlash_function) func_tone);
  addBitlashFunction("notone", (bitlash_function) func_notone);
}


void loop() {
  runBitlash();
  int ton = getVar('F' - 'A');// Устанавливаем частоту шагов
  int ton_down = abs(getVar('Z' - 'A'));// Устанавливаем скорость затухания
  int freq = abs(ton);
  
  // Скорость F затухает согласно значений Z
  if (millis() % 50 < 5) {
    if (freq > ton_down) {
      freq = freq - ton_down;
    }
    if (freq > 0 && freq <= ton_down) {
      freq = 0;
    }
  }

  if (ton == 0) {
    noTone(49);
  } else {
    if (ton > 0) {
      digitalWrite(48, LOW); // UP DIR
      tone(49, ton);
      assignVar('F' - 'A', freq); // Устанавливаем частоту шагов
    } else {
      digitalWrite(48, HIGH); // DOWN DIR
      tone(49, abs(ton));
      assignVar('F' - 'A', -freq); // Устанавливаем частоту шагов
    }

  }

  if (digitalRead(2) == 0) {
    assignVar('F' - 'A', 0); // Обнуляем частоту шагов
    assignVar('Z' - 'A', 0); // Обнуляем затухание шагов
    if (millis() % 5 == 0) {
      Serial.println('-');
    }
    digitalWrite(48, LOW); // DOWN DIR
    noTone(49); // Отключаем STP
    tone(55, 2300);
    for (int i = 0; i < 100; i++) {
      digitalWrite(49, !digitalRead(49));
      //digitalWrite(55, !digitalRead(55));
      //delay(1);
    }
    digitalWrite(48, HIGH); // UP DIR
    noTone(55); // Отключаем Buzzer
  }
  if (digitalRead(3) == 0) {
    assignVar('F' - 'A', 0);// Обнуляем частоту шагов
    assignVar('Z' - 'A', 0); // Обнуляем затухание шагов
    if (millis() % 5 == 0) {
      Serial.println('+');
    }
    digitalWrite(48, HIGH); // UP DIR
    noTone(49); // Отключаем STP
    tone(55, 2300);
    for (int i = 0; i < 100; i++) {
      digitalWrite(49, !digitalRead(49));
      //digitalWrite(55, !digitalRead(55));
      //delay(1);
    }
    digitalWrite(48, LOW); // DOWN DIR
    noTone(55); // Отключаем Buzzer
  }
}


/*
  // Разкомментируйте строку ниже, чтобы раскрыть все внутренности
  // ядра Bitlash в вашем скетче.
  //
  //#include "src/bitlash.h"

  ///////////////////////
  //  Запуск Bitlash и предоставление ему циклов для выполнения задач
  //
  void initBitlash(unsigned long baud); // запуск и установка скорости передачи данных
  void runBitlash(void);          // вызывать это в функции loop() часто

  // Переменные Bitlash имеют тип "numvar"
  //
  typedef long int numvar;          // Bitlash возвращает значения типа numvar
  typedef unsigned long int unumvar;      // иногда лучше использовать беззнаковое представление (например, millis)

  ///////////////////////
  //  Передача команды для интерпретации Bitlash
  //
  numvar doCommand(char *);       // выполнить команду из вашего скетча
  void doCharacter(char);         // передать символ входного потока редактора строки

  ///////////////////////
  //  Доступ к числовым переменным
  //
  //  ПРИМЕЧАНИЕ: доступ к переменным a..z осуществляется через индекс 0..25, а не через имена переменных. Понятно?
  //
  numvar getVar(unsigned char);       // возвращает значение переменной Bitlash. Идентификатор - это число от 0 до 25 для a..z
  void assignVar(unsigned char, numvar);    // присваивает значение переменной. Идентификатор - это число от 0 до 25 для a..z
  numvar incVar(unsigned char);       // увеличивает значение переменной на единицу. Идентификатор - это число от 0 до 25 для a..z

  ///////////////////////
  //  Доступ к таблице символов Bitlash
  //
  // Поиск идентификатора и возврат TRUE, если он существует
  //
  byte findscript(char *);    // возвращает TRUE, если сценарий с таким идентификатором существует
  int getValue(char *key);      // возвращает местоположение значения макроса в EEPROM или -1

  ///////////////////////
  //  Добавление пользовательской функции в Bitlash
  //
  typedef numvar (*bitlash_function)(void);
  void addBitlashFunction(const char *, bitlash_function);
  numvar getarg(numvar);
  numvar isstringarg(numvar);
  numvar getstringarg(numvar which);

  ///////////////////////
  //  Перехват вывода в серийный порт
  //
  typedef void (*serialOutputFunc)(byte);
  byte serialIsOverridden(void);
  void setOutputHandler(serialOutputFunc);
  void setOutput(byte pin);
  void resetOutputHandler(void);
  numvar func_printf_handler(byte, byte);

  ///////////////////////
  //  Функции файловой системы
  //
  numvar sdcat(void);
  numvar sdwrite(char *filename, char *contents, byte append);
  numvar func_fprintf(void);
*/
