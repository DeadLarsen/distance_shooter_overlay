#!/bin/bash
# Distance Attack - Безопасный запуск для Linux

echo "==================================="
echo "Distance Attack - Оверлей дистанций"
echo "БЕЗОПАСНЫЙ РЕЖИМ ДЛЯ LINUX"
echo "==================================="
echo

# Проверяем систему
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "⚠️  ВНИМАНИЕ: Вы запускаете программу на Linux!"
    echo "   В этом режиме:"
    echo "   - Окно НЕ будет полноэкранным"
    echo "   - Оставлены элементы управления окном"
    echo "   - Добавлена красная кнопка выхода"
    echo "   - Доступны дополнительные горячие клавиши"
    echo
    echo "🔑 Способы выхода из программы:"
    echo "   - ESC"
    echo "   - Ctrl+C"
    echo "   - Ctrl+Q" 
    echo "   - Alt+F4"
    echo "   - Красная кнопка ✕ ВЫХОД в левом верхнем углу"
    echo "   - Кнопка X в заголовке окна"
    echo
    echo "❓ Продолжить? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "Запуск отменен."
        exit 0
    fi
fi

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
echo "🚀 Запуск Distance Attack в безопасном режиме..."
echo

# Запуск программы
timeout 300 python3 main.py &  # Автовыключение через 5 минут
PID=$!

echo "📋 Программа запущена (PID: $PID)"
echo "⏰ Автовыключение через 5 минут"
echo "🛑 Для принудительной остановки: kill $PID"
echo

# Ждем завершения
wait $PID
echo "✅ Программа завершена" 