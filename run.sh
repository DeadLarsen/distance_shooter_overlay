#!/bin/bash
# Distance Attack - Launcher Script

echo "==================================="
echo "Distance Attack - Оверлей дистанций"
echo "==================================="
echo

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден. Установите Python 3.6+"
    exit 1
fi

# Проверка tkinter
python3 -c "import tkinter" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ tkinter не найден. Установите: sudo apt-get install python3-tk"
    exit 1
fi

echo "✅ Все зависимости найдены"
echo "🚀 Запуск Distance Attack..."
echo
echo "Горячие клавиши:"
echo "F1 - Калибровка"
echo "F2 - Включить/Выключить оверлей"
echo "ESC - Выход"
echo
echo "Для остановки программы нажмите Ctrl+C"
echo

# Запуск программы
python3 main.py 