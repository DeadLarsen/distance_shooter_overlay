#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Distance Attack - Оверлей для показа расстояний в шутерах
Автор: DeadLarsen
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
import math
import json
import os
from threading import Thread
import time

class DistanceOverlay:
    def __init__(self):
        self.root = tk.Tk()
        
        # Настройки по умолчанию (ДОЛЖНЫ БЫТЬ ДО setup_window!)
        self.calibration_pixels_per_meter = 100  # пикселей на метр (будет калиброваться)
        self.distances = [1, 5, 10, 25, 40]  # метры
        self.overlay_enabled = False
        self.calibration_mode = False
        
        # Настройки перспективы
        self.perspective_enabled = True  # Включить перспективу (эллипсы вместо кругов)
        self.horizon_offset = 0.3  # Высота горизонта (0.0 = низ экрана, 1.0 = верх экрана)
        self.perspective_ratio = 0.2  # Сжатие эллипсов (0.1 = сильно сжато, 1.0 = круг)
        self.foot_position_ratio = 0.85  # Позиция ног в процентах от высоты экрана
        
        # Настройки мониторов
        self.current_monitor = 0  # Текущий монитор (по умолчанию основной)
        self.monitor_geometries = []  # Список геометрий мониторов
        
        # Цвета кругов
        self.circle_colors = ['#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF']
        
        # Настройки
        self.settings_file = 'distance_settings.json'
        self.load_settings()
        
        # Определяем мониторы
        self.detect_monitors()
        
        # Настройка окна (ПОСЛЕ инициализации переменных!)
        self.setup_window()
        
        # UI элементы
        self.setup_ui()
        
        # Привязка клавиш
        self.setup_keybinds()
        
        # Создаем кнопку экстренного выхода на оверлее для Linux
        import platform
        if platform.system() == 'Linux':
            self.create_emergency_exit_button()
    
    def setup_window(self):
        """Настройка главного окна с прозрачностью на выбранном мониторе"""
        import platform
        
        self.root.title("Distance Attack")
        
        # Получаем геометрию выбранного монитора
        if self.current_monitor < len(self.monitor_geometries):
            monitor = self.monitor_geometries[self.current_monitor]
            monitor_x = monitor['x']
            monitor_y = monitor['y']
            monitor_width = monitor['width']
            monitor_height = monitor['height']
        else:
            # Fallback на весь экран
            monitor_x = 0
            monitor_y = 0
            monitor_width = self.root.winfo_screenwidth()
            monitor_height = self.root.winfo_screenheight()
        
        # Безопасная настройка для Linux
        if platform.system() == 'Linux':
            # В Linux НЕ убираем рамку окна для безопасности
            window_width = monitor_width - 100
            window_height = monitor_height - 100
            window_x = monitor_x + 50
            window_y = monitor_y + 50
            
            self.root.geometry(f"{window_width}x{window_height}+{window_x}+{window_y}")
            self.root.configure(bg='black')
            self.root.attributes('-topmost', True)
            self.root.attributes('-alpha', 0.8)  # Менее прозрачный для видимости
            
            # Добавляем кнопку экстренного выхода в заголовок
            self.root.protocol("WM_DELETE_WINDOW", self.quit_app)
            
            self.screen_width = window_width
            self.screen_height = window_height
            
        else:
            # Для Windows используем полноэкранный режим на выбранном мониторе
            self.root.attributes('-topmost', True)
            self.root.attributes('-alpha', 0.3)
            try:
                self.root.wm_attributes('-transparentcolor', 'black')
            except tk.TclError:
                pass
            
            self.root.geometry(f"{monitor_width}x{monitor_height}+{monitor_x}+{monitor_y}")
            self.root.configure(bg='black')
            self.root.overrideredirect(True)
            
            self.screen_width = monitor_width
            self.screen_height = monitor_height
        
        # Canvas для рисования кругов
        self.canvas = tk.Canvas(
            self.root, 
            width=self.screen_width, 
            height=self.screen_height,
            bg='black',
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Центр экрана по горизонтали
        self.center_x = self.screen_width // 2
        
        # Позиция ног игрока (центр окружностей) - в нижней части экрана
        self.foot_position_y = int(self.screen_height * self.foot_position_ratio)
        
        # Центр прицела остается в центре экрана
        self.crosshair_y = self.screen_height // 2
    
    def setup_ui(self):
        """Создание интерфейса управления"""
        # Создаем отдельное окно для управления
        self.control_window = tk.Toplevel(self.root)
        self.control_window.title("Distance Attack - Управление")
        self.control_window.geometry("450x800")
        self.control_window.attributes('-topmost', True)
        
        # Выбор монитора
        monitor_frame = tk.Frame(self.control_window)
        monitor_frame.pack(pady=10)
        
        tk.Label(monitor_frame, text="Выбор монитора:", font=('Arial', 10, 'bold')).pack()
        
        self.monitor_var = tk.StringVar()
        monitor_options = []
        for i, monitor in enumerate(self.monitor_geometries):
            monitor_options.append(f"{i}: {monitor['name']} ({monitor['width']}x{monitor['height']})")
        
        if monitor_options:
            self.monitor_combo = tk.OptionMenu(monitor_frame, self.monitor_var, *monitor_options, command=self.change_monitor)
            self.monitor_var.set(monitor_options[self.current_monitor] if self.current_monitor < len(monitor_options) else monitor_options[0])
            self.monitor_combo.pack(pady=5)
        
        # Кнопки управления
        tk.Button(
            self.control_window, 
            text="Калибровка", 
            command=self.start_calibration,
            font=('Arial', 12)
        ).pack(pady=10)
        
        tk.Button(
            self.control_window, 
            text="Включить/Выключить оверлей", 
            command=self.toggle_overlay,
            font=('Arial', 12)
        ).pack(pady=5)
        
        # Настройки дистанций
        tk.Label(self.control_window, text="Дистанции (метры):", font=('Arial', 10)).pack(pady=(20,5))
        
        self.distance_frame = tk.Frame(self.control_window)
        self.distance_frame.pack(pady=5)
        
        self.distance_entries = []
        for i, dist in enumerate(self.distances):
            frame = tk.Frame(self.distance_frame)
            frame.pack(side=tk.LEFT, padx=5)
            
            tk.Label(frame, text=f"#{i+1}:", font=('Arial', 9)).pack()
            entry = tk.Entry(frame, width=6, justify='center')
            entry.insert(0, str(dist))
            entry.pack()
            self.distance_entries.append(entry)
        
        tk.Button(
            self.control_window, 
            text="Применить дистанции", 
            command=self.update_distances,
            font=('Arial', 10)
        ).pack(pady=10)
        
        # Настройки перспективы
        tk.Label(self.control_window, text="Настройки перспективы:", font=('Arial', 10, 'bold')).pack(pady=(20,5))
        
        # Включение/выключение перспективы
        self.perspective_var = tk.BooleanVar(value=self.perspective_enabled)
        tk.Checkbutton(
            self.control_window,
            text="Включить перспективу (эллипсы вместо кругов)",
            variable=self.perspective_var,
            command=self.toggle_perspective,
            font=('Arial', 9)
        ).pack(pady=5)
        
        # Настройка горизонта
        perspective_frame = tk.Frame(self.control_window)
        perspective_frame.pack(pady=10)
        
        tk.Label(perspective_frame, text="Высота горизонта:", font=('Arial', 9)).pack()
        self.horizon_scale = tk.Scale(
            perspective_frame,
            from_=0.0,
            to=0.8,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            length=200,
            command=self.update_perspective
        )
        self.horizon_scale.set(self.horizon_offset)
        self.horizon_scale.pack()
        
        # Настройка сжатия
        tk.Label(perspective_frame, text="Сжатие эллипсов:", font=('Arial', 9)).pack()
        self.ratio_scale = tk.Scale(
            perspective_frame,
            from_=0.1,
            to=1.0,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            length=200,
            command=self.update_perspective
        )
        self.ratio_scale.set(self.perspective_ratio)
        self.ratio_scale.pack()
        
        # Настройка позиции ног
        tk.Label(perspective_frame, text="Позиция ног (% от высоты экрана):", font=('Arial', 9)).pack()
        self.foot_scale = tk.Scale(
            perspective_frame,
            from_=0.6,
            to=0.95,
            resolution=0.05,
            orient=tk.HORIZONTAL,
            length=200,
            command=self.update_foot_position
        )
        self.foot_scale.set(self.foot_position_ratio)
        self.foot_scale.pack()
        
        # Информация о калибровке
        self.calibration_info = tk.Label(
            self.control_window, 
            text=f"Калибровка: {self.calibration_pixels_per_meter:.1f} пикс/метр",
            font=('Arial', 10)
        )
        self.calibration_info.pack(pady=10)
        
        # Статус
        self.status_label = tk.Label(
            self.control_window, 
            text="Статус: Выключен",
            font=('Arial', 10),
            fg='red'
        )
        self.status_label.pack(pady=5)
        
        # Горячие клавиши
        import platform
        hotkeys_text = "Горячие клавиши:\nF1 - Калибровка\nF2 - Вкл/Выкл оверлей\nESC - Выход"
        if platform.system() == 'Linux':
            hotkeys_text += "\nCtrl+C, Ctrl+Q, Alt+F4 - Выход\nКрасная кнопка на оверлее - Выход"
        
        tk.Label(
            self.control_window, 
            text=hotkeys_text,
            font=('Arial', 9),
            justify='left'
        ).pack(pady=20)
        
        tk.Button(
            self.control_window, 
            text="Выход", 
            command=self.quit_app,
            font=('Arial', 12),
            bg='red',
            fg='white'
        ).pack(pady=20)
    
    def setup_keybinds(self):
        """Настройка горячих клавиш"""
        self.root.bind('<F1>', lambda e: self.start_calibration())
        self.root.bind('<F2>', lambda e: self.toggle_overlay())
        self.root.bind('<Escape>', lambda e: self.quit_app())
        
        # Дополнительные клавиши для экстренного выхода
        self.root.bind('<Control-c>', lambda e: self.quit_app())
        self.root.bind('<Control-q>', lambda e: self.quit_app())
        self.root.bind('<Alt-F4>', lambda e: self.quit_app())
        
        # Фокус на главном окне для получения событий клавиатуры
        self.root.focus_set()
    
    def detect_monitors(self):
        """Определение доступных мониторов"""
        import platform
        
        # Базовая геометрия (весь экран)
        total_width = self.root.winfo_screenwidth()
        total_height = self.root.winfo_screenheight()
        
        # Список мониторов (по умолчанию один основной)
        self.monitor_geometries = [
            {"name": "Основной монитор", "x": 0, "y": 0, "width": total_width, "height": total_height}
        ]
        
        # Пытаемся определить дополнительные мониторы в Linux
        if platform.system() == 'Linux':
            try:
                import subprocess
                result = subprocess.run(['xrandr', '--query'], capture_output=True, text=True)
                if result.returncode == 0:
                    self.parse_xrandr_output(result.stdout)
            except Exception as e:
                print(f"Не удалось определить мониторы: {e}")
        
        print(f"Найдено мониторов: {len(self.monitor_geometries)}")
        for i, monitor in enumerate(self.monitor_geometries):
            print(f"  {i}: {monitor['name']} - {monitor['width']}x{monitor['height']} at ({monitor['x']}, {monitor['y']})")
    
    def parse_xrandr_output(self, xrandr_output):
        """Парсинг вывода xrandr для определения мониторов"""
        import re
        
        monitors = []
        lines = xrandr_output.split('\n')
        
        for line in lines:
            # Ищем подключенные мониторы
            if ' connected ' in line:
                # Пример: "DP-1 connected 1920x1080+1920+0 (normal left inverted right x axis y axis) 510mm x 287mm"
                match = re.search(r'(\S+) connected(?: primary)? (\d+)x(\d+)\+(\d+)\+(\d+)', line)
                if match:
                    name = match.group(1)
                    width = int(match.group(2))
                    height = int(match.group(3))
                    x = int(match.group(4))
                    y = int(match.group(5))
                    
                    monitors.append({
                        "name": name,
                        "x": x,
                        "y": y,
                        "width": width,
                        "height": height
                    })
        
        if monitors:
            # Сортируем мониторы по позиции (слева направо, сверху вниз)
            monitors.sort(key=lambda m: (m['y'], m['x']))
            self.monitor_geometries = monitors
    
    def create_emergency_exit_button(self):
        """Создает видимую кнопку экстренного выхода для Linux"""
        exit_button = tk.Button(
            self.root,
            text="✕ ВЫХОД",
            command=self.quit_app,
            bg='red',
            fg='white',
            font=('Arial', 12, 'bold'),
            relief='raised',
            bd=3
        )
        exit_button.place(x=10, y=10, width=100, height=40)
    
    def start_calibration(self):
        """Начать калибровку"""
        if self.calibration_mode:
            return
            
        self.calibration_mode = True
        self.overlay_enabled = False
        self.clear_canvas()
        
        # Диалог для ввода эталонного расстояния
        distance_str = simpledialog.askstring(
            "Калибровка", 
            "Введите эталонное расстояние в метрах\n(например, 10 для 10 метров):",
            initialvalue="10"
        )
        
        if not distance_str:
            self.calibration_mode = False
            return
            
        try:
            self.calibration_distance = float(distance_str)
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректное число!")
            self.calibration_mode = False
            return
        
        # Инструкции для калибровки
        messagebox.showinfo(
            "Калибровка", 
            f"Сейчас появится красный круг.\n"
            f"Измените его размер колесиком мыши так,\n"
            f"чтобы он соответствовал {self.calibration_distance} метрам в игре.\n"
            f"Нажмите Enter когда закончите, Esc для отмены."
        )
        
        # Показываем калибровочный круг
        self.calibration_radius = 100
        self.draw_calibration_circle()
        
        # Привязываем события для калибровки
        self.root.bind('<MouseWheel>', self.on_mouse_wheel)
        self.root.bind('<Button-4>', self.on_mouse_wheel)  # Linux
        self.root.bind('<Button-5>', self.on_mouse_wheel)  # Linux
        self.root.bind('<Return>', self.finish_calibration)
        self.root.bind('<Escape>', self.cancel_calibration)
    
    def draw_calibration_circle(self):
        """Рисование калибровочного круга с центром в позиции ног"""
        self.clear_canvas()
        
        # Рисуем калибровочный круг с центром в позиции ног
        self.canvas.create_oval(
            self.center_x - self.calibration_radius,
            self.foot_position_y - self.calibration_radius,
            self.center_x + self.calibration_radius,
            self.foot_position_y + self.calibration_radius,
            outline='red',
            width=3,
            tags='calibration'
        )
        
        # Центральная точка в позиции ног
        self.canvas.create_oval(
            self.center_x - 3,
            self.foot_position_y - 3,
            self.center_x + 3,
            self.foot_position_y + 3,
            fill='red',
            outline='red',
            tags='calibration'
        )
        
        # Прицел в центре экрана
        self.canvas.create_oval(
            self.center_x - 2,
            self.crosshair_y - 2,
            self.center_x + 2,
            self.crosshair_y + 2,
            fill='white',
            outline='white',
            tags='calibration'
        )
        
        # Текст с информацией (с контуром для лучшей видимости)
        text_content = f"Калибровка: {self.calibration_distance}м\nКолесико для изменения размера\nЦентр круга = позиция ваших ног"
        # Контур текста
        for dx, dy in [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]:
            self.canvas.create_text(
                self.center_x + dx,
                self.foot_position_y - self.calibration_radius - 50 + dy,
                text=text_content,
                fill='black',
                font=('Arial', 12, 'bold'),
                tags='calibration'
            )
        # Основной текст
        self.canvas.create_text(
            self.center_x,
            self.foot_position_y - self.calibration_radius - 50,
            text=text_content,
            fill='white',
            font=('Arial', 12, 'bold'),
            tags='calibration'
        )
    
    def on_mouse_wheel(self, event):
        """Обработка колесика мыши для изменения размера калибровочного круга"""
        if not self.calibration_mode:
            return
            
        # Определяем направление прокрутки
        if event.delta > 0 or event.num == 4:
            self.calibration_radius += 5
        elif event.delta < 0 or event.num == 5:
            self.calibration_radius = max(10, self.calibration_radius - 5)
        
        self.draw_calibration_circle()
    
    def finish_calibration(self, event=None):
        """Завершить калибровку"""
        if not self.calibration_mode:
            return
            
        # Вычисляем пиксели на метр
        self.calibration_pixels_per_meter = self.calibration_radius / self.calibration_distance
        
        # Очищаем привязки событий калибровки
        self.root.unbind('<MouseWheel>')
        self.root.unbind('<Button-4>')
        self.root.unbind('<Button-5>')
        self.root.unbind('<Return>')
        
        # Восстанавливаем основные привязки
        self.root.bind('<Escape>', lambda e: self.quit_app())
        
        self.calibration_mode = False
        self.clear_canvas()
        
        # Обновляем информацию о калибровке
        self.calibration_info.config(
            text=f"Калибровка: {self.calibration_pixels_per_meter:.1f} пикс/метр"
        )
        
        # Сохраняем настройки
        self.save_settings()
        
        messagebox.showinfo("Калибровка", "Калибровка завершена!")
    
    def cancel_calibration(self, event=None):
        """Отменить калибровку"""
        if not self.calibration_mode:
            return
            
        # Очищаем привязки событий калибровки
        self.root.unbind('<MouseWheel>')
        self.root.unbind('<Button-4>')
        self.root.unbind('<Button-5>')
        self.root.unbind('<Return>')
        
        # Восстанавливаем основные привязки
        self.root.bind('<Escape>', lambda e: self.quit_app())
        
        self.calibration_mode = False
        self.clear_canvas()
    
    def toggle_overlay(self):
        """Включить/выключить оверлей"""
        if self.calibration_mode:
            return
            
        self.overlay_enabled = not self.overlay_enabled
        
        if self.overlay_enabled:
            self.draw_distance_circles()
            self.status_label.config(text="Статус: Включен", fg='green')
        else:
            self.clear_canvas()
            self.status_label.config(text="Статус: Выключен", fg='red')
    
    def draw_distance_circles(self):
        """Рисование кругов дистанций с перспективой от позиции ног"""
        self.clear_canvas()
        
        if not self.overlay_enabled:
            return
        
        # Вычисляем горизонт относительно позиции ног
        horizon_y = self.foot_position_y - (self.screen_height * self.horizon_offset)
        
        # Рисуем круги для каждой дистанции
        for i, distance in enumerate(self.distances):
            if distance <= 0:
                continue
                
            radius = distance * self.calibration_pixels_per_meter
            color = self.circle_colors[i % len(self.circle_colors)]
            
            if self.perspective_enabled:
                # Рисуем эллипс с перспективой
                # Горизонтальный радиус остается тем же
                radius_x = radius
                # Вертикальный радиус сжимается для создания перспективы
                radius_y = radius * self.perspective_ratio
                
                # Центр эллипса находится в позиции ног игрока
                # Чем дальше дистанция, тем выше к горизонту поднимается эллипс
                distance_factor = min(distance / 50.0, 1.0)  # Нормализуем до 50 метров
                ellipse_center_y = self.foot_position_y - (distance_factor * (self.foot_position_y - horizon_y))
                
                # Рисуем эллипс
                self.canvas.create_oval(
                    self.center_x - radius_x,
                    ellipse_center_y - radius_y,
                    self.center_x + radius_x,
                    ellipse_center_y + radius_y,
                    outline=color,
                    width=2,
                    tags='distance_circle'
                )
                
                # Подпись дистанции (размещаем над эллипсом)
                text_y = ellipse_center_y - radius_y - 15
                
            else:
                # Рисуем обычный круг с центром в позиции ног
                self.canvas.create_oval(
                    self.center_x - radius,
                    self.foot_position_y - radius,
                    self.center_x + radius,
                    self.foot_position_y + radius,
                    outline=color,
                    width=2,
                    tags='distance_circle'
                )
                text_y = self.foot_position_y - radius - 15
            
            # Подпись дистанции (с контуром для лучшей видимости)
            text_content = f"{distance}м"
            # Контур текста
            for dx, dy in [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]:
                self.canvas.create_text(
                    self.center_x + dx,
                    text_y + dy,
                    text=text_content,
                    fill='black',
                    font=('Arial', 10, 'bold'),
                    tags='distance_circle'
                )
            # Основной текст
            self.canvas.create_text(
                self.center_x,
                text_y,
                text=text_content,
                fill=color,
                font=('Arial', 10, 'bold'),
                tags='distance_circle'
            )
        
        # Центральная точка (прицел) - остается в центре экрана
        self.canvas.create_oval(
            self.center_x - 2,
            self.crosshair_y - 2,
            self.center_x + 2,
            self.crosshair_y + 2,
            fill='white',
            outline='white',
            tags='distance_circle'
        )
    
    def update_distances(self):
        """Обновить дистанции из полей ввода"""
        new_distances = []
        
        for entry in self.distance_entries:
            try:
                dist = float(entry.get())
                if dist > 0:
                    new_distances.append(dist)
                else:
                    new_distances.append(0)
            except ValueError:
                new_distances.append(0)
        
        self.distances = new_distances
        
        # Перерисовываем круги если оверлей включен
        if self.overlay_enabled:
            self.draw_distance_circles()
        
        # Сохраняем настройки
        self.save_settings()
    
    def toggle_perspective(self):
        """Включить/выключить перспективу"""
        self.perspective_enabled = self.perspective_var.get()
        
        # Перерисовываем круги если оверлей включен
        if self.overlay_enabled:
            self.draw_distance_circles()
        
        # Сохраняем настройки
        self.save_settings()
    
    def update_perspective(self, value=None):
        """Обновить настройки перспективы"""
        self.horizon_offset = self.horizon_scale.get()
        self.perspective_ratio = self.ratio_scale.get()
        
        # Перерисовываем круги если оверлей включен
        if self.overlay_enabled:
            self.draw_distance_circles()
        
        # Сохраняем настройки
        self.save_settings()
    
    def update_foot_position(self, value=None):
        """Обновить позицию ног"""
        foot_ratio = self.foot_scale.get()
        self.foot_position_y = int(self.screen_height * foot_ratio)
        
        # Перерисовываем круги если оверлей включен
        if self.overlay_enabled:
            self.draw_distance_circles()
        
        # Перерисовываем калибровочный круг если в режиме калибровки
        if self.calibration_mode:
            self.draw_calibration_circle()
        
        # Сохраняем настройки
        self.save_settings()
    
    def change_monitor(self, selection):
        """Сменить монитор"""
        try:
            # Извлекаем номер монитора из строки выбора
            monitor_index = int(selection.split(':')[0])
            if monitor_index != self.current_monitor and monitor_index < len(self.monitor_geometries):
                self.current_monitor = monitor_index
                
                # Сохраняем настройки
                self.save_settings()
                
                # Перезапускаем окно на новом мониторе
                self.restart_on_monitor()
                
        except (ValueError, IndexError) as e:
            print(f"Ошибка при смене монитора: {e}")
    
    def restart_on_monitor(self):
        """Перезапуск оверлея на новом мониторе"""
        # Сохраняем текущее состояние
        was_overlay_enabled = self.overlay_enabled
        was_calibration_mode = self.calibration_mode
        
        # Закрываем текущее окно оверлея
        self.canvas.destroy()
        
        # Пересоздаем окно на новом мониторе
        self.setup_window()
        
        # Восстанавливаем состояние
        if was_overlay_enabled:
            self.overlay_enabled = True
            self.draw_distance_circles()
        
        if was_calibration_mode:
            self.calibration_mode = True
            self.draw_calibration_circle()
        
        # Пересоздаем кнопку экстренного выхода для Linux
        import platform
        if platform.system() == 'Linux':
            self.create_emergency_exit_button()
    
    def clear_canvas(self):
        """Очистить canvas"""
        self.canvas.delete('all')
    
    def save_settings(self):
        """Сохранить настройки в файл"""
        settings = {
            'calibration_pixels_per_meter': self.calibration_pixels_per_meter,
            'distances': self.distances,
            'circle_colors': self.circle_colors,
            'perspective_enabled': self.perspective_enabled,
            'horizon_offset': self.horizon_offset,
            'perspective_ratio': self.perspective_ratio,
            'foot_position_ratio': self.foot_position_ratio,
            'current_monitor': self.current_monitor
        }
        
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка сохранения настроек: {e}")
    
    def load_settings(self):
        """Загрузить настройки из файла"""
        if not os.path.exists(self.settings_file):
            return
        
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            self.calibration_pixels_per_meter = settings.get('calibration_pixels_per_meter', 100)
            self.distances = settings.get('distances', [1, 5, 10, 25, 40])
            self.circle_colors = settings.get('circle_colors', ['#FF0000', '#00FF00', '#0000FF', '#FFFF00', '#FF00FF'])
            self.perspective_enabled = settings.get('perspective_enabled', True)
            self.horizon_offset = settings.get('horizon_offset', 0.3)
            self.perspective_ratio = settings.get('perspective_ratio', 0.2)
            self.foot_position_ratio = settings.get('foot_position_ratio', 0.85)
            self.current_monitor = settings.get('current_monitor', 0)
            
        except Exception as e:
            print(f"Ошибка загрузки настроек: {e}")
    
    def quit_app(self):
        """Выход из приложения"""
        self.save_settings()
        self.root.quit()
        self.root.destroy()
    
    def run(self):
        """Запуск приложения"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.quit_app()

def main():
    """Главная функция"""
    print("Distance Attack - Оверлей для показа расстояний в шутерах")
    print("Автор: DeadLarsen")
    print()
    print("Горячие клавиши:")
    print("F1 - Калибровка")
    print("F2 - Включить/Выключить оверлей")
    print("ESC - Выход")
    print()
    
    app = DistanceOverlay()
    app.run()

if __name__ == "__main__":
    main() 