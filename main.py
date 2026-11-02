import pygame
import random
import math
import json
import os
import sys

pygame.init()

# Procedural sound effects: no external audio files are required.
try:
    pygame.mixer.pre_init(44100, -16, 1, 512)
    if not pygame.mixer.get_init():
        pygame.mixer.init()
    import array
    import struct

    def make_tone(start_freq, end_freq, duration, volume=0.25, noise=0.0):
        sample_rate = 22050
        count = max(1, int(sample_rate * duration))
        samples = array.array("h")
        for i in range(count):
            t = i / sample_rate
            fade = min(1.0, i / max(1, count * 0.04),
                       (count - i) / max(1, count * 0.18))
            freq = start_freq + (end_freq - start_freq) * (i / count)
            wave = math.sin(2 * math.pi * freq * t)
            n = random.uniform(-1, 1) * noise
            samples.append(int(max(-1, min(1, (wave * (1-noise) + n) * volume * fade)) * 32767))
        return pygame.mixer.Sound(buffer=samples.tobytes())

    SOUNDS = {
        "rifle": make_tone(190, 75, 0.075, 0.28, 0.35),
        "shotgun": make_tone(105, 42, 0.16, 0.42, 0.55),
        "rail": make_tone(850, 180, 0.18, 0.32, 0.12),
        "enemy": make_tone(300, 95, 0.11, 0.22, 0.5),
        "hit": make_tone(180, 55, 0.09, 0.26, 0.5),
        "pickup": make_tone(520, 1050, 0.15, 0.22, 0.05),
        "reload": make_tone(240, 390, 0.10, 0.15, 0.08),
        "dash": make_tone(500, 130, 0.14, 0.18, 0.25),
        "level": make_tone(400, 900, 0.30, 0.20, 0.03),
        "death": make_tone(260, 40, 0.45, 0.28, 0.25),
    }
    for _sound in SOUNDS.values():
        _sound.set_volume(0.55)
except (pygame.error, ImportError, RuntimeError):
    SOUNDS = {}


def play_sound(name):
    sound = SOUNDS.get(name)
    if sound:
        try:
            sound.play()
        except pygame.error:
            pass


        


# ============================================================
# OUTPOST ZERO: SURVIVAL PROTOCOL
# ============================================================

WIDTH, HEIGHT = 1100, 700
WORLD_W, WORLD_H = 2200, 1700
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("OUTPOST ZERO // SURVIVAL PROTOCOL")
clock = pygame.time.Clock()

FONT = pygame.font.SysFont("consolas", 19)
SMALL = pygame.font.SysFont("consolas", 14)
MED = pygame.font.SysFont("consolas", 29, bold=True)
BIG = pygame.font.SysFont("consolas", 62, bold=True)

BG = (9, 14, 23)
WHITE = (235, 245, 255)
CYAN = (60, 225, 255)
RED = (255, 70, 85)
ORANGE = (255, 155, 65)
GREEN = (80, 245, 155)
YELLOW = (255, 220, 85)
PURPLE = (190, 105, 255)
MUTED = (115, 145, 165)

V = pygame.Vector2
SAVE_FILE = "outpost_zero_save.json"


def clamp(v, low, high):
    return max(low, min(v, high))


def draw_text(text, font, color, pos, center=False):
    image = font.render(str(text), True, color)
    rect = image.get_rect()
    if center:
        rect.center = (int(pos[0]), int(pos[1]))
    else:
        rect.topleft = (int(pos[0]), int(pos[1]))
    screen.blit(image, rect)


def draw_bar(x, y, w, h, value, maximum, color):
    pygame.draw.rect(screen, (25, 36, 49),
                     (int(x), int(y), int(w), int(h)), border_radius=4)
    ratio = clamp(value / max(1, maximum), 0, 1)
    if ratio:
        pygame.draw.rect(screen, color,
                         (int(x), int(y), int(w * ratio), int(h)),
                         border_radius=4)
    pygame.draw.rect(screen, (70, 94, 112),
                     (int(x), int(y), int(w), int(h)), 1, border_radius=4)


def rounded(surface, color, rect, radius=5, width=0):
    pygame.draw.rect(surface, color, rect, width, border_radius=radius)


# ---------------- SPRITE GENERATION ----------------

def make_player_sprite():
    s = pygame.Surface((64, 64), pygame.SRCALPHA)

    # Boots and legs
    rounded(s, (25, 39, 51), (17, 39, 13, 15), 4)
    rounded(s, (25, 39, 51), (34, 39, 13, 15), 4)
    rounded(s, (100, 140, 150), (16, 49, 15, 7), 2)
    rounded(s, (100, 140, 150), (33, 49, 15, 7), 2)

    # Backpack
    rounded(s, (29, 77, 92), (10, 22, 10, 22), 4)
    rounded(s, (29, 77, 92), (44, 22, 10, 22), 4)

    # Body armor
    pygame.draw.polygon(
        s, (38, 112, 135),
        [(18, 22), (25, 17), (39, 17), (46, 22),
         (43, 42), (21, 42)]
    )
    pygame.draw.polygon(
        s, (100, 210, 220),
        [(25, 23), (39, 23), (37, 36), (27, 36)]
    )
    pygame.draw.line(s, WHITE, (27, 26), (37, 26), 2)

    # Shoulder armor
    pygame.draw.circle(s, (145, 185, 198), (18, 25), 6)
    pygame.draw.circle(s, (145, 185, 198), (46, 25), 6)

    # Helmet and visor
    pygame.draw.circle(s, (30, 65, 82), (32, 14), 12)
    pygame.draw.circle(s, (90, 175, 195), (32, 14), 9)
    rounded(s, (8, 25, 38), (23, 11, 18, 7), 3)
    pygame.draw.line(s, CYAN, (25, 14), (39, 14), 2)
    pygame.draw.circle(s, WHITE, (32, 31), 3)

    return s


def make_enemy_sprite(kind):
    s = pygame.Surface((64, 64), pygame.SRCALPHA)

    if kind == "runner":
        pygame.draw.polygon(
            s, (100, 72, 25),
            [(32, 5), (47, 25), (40, 49), (32, 58),
             (24, 49), (17, 25)]
        )
        pygame.draw.polygon(
            s, YELLOW,
            [(32, 10), (42, 27), (36, 45), (28, 45), (22, 27)], 3
        )
        pygame.draw.line(s, YELLOW, (23, 29), (12, 43), 4)
        pygame.draw.line(s, YELLOW, (41, 29), (52, 43), 4)
        pygame.draw.circle(s, WHITE, (32, 25), 5)

    elif kind == "shooter":
        rounded(s, (60, 30, 80), (12, 13, 40, 40), 7)
        rounded(s, PURPLE, (12, 13, 40, 40), 7, 3)
        pygame.draw.circle(s, WHITE, (32, 29), 8)
        pygame.draw.circle(s, PURPLE, (32, 29), 4)
        rounded(s, (120, 75, 155), (26, 2, 12, 18), 3)
        rounded(s, (120, 75, 155), (26, 45, 12, 17), 3)
        rounded(s, (120, 75, 155), (2, 26, 17, 12), 3)
        rounded(s, (120, 75, 155), (45, 26, 17, 12), 3)

    elif kind == "boss":
        pygame.draw.polygon(
            s, (100, 25, 38),
            [(32, 3), (53, 14), (61, 33), (46, 56),
             (18, 56), (3, 33), (11, 14)]
        )
        pygame.draw.polygon(
            s, (210, 55, 72),
            [(32, 9), (47, 19), (52, 34), (40, 49),
             (24, 49), (12, 34), (17, 19)]
        )
        pygame.draw.circle(s, (255, 180, 180), (32, 29), 10)
        pygame.draw.circle(s, (70, 12, 25), (32, 29), 5)
        rounded(s, (135, 38, 55), (27, 0, 10, 20), 3)

    else:
        pygame.draw.polygon(
            s, (70, 25, 38),
            [(32, 4), (58, 32), (32, 60), (6, 32)]
        )
        pygame.draw.polygon(
            s, RED,
            [(32, 10), (50, 32), (32, 52), (14, 32)], 3
        )
        pygame.draw.circle(s, WHITE, (32, 32), 7)
        pygame.draw.line(s, ORANGE, (8, 12), (20, 22), 3)
        pygame.draw.line(s, ORANGE, (56, 12), (44, 22), 3)

    return s


PLAYER_SPRITE = make_player_sprite()
ENEMY_SPRITES = {
    "drone": make_enemy_sprite("drone"),
    "runner": make_enemy_sprite("runner"),
    "shooter": make_enemy_sprite("shooter"),
    "boss": make_enemy_sprite("boss"),
}


# ---------------- EFFECTS ----------------

class Particle:
    def __init__(self, pos, color, speed=180, life=0.4, radius=3):
        self.pos = V(pos)
        angle = random.random() * math.tau
        velocity = random.uniform(speed * 0.2, speed)
        self.vel = V(math.cos(angle), math.sin(angle)) * velocity
        self.color = color
        self.life = self.max_life = life * random.uniform(0.7, 1.3)
        self.radius = radius
        self.drag = random.uniform(2.0, 4.0)

    def update(self, dt):
        self.pos += self.vel * dt
        self.vel *= max(0, 1 - self.drag * dt)
        self.life -= dt

    def draw(self, cam):
        if self.life <= 0:
            return
        p = self.pos - cam
        r = max(1, int(self.radius * self.life / self.max_life))
        pygame.draw.circle(screen, self.color, (int(p.x), int(p.y)), r)


class FloatingText:
    def __init__(self, pos, value, color):
        self.pos = V(pos)
        self.value = str(value)
        self.color = color
        self.life = 0.7

    def update(self, dt):
        self.pos.y -= 38 * dt
        self.life -= dt

    def draw(self, cam):
        if self.life <= 0:
            return
        p = self.pos - cam
        image = SMALL.render(self.value, True, self.color)
        image.set_alpha(int(255 * clamp(self.life / 0.7, 0, 1)))
        screen.blit(image, image.get_rect(center=(int(p.x), int(p.y))))


class Casing:
    def __init__(self, pos, direction):
        self.pos = V(pos)
        self.vel = V(-direction.y, direction.x) * random.randint(80, 170)
        self.vel.y -= random.randint(20, 90)
        self.life = 0.9

    def update(self, dt):
        self.pos += self.vel * dt
        self.vel.y += 230 * dt
        self.vel *= max(0, 1 - 1.6 * dt)
        self.life -= dt

    def draw(self, cam):
        p = self.pos - cam
        color = (205, 160, 75) if self.life > 0.25 else (100, 85, 60)
        pygame.draw.line(screen, color, (int(p.x - 3), int(p.y)),
                         (int(p.x + 3), int(p.y)), 3)


# ---------------- PROJECTILES ----------------

class Bullet:
    def __init__(self, pos, direction, friendly, damage,
                 speed=None, color=None, radius=4, pierce=0):
        self.pos = V(pos)
        self.direction = V(direction)

        if self.direction.length_squared() == 0:
            self.direction = V(1, 0)

        self.direction = self.direction.normalize()
        self.speed = speed or (850 if friendly else 370)
        self.vel = self.direction * self.speed
        self.friendly = friendly
        self.damage = damage
        self.color = color or (CYAN if friendly else RED)
        self.radius = radius
        self.life = 1.6
        self.pierce = pierce
        self.hit = set()

    def update(self, dt, obstacles):
        self.pos += self.vel * dt
        self.life -= dt

        if not (0 <= self.pos.x <= WORLD_W and
                0 <= self.pos.y <= WORLD_H):
            self.life = 0

        for r in obstacles:
            if r.collidepoint(self.pos.x, self.pos.y):
                self.life = 0
                break

    def draw(self, cam):
        p = self.pos - cam
        tail = p - self.direction * 17
        pygame.draw.line(screen, self.color, tail, p, 3)
        pygame.draw.circle(screen, WHITE, (int(p.x), int(p.y)), 2)


# ---------------- PLAYER ----------------

class Player:
    def __init__(self):
        self.pos = V(WORLD_W / 2, WORLD_H / 2)
        self.radius = 17
        self.speed = 245

        self.max_hp = 100
        self.hp = 100

        self.weapons = [
            {"name": "ASSAULT RIFLE", "damage": 24, "delay": 0.13,
             "pellets": 1, "spread": 2.5, "reload": 1.1, "mag": 18,
             "color": CYAN, "ammo": 18, "reserve": 90},
            {"name": "SCATTERGUN", "damage": 14, "delay": 0.48,
             "pellets": 6, "spread": 18, "reload": 1.45, "mag": 8,
             "color": ORANGE, "ammo": 8, "reserve": 40},
            {"name": "RAIL PISTOL", "damage": 58, "delay": 0.52,
             "pellets": 1, "spread": 0.5, "reload": 1.3, "mag": 7,
             "color": PURPLE, "ammo": 7, "reserve": 35},
        ]

        self.weapon = 0
        self.ammo = self.gun["mag"]
        self.reserve = 150
        self.fire_timer = 0
        self.reload_timer = 0
        self.reloading = False

        self.invulnerable = 0
        self.dash_cd = 0
        self.dash_time = 0
        self.dash_dir = V(1, 0)

        self.level = 1
        self.xp = 0
        self.next_xp = 100
        self.damage_bonus = 0
        self.speed_bonus = 0
        self.crit = 0.08
        self.lifesteal = 0

        self.kills = 0
        self.score = 0
        self.combo = 0
        self.combo_timer = 0

    @property
    def gun(self):
        return self.weapons[self.weapon]

    @property
    def ammo(self):
        return self.gun["ammo"]

    @ammo.setter
    def ammo(self, value):
        self.gun["ammo"] = max(0, int(value))

    @property
    def reserve(self):
        return self.gun["reserve"]

    @reserve.setter
    def reserve(self, value):
        self.gun["reserve"] = max(0, int(value))

    def change_weapon(self, index):
        if index == self.weapon or not 0 <= index < len(self.weapons):
            return
        self.weapon = index
        self.reloading = False
        self.reload_timer = 0
        play_sound("pickup")

    def reload(self):
        if (not self.reloading and self.ammo < self.gun["mag"]
                and self.reserve > 0):
            self.reloading = True
            self.reload_timer = self.gun["reload"]
            play_sound("reload")

    def update(self, dt, keys, obstacles):
        self.fire_timer = max(0, self.fire_timer - dt)
        self.invulnerable = max(0, self.invulnerable - dt)
        self.dash_cd = max(0, self.dash_cd - dt)
        self.combo_timer -= dt

        if self.combo_timer <= 0:
            self.combo = 0

        if self.reloading:
            self.reload_timer -= dt
            if self.reload_timer <= 0:
                amount = min(self.gun["mag"] - self.ammo, self.reserve)
                self.ammo += amount
                self.reserve -= amount
                self.reloading = False

        move = V(
            int(keys[pygame.K_d] or keys[pygame.K_RIGHT])
            - int(keys[pygame.K_a] or keys[pygame.K_LEFT]),
            int(keys[pygame.K_s] or keys[pygame.K_DOWN])
            - int(keys[pygame.K_w] or keys[pygame.K_UP])
        )

        if move.length_squared():
            move = move.normalize()

        speed = self.speed + self.speed_bonus
        velocity = self.dash_dir * 900 if self.dash_time > 0 else move * speed
        self.dash_time = max(0, self.dash_time - dt)

        self.pos.x += velocity.x * dt

        for r in obstacles:
            nx = clamp(self.pos.x, r.left, r.right)
            ny = clamp(self.pos.y, r.top, r.bottom)
            if (self.pos.x - nx) ** 2 + (self.pos.y - ny) ** 2 < self.radius ** 2:
                self.pos.x = r.left - self.radius if velocity.x > 0 else r.right + self.radius

        self.pos.y += velocity.y * dt
        for r in obstacles:
            nx = clamp(self.pos.x, r.left, r.right)
            ny = clamp(self.pos.y, r.top, r.bottom)
            if (self.pos.x - nx) ** 2 + (self.pos.y - ny) ** 2 < self.radius ** 2:
                self.pos.y = r.top - self.radius if velocity.y > 0 else r.bottom + self.radius

        self.pos.x = clamp(self.pos.x, self.radius, WORLD_W - self.radius)
        self.pos.y = clamp(self.pos.y, self.radius, WORLD_H - self.radius)

    def shoot(self, target, bullets, particles, casings):
        if self.reloading or self.fire_timer > 0:
            return

        if self.ammo <= 0:
            self.reload()
            return

        direction = V(target) - self.pos
        if direction.length_squared() == 0:
            return
        direction = direction.normalize()

        gun = self.gun
        self.fire_timer = gun["delay"]
        self.ammo -= 1
        play_sound(("rifle", "shotgun", "rail")[self.weapon])

        muzzle = self.pos + direction * 30

        for _ in range(gun["pellets"]):
            angle = math.radians(random.uniform(-gun["spread"], gun["spread"]))
            d = direction.rotate_rad(angle)
            bullets.append(Bullet(
                muzzle, d, True, gun["damage"] + self.damage_bonus,
                color=gun["color"], pierce=1 if self.weapon == 2 else 0
            ))

        for _ in range(9 if self.weapon == 1 else 5):
            particles.append(Particle(
                muzzle, random.choice([gun["color"], WHITE, YELLOW]),
                180, 0.22, 3
            ))

        casings.append(Casing(self.pos, direction))

    def dash(self, keys, target):
        if self.dash_cd > 0:
            return

        move = V(
            int(keys[pygame.K_d] or keys[pygame.K_RIGHT])
            - int(keys[pygame.K_a] or keys[pygame.K_LEFT]),
            int(keys[pygame.K_s] or keys[pygame.K_DOWN])
            - int(keys[pygame.K_w] or keys[pygame.K_UP])
        )

        if move.length_squared():
            self.dash_dir = move.normalize()
        else:
            direction = V(target) - self.pos
            self.dash_dir = direction.normalize() if direction.length_squared() else V(1, 0)

        self.dash_time = 0.15
        self.dash_cd = 1.5
        self.invulnerable = 0.28
        play_sound("dash")

    def draw(self, cam, mouse_world):
        p = self.pos - cam
        direction = V(mouse_world) - self.pos

        if not direction.length_squared():
            direction = V(1, 0)
        direction = direction.normalize()

        # Weapon barrel
        start = p + direction * 7
        end = p + direction * 31
        pygame.draw.line(screen, (25, 39, 51), start, end, 10)
        pygame.draw.line(screen, self.gun["color"], start, end, 5)

        angle = -math.degrees(math.atan2(direction.y, direction.x)) - 90
        image = pygame.transform.rotate(PLAYER_SPRITE, angle)

        if self.invulnerable > 0 and int(self.invulnerable * 40) % 2 == 0:
            image.set_alpha(120)

        screen.blit(image, image.get_rect(center=(int(p.x), int(p.y))))
        pygame.draw.circle(screen, CYAN, (int(p.x), int(p.y)), 23, 1)


# ---------------- ENEMIES ----------------

class Enemy:
    def __init__(self, pos, kind, wave, boss=False):
        self.pos = V(pos)
        self.kind = "boss" if boss else kind
        self.boss = boss
        self.alive = True
        self.flash = 0
        self.attack_timer = random.uniform(0.5, 1.4)
        self.phase = random.random() * math.tau
        self.uid = random.random()

        if self.kind == "runner":
            self.max_hp = 42 + wave * 4
            self.speed = 180 + min(wave * 2, 40)
            self.radius = 14
            self.damage = 12
            self.value = 100
        elif self.kind == "shooter":
            self.max_hp = 75 + wave * 6
            self.speed = 75
            self.radius = 18
            self.damage = 10
            self.value = 175
        elif self.kind == "boss":
            self.max_hp = 650 + wave * 65
            self.speed = 68
            self.radius = 30
            self.damage = 24
            self.value = 1500
        else:
            self.max_hp = 100 + wave * 7
            self.speed = 105 + min(wave, 20)
            self.radius = 19
            self.damage = 15
            self.value = 150

        self.hp = self.max_hp

    def update(self, dt, player, bullets):
        self.flash = max(0, self.flash - dt)
        self.phase += dt * 5

        delta = player.pos - self.pos
        distance = delta.length()
        direction = delta.normalize() if distance else V(1, 0)

        if self.kind == "shooter":
            if distance > 340:
                self.pos += direction * self.speed * dt
            elif distance < 220:
                self.pos -= direction * self.speed * 0.75 * dt

            self.attack_timer -= dt
            if self.attack_timer <= 0 and distance < 680:
                bullets.append(Bullet(
                    self.pos, direction, False, self.damage,
                    speed=370, color=RED
                ))
                play_sound("enemy")

                if self.boss:
                    for angle in (-22, 0, 22):
                        bullets.append(Bullet(
                            self.pos, direction.rotate(angle), False, 13,
                            speed=340, color=ORANGE
                        ))

                self.attack_timer = 1.5 if not self.boss else 0.75

        else:
            self.pos += direction * self.speed * dt * (
                1 + 0.05 * math.sin(self.phase)
            )

        self.pos.x = clamp(self.pos.x, self.radius, WORLD_W - self.radius)
        self.pos.y = clamp(self.pos.y, self.radius, WORLD_H - self.radius)

    def draw(self, cam, player_pos):
        p = self.pos - cam
        direction = player_pos - self.pos
        angle = -math.degrees(math.atan2(direction.y, direction.x)) - 90

        image = pygame.transform.rotate(ENEMY_SPRITES[self.kind], angle)
        size = int(self.radius * 2.65)
        image = pygame.transform.scale(image, (size, size))

        if self.flash > 0:
            image = image.copy()
            image.fill((130, 130, 130, 0), special_flags=pygame.BLEND_RGBA_ADD)

        screen.blit(image, image.get_rect(center=(int(p.x), int(p.y))))

        if self.hp < self.max_hp or self.boss:
            w = self.radius * 2 + (45 if self.boss else 0)
            draw_bar(p.x - w / 2, p.y - self.radius - 13,
                     w, 5, self.hp, self.max_hp, RED)

        if self.boss:
            draw_text("ELITE", SMALL, RED, (p.x, p.y - self.radius - 33), True)


class Pickup:
    def __init__(self, pos, kind):
        self.pos = V(pos)
        self.kind = kind
        self.time = random.random() * 5

    def update(self, dt):
        self.time += dt

    def draw(self, cam):
        p = self.pos - cam
        y = p.y + math.sin(self.time * 4) * 3
        color = GREEN if self.kind == "med" else CYAN if self.kind == "ammo" else YELLOW

        pygame.draw.circle(screen, color, (int(p.x), int(y)), 16, 1)
        pygame.draw.circle(screen, (20, 38, 48), (int(p.x), int(y)), 11)

        if self.kind == "med":
            pygame.draw.rect(screen, GREEN, (p.x - 3, y - 7, 6, 14))
            pygame.draw.rect(screen, GREEN, (p.x - 7, y - 3, 14, 6))
        elif self.kind == "ammo":
            pygame.draw.rect(screen, CYAN, (p.x - 5, y - 7, 10, 14))
            pygame.draw.line(screen, WHITE, (p.x, y - 4), (p.x, y + 4), 2)
        else:
            pygame.draw.polygon(screen, YELLOW, [
                (p.x, y - 8), (p.x + 7, y), (p.x, y + 8), (p.x - 7, y)
            ])


# ---------------- GAME ----------------

class Game:
    def __init__(self):
        self.best = self.load_best()
        self.reset()
        self.state = "menu"

    def load_best(self):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                return int(json.load(f).get("best", 0))
        except (OSError, ValueError, TypeError):
            return 0

    def save_best(self):
        try:
            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump({"best": self.best}, f)
        except OSError:
            pass

    def reset(self):
        self.player = Player()
        self.bullets = []
        self.enemies = []
        self.particles = []
        self.casings = []
        self.pickups = []
        self.floaters = []
        self.wave = 0
        self.wave_wait = 1.4
        self.pickup_spawn_timer = 2.0
        self.shake = 0
        self.message_text = ""
        self.message_timer = 0
        self.upgrades = []
        self.obstacles = []
        self.decor = []

        rng = random.Random(42)

        for _ in range(45):
            w = rng.choice([55, 75, 95, 120])
            h = rng.choice([45, 65, 85, 100])
            r = pygame.Rect(
                rng.randint(70, WORLD_W - w - 70),
                rng.randint(70, WORLD_H - h - 70), w, h
            )

            if r.inflate(120, 120).collidepoint(self.player.pos):
                continue

            if r.colliderect(pygame.Rect(
                WORLD_W / 2 - 150, WORLD_H / 2 - 150, 300, 300
            )):
                continue

            self.obstacles.append(r)

        for _ in range(260):
            self.decor.append((
                rng.randint(0, WORLD_W),
                rng.randint(0, WORLD_H),
                rng.choice([1, 2, 3])
            ))

        self.state = "playing"

    def notify(self, message):
        self.message_text = message
        self.message_timer = 2.0

    def spawn_enemy(self, boss=False):
        for _ in range(80):
            side = random.randrange(4)

            if side == 0:
                pos = V(random.randint(50, WORLD_W - 50), 45)
            elif side == 1:
                pos = V(random.randint(50, WORLD_W - 50), WORLD_H - 45)
            elif side == 2:
                pos = V(45, random.randint(50, WORLD_H - 50))
            else:
                pos = V(WORLD_W - 45, random.randint(50, WORLD_H - 50))

            if pos.distance_to(self.player.pos) < 420:
                continue

            if any(r.inflate(25, 25).collidepoint(pos.x, pos.y)
                   for r in self.obstacles):
                continue

            if boss:
                kind = "boss"
            else:
                roll = random.random()
                if self.wave >= 3 and roll < 0.24:
                    kind = "shooter"
                elif self.wave >= 2 and roll < 0.56:
                    kind = "runner"
                else:
                    kind = "drone"

            self.enemies.append(Enemy(pos, kind, self.wave, boss))
            return

    def spawn_pickup(self, kind=None):
        # Pickups can appear anywhere on the map, not only near the player.
        if len(self.pickups) >= 24:
            return
        if kind is None:
            kind = random.choices(
                ["med", "ammo", "data"], weights=[35, 50, 15], k=1
            )[0]
        for _ in range(100):
            pos = V(random.randint(45, WORLD_W - 45),
                    random.randint(45, WORLD_H - 45))
            if pos.distance_to(self.player.pos) < 75:
                continue
            if any(r.inflate(35, 35).collidepoint(pos.x, pos.y)
                   for r in self.obstacles):
                continue
            self.pickups.append(Pickup(pos, kind))
            return

    def start_wave(self):
        self.wave += 1
        boss = self.wave % 5 == 0

        for _ in range(min(4 + self.wave * 2, 26)):
            self.spawn_enemy()

        if boss:
            self.spawn_enemy(True)
            self.notify(f"WAVE {self.wave} // ELITE DETECTED")
        else:
            self.notify(f"WAVE {self.wave} // HOSTILES INBOUND")

    def explosion(self, pos, color, count=18):
        for _ in range(count):
            self.particles.append(Particle(
                pos, random.choice([color, WHITE, ORANGE]),
                random.randint(100, 300), random.uniform(0.25, 0.65),
                random.randint(2, 5)
            ))
        self.shake = max(self.shake, 5)

    def kill_enemy(self, enemy):
        enemy.alive = False
        p = self.player

        p.kills += 1
        p.combo += 1
        p.combo_timer = 3
        multiplier = min(5, 1 + p.combo // 5)
        gained = enemy.value * self.wave * multiplier
        p.score += gained

        self.floaters.append(FloatingText(enemy.pos, f"+{gained}", YELLOW))
        self.explosion(
            enemy.pos, RED if enemy.kind in ("drone", "boss") else
            PURPLE if enemy.kind == "shooter" else YELLOW,
            38 if enemy.boss else 15
        )

        p.xp += 30 if enemy.boss else 12

        if random.random() < (0.95 if enemy.boss else 0.38):
            self.pickups.append(Pickup(
                enemy.pos, random.choice(["med", "ammo", "data"])
            ))

        if p.xp >= p.next_xp:
            p.xp -= p.next_xp
            p.level += 1
            p.next_xp = int(p.next_xp * 1.35)

            all_upgrades = [
                ("damage", "HIGH CALIBER", "+8 weapon damage"),
                ("health", "REINFORCED ARMOR", "+25 max HP and heal"),
                ("speed", "OVERDRIVE", "+22 movement speed"),
                ("crit", "TARGETING AI", "+8% critical chance"),
                ("mag", "EXTENDED MAG", "+5 magazine capacity"),
                ("vamp", "NANITE LEECH", "Heal 4 HP per kill"),
            ]

            self.upgrades = random.sample(all_upgrades, 3)
            self.state = "levelup"
            play_sound("level")

    def choose_upgrade(self, index):
        p = self.player
        kind = self.upgrades[index][0]

        if kind == "damage":
            p.damage_bonus += 8
        elif kind == "health":
            p.max_hp += 25
            p.hp = min(p.max_hp, p.hp + 40)
        elif kind == "speed":
            p.speed_bonus += 22
        elif kind == "crit":
            p.crit = min(0.55, p.crit + 0.08)
        elif kind == "mag":
            for gun in p.weapons:
                gun["mag"] += 5
                gun["ammo"] = min(gun["mag"], gun["ammo"] + 5)
        elif kind == "vamp":
            p.lifesteal += 4

        self.state = "playing"
        self.notify("UPGRADE INSTALLED")

    def camera(self):
        return V(
            clamp(self.player.pos.x - WIDTH / 2, 0, WORLD_W - WIDTH),
            clamp(self.player.pos.y - HEIGHT / 2, 0, WORLD_H - HEIGHT)
        )

    def update(self, dt):
        if self.state != "playing":
            return

        self.shake = max(0, self.shake - 22 * dt)
        self.message_timer = max(0, self.message_timer - dt)

        p = self.player
        keys = pygame.key.get_pressed()
        cam = self.camera()
        mouse_world = V(pygame.mouse.get_pos()) + cam

        p.update(dt, keys, self.obstacles)

        self.pickup_spawn_timer -= dt
        if self.pickup_spawn_timer <= 0:
            # Frequent supplies across the whole world.
            self.spawn_pickup()
            if random.random() < 0.38:
                self.spawn_pickup(random.choice(["med", "ammo"]))
            self.pickup_spawn_timer = random.uniform(3.0, 5.5)

        if pygame.mouse.get_pressed()[0]:
            p.shoot(mouse_world, self.bullets, self.particles, self.casings)

        # Projectile collisions
        for bullet in self.bullets:
            bullet.update(dt, self.obstacles)

            if bullet.life <= 0:
                continue

            if bullet.friendly:
                for enemy in self.enemies:
                    if not enemy.alive or enemy.uid in bullet.hit:
                        continue

                    if bullet.pos.distance_to(enemy.pos) < enemy.radius + bullet.radius:
                        critical = random.random() < p.crit
                        damage = bullet.damage * (2 if critical else 1)
                        enemy.hp -= damage
                        enemy.flash = 0.1
                        bullet.hit.add(enemy.uid)

                        self.floaters.append(FloatingText(
                            enemy.pos, f"{int(damage)}{'!' if critical else ''}",
                            YELLOW if critical else WHITE
                        ))

                        for _ in range(5):
                            self.particles.append(Particle(
                                bullet.pos, random.choice([RED, WHITE, ORANGE]),
                                140, 0.3, 3
                            ))

                        if p.lifesteal:
                            p.hp = min(p.max_hp, p.hp + p.lifesteal)

                        if enemy.hp <= 0:
                            self.kill_enemy(enemy)

                        if bullet.pierce <= 0:
                            bullet.life = 0
                            break

                        bullet.pierce -= 1

            elif (p.invulnerable <= 0 and
                  bullet.pos.distance_to(p.pos) < p.radius + bullet.radius):
                p.hp -= bullet.damage
                play_sound("hit")
                p.invulnerable = 0.45
                bullet.life = 0
                self.shake = 8
                self.explosion(p.pos, RED, 10)

        self.bullets = [b for b in self.bullets if b.life > 0]

        # Enemies and contact damage
        for enemy in self.enemies:
            enemy.update(dt, p, self.bullets)

            if not enemy.alive:
                continue

            if enemy.pos.distance_to(p.pos) < enemy.radius + p.radius:
                if p.invulnerable <= 0:
                    p.hp -= enemy.damage
                    play_sound("hit")
                    p.invulnerable = 0.6
                    self.shake = 8

                    d = p.pos - enemy.pos
                    if d.length_squared():
                        p.pos += d.normalize() * 20

                    self.explosion(p.pos, RED, 10)

        self.enemies = [e for e in self.enemies if e.alive]

        # Pickups
        for pickup in self.pickups:
            pickup.update(dt)

            if pickup.pos.distance_to(p.pos) < 32:
                if pickup.kind == "med":
                    if p.hp >= p.max_hp:
                        continue
                    p.hp = min(p.max_hp, p.hp + 35)
                    self.notify("MEDKIT +35 HP")

                elif pickup.kind == "ammo":
                    p.reserve += 35
                    self.notify("AMMO +35")

                else:
                    p.score += 250
                    self.notify("DATA CORE +250")

                play_sound("pickup")
                pickup.time = -1000

        self.pickups = [x for x in self.pickups if x.time > -100]

        for collection in (self.particles, self.casings, self.floaters):
            for item in collection:
                item.update(dt)

        self.particles = [x for x in self.particles if x.life > 0]
        self.casings = [x for x in self.casings if x.life > 0]
        self.floaters = [x for x in self.floaters if x.life > 0]

        if p.hp <= 0:
            p.hp = 0
            self.best = max(self.best, p.score)
            self.save_best()
            self.state = "gameover"
            play_sound("death")
            return

        if not self.enemies:
            self.wave_wait -= dt
            if self.wave_wait <= 0:
                self.start_wave()
                self.wave_wait = 2.5

    def draw_world(self):
        cam = self.camera()
        shake = V(
            random.uniform(-self.shake, self.shake),
            random.uniform(-self.shake, self.shake)
        ) if self.shake > 0.2 else V()

        screen.fill(BG)

        # Industrial floor grid
        gx, gy = -int(cam.x) % 60, -int(cam.y) % 60

        for x in range(gx, WIDTH, 60):
            pygame.draw.line(screen, (17, 28, 42), (x, 0), (x, HEIGHT))

        for y in range(gy, HEIGHT, 60):
            pygame.draw.line(screen, (17, 28, 42), (0, y), (WIDTH, y))

        # Ground debris
        for x, y, radius in self.decor:
            sx = int(x - cam.x + shake.x)
            sy = int(y - cam.y + shake.y)

            if -5 < sx < WIDTH + 5 and -5 < sy < HEIGHT + 5:
                pygame.draw.circle(
                    screen, (32, 45, 58), (sx, sy), radius
                )

        # Cover crates
        for r in self.obstacles:
            rr = pygame.Rect(
                int(r.x - cam.x + shake.x),
                int(r.y - cam.y + shake.y), r.w, r.h
            )

            if not screen.get_rect().colliderect(rr):
                continue

            rounded(screen, (25, 39, 53), rr, 5)
            rounded(screen, (75, 102, 119), rr, 5, 2)
            pygame.draw.line(
                screen, (43, 68, 82),
                (rr.left + 7, rr.top + 8),
                (rr.right - 7, rr.top + 8), 2
            )
            pygame.draw.rect(
                screen, (45, 67, 82),
                (rr.left + 7, rr.top + 15, max(1, rr.w - 14), 4)
            )

        for casing in self.casings:
            casing.draw(cam - shake)

        for pickup in self.pickups:
            pickup.draw(cam - shake)

        for bullet in self.bullets:
            bullet.draw(cam - shake)

        for enemy in self.enemies:
            enemy.draw(cam - shake, self.player.pos)

        for particle in self.particles:
            particle.draw(cam - shake)

        for floater in self.floaters:
            floater.draw(cam - shake)

        mouse_world = V(pygame.mouse.get_pos()) + cam
        self.player.draw(cam - shake, mouse_world)

    def draw_hud(self):
        p = self.player

        rounded(screen, (7, 15, 25), (16, 16, 325, 126), 8)
        rounded(screen, (45, 89, 111), (16, 16, 325, 126), 8, 1)

        draw_text("OUTPOST ZERO", MED, CYAN, (28, 22))
        draw_text(f"WAVE {self.wave:02d}", FONT, WHITE, (28, 58))
        draw_text(f"KILLS {p.kills}", SMALL, MUTED, (28, 89))
        draw_text(f"SCORE {p.score}", SMALL, YELLOW, (125, 89))
        draw_text(f"LVL {p.level}", SMALL, PURPLE, (245, 89))
        draw_bar(28, 116, 295, 8, p.xp, p.next_xp, PURPLE)

        draw_text("VITALS", SMALL, WHITE, (WIDTH - 285, 18))
        draw_bar(
            WIDTH - 285, 40, 255, 15,
            p.hp, p.max_hp, GREEN if p.hp > 30 else RED
        )
        draw_text(
            f"{int(p.hp)} / {p.max_hp} HP",
            SMALL, WHITE, (WIDTH - 285, 60)
        )

        rounded(
            screen, (7, 15, 25),
            (WIDTH - 285, HEIGHT - 111, 260, 89), 8
        )
        rounded(
            screen, (45, 89, 111),
            (WIDTH - 285, HEIGHT - 111, 260, 89), 8, 1
        )

        draw_text(
            p.gun["name"], SMALL, p.gun["color"],
            (WIDTH - 270, HEIGHT - 101)
        )
        draw_text(
            f"{p.ammo:02d} / {p.reserve:03d}",
            MED, p.gun["color"], (WIDTH - 270, HEIGHT - 79)
        )

        if p.reloading:
            draw_text(
                "RELOADING", SMALL, YELLOW,
                (WIDTH - 270, HEIGHT - 48)
            )
            progress = p.gun["reload"] - p.reload_timer
            draw_bar(
                WIDTH - 165, HEIGHT - 44, 120, 7,
                progress, p.gun["reload"], YELLOW
            )

        dash = "READY" if p.dash_cd <= 0 else f"{p.dash_cd:.1f}s"
        draw_text(
            f"SHIFT DASH: {dash}", SMALL,
            CYAN if p.dash_cd <= 0 else MUTED,
            (22, HEIGHT - 30)
        )

        if p.combo >= 3:
            draw_text(
                f"{p.combo}x COMBO", MED, YELLOW,
                (WIDTH // 2, 28), True
            )

        # Minimap
        mw, mh = 150, 110
        mx, my = WIDTH - mw - 20, 98

        pygame.draw.rect(screen, (7, 15, 25), (mx, my, mw, mh))
        pygame.draw.rect(screen, (48, 85, 104), (mx, my, mw, mh), 1)

        for enemy in self.enemies:
            ex = int(mx + enemy.pos.x / WORLD_W * mw)
            ey = int(my + enemy.pos.y / WORLD_H * mh)
            pygame.draw.circle(
                screen, ORANGE if enemy.boss else RED,
                (ex, ey), 3 if enemy.boss else 2
            )

        px = int(mx + p.pos.x / WORLD_W * mw)
        py = int(my + p.pos.y / WORLD_H * mh)
        pygame.draw.circle(screen, CYAN, (px, py), 4)

        # Crosshair
        mx, my = pygame.mouse.get_pos()
        pygame.draw.circle(screen, CYAN, (mx, my), 9, 1)
        pygame.draw.line(screen, CYAN, (mx - 14, my), (mx - 5, my), 1)
        pygame.draw.line(screen, CYAN, (mx + 5, my), (mx + 14, my), 1)
        pygame.draw.line(screen, CYAN, (mx, my - 14), (mx, my - 5), 1)
        pygame.draw.line(screen, CYAN, (mx, my + 5), (mx, my + 14), 1)

        if self.message_timer > 0:
            panel = pygame.Surface((600, 42), pygame.SRCALPHA)
            panel.fill((5, 17, 29, 220))
            screen.blit(panel, (WIDTH // 2 - 300, 68))
            draw_text(
                self.message_text, FONT, CYAN,
                (WIDTH // 2, 89), True
            )

        draw_text(
            "WASD MOVE | LMB FIRE | R RELOAD | SHIFT DASH | P PAUSE",
            SMALL, (100, 125, 145), (WIDTH // 2, HEIGHT - 10), True
        )

    def overlay(self, title, subtitle, lines):
        shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        shade.fill((2, 6, 13, 218))
        screen.blit(shade, (0, 0))

        draw_text("OUTPOST", BIG, CYAN, (WIDTH // 2, HEIGHT // 2 - 190), True)
        draw_text("ZERO", BIG, WHITE, (WIDTH // 2, HEIGHT // 2 - 125), True)

        pygame.draw.line(
            screen, CYAN,
            (WIDTH // 2 - 175, HEIGHT // 2 - 82),
            (WIDTH // 2 + 175, HEIGHT // 2 - 82), 2
        )

        draw_text(title, MED, WHITE, (WIDTH // 2, HEIGHT // 2 - 48), True)
        draw_text(subtitle, SMALL, MUTED, (WIDTH // 2, HEIGHT // 2 - 14), True)

        for i, line in enumerate(lines):
            draw_text(
                line, FONT, CYAN if i == 0 else WHITE,
                (WIDTH // 2, HEIGHT // 2 + 42 + i * 35), True
            )

    def draw(self):
        self.draw_world()
        self.draw_hud()

        if self.state == "menu":
            self.overlay("SURVIVAL PROTOCOL", f"BEST SCORE: {self.best}", [
                "ENTER — START MISSION",
                "WASD MOVE | MOUSE AIM | LMB FIRE",
                "R RELOAD | SHIFT DASH | 1 / 2 / 3 WEAPONS",
                "P / ESC PAUSE | BOSS EVERY FIFTH WAVE",
            ])

        elif self.state == "paused":
            self.overlay("MISSION PAUSED", "Combat suspended", [
                "P / ESC — RESUME",
                "ENTER — RESTART",
                "Q — QUIT",
            ])

        elif self.state == "gameover":
            self.overlay("SIGNAL LOST",
                         f"SCORE {self.player.score} // WAVE {self.wave} // BEST {self.best}", [
                "ENTER — TRY AGAIN",
                "Q — QUIT",
            ])

        elif self.state == "levelup":
            self.overlay("LEVEL UP", "Choose upgrade with 1, 2 or 3", [
                f"1 — {self.upgrades[0][1]}: {self.upgrades[0][2]}",
                f"2 — {self.upgrades[1][1]}: {self.upgrades[1][2]}",
                f"3 — {self.upgrades[2][1]}: {self.upgrades[2][2]}",
            ])

        pygame.display.flip()

    def run(self):
        while True:
            dt = min(clock.tick(FPS) / 1000, 0.033)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.best = max(self.best, self.player.score)
                    self.save_best()
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        self.save_best()
                        pygame.quit()
                        sys.exit()

                    if self.state == "menu":
                        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            self.reset()

                    elif self.state == "playing":
                        if event.key in (pygame.K_ESCAPE, pygame.K_p):
                            self.state = "paused"

                        elif event.key == pygame.K_r:
                            self.player.reload()

                        elif event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                            target = V(pygame.mouse.get_pos()) + self.camera()
                            self.player.dash(pygame.key.get_pressed(), target)

                        elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                            index = event.key - pygame.K_1
                            self.player.change_weapon(index)

                    elif self.state == "paused":
                        if event.key in (pygame.K_ESCAPE, pygame.K_p):
                            self.state = "playing"
                        elif event.key == pygame.K_RETURN:
                            self.reset()

                    elif self.state == "gameover":
                        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            self.reset()

                    elif self.state == "levelup":
                        if event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                            self.choose_upgrade(event.key - pygame.K_1)

            self.update(dt)
            self.draw()


if __name__ == "__main__":
    Game().run()