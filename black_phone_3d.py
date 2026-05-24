#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController

# Создаем приложение Ursina
app = Ursina()

# Окно настроек
window.title = "Чёрный телефон 3D: Побег"
window.borderless = False
window.fullscreen = False
window.exit_button.visible = False
window.fps_counter.visible = True

# --- СОСТОЯНИЯ ИГРЫ ---
phone_timer = 10.0
phone_ringing = False
phone_answered = False

grabber_timer = 30.0
grabber_warning = False
grabber_active = False
grabber_check_time = 0.0

is_pretending = False
code_discovered = False
code_read_from_mattress = False
door_unlocked = False

is_dead = False
is_won = False

# Хранилище для возврата игрока в нормальное состояние
player_saved_pos = Vec3(0, 2, 0)
grabber_entity = None

# --- СОЗДАНИЕ 3D-СЦЕНЫ (ПОДВАЛ) ---
# Пол
floor = Entity(
    model='cube',
    scale=(14, 1, 14),
    position=(0, 0, 0),
    color=color.rgb32(50, 45, 40),
    texture='white_cube',
    collider='box'
)

# Потолок
ceiling = Entity(
    model='cube',
    scale=(14, 1, 14),
    position=(0, 6, 0),
    color=color.rgb32(20, 20, 20),
    texture='white_cube',
    collider='box'
)

# Стены подвала
wall_left = Entity(
    model='cube',
    scale=(1, 6, 14),
    position=(-7, 3, 0),
    color=color.rgb32(35, 35, 35),
    texture='white_cube',
    collider='box'
)

wall_right = Entity(
    model='cube',
    scale=(1, 6, 14),
    position=(7, 3, 0),
    color=color.rgb32(35, 35, 35),
    texture='white_cube',
    collider='box'
)

wall_back = Entity(
    model='cube',
    scale=(14, 6, 1),
    position=(0, 3, -7),
    color=color.rgb32(30, 30, 30),
    texture='white_cube',
    collider='box'
)

wall_front = Entity(
    model='cube',
    scale=(14, 6, 1),
    position=(0, 3, 7),
    color=color.rgb32(30, 30, 30),
    texture='white_cube',
    collider='box'
)

# --- ИНТЕРАКТИВНЫЕ ОБЪЕКТЫ ---

# Грязный матрас в углу
mattress = Entity(
    model='cube',
    scale=(3.5, 0.4, 5.5),
    position=(-4.5, 0.7, -3.5),
    color=color.rgb32(120, 110, 95),
    texture='white_cube',
    collider='box'
)

# Дверь подвала (выход)
door = Entity(
    model='cube',
    scale=(0.2, 5, 2.5),
    position=(6.4, 3, 2),
    color=color.rgb32(40, 25, 20),
    texture='white_cube',
    collider='box'
)

# Чёрный телефон на стене
phone_base = Entity(
    model='cube',
    scale=(0.4, 0.6, 0.2),
    position=(-2, 3.5, -6.4),
    color=color.black,
    collider='box'
)

phone_receiver = Entity(
    parent=phone_base,
    model='cube',
    scale=(0.15, 0.7, 0.25),
    position=(0, 0, 0.1),
    color=color.rgb32(15, 15, 15),
    collider='box'
)

# --- ОСВЕЩЕНИЕ ---
# Лампочка
bulb = Entity(
    model='sphere',
    scale=0.3,
    position=(0, 5.3, 0),
    color=color.yellow
)

light = PointLight(
    parent=bulb,
    color=color.rgb32(230, 200, 160),
    attenuation=(0.02, 0.05, 0.01)
)

# Очень слабое окружающее освещение для создания темноты по углам
AmbientLight(color=color.rgb32(30, 30, 35))


# --- FPS КОНТРОЛЛЕР ИГРОКА ---
player = FirstPersonController(
    position=(0, 2, 0),
    speed=5,
    height=2
)
# Отключаем прыжок, чтобы не прыгать сквозь потолок
player.jump_height = 0
player.cursor.scale = 0

# --- ИНТЕРФЕЙС UI ---
# Прицел (crosshair)
crosshair = Entity(
    parent=camera.ui,
    model='quad',
    color=color.white,
    scale=0.008
)

# Текст подсказок по центру снизу
prompt_text = Text(
    text='',
    origin=(0, 0),
    position=(0, -0.2),
    scale=1.5,
    color=color.yellow
)

# Текст диалога призраков сверху
dialogue_box = Text(
    text='',
    origin=(0, 0),
    position=(0, 0.35),
    scale=1.5,
    color=color.green,
    background=True
)
dialogue_box.background.enabled = False

def set_dialogue_text(text):
    dialogue_box.text = text
    if dialogue_box.background:
        dialogue_box.background.enabled = bool(text)

# Тревожный текст предупреждения об опасности
warning_text = Text(
    text='',
    origin=(0, 0),
    position=(0, 0.1),
    scale=2.0,
    color=color.red
)

# Черный/красный фон для скримера смерти или экрана победы
screamer_overlay = Entity(
    parent=camera.ui,
    model='quad',
    color=color.clear,
    scale=(2, 2)
)

screamer_text = Text(
    text='',
    origin=(0, 0),
    position=(0, 0),
    scale=3.0,
    color=color.red
)

# --- ИГРОВАЯ ЛОГИКА И ФУНКЦИИ ---

def trigger_phone_call():
    """Активация диалога при ответе на телефон."""
    global phone_ringing, phone_answered, code_discovered
    phone_ringing = False
    phone_answered = True
    phone_base.color = color.black
    
    set_dialogue_text(
        "БРЮС (Призрак в трубке):\n"
        "«Привет, Финни... Это Брюс Шоу.\n"
        "Я нацарапал код от двери прямо под твоим матрасом.\n"
        "Найди его, пока Граббер не спустился!»"
    )
    code_discovered = True
    # Убираем текст диалога через 7 секунд
    invoke(clear_dialogue, delay=7)

def clear_dialogue():
    set_dialogue_text("")

def read_code_from_mattress():
    """Событие нахождения кода на полу под матрасом."""
    global code_read_from_mattress
    code_read_from_mattress = True
    set_dialogue_text("Вы приподняли матрас и обнаружили нацарапанный на бетоне код: 3241")
    invoke(clear_dialogue, delay=5)

def unlock_door():
    """Открытие замка на двери."""
    global door_unlocked
    door_unlocked = True
    set_dialogue_text("Вы ввели код 3241. Навесной замок со щелчком раскрылся!")
    invoke(clear_dialogue, delay=4)

def trigger_win():
    """Победа в игре."""
    global is_won
    is_won = True
    player.enabled = False
    screamer_overlay.color = color.black
    screamer_text.color = color.green
    screamer_text.text = "ВЫ ВЫЖИЛИ!\n\nФинни успешно сбежал из подвала."
    invoke(restart_game, delay=6)

def start_pretending_sleep():
    """Игрок ложится на матрас и притворяется спящим."""
    global is_pretending, player_saved_pos
    is_pretending = True
    player_saved_pos = player.position
    
    # Отключаем управление игроком
    player.enabled = False
    mouse.locked = True
    
    # Отсоединяем камеру от игрока и кладем ее на матрас
    camera.parent = scene
    camera.position = mattress.position + Vec3(0, 0.8, 0)
    # Поворачиваем камеру лицом вверх (к потолку)
    camera.rotation = Vec3(-90, 0, 0)

def stop_pretending_sleep():
    """Игрок встает с матраса."""
    global is_pretending
    is_pretending = False
    
    # Возвращаем камеру игроку
    camera.parent = player.camera_pivot
    camera.position = Vec3(0, 0, 0)
    camera.rotation = Vec3(0, 0, 0)
    
    # Перемещаем игрока рядом с матрасом
    player.position = mattress.position + Vec3(2, 1, 0)
    player.enabled = True
    mouse.locked = True

def trigger_screamer():
    """Смерть игрока от маньяка со скримером."""
    global is_dead
    is_dead = True
    player.enabled = False
    
    # Страшный красный экран со скример-надписью
    screamer_overlay.color = color.red
    screamer_text.color = color.black
    screamer_text.text = "ГРАББЕР ПОЙМАЛ ТЕБЯ!"
    
    # Камера смотрит на Граббера (красный куб)
    if grabber_entity:
        camera.parent = scene
        camera.look_at(grabber_entity)
        
    invoke(restart_game, delay=4)

def restart_game():
    """Сброс всех параметров игры к начальным."""
    global phone_timer, phone_ringing, phone_answered
    global grabber_timer, grabber_warning, grabber_active
    global is_pretending, code_discovered, code_read_from_mattress, door_unlocked, is_dead, is_won
    global grabber_entity
    
    phone_timer = 10.0
    phone_ringing = False
    phone_answered = False
    
    grabber_timer = 30.0
    grabber_warning = False
    grabber_active = False
    
    # Всегда принудительно возвращаем камеру игроку при сбросе
    camera.parent = player.camera_pivot
    camera.position = Vec3(0, 0, 0)
    camera.rotation = Vec3(0, 0, 0)
        
    is_pretending = False
    code_discovered = False
    code_read_from_mattress = False
    door_unlocked = False
    is_dead = False
    is_won = False
    
    # Закрываем дверь обратно
    door.position = Vec3(6.4, 3, 2)
    door.rotation_y = 0
    
    # Удаляем фигуру Граббера
    if grabber_entity:
        destroy(grabber_entity)
        grabber_entity = None
        
    # Сбрасываем игрока
    player.position = Vec3(0, 2, 0)
    player.enabled = True
    mouse.locked = True
    
    # Очищаем экраны
    screamer_overlay.color = color.clear
    screamer_text.text = ""
    warning_text.text = ""
    set_dialogue_text("")
    prompt_text.text = ""
    
    # Восстанавливаем свет
    light.color = color.rgb32(230, 200, 160)


# --- ПОТОКОВАЯ ОБРАБОТКА (ИГРОВОЙ ЦИКЛ) ---

def update():
    global phone_timer, phone_ringing, grabber_timer, grabber_warning, grabber_active, grabber_entity, grabber_check_time
    
    if is_dead or is_won:
        return
        
    # --- 1. Логика Таймеров ---
    
    # Таймер телефона
    if not phone_answered and not phone_ringing:
        phone_timer -= time.dt
        if phone_timer <= 0:
            phone_ringing = True
            
    # Эффект мерцания телефона при звонке
    if phone_ringing:
        phone_base.color = color.red if int(time.time() * 6) % 2 == 0 else color.black
        
    # Таймер появления Граббера
    if not grabber_active:
        grabber_timer -= time.dt
        
        # Предупреждение за 5 секунд до прихода
        if grabber_timer <= 5.0:
            if not grabber_warning:
                grabber_warning = True
                warning_text.text = "Слышны шаги Граббера сверху! Притворись спящим на матрасе!"
                
            # Эффект мигания лампочки (хоррор-эффект)
            if random.random() < 0.15:
                light.color = color.black if light.color != color.black else color.rgb32(230, 200, 160)
            
            # Дверь начинает медленно открываться
            door.position = Vec3(6.4, 3, 2.8)
            door.rotation_y = -45
        else:
            warning_text.text = ""
            
        # Наступление события (0 секунд)
        if grabber_timer <= 0:
            grabber_active = True
            grabber_check_time = 3.0  # У Граббера есть 3 секунды, чтобы оценить состояние игрока
            
            # Спавним фигуру Граббера у проема
            grabber_entity = Entity(
                model='cube',
                scale=(1.2, 4.5, 1.2),
                position=(5.5, 2.5, 2),
                color=color.rgb32(180, 0, 0),
                texture='white_cube'
            )
            # Приделываем ему рога к маске для узнаваемости
            Entity(parent=grabber_entity, model='cube', scale=(0.3, 0.6, 0.3), position=(-0.4, 2.2, 0), color=color.black)
            Entity(parent=grabber_entity, model='cube', scale=(0.3, 0.6, 0.3), position=(0.4, 2.2, 0), color=color.black)
            
            warning_text.text = "ГРАББЕР ЗАШЕЛ В ПОДВАЛ..."
            light.color = color.rgb32(80, 50, 50)  # Меняем свет на багровый
            
    else:
        # Фаза пребывания Граббера в комнате
        grabber_check_time -= time.dt
        if grabber_check_time <= 0:
            # Проверяем состояние Финни
            if is_pretending:
                # Финни спасся в этот раз
                set_dialogue_text("ГРАББЕР:\n«Спит... Хороший мальчик Финни.»")
                invoke(clear_dialogue, delay=3)
                
                # Закрываем дверь
                door.position = Vec3(6.4, 3, 2)
                door.rotation_y = 0
                
                # Убираем маньяка
                destroy(grabber_entity)
                grabber_entity = None
                
                # Восстанавливаем таймеры
                grabber_timer = random.randint(25, 35)
                grabber_warning = False
                grabber_active = False
                
                light.color = color.rgb32(230, 200, 160)
                warning_text.text = ""
            else:
                # Граббер замечает игрока стоящим или ходящим
                trigger_screamer()

    # --- 2. Логика Взаимодействия (Рейкастинг) ---
    
    # Если мы спим, мы можем смотреть только на потолок, рейкаст не нужен для поиска объектов
    if is_pretending:
        prompt_text.text = "Нажмите [E], чтобы встать с матраса"
        return

    # Выпускаем луч вперед из камеры
    hit_info = raycast(camera.world_position, camera.forward, distance=4.5, ignore=[player])
    hovered = hit_info.entity if hit_info.hit else None
    
    # Обработка подсказок интерфейса
    if hovered == phone_base or hovered == phone_receiver:
        if phone_ringing:
            prompt_text.text = "Нажмите [E], чтобы ответить на телефон"
        elif not phone_answered:
            prompt_text.text = "Телефон молчит. Провод обрезан."
        else:
            prompt_text.text = "Телефон издает лишь тихое шипение призраков..."
            
    elif hovered == mattress:
        if grabber_warning:
            prompt_text.text = "Нажмите [E], чтобы быстро лечь и притвориться спящим!"
        elif code_discovered and not code_read_from_mattress:
            prompt_text.text = "Нажмите [E], чтобы осмотреть под матрасом"
        else:
            prompt_text.text = "Грязный матрас. От него пахнет сыростью."
            
    elif hovered == door:
        if door_unlocked:
            prompt_text.text = "Нажмите [E], чтобы сбежать на свободу!"
        elif code_read_from_mattress:
            prompt_text.text = "Нажмите [E], чтобы ввести кодовый замок"
        else:
            prompt_text.text = "Тяжелая железная дверь. Заперта снаружи на замок."
            
    else:
        prompt_text.text = ""


def input(key):
    """Слушатель клавиш."""
    global is_pretending, code_read_from_mattress, door_unlocked
    
    if is_dead or is_won:
        return
        
    if key == 'e':
        # Если притворяемся спящим, нажатие E заставляет встать
        if is_pretending:
            stop_pretending_sleep()
            return
            
        # Проверяем, на что смотрит игрок
        hit_info = raycast(camera.world_position, camera.forward, distance=4.5, ignore=[player])
        if hit_info.hit:
            obj = hit_info.entity
            
            # Телефон
            if (obj == phone_base or obj == phone_receiver) and phone_ringing:
                trigger_phone_call()
                
            # Матрас
            elif obj == mattress:
                if grabber_warning:
                    start_pretending_sleep()
                elif code_discovered and not code_read_from_mattress:
                    read_code_from_mattress()
                    
            # Дверь
            elif obj == door:
                if door_unlocked:
                    trigger_win()
                elif code_read_from_mattress:
                    unlock_door()


# Запускаем Ursina Engine
app.run()
