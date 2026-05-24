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

# --- КОНСТАНТЫ СТАДИЙ ИГРЫ ---
STAGE_BASEMENT_1 = 1        # Подвал 1: Побег от навесного замка
STAGE_UPSTAIRS_1 = 2        # Дом 1: Скрытное прохождение до входной двери
STAGE_STREET_RECAPTURE = 3  # Улица 1: Побег и захват черным фургоном (скрипт)
STAGE_BASEMENT_2 = 4        # Подвал 2: Противостояние, подготовка оружия и ловушки
STAGE_UPSTAIRS_2 = 5        # Дом 2: Отвлечение собаки едой и побег
STAGE_STREET_FINAL = 6      # Улица 2: Финал, встреча с Гвен и полицией

# --- СОСТОЯНИЯ ИГРЫ ---
game_stage = STAGE_BASEMENT_1

# Stage 1 (Basement 1)
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

# Stage 2 (Upstairs 1)
upstairs_alert_timer = 0.0
upstairs_discovered = False
chain_unlocked = False

# Stage 4 (Basement 2)
b2_phone_ringing = False
b2_phone_answered = False
b2_phone_timer = 5.0
b2_grabber_timer = 60.0
dirt_count = 0
trap_dug = False
has_weapon = False
grabber_descending = False
grabber_defeated = False
has_keys = False
fight_stage = 0  # 0: нет боя, 1: спуск Граббера, 2: упал в яму, 3: финальные QTE

# Stage 5 (Upstairs 2)
has_meat = False
dog_distracted = False

# Общие переменные
is_dead = False
is_won = False
player_saved_pos = Vec3(0, 2, 0)
grabber_entity = None

# Начальные позиции игрока для каждой стадии
start_positions = {
    STAGE_BASEMENT_1: Vec3(0, 2, 0),
    STAGE_UPSTAIRS_1: Vec3(0, 2, -12),
    STAGE_STREET_RECAPTURE: Vec3(0, 2, -30),
    STAGE_BASEMENT_2: Vec3(0, 2, 0),
    STAGE_UPSTAIRS_2: Vec3(0, 2, -12),
    STAGE_STREET_FINAL: Vec3(0, 2, -30),
}

# --- СОЗДАНИЕ РОДИТЕЛЬСКИХ ОБЪЕКТОВ ДЛЯ СЦЕН ---
basement_scene = Entity()
upstairs_scene = Entity()
street_scene = Entity()

# --- СЦЕНА 1: ПОДВАЛ (BASEMENT) ---
# Пол
floor = Entity(
    parent=basement_scene,
    model='cube',
    scale=(14, 1, 14),
    position=(0, 0, 0),
    color=color.rgb32(50, 45, 40),
    texture='white_cube',
    collider='box'
)
# Потолок
ceiling = Entity(
    parent=basement_scene,
    model='cube',
    scale=(14, 1, 14),
    position=(0, 6, 0),
    color=color.rgb32(20, 20, 20),
    texture='white_cube',
    collider='box'
)
# Стены подвала
wall_left = Entity(parent=basement_scene, model='cube', scale=(1, 6, 14), position=(-7, 3, 0), color=color.rgb32(35, 35, 35), texture='white_cube', collider='box')
wall_right = Entity(parent=basement_scene, model='cube', scale=(1, 6, 14), position=(7, 3, 0), color=color.rgb32(35, 35, 35), texture='white_cube', collider='box')
wall_back = Entity(parent=basement_scene, model='cube', scale=(14, 6, 1), position=(0, 3, -7), color=color.rgb32(30, 30, 30), texture='white_cube', collider='box')
wall_front = Entity(parent=basement_scene, model='cube', scale=(14, 6, 1), position=(0, 3, 7), color=color.rgb32(30, 30, 30), texture='white_cube', collider='box')

# Грязный матрас в углу
mattress = Entity(
    parent=basement_scene,
    model='cube',
    scale=(3.5, 0.4, 5.5),
    position=(-4.5, 0.7, -3.5),
    color=color.rgb32(120, 110, 95),
    texture='white_cube',
    collider='box'
)
# Дверь подвала (выход)
door = Entity(
    parent=basement_scene,
    model='cube',
    scale=(0.2, 5, 2.5),
    position=(6.4, 3, 2),
    color=color.rgb32(40, 25, 20),
    texture='white_cube',
    collider='box'
)
# Чёрный телефон на стене
phone_base = Entity(
    parent=basement_scene,
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
# Лампочка и свет
bulb = Entity(
    parent=basement_scene,
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

# Ковер, прикрывающий ловушку (используется на 4-й стадии)
carpet = Entity(
    parent=basement_scene,
    model='cube',
    scale=(3.2, 0.1, 2.8),
    position=(4.5, 0.51, 2),
    color=color.rgb32(80, 70, 60),
    texture='white_cube',
    collider='box'
)
# Яма-ловушка под ковром
pit_hole = Entity(
    parent=basement_scene,
    model='cube',
    scale=(2.8, 0.1, 2.4),
    position=(4.5, 0.50, 2),
    color=color.black,
    enabled=False
)

# --- СЦЕНА 2: ВНУТРИ ДОМА (UPSTAIRS HOUSE) ---
upstairs_floor = Entity(parent=upstairs_scene, model='cube', scale=(14, 1, 32), position=(0, 0, 0), color=color.rgb32(75, 60, 50), texture='white_cube', collider='box')
upstairs_ceiling = Entity(parent=upstairs_scene, model='cube', scale=(14, 1, 32), position=(0, 6, 0), color=color.rgb32(20, 20, 20), texture='white_cube', collider='box')
upstairs_wall_l = Entity(parent=upstairs_scene, model='cube', scale=(1, 6, 32), position=(-7, 3, 0), color=color.rgb32(45, 45, 45), texture='white_cube', collider='box')
upstairs_wall_r = Entity(parent=upstairs_scene, model='cube', scale=(1, 6, 32), position=(7, 3, 0), color=color.rgb32(45, 45, 45), texture='white_cube', collider='box')
upstairs_wall_b = Entity(parent=upstairs_scene, model='cube', scale=(14, 6, 1), position=(0, 3, -16), color=color.rgb32(45, 45, 45), texture='white_cube', collider='box')
# Передняя стена с проемом для двери
upstairs_wall_f_l = Entity(parent=upstairs_scene, model='cube', scale=(5.75, 6, 1), position=(-4.125, 3, 16), color=color.rgb32(45, 45, 45), texture='white_cube', collider='box')
upstairs_wall_f_r = Entity(parent=upstairs_scene, model='cube', scale=(5.75, 6, 1), position=(4.125, 3, 16), color=color.rgb32(45, 45, 45), texture='white_cube', collider='box')
upstairs_wall_f_t = Entity(parent=upstairs_scene, model='cube', scale=(2.5, 1, 1), position=(0, 5.5, 16), color=color.rgb32(45, 45, 45), texture='white_cube', collider='box')

# Дверь с лестницы подвала
upstairs_stairs_door = Entity(parent=upstairs_scene, model='cube', scale=(2.5, 5, 0.2), position=(0, 3, -15.8), color=color.rgb32(30, 20, 15), texture='white_cube', collider='box')
# Входная дверь (выход на улицу)
upstairs_front_door = Entity(parent=upstairs_scene, model='cube', scale=(2.5, 5, 0.2), position=(0, 3, 15.9), color=color.rgb32(20, 25, 30), texture='white_cube', collider='box')
# Цепь на двери (для 2-й стадии)
upstairs_chain = Entity(parent=upstairs_scene, model='cube', scale=(0.5, 0.5, 0.2), position=(0.8, 3.2, 15.7), color=color.light_gray, collider='box')

# Мебель и персонажи
upstairs_armchair = Entity(parent=upstairs_scene, model='cube', scale=(2.5, 2, 2.5), position=(-3.5, 1.5, 2), color=color.rgb32(90, 30, 30), texture='white_cube', collider='box')
upstairs_grabber = Entity(parent=upstairs_scene, model='cube', scale=(1.2, 3.5, 1.2), position=(-3.5, 2.2, 2), color=color.rgb32(180, 0, 0), texture='white_cube')
# Маска с рогами Граббера
Entity(parent=upstairs_grabber, model='cube', scale=(0.3, 0.6, 0.3), position=(-0.4, 2.2, 0), color=color.black)
Entity(parent=upstairs_grabber, model='cube', scale=(0.3, 0.6, 0.3), position=(0.4, 2.2, 0), color=color.black)

# Собака Граббера
upstairs_dog = Entity(parent=upstairs_scene, model='cube', scale=(1, 1.2, 2.2), position=(3.5, 1, 2), color=color.rgb32(50, 40, 35), texture='white_cube', collider='box')
# Холодильник (для мяса на 5-й стадии)
upstairs_fridge = Entity(parent=upstairs_scene, model='cube', scale=(2.2, 4.5, 2.2), position=(4.5, 2.7, -6), color=color.white, texture='white_cube', collider='box')

# Слабый свет в доме
upstairs_bulb = Entity(parent=upstairs_scene, model='sphere', scale=0.3, position=(0, 5, 0), color=color.rgb32(255, 220, 180))
upstairs_light = PointLight(parent=upstairs_bulb, color=color.rgb32(240, 210, 170), attenuation=(0.02, 0.05, 0.01))

# --- СЦЕНА 3: УЛИЦА (STREET) ---
street_floor = Entity(parent=street_scene, model='cube', scale=(40, 1, 80), position=(0, 0, 0), color=color.rgb32(35, 35, 35), texture='white_cube', collider='box')
street_wall_l = Entity(parent=street_scene, model='cube', scale=(10, 15, 80), position=(-20, 7.5, 0), color=color.rgb32(50, 50, 60), texture='white_cube', collider='box')
street_wall_r = Entity(parent=street_scene, model='cube', scale=(10, 15, 80), position=(20, 7.5, 0), color=color.rgb32(50, 50, 60), texture='white_cube', collider='box')
street_wall_b = Entity(parent=street_scene, model='cube', scale=(40, 15, 1), position=(0, 7.5, -40), color=color.rgb32(30, 30, 35), texture='white_cube', collider='box')

# Полицейские машины с мигалками
car1 = Entity(parent=street_scene, model='cube', scale=(3, 2, 6), position=(-8, 1.5, 15), color=color.blue, collider='box')
car1_light = Entity(parent=car1, model='sphere', scale=0.6, position=(0, 1.2, 0), color=color.red)

car2 = Entity(parent=street_scene, model='cube', scale=(3, 2, 6), position=(8, 1.5, 20), color=color.white, collider='box')
car2_light = Entity(parent=car2, model='sphere', scale=0.6, position=(0, 1.2, 0), color=color.blue)

# Гвен и Отец
gwen = Entity(parent=street_scene, model='cube', scale=(1, 2.5, 1), position=(0, 1.75, 5), color=color.rgb32(230, 100, 150), collider='box')
father = Entity(parent=street_scene, model='cube', scale=(1.2, 3.2, 1.2), position=(2.5, 2.1, 6), color=color.rgb32(70, 70, 70), collider='box')

# Черный фургон Граббера
black_van = Entity(parent=street_scene, model='cube', scale=(4, 3.5, 8), position=(0, 2.2, 45), color=color.black, collider='box')
van_light_l = Entity(parent=black_van, model='sphere', scale=0.4, position=(-1.5, -0.5, -4.1), color=color.yellow)
van_light_r = Entity(parent=black_van, model='sphere', scale=0.4, position=(1.5, -0.5, -4.1), color=color.yellow)


# --- FPS КОНТРОЛЛЕР ИГРОКА ---
player = FirstPersonController(
    position=(0, 2, 0),
    speed=5,
    height=2
)
player.jump_height = 0
player.cursor.scale = 0

# --- ИНТЕРФЕЙС UI ---
crosshair = Entity(
    parent=camera.ui,
    model='quad',
    color=color.white,
    scale=0.008
)

# Подсказки по центру снизу
prompt_text = Text(
    text='',
    origin=(0, 0),
    position=(0, -0.2),
    scale=1.5,
    color=color.yellow
)

# Диалоговое окно (призраки, Граббер, сюжет)
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

def clear_dialogue():
    set_dialogue_text("")

# Предупреждения на экране
warning_text = Text(
    text='',
    origin=(0, 0),
    position=(0, 0.1),
    scale=2.0,
    color=color.red
)

# Черный/красный фон оверлея при поимке/финале
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

# Глобальное освещение окружения
ambient_light = AmbientLight(color=color.rgb32(30, 30, 35))


# --- ФУНКЦИИ СМЕНЫ СТАДИЙ И СЦЕН ---

def set_stage(stage):
    """Переключает стадию игры, настраивает 3D-сцены и координаты."""
    global game_stage, is_pretending, is_won, is_dead, grabber_entity
    global phone_timer, phone_ringing, phone_answered, grabber_timer, grabber_warning, grabber_active
    global b2_phone_ringing, b2_phone_answered, b2_phone_timer, b2_grabber_timer, dirt_count, trap_dug, has_weapon, grabber_descending, grabber_defeated, has_keys, fight_stage
    global upstairs_alert_timer, upstairs_discovered, chain_unlocked, has_meat, dog_distracted
    
    game_stage = stage
    is_pretending = False
    is_dead = False
    is_won = False
    
    # Возвращаем камеру игроку
    camera.parent = player.camera_pivot
    camera.position = Vec3(0, 0, 0)
    camera.rotation = Vec3(0, 0, 0)
    player.enabled = True
    mouse.locked = True
    
    screamer_overlay.color = color.clear
    screamer_text.text = ""
    warning_text.text = ""
    set_dialogue_text("")
    prompt_text.text = ""
    
    # Переключение видимости сцен
    if game_stage in [STAGE_BASEMENT_1, STAGE_BASEMENT_2]:
        basement_scene.enabled = True
        upstairs_scene.enabled = False
        street_scene.enabled = False
        ambient_light.color = color.rgb32(30, 30, 35)
        light.color = color.rgb32(230, 200, 160)
        door.position = Vec3(6.4, 3, 2)
        door.rotation_y = 0
        phone_receiver.enabled = True
        
        if game_stage == STAGE_BASEMENT_1:
            phone_timer = 10.0
            phone_ringing = False
            phone_answered = False
            grabber_timer = 30.0
            grabber_warning = False
            grabber_active = False
            code_discovered = False
            code_read_from_mattress = False
            door_unlocked = False
            carpet.enabled = False
            pit_hole.enabled = False
        else: # STAGE_BASEMENT_2
            b2_phone_timer = 4.0
            b2_phone_ringing = False
            b2_phone_answered = False
            b2_grabber_timer = 60.0
            dirt_count = 0
            trap_dug = False
            has_weapon = False
            grabber_descending = False
            grabber_defeated = False
            has_keys = False
            fight_stage = 0
            carpet.enabled = True
            carpet.position = Vec3(4.5, 0.51, 2)
            pit_hole.enabled = False
            if grabber_entity:
                destroy(grabber_entity)
                grabber_entity = None
            
    elif game_stage in [STAGE_UPSTAIRS_1, STAGE_UPSTAIRS_2]:
        basement_scene.enabled = False
        upstairs_scene.enabled = True
        street_scene.enabled = False
        ambient_light.color = color.rgb32(20, 20, 25)
        
        upstairs_front_door.position = Vec3(0, 3, 15.9)
        upstairs_front_door.rotation_y = 0
        
        if game_stage == STAGE_UPSTAIRS_1:
            upstairs_chain.enabled = True
            upstairs_chain.position = Vec3(0.8, 3.2, 15.7)
            upstairs_grabber.enabled = True
            upstairs_grabber.position = Vec3(-3.5, 2.2, 2)
            upstairs_grabber.rotation = Vec3(0, 0, 0)
            upstairs_dog.position = Vec3(3.5, 1, 2)
            upstairs_dog.rotation = Vec3(0, 0, 0)
            upstairs_dog.color = color.rgb32(50, 40, 35)
            upstairs_alert_timer = 0.0
            upstairs_discovered = False
            chain_unlocked = False
        else: # STAGE_UPSTAIRS_2
            upstairs_chain.enabled = False
            upstairs_grabber.enabled = False # Граббер одолен в подвале
            upstairs_dog.position = Vec3(0, 1, 10) # Пес загораживает выход
            upstairs_dog.rotation = Vec3(0, 0, 0)
            upstairs_dog.color = color.rgb32(50, 40, 35)
            has_meat = False
            dog_distracted = False
            
    elif game_stage in [STAGE_STREET_RECAPTURE, STAGE_STREET_FINAL]:
        basement_scene.enabled = False
        upstairs_scene.enabled = False
        street_scene.enabled = True
        
        if game_stage == STAGE_STREET_RECAPTURE:
            ambient_light.color = color.rgb32(10, 10, 15)
            black_van.enabled = True
            black_van.position = Vec3(0, 2.2, 45)
            gwen.enabled = False
            father.enabled = False
            car1.enabled = False
            car2.enabled = False
        else: # STAGE_STREET_FINAL
            ambient_light.color = color.rgb32(180, 180, 200) # Утренний свет
            black_van.enabled = False
            gwen.enabled = True
            gwen.position = Vec3(0, 1.75, 5)
            father.enabled = True
            father.position = Vec3(2.5, 2.1, 6)
            car1.enabled = True
            car2.enabled = True
            
    # Телепортация игрока
    player.position = start_positions[game_stage]
    player.rotation = Vec3(0, 0, 0)
    player.velocity = Vec3(0, 0, 0)


def reset_current_stage():
    """Сбрасывает текущую стадию при смерти."""
    set_stage(game_stage)

def restart_game():
    """Полный перезапуск игры."""
    set_stage(STAGE_BASEMENT_1)

def trigger_screamer(text="ГРАББЕР ПОЙМАЛ ТЕБЯ!", look_target=None):
    """Эффект скримера смерти."""
    global is_dead
    is_dead = True
    player.enabled = False
    
    screamer_overlay.color = color.red
    screamer_text.color = color.black
    screamer_text.text = text
    
    if look_target:
        camera.parent = scene
        camera.look_at(look_target)
        
    invoke(reset_current_stage, delay=3.0)


# --- СЮЖЕТНЫЕ СОБЫТИЯ И ДИАЛОГИ ---

# --- СТАДИЯ 1 (BASEMENT 1) ---
def trigger_phone_call_b1():
    """Звонок Брюса на первой стадии."""
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
    invoke(clear_dialogue, delay=7.0)

def read_code_from_mattress():
    global code_read_from_mattress
    code_read_from_mattress = True
    set_dialogue_text("Вы приподняли матрас и обнаружили нацарапанный на бетоне код: 3241")
    invoke(clear_dialogue, delay=5.0)

def unlock_door():
    global door_unlocked
    door_unlocked = True
    set_dialogue_text("Вы ввели код 3241. Навесной замок со щелчком раскрылся!")
    invoke(clear_dialogue, delay=4.0)

# Притворяемся спящим
def start_pretending_sleep():
    global is_pretending, player_saved_pos
    is_pretending = True
    player_saved_pos = player.position
    
    player.enabled = False
    mouse.locked = True
    
    camera.parent = scene
    camera.position = mattress.position + Vec3(0, 0.8, 0)
    camera.rotation = Vec3(-90, 0, 0)

def stop_pretending_sleep():
    global is_pretending
    is_pretending = False
    
    camera.parent = player.camera_pivot
    camera.position = Vec3(0, 0, 0)
    camera.rotation = Vec3(0, 0, 0)
    
    player.position = mattress.position + Vec3(2, 1, 0)
    player.enabled = True
    mouse.locked = True


# --- СТАДИЯ 2 (UPSTAIRS 1) ---
def trigger_upstairs_recapture_immediate():
    """Граббер просыпается в доме."""
    trigger_screamer("ГРАББЕР ПРОСНУЛСЯ И ПОЙМАЛ ТЕБЯ!", upstairs_grabber)


# --- СТАДИЯ 3 (STREET RECAPTURE) ---
def trigger_scripted_recapture():
    """Скриптованный захват черным фургоном на улице."""
    global is_dead
    is_dead = True
    player.enabled = False
    
    screamer_overlay.color = color.black
    screamer_text.color = color.red
    screamer_text.text = (
        "Финни бежит во весь дух по ночной улице...\n"
        "Дома молчат. Никто не слышит его криков.\n\n"
        "Вдруг сзади бесшумно подкатывает черный фургон Граббера!\n"
        "Дверь открывается, и сильные руки затаскивают Финни внутрь.\n\n"
        "«Думал сбежать от меня, щенок?!»"
    )
    
    invoke(transition_to_basement_2, delay=6.0)

def transition_to_basement_2():
    set_stage(STAGE_BASEMENT_2)


# --- СТАДИЯ 4 (BASEMENT 2) ---
def trigger_phone_call_b2():
    """Звонок Робина на 4 стадии."""
    global b2_phone_ringing, b2_phone_answered
    b2_phone_ringing = False
    b2_phone_answered = True
    phone_base.color = color.black
    
    set_dialogue_text(
        "РОБИН (Призрак в трубке):\n"
        "«Финни... Это Робин. Ты не можешь просто сбежать, он поймает тебя на улице.\n"
        "Ты должен дать ему бой.\n"
        "Используй телефонную трубку как оружие. Оторви её и набей её грязью из-под матраса.\n"
        "И выкопай яму у входа под ковриком, чтобы он упал. Будь храбрым!»"
    )
    invoke(clear_dialogue, delay=8.0)

def start_fight_scene():
    """Запуск финала боя."""
    global grabber_descending, fight_stage, grabber_entity
    grabber_descending = True
    fight_stage = 1
    warning_text.text = "Слышны шаги Граббера. Он спускается... Приготовьтесь!"
    
    # Открываем дверь
    door.position = Vec3(6.4, 3, 2.8)
    door.rotation_y = -45
    
    # Спавним Граббера
    grabber_entity = Entity(
        parent=basement_scene,
        model='cube',
        scale=(1.2, 4.5, 1.2),
        position=(5.5, 2.5, 2),
        color=color.rgb32(180, 0, 0),
        texture='white_cube',
        collider='box'
    )
    Entity(parent=grabber_entity, model='cube', scale=(0.3, 0.6, 0.3), position=(-0.4, 2.2, 0), color=color.black)
    Entity(parent=grabber_entity, model='cube', scale=(0.3, 0.6, 0.3), position=(0.4, 2.2, 0), color=color.black)

def trigger_basement_2_unprepared_death():
    global grabber_entity
    grabber_entity = Entity(
        parent=basement_scene,
        model='cube',
        scale=(1.2, 4.5, 1.2),
        position=(5.5, 2.5, 2),
        color=color.rgb32(180, 0, 0),
        texture='white_cube',
        collider='box'
    )
    trigger_screamer("ГРАББЕР ЗАШЕЛ И УБИЛ ВАС (ВЫ НЕ ПОДГОТОВИЛИСЬ)!", grabber_entity)

def trigger_fight_victory_sequence():
    """Анимация победы над Граббером (QTE)."""
    global fight_stage
    fight_stage = 3
    player.enabled = False
    
    screamer_overlay.color = color.white
    warning_text.text = ""
    set_dialogue_text("БУМ! Вы наносите сокрушительный удар тяжелой трубкой по маске Граббера!")
    
    invoke(fight_victory_step_2, delay=2.5)

def fight_victory_step_2():
    screamer_overlay.color = color.rgb32(180, 0, 0)
    set_dialogue_text(
        "ФИННИ: «Это за Брюса! За Билли! За Гриффина! За Вэнса! За Робина!»\n"
        "Вы плотно накидываете телефонный шнур на шею маньяка..."
    )
    invoke(fight_victory_step_3, delay=3.0)

def fight_victory_step_3():
    screamer_overlay.color = color.black
    set_dialogue_text(
        "Телефон на стене неожиданно звонит. Голоса всех призраков шепчут в динамике:\n"
        "«ЭТО ЗВОНОК ДЛЯ ТЕБЯ, ГРАББЕР!»\n\n"
        "*ХРУСТ*"
    )
    invoke(fight_victory_end, delay=4.0)

def fight_victory_end():
    global grabber_defeated
    grabber_defeated = True
    
    screamer_overlay.color = color.clear
    player.enabled = True
    mouse.locked = True
    
    # Кладем Граббера мертвым
    grabber_entity.rotation_x = 90
    grabber_entity.y = 0.6
    grabber_entity.color = color.rgb32(100, 20, 20)
    
    # Обновляем коллайдер для лежачего положения
    grabber_entity.collider = 'box'
    
    set_dialogue_text("Маньяк повержен. Обыщите его тело [E], чтобы забрать ключи.")


# --- СТАДИЯ 6 (STREET FINAL) ---
def trigger_final_reunion_scene():
    """Сцена воссоединения с Гвен."""
    global is_won
    is_won = True
    player.enabled = False
    
    # Гвен бежит к игроку
    gwen.animate_position(player.position - Vec3(0, 0.2, 1.5), duration=1.2)
    
    set_dialogue_text("ГВЕН: «Финни! О боже, Финни! Ты жив!»")
    invoke(reunion_step_2, delay=3.0)

def reunion_step_2():
    father.animate_position(player.position - Vec3(1.5, 0.2, 1.5), duration=1.5)
    set_dialogue_text("ОТЕЦ: «Финни... Прости меня, сынок... Я был так неправ с вами...»")
    invoke(reunion_step_3, delay=4.5)

def reunion_step_3():
    set_dialogue_text("Вы крепко обнимаете Гвен. Кошмар Чёрного Телефона позади.")
    invoke(reunion_final, delay=4.0)

def reunion_final():
    screamer_overlay.color = color.black
    screamer_text.color = color.green
    screamer_text.text = (
        "ВЫ ВЫЖИЛИ!\n\n"
        "Финни Шоу успешно спасся из дома Граббера.\n"
        "Брюс, Билли, Гриффин, Вэнс и Робин обрели покой."
    )
    invoke(restart_game, delay=7.0)


# --- ПОТОКОВАЯ ОБРАБОТКА (ИГРОВОЙ ЦИКЛ) ---

def update():
    global phone_timer, phone_ringing, grabber_timer, grabber_warning, grabber_active, grabber_entity, grabber_check_time
    global b2_phone_timer, b2_phone_ringing, b2_phone_answered, b2_grabber_timer, grabber_descending, fight_stage
    global upstairs_alert_timer, upstairs_discovered
    
    if is_dead or is_won:
        return
        
    # --- 0. Механика бесшумной ходьбы ---
    if game_stage in [STAGE_UPSTAIRS_1, STAGE_UPSTAIRS_2]:
        if held_keys['shift']:
            player.speed = 1.8
        else:
            player.speed = 4.5
            
    # --- 1. Логика по стадиям ---
    
    if game_stage == STAGE_BASEMENT_1:
        # Звонок телефона
        if not phone_answered and not phone_ringing:
            phone_timer -= time.dt
            if phone_timer <= 0:
                phone_ringing = True
                
        if phone_ringing:
            phone_base.color = color.red if int(time.time() * 6) % 2 == 0 else color.black
            
        # Таймер Граббера
        if not grabber_active:
            grabber_timer -= time.dt
            
            if grabber_timer <= 5.0:
                if not grabber_warning:
                    grabber_warning = True
                    warning_text.text = "Слышны шаги Граббера сверху! Притворись спящим на матрасе!"
                    
                if random.random() < 0.15:
                    light.color = color.black if light.color != color.black else color.rgb32(230, 200, 160)
                
                door.position = Vec3(6.4, 3, 2.8)
                door.rotation_y = -45
            else:
                warning_text.text = ""
                
            if grabber_timer <= 0:
                grabber_active = True
                grabber_check_time = 3.0
                
                grabber_entity = Entity(
                    parent=basement_scene,
                    model='cube',
                    scale=(1.2, 4.5, 1.2),
                    position=(5.5, 2.5, 2),
                    color=color.rgb32(180, 0, 0),
                    texture='white_cube',
                    collider='box'
                )
                Entity(parent=grabber_entity, model='cube', scale=(0.3, 0.6, 0.3), position=(-0.4, 2.2, 0), color=color.black)
                Entity(parent=grabber_entity, model='cube', scale=(0.3, 0.6, 0.3), position=(0.4, 2.2, 0), color=color.black)
                
                warning_text.text = "ГРАББЕР ЗАШЕЛ В ПОДВАЛ..."
                light.color = color.rgb32(80, 50, 50)
                
        else:
            grabber_check_time -= time.dt
            if grabber_check_time <= 0:
                if is_pretending:
                    set_dialogue_text("ГРАББЕР:\n«Спит... Хороший мальчик Финни.»")
                    invoke(clear_dialogue, delay=3.0)
                    
                    door.position = Vec3(6.4, 3, 2)
                    door.rotation_y = 0
                    
                    destroy(grabber_entity)
                    grabber_entity = None
                    
                    grabber_timer = random.randint(25, 35)
                    grabber_warning = False
                    grabber_active = False
                    
                    light.color = color.rgb32(230, 200, 160)
                    warning_text.text = ""
                else:
                    trigger_screamer("ГРАББЕР ПОЙМАЛ ТЕБЯ!", grabber_entity)

    elif game_stage == STAGE_UPSTAIRS_1:
        # Проверяем шум игрока около Граббера и собаки
        dist_to_grabber = (player.position - upstairs_grabber.position).length()
        dist_to_dog = (player.position - upstairs_dog.position).length()
        
        is_moving = player.velocity.length() > 0.1
        if is_moving and not held_keys['shift']:
            if dist_to_grabber < 7.0 or dist_to_dog < 7.0:
                if not upstairs_discovered:
                    upstairs_discovered = True
                    warning_text.text = "Вы издали слишком много шума! Граббер просыпается!"
                    upstairs_dog.color = color.red
                    upstairs_grabber.look_at(player)
                    invoke(trigger_upstairs_recapture_immediate, delay=1.5)

    elif game_stage == STAGE_STREET_RECAPTURE:
        # Езда черного фургона навстречу бегущему игроку
        if player.z > -25:
            black_van.z -= time.dt * 18.0
            if black_van.z - player.z < 5.0:
                trigger_scripted_recapture()

    elif game_stage == STAGE_BASEMENT_2:
        # Звонок Робина
        if not b2_phone_answered and not b2_phone_ringing:
            b2_phone_timer -= time.dt
            if b2_phone_timer <= 0:
                b2_phone_ringing = True
                
        if b2_phone_ringing:
            phone_base.color = color.red if int(time.time() * 6) % 2 == 0 else color.black
            
        # Таймер Граббера после ответа на звонок
        if b2_phone_answered and not grabber_descending and fight_stage == 0:
            b2_grabber_timer -= time.dt
            
            if b2_grabber_timer <= 0:
                if has_weapon and trap_dug:
                    start_fight_scene()
                else:
                    trigger_basement_2_unprepared_death()
            else:
                warning_text.text = f"Граббер спустится через: {int(b2_grabber_timer)}с"
                if b2_grabber_timer <= 10.0:
                    if random.random() < 0.15:
                        light.color = color.black if light.color != color.black else color.rgb32(230, 200, 160)

        # Фаза 1 боя: движение к ловушке
        if fight_stage == 1:
            dir = (Vec3(4.5, 2.5, 2) - grabber_entity.position).normalized()
            grabber_entity.position += dir * time.dt * 2.5
            
            # Упал в ловушку
            if (grabber_entity.position - Vec3(4.5, 2.5, 2)).length() < 0.5:
                fight_stage = 2
                grabber_entity.rotation_z = 75
                grabber_entity.y = 1.0
                warning_text.text = "ГРАББЕР УПАЛ В ЯМУ! НАЖМИТЕ [ПРОБЕЛ] ДЛЯ УДАРА!"

    elif game_stage == STAGE_UPSTAIRS_2:
        # Проверяем злую собаку
        if not dog_distracted:
            dist_to_dog = (player.position - upstairs_dog.position).length()
            if dist_to_dog < 4.5:
                trigger_screamer("ПЕС ГРАББЕРА РАСТЕРЗАЛ ВАС!", upstairs_dog)

    elif game_stage == STAGE_STREET_FINAL:
        # Мигалки полицейских машин
        car1_light.color = color.red if int(time.time() * 5) % 2 == 0 else color.blue
        car2_light.color = color.blue if int(time.time() * 5) % 2 == 0 else color.red
        
        # Близость к Гвен для триггера финала
        dist_to_gwen = (player.position - gwen.position).length()
        if dist_to_gwen < 4.5 and not is_won:
            trigger_final_reunion_scene()

    # --- 2. Логика Взаимодействия (Рейкастинг) ---
    if not is_pretending and fight_stage != 2:
        hit_info = raycast(camera.world_position, camera.forward, distance=4.5, ignore=[player])
        hovered = hit_info.entity if hit_info.hit else None
        
        prompt_text.text = ""
        
        if game_stage == STAGE_BASEMENT_1:
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
                    prompt_text.text = "Нажмите [E], чтобы открыть дверь и сбежать вверх!"
                elif code_read_from_mattress:
                    prompt_text.text = "Нажмите [E], чтобы ввести кодовый замок"
                else:
                    prompt_text.text = "Тяжелая железная дверь. Заперта снаружи на замок."
                    
        elif game_stage == STAGE_UPSTAIRS_1:
            if hovered == upstairs_chain:
                if not chain_unlocked:
                    prompt_text.text = "Нажмите [E], чтобы снять цепь с двери"
                else:
                    prompt_text.text = "Цепь снята с двери."
            elif hovered == upstairs_front_door:
                if not chain_unlocked:
                    prompt_text.text = "Дверь заперта на цепь!"
                else:
                    prompt_text.text = "Нажмите [E], чтобы открыть дверь и выйти на улицу"
            elif hovered == upstairs_fridge:
                prompt_text.text = "Обычный холодильник. Внутри пусто."
            elif hovered == upstairs_dog:
                prompt_text.text = "Огромный пес Граббера. Он спит. Тссс..."
            elif hovered == upstairs_grabber:
                prompt_text.text = "Граббер спит в кресле. Не шумите!"
                
        elif game_stage == STAGE_BASEMENT_2:
            if hovered == phone_base or hovered == phone_receiver:
                if b2_phone_ringing:
                    prompt_text.text = "Нажмите [E], чтобы ответить на телефон"
                elif b2_phone_answered:
                    if not has_weapon:
                        if dirt_count >= 2:
                            prompt_text.text = "Нажмите [E], чтобы набить трубку телефона грязью"
                        else:
                            prompt_text.text = "Вам нужно 2 горсти земли для создания оружия"
                    else:
                        prompt_text.text = "Телефонная трубка оторвана. Тяжелое оружие готово!"
            elif hovered == mattress:
                if dirt_count < 3:
                    prompt_text.text = "Нажмите [E], чтобы копать землю под матрасом"
                else:
                    prompt_text.text = "Вы выкопали достаточно земли."
            elif hovered == carpet:
                if not trap_dug:
                    if dirt_count >= 1:
                        prompt_text.text = "Нажмите [E], чтобы выкопать ловушку-яму под ковриком"
                    else:
                        prompt_text.text = "Вам нужна 1 горсть земли, чтобы вырыть яму"
                else:
                    prompt_text.text = "Яма-ловушка готова под ковриком."
            elif hovered == grabber_entity and grabber_defeated and not has_keys:
                prompt_text.text = "Нажмите [E], чтобы обыскать Граббера и забрать ключи"
            elif hovered == door:
                if has_keys:
                    prompt_text.text = "Нажмите [E], чтобы открыть дверь и подняться наверх"
                else:
                    prompt_text.text = "Дверь заперта. Нужно одолеть Граббера и взять ключи."
                    
        elif game_stage == STAGE_UPSTAIRS_2:
            if hovered == upstairs_fridge:
                if not has_meat:
                    prompt_text.text = "Нажмите [E], чтобы открыть холодильник"
                else:
                    prompt_text.text = "Холодильник открыт."
            elif hovered == upstairs_dog:
                if not dog_distracted:
                    if has_meat:
                        prompt_text.text = "Нажмите [E], чтобы бросить псу замороженное мясо"
                    else:
                        prompt_text.text = "Злой пес преграждает путь! Нужно его чем-то отвлечь."
                else:
                    prompt_text.text = "Пес жадно ест мясо и не трогает вас."
            elif hovered == upstairs_front_door:
                if not dog_distracted:
                    prompt_text.text = "Пес не дает подойти к двери!"
                else:
                    prompt_text.text = "Нажмите [E], чтобы открыть дверь ключами Граббера"
    elif is_pretending:
        prompt_text.text = "Нажмите [E], чтобы встать с матраса"


def input(key):
    global is_pretending, code_read_from_mattress, door_unlocked
    global b2_phone_answered, dirt_count, trap_dug, has_weapon, grabber_defeated, has_keys, fight_stage
    global chain_unlocked, has_meat, dog_distracted
    
    if is_dead or is_won:
        return
        
    # QTE удар по Грабберу в яме
    if game_stage == STAGE_BASEMENT_2 and fight_stage == 2 and key == 'space':
        trigger_fight_victory_sequence()
        return
        
    if key == 'e':
        if is_pretending:
            stop_pretending_sleep()
            return
            
        hit_info = raycast(camera.world_position, camera.forward, distance=4.5, ignore=[player])
        if hit_info.hit:
            obj = hit_info.entity
            
            # --- STAGE 1 ---
            if game_stage == STAGE_BASEMENT_1:
                if (obj == phone_base or obj == phone_receiver) and phone_ringing:
                    trigger_phone_call_b1()
                elif obj == mattress:
                    if grabber_warning:
                        start_pretending_sleep()
                    elif code_discovered and not code_read_from_mattress:
                        read_code_from_mattress()
                elif obj == door:
                    if door_unlocked:
                        set_stage(STAGE_UPSTAIRS_1)
                    elif code_read_from_mattress:
                        unlock_door()
                        
            # --- STAGE 2 ---
            elif game_stage == STAGE_UPSTAIRS_1:
                if obj == upstairs_chain and not chain_unlocked:
                    chain_unlocked = True
                    upstairs_chain.enabled = False
                    set_dialogue_text("*Дзинь*... Вы аккуратно сняли тяжелую цепь.")
                    invoke(clear_dialogue, delay=3.0)
                elif obj == upstairs_front_door:
                    if chain_unlocked:
                        set_stage(STAGE_STREET_RECAPTURE)
                    else:
                        set_dialogue_text("Дверь заперта на цепь изнутри.")
                        invoke(clear_dialogue, delay=3.0)
                        
            # --- STAGE 4 ---
            elif game_stage == STAGE_BASEMENT_2:
                if (obj == phone_base or obj == phone_receiver) and b2_phone_ringing:
                    trigger_phone_call_b2()
                elif (obj == phone_base or obj == phone_receiver) and b2_phone_answered and not has_weapon:
                    if dirt_count >= 2:
                        dirt_count -= 2
                        has_weapon = True
                        phone_receiver.enabled = False
                        set_dialogue_text("Вы набили слуховую трубку песком и камнями. Оружие готово!")
                        invoke(clear_dialogue, delay=4.0)
                        if has_weapon and trap_dug:
                            start_fight_scene()
                elif obj == mattress and b2_phone_answered and dirt_count < 3:
                    dirt_count += 1
                    set_dialogue_text(f"Вы приподняли матрас и накопали горсть земли ({dirt_count}/3)")
                    invoke(clear_dialogue, delay=3.0)
                elif obj == carpet and not trap_dug:
                    if dirt_count >= 1:
                        dirt_count -= 1
                        trap_dug = True
                        carpet.position = Vec3(3.8, 0.51, 2)
                        pit_hole.enabled = True
                        set_dialogue_text("Вы выкопали яму перед дверью и замаскировали ее ковриком.")
                        invoke(clear_dialogue, delay=4.0)
                        if has_weapon and trap_dug:
                            start_fight_scene()
                elif obj == grabber_entity and grabber_defeated and not has_keys:
                    has_keys = True
                    set_dialogue_text("Вы обыскали Граббера и нашли связку ключей от дома!")
                    invoke(clear_dialogue, delay=4.0)
                elif obj == door:
                    if has_keys:
                        set_stage(STAGE_UPSTAIRS_2)
                        
            # --- STAGE 5 ---
            elif game_stage == STAGE_UPSTAIRS_2:
                if obj == upstairs_fridge and not has_meat:
                    has_meat = True
                    set_dialogue_text("Вы открыли холодильник и взяли кусок замороженного мяса.")
                    invoke(clear_dialogue, delay=3.0)
                elif obj == upstairs_dog and not dog_distracted and has_meat:
                    dog_distracted = True
                    has_meat = False
                    upstairs_dog.position = Vec3(-3.5, 1, -6)
                    upstairs_dog.rotation = Vec3(0, 90, 0)
                    upstairs_dog.color = color.green
                    set_dialogue_text("Вы бросили мясо собаке. Она жадно грызет его в углу.")
                    invoke(clear_dialogue, delay=4.0)
                elif obj == upstairs_front_door:
                    if dog_distracted:
                        upstairs_front_door.position = Vec3(0, 3, 16.6)
                        upstairs_front_door.rotation_y = 90
                        set_dialogue_text("Дверь со щелчком открылась! Вы на свободе!")
                        invoke(set_stage, STAGE_STREET_FINAL, delay=2.0)


# Запуск игры с первого этапа
set_stage(STAGE_BASEMENT_1)
app.run()
