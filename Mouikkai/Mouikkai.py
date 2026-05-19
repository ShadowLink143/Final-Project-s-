import pygame, random, math
import math
import json
import os
#for now, z is jump, x is run, and shift is dash. to wall jump, be in air, press the other direction, and jump. 
#and for joystick, A/B is jump, X/Y is run, and shoulder buttons are dash


pygame.display.init()
# some lists and stuff
joysticks = []
npcs = []
hazards = []

# Constants
WIDTH, HEIGHT = 1200, 800
SCALE = 3
TILE_SIZE = 16 * SCALE
GRAVITY = 0.6
WALK_SPEED = 5
RUN_SPEED = 8  
JUMP_FORCE = -16
RUN_JUMP_FORCE = -18
DASH_SPEED = 18
DASH_TIME = 15  
DASH_COOLDOWN = 20

DEBUG_LEVEL_2 = False
DEBUG_ENABLED = True  # debug warping 
DEBUG_SHIP_SPAWN = False
canSkip = True

active_dialogue=None
boss_triggered = False
boss2_triggered = False
boss2_first_time = True
boss2_finished = False
boss_finished = False
boss_manager = None  
kira_boss_manager = None
boss_state = None  # Can be "INTRO", "FIGHTING", "DAZED", "BONKED"
boss_first_entry = True  
dialogue_start_timer = 0
#animation. music. broken.

has_not_dropped_floor = True
# Level state
current_level = None
active_neon_color = 'green'
neon_images = {}
neon_toggle_timer = 0  # Timer for delaying neon color toggle after jump
 
ship = None
shadow = None
moon_spike_images = None

# Level 2 boss defeat transition
sheet_spawned = False
sheet_x = 0
sheet_y = 0
sheet_img = None
sheet_visible = False
violin_timer = 0
transition_fading = False
transition_fade_alpha = 0
transition_fade_in = False
memory_started = False
transition_started = False
boss2_defeated = False
final_intro_dialogue_not_started=True
Melody2 = None


ship_scene_state = None  
melody3_img = None
the_melody_img = None
melody3_alpha = 0
the_melody_alpha = 0
melody_glow_alpha = 0
performing_img = None
performing_alpha = 0
performing_timer = 0
performing_sound_started = False
door_img = None
door_alpha = 0
door_fade_out = False

ship_image = None
ship_to_final_transition = False
flash_lights_active = False
flash_lights_timer = 0
flash_lights_intensity = 0
ships_stars_moving = False

font = None
# Final level variables
final_level_frame_count = 0
floating_dialogue = None
final_level_autoscroll = False
FINAL_LEVEL_AUTOSCROLL_SPEED = 18  # Pixels per frame to scroll right (increased for faster pacing)
final_level_autoscroll_speed = FINAL_LEVEL_AUTOSCROLL_SPEED
FINAL_LEVEL_FPS = 60
FINAL_LEVEL_AUTOSCROLL_START_FRAME = 90  # Frames of intro before music and world movement begin
FINAL_LEVEL_PHASE_1_SECONDS = 39.95
FINAL_LEVEL_PHASE_2_SECONDS = 49.3
FINAL_LEVEL_PHASE_1_FRAMES = int(FINAL_LEVEL_PHASE_1_SECONDS * FINAL_LEVEL_FPS)
FINAL_LEVEL_PHASE_2_FRAMES = int(FINAL_LEVEL_PHASE_2_SECONDS * FINAL_LEVEL_FPS)
FINAL_LEVEL_PHASE_2_START_X = FINAL_LEVEL_PHASE_1_FRAMES * FINAL_LEVEL_AUTOSCROLL_SPEED
FINAL_LEVEL_PHASE_3_START_X = (FINAL_LEVEL_PHASE_1_FRAMES + FINAL_LEVEL_PHASE_2_FRAMES) * FINAL_LEVEL_AUTOSCROLL_SPEED
final_level_music_phase = 0
final_level_dialogue_queues = {1: None, 2: None, 3: None}
final_level_dialogue_queue_phase = None
floating_dialogue_queue = None
tentacle_attacks = []
final_level_tentacle_schedule = []
final_cutscene_triggered = False
final_cutscene_state = None
final_cutscene_trigger_x = 164600
final_cutscene_timer = 0
final_cutscene_music_stopped = False
final_cutscene_dialogue_started = False
final_phase_shake_timer = 0
final_phase_shake_offset = (0, 0)

credits_y = HEIGHT
credits_speed = 1
CREDITS_TEXT = [
    "GAME BY:",
    "                            ",
    "                            ",
    "                            ",
    "shadowcat",
    "                            ",
    "                            ",
    "                            ",
    "                            ",
    "MAIN PROGRAMMER:",
    "                            ",
    "                            ",
    "                            ",
    #"StitchedMask",
    "shadowcat                           ",
    "                            ",
    "                            ",
    "                            ",
    "                            ",
    "MUSIC:", 
    "                            ",
    "                            ",
    "                            ",
    "shadowcat",
    "goober-404",
    "DeltaDunked",
    "                            ",
    #"                            ",
    "Rolling Girl by: wowaka",
    "",
    "                            ",
    "                            ",
    "                            ",
    "ART:",
    "                            ",
    "                            ",
    "                            ",
    "shadowcat",
    "goober-404",
    "DeltaDunked",
    "",
    "                            ",
    "                            ",
    "                            ",
    #"SPECIAL THANKS TO:",
    #"PLAYTESTERS AND SUPPORTERS",
    "THANK YOU FOR PLAYING!",
]
checkpoint_message = ""
checkpoint_message_timer = 0

# Pause and exit state
is_paused = False
pause_selected = 0  # 0 = Continue, 1 = Exit
esc_hold_timer = 0  # Timer for holding ESC to exit

DARK_PURPLE = (132,102,158)

class FloatingDialogue:
    """Dialogue that floats from right to left while fading out."""
    global DARK_PURPLE
    def __init__(self, text, font, start_x=None, speed=2.0, fade_speed=2.0, color=None, font_size=None, y=None):
        self.text = text
        self.font = font
        self.color = color if color else (255, 255, 255)
        self.font_size = font_size  
        self.x = start_x if start_x is not None else WIDTH + 50  
        self.y = y if y is not None else HEIGHT // 2 - 50
        self.speed = speed  
        self.fade_speed = fade_speed 
        self.alpha = 255
        self.char_index = 0
        self.timer_ms = 0.0
        self.typing_speed = 4  
        self.typing_speed_ms = self.typing_speed * (1000.0 / 60.0)
        self.finished = False
        self.current_text = ""
    
    def update(self, dt_ms=None):
        """Update the floating dialogue."""
        if dt_ms is None:
            dt_ms = 1000.0 / 60.0
        if self.char_index < len(self.text):
            self.timer_ms += dt_ms
            while self.char_index < len(self.text) and self.timer_ms >= self.typing_speed_ms:
                if self.color == DARK_PURPLE:
                    if self.text[self.char_index] != " ":
                        type2.play()
                elif self.text[self.char_index] != " ":
                    type1.play()
                self.current_text += self.text[self.char_index]
                self.char_index += 1
                self.timer_ms -= self.typing_speed_ms
        else:
            # Fade out
            self.alpha = max(0, self.alpha - self.fade_speed * (dt_ms / (1000.0 / 60.0)))
            if self.alpha <= 0:
                self.finished = True
        
        self.x -= self.speed * (dt_ms / (1000.0 / 60.0))
    
    def draw(self, screen):
        """Draw the floating dialogue with fade effect."""
        if self.alpha > 0:

            if self.font_size is not None:
                render_font = pygame.font.Font(None, self.font_size)
            else:
                render_font = self.font
            text_surf = render_font.render(self.current_text, True, self.color)
            text_surf.set_alpha(self.alpha)
            screen.blit(text_surf, (self.x, self.y))

class FloatingDialogueQueue:
    def __init__(self, lines, font, default_delay=90, initial_delay=0, default_speed=3.0, default_fade_speed=2.0, default_color=(255, 255, 255), default_font_size=None, default_start_x=None):
        self.font = font
        self.default_delay = default_delay
        self.default_speed = default_speed
        self.default_fade_speed = default_fade_speed
        self.default_color = default_color
        self.default_font_size = default_font_size
        self.default_start_x = default_start_x
        self.entries = []
        for item in lines:
            entry = {
                'text': '',
                'y': HEIGHT // 2 - 50,
                'speed': self.default_speed,
                'fade_speed': self.default_fade_speed,
                'color': self.default_color,
                'font_size': self.default_font_size,
                'start_x': self.default_start_x,
                'delay_after': self.default_delay,
            }
            if isinstance(item, str):
                entry['text'] = item
            elif isinstance(item, dict):
                entry.update(item)
            elif isinstance(item, (list, tuple)):
                if len(item) > 0:
                    entry['text'] = item[0]
                if len(item) > 1:
                    entry['y'] = item[1]
                if len(item) > 2:
                    entry['speed'] = item[2]
                if len(item) > 3:
                    entry['fade_speed'] = item[3]
                if len(item) > 4:
                    entry['color'] = item[4]
                if len(item) > 5:
                    entry['font_size'] = item[5]
                if len(item) > 6:
                    entry['start_x'] = item[6]
                if len(item) > 7:
                    entry['delay_after'] = item[7]
            self.entries.append(entry)

        # Compute absolute millisecond timestamps for each entry
        self.timestamps = []
        ms_per_frame = 1000.0 / 60.0
        current_time_ms = initial_delay * ms_per_frame
        self.typing_speed = 4
        self.typing_speed_ms = self.typing_speed * ms_per_frame
        for entry in self.entries:
            entry['triggered'] = False
            entry['trigger_time_ms'] = current_time_ms
            self.timestamps.append(current_time_ms)
            typing_duration_ms = len(entry['text']) * self.typing_speed_ms
            fade_duration_ms = (255.0 / max(0.01, entry['fade_speed'])) * ms_per_frame
            delay_duration_ms = entry['delay_after'] * ms_per_frame
            current_time_ms += typing_duration_ms + fade_duration_ms + delay_duration_ms

        self.current_index = 0
        self.current_dialogue = None
        self.active_dialogues = []
        self.finished = False
        self.elapsed_ms = 0
        self.total_duration_ms = current_time_ms
        
    def _instantiate_entry(self, entry):
        dialogue = FloatingDialogue(
            entry['text'], self.font,
            start_x=entry['start_x'],
            speed=entry['speed'],
            fade_speed=entry['fade_speed'],
            color=entry['color'],
            font_size=entry['font_size'],
            y=entry['y']
        )
        self.active_dialogues.append(dialogue)

    def _start_next_if_ready(self):
        if self.current_dialogue is None and self.current_index < len(self.entries):
            entry = self.entries[self.current_index]
            self.current_dialogue = FloatingDialogue(
                entry['text'], self.font,
                start_x=entry['start_x'],
                speed=entry['speed'],
                fade_speed=entry['fade_speed'],
                color=entry['color'],
                font_size=entry['font_size'],
                y=entry['y']
            )
        elif self.current_index >= len(self.entries) and self.current_dialogue is None:
            self.finished = True

    def update(self, dt):
        if self.finished:
            return
        self.elapsed_ms += dt
        for entry in self.entries:
            if not entry.get('triggered', False) and self.elapsed_ms >= entry['trigger_time_ms']:
                self._instantiate_entry(entry)
                entry['triggered'] = True
                self.current_index += 1
        for dialogue in self.active_dialogues[:]:
            dialogue.update(dt)
            if dialogue.finished:
                self.active_dialogues.remove(dialogue)
        if self.current_index >= len(self.entries) and not self.active_dialogues:
            self.finished = True

    def draw(self, screen):
        for dialogue in self.active_dialogues:
            dialogue.draw(screen)

    def clear(self):
        self.active_dialogues = []
        self.finished = True

    def reset_for_phase_restart(self):
        """Reset the queue for phase restart (e.g., on player death)."""
        self.current_index = 0
        self.current_dialogue = None
        self.active_dialogues = []
        for entry in self.entries:
            entry['triggered'] = False
        self.elapsed_ms = 0
        self.finished = False

class TargetedTentacleStrike:
    TRACKING = "TRACKING"
    LOCKED = "LOCKED"
    STRIKE = "STRIKE"

    def __init__(
        self,
        attack_direction,
        player,
        font,
        start_frame=None,
        tracking_frames=45,
        locked_frames=20,
        strike_frames=30,
        strike_color=(255, 80, 80),
        warning_color=(255, 0, 0),
        lock_color=(255, 220, 80),
        image=None,
        screen_padding=20,
        phase_multiplier=1.0,
    ):
        self.attack_direction = attack_direction.upper()
        if self.attack_direction not in ('LEFT', 'RIGHT', 'TOP', 'BOTTOM'):
            self.attack_direction = 'LEFT'
        self.player = player
        self.font = font
        self.start_frame = final_level_frame_count if start_frame is None else start_frame
        self.state = self.TRACKING
        self.state_durations = {
            self.TRACKING: tracking_frames,
            self.LOCKED: locked_frames,
            self.STRIKE: strike_frames,
        }
        self.phase_multiplier = phase_multiplier
        self.warning_color = warning_color
        self.lock_color = lock_color
        self.strike_color = strike_color
        self.image = image if image is not None else shadow_tentacle_img
        self.screen_padding = screen_padding
        self.track_position = None
        self.locked_position = None
        self.strike_start = None
        self.strike_center = None
        self.strike_rect = None
        self.has_damaged = False
        self.damage_amount = 1
        self.flashing_timer = 0
        self.finished = False
        self._prepare_strike_image()

    def _prepare_strike_image(self):
        if self.attack_direction == 'LEFT':
            angle = 90
        elif self.attack_direction == 'RIGHT':
            angle = -90
        elif self.attack_direction == 'TOP':
            angle = 180
        else:
            angle = 0
        self.rotated_image = pygame.transform.rotate(self.image, angle)
        self.rotated_rect = self.rotated_image.get_rect()

    def _get_player_screen_pos(self):
        screen_x = self.player.rect.centerx - camera.offset_x
        screen_y = self.player.rect.centery - camera.offset_y
        return screen_x, screen_y

    def _state_elapsed(self):
        return final_level_frame_count - self.start_frame

    def _state_boundary(self, state):
        tracking = self.state_durations[self.TRACKING] * self.phase_multiplier
        locked = self.state_durations[self.LOCKED] * self.phase_multiplier
        strike = self.state_durations[self.STRIKE] * self.phase_multiplier
        if state == self.TRACKING:
            return tracking
        if state == self.LOCKED:
            return tracking + locked
        return tracking + locked + strike

    def set_state_durations(self, tracking=None, locked=None, strike=None):
        if tracking is not None:
            self.state_durations[self.TRACKING] = tracking
        if locked is not None:
            self.state_durations[self.LOCKED] = locked
        if strike is not None:
            self.state_durations[self.STRIKE] = strike

    def set_phase_multiplier(self, multiplier):
        self.phase_multiplier = multiplier

    def _enter_locked(self):
        self.state = self.LOCKED
        self.locked_position = self.track_position
        self.start_frame = final_level_frame_count - self.state_durations[self.TRACKING] * self.phase_multiplier

    def _enter_strike(self):
        self.state = self.STRIKE
        if self.locked_position is None:
            self.locked_position = self.track_position
        self._init_strike_rect()
        self.start_frame = final_level_frame_count - (
            self.state_durations[self.TRACKING] + self.state_durations[self.LOCKED]
        ) * self.phase_multiplier

    def _init_strike_rect(self):
        self._prepare_strike_path()
        rect = self.rotated_image.get_rect()
        rect.center = self.strike_start
        self.strike_rect = rect

    def _prepare_strike_path(self):
        screen_x, screen_y = self.locked_position or (WIDTH // 2, HEIGHT // 2)
        if self.attack_direction == 'LEFT':
            self.strike_start = (-self.screen_padding - self.rotated_rect.width, screen_y)
            self.strike_center = (WIDTH // 2-400, screen_y)
        elif self.attack_direction == 'RIGHT':
            self.strike_start = (WIDTH + self.screen_padding + self.rotated_rect.width, screen_y)
            self.strike_center = (WIDTH // 2+100, screen_y)
        elif self.attack_direction == 'TOP':
            self.strike_start = (screen_x, -self.screen_padding - self.rotated_rect.height)
            self.strike_center = (screen_x, HEIGHT // 2-100)
        else:
            self.strike_start = (screen_x, HEIGHT + self.screen_padding + self.rotated_rect.height)
            self.strike_center = (screen_x, (HEIGHT // 2)+300)

    @staticmethod
    def _lerp(start, end, t):
        return (start[0] + (end[0] - start[0]) * t, start[1] + (end[1] - start[1]) * t)

    def _get_player_screen_rect(self):
        player_rect = self.player.rect.copy()
        player_rect.x -= camera.offset_x
        player_rect.y -= camera.offset_y
        return player_rect

    def _check_player_hit(self):
        if self.has_damaged or self.strike_rect is None:
            return
        if self.strike_rect.colliderect(self._get_player_screen_rect()):
            self.player.take_damage(self.damage_amount)
            self.has_damaged = True

    def update(self):
        if self.finished:
            return
        elapsed = self._state_elapsed()
        if self.state == self.TRACKING:
            player_x, player_y = self._get_player_screen_pos()
            self.track_position = (player_x, player_y)
            if elapsed >= self._state_boundary(self.TRACKING):
                self._enter_locked()
        elif self.state == self.LOCKED:
            if elapsed >= self._state_boundary(self.LOCKED):
                self._enter_strike()
        elif self.state == self.STRIKE:
            if self.strike_rect is None:
                self._init_strike_rect()
            strike_elapsed = elapsed - self._state_boundary(self.LOCKED)
            strike_duration = max(1, self.state_durations[self.STRIKE] * self.phase_multiplier)
            progress = min(1.0, max(0.0, strike_elapsed / strike_duration))
            if progress <= 0.5:
                self.strike_rect.center = self._lerp(self.strike_start, self.strike_center, progress * 2)
            else:
                self.strike_rect.center = self._lerp(self.strike_center, self.strike_start, (progress - 0.5) * 2)
            self._check_player_hit()
            if progress >= 1.0:
                self.finished = True
        self.flashing_timer = (self.flashing_timer + 1) % 30

    def _is_off_screen(self):
        if self.strike_rect is None:
            return False
        return (
            self.strike_rect.right < -self.screen_padding
            or self.strike_rect.left > WIDTH + self.screen_padding
            or self.strike_rect.bottom < -self.screen_padding
            or self.strike_rect.top > HEIGHT + self.screen_padding
        )

    def draw(self, screen):
        if self.finished:
            return
        if self.state == self.TRACKING:
            self._draw_tracking(screen)
        elif self.state == self.LOCKED:
            self._draw_locked(screen)
        elif self.state == self.STRIKE:
            self._draw_strike(screen)

    def _draw_tracking(self, screen):
        if self.track_position is None:
            return
        px, py = self.track_position
        thickness = 6
        if self.attack_direction == 'LEFT':
            pygame.draw.line(screen, self.warning_color, (0, py), (min(150, WIDTH // 4), py), thickness)
            pygame.draw.circle(screen, self.warning_color, (0, py), 8)
           # if self.font:
           #     label = self.font.render('TRACK', True, self.warning_color)
           #     screen.blit(label, (20, py - 30))
        elif self.attack_direction == 'RIGHT':
            pygame.draw.line(screen, self.warning_color, (WIDTH, py), (max(WIDTH - 150, WIDTH * 3 // 4), py), thickness)
            pygame.draw.circle(screen, self.warning_color, (WIDTH, py), 8)
            #if self.font:
            #    label = self.font.render('TRACK', True, self.warning_color)
            #    screen.blit(label, (WIDTH - label.get_width() - 20, py - 30))
        elif self.attack_direction == 'TOP':
            pygame.draw.line(screen, self.warning_color, (px, 0), (px, min(150, HEIGHT // 4)), thickness)
            pygame.draw.circle(screen, self.warning_color, (px, 0), 8)
            #if self.font:
            #    label = self.font.render('TRACK', True, self.warning_color)
            #    screen.blit(label, (px + 10, 10))
        else:
            pygame.draw.line(screen, self.warning_color, (px, HEIGHT), (px, max(HEIGHT - 150, HEIGHT * 3 // 4)), thickness)
            pygame.draw.circle(screen, self.warning_color, (px, HEIGHT), 8)
           # if self.font:
                #label = self.font.render('TRACK', True, self.warning_color)
                #screen.blit(label, (px + 10, HEIGHT - 40))

    def _draw_locked(self, screen):
        if self.locked_position is None:
            return
        px, py = self.locked_position
        color = self.lock_color if self.flashing_timer < 15 else self.warning_color
        thickness = 14
        if self.attack_direction in ('LEFT', 'RIGHT'):
            pygame.draw.line(screen, color, (0, py), (WIDTH, py), thickness)
            pygame.draw.circle(screen, color, (WIDTH // 2, py), 18, 4)
            #if self.font:
               # label = self.font.render('LOCKED', True, color)
               # screen.blit(label, (WIDTH // 2 - label.get_width() // 2, py - 30))
        else:
            pygame.draw.line(screen, color, (px, 0), (px, HEIGHT), thickness)
            pygame.draw.circle(screen, color, (px, HEIGHT // 2), 18, 4)
            #if self.font:
            #    label = self.font.render('LOCKED', True, color)
            #    screen.blit(label, (px + 10, HEIGHT // 2 - 30))

    def _draw_strike(self, screen):
        if self.strike_rect is None:
            return
        screen.blit(self.rotated_image, self.strike_rect)
       # if self.state == self.STRIKE and self.strike_rect is not None:
            #impact_color = (255, 180, 60)
            #if self.attack_direction in ('LEFT', 'RIGHT'):
            #    pygame.draw.line(screen, impact_color, (self.strike_rect.centerx, 0), (self.strike_rect.centerx, HEIGHT), 2)
           # else:
            #    pygame.draw.line(screen, impact_color, (0, self.strike_rect.centery), (WIDTH, self.strike_rect.centery), 2)

class Camera:
    def __init__(self, width, height):
        self.offset_x = 0
        self.offset_y = 0
        self.width = width
        self.height = height
        self.shake_x = 0
        self.shake_y = 0
        
    def apply(self, entity_rect):
        return entity_rect.move(-self.offset_x - self.shake_x, -self.offset_y - self.shake_y)

    def update(self, target_rect):
        global boss_triggered, boss_finished, boss2_triggered, boss2_finished, current_level, final_level_autoscroll, final_level_autoscroll_speed
        
        # Final level autoscroll
        if current_level == 'FINAL' and final_level_autoscroll:
            self.offset_x = min(self.offset_x + final_level_autoscroll_speed, 1650000)
            self.offset_y = 390
            return
        if current_level == 'FINAL' and final_cutscene_triggered:
            self.offset_x = min(self.offset_x + 10, final_cutscene_trigger_x)
            self.offset_y = 390
            return
        if boss2_triggered and not boss2_finished:
            desired_x = target_rect.centerx - WIDTH // 2
            desired_y = target_rect.centery - int(HEIGHT * 0.65)
            self.offset_x = max(BOSS2_ARENA_LEFT, min(desired_x, BOSS2_ARENA_LEFT + BOSS2_ARENA_WIDTH - WIDTH))
            self.offset_y = max(BOSS2_ARENA_TOP, min(desired_y, BOSS2_ARENA_TOP + BOSS2_ARENA_HEIGHT - HEIGHT))
            return

        if boss_triggered and not boss_finished:
            # Lock the camera to the arena coordinates
            self.offset_x = 15000
            self.offset_y = 200
            return

        if current_level == 'SHIP':
                self.offset_x = 0
                self.offset_y = -300

        else:
            # Normal camera follow logic
            self.offset_x = target_rect.centerx - int(WIDTH / 2 - 20)
            self.offset_y = target_rect.centery - int(HEIGHT * 0.65)
            
            self.offset_x = max(0, self.offset_x)
            self.offset_y = max(-10000000, self.offset_y) 
pygame.init()
pygame.joystick.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
camera = Camera(WIDTH, HEIGHT)

BOSS2_ARENA_LEFT = 22000
BOSS2_ARENA_TOP = -HEIGHT + 1500
BOSS2_ARENA_WIDTH = WIDTH * 2
BOSS2_ARENA_HEIGHT = HEIGHT * 2 +200

BOSS_ARENA1_START_X = (15000)

PORTRAITS = {
    "Captain Vio": pygame.image.load("Vio_Portrait.png").convert_alpha(),
    "Captain Vio_Down": pygame.image.load("Vio_Down.png").convert_alpha(),
    "Captain Vio (young)_Young": pygame.image.load("Vio_Young.png").convert_alpha(),
    "Captain Vio_Confused": pygame.image.load("Vio_Confused.png").convert_alpha(),
    "Captain Vio_Surprised": pygame.image.load("Vio_Surprised.png").convert_alpha(),
    "Captain Vio_Joy": pygame.image.load("Vio_Joy.png").convert_alpha(),
    "Lin":pygame.image.load("Lin_Portrait.png").convert_alpha(),
    #"Moistar": pygame.image.load("moistar_portrait.png").convert_alpha(),
    #"DJ Oser": pygame.image.load("mo_portrait.png").convert_alpha(),
    #"???": pygame.image.load("unknown_portrait.png").convert_alpha()
}

pygame.mixer.init()
pygame.mixer.set_reserved(1)
music_channel = pygame.mixer.Channel(0)
ship_img = pygame.image.load("Allegro(open).png").convert_alpha()
mois_snd = pygame.mixer.Sound('Mois_bytes.wav')
snd_hurt = pygame.mixer.Sound('snd_hurt.wav')
snd_speaker_explode =pygame.mixer.Sound('snd_speaker_explode.wav')
snd_speaker_hurt =pygame.mixer.Sound('snd_speaker_hurt.wav')
glitch_snd = pygame.mixer.Sound('glitch_snd.wav')
laser_blast = pygame.mixer.Sound('laser_blast.wav')
Melody1 = pygame.mixer.Sound('Melody1.mp3')
#Melody2 = pygame.mixer.Sound('Melody2.wav')
Melody2 = pygame.mixer.Sound('Melody2.mp3')
Melody3 = pygame.mixer.Sound('Melody3.mp3')
The_Melody = pygame.mixer.Sound('To Confront the Tears.mp3')

rolling_girl_phase1 = pygame.mixer.Sound('Rolling Girl(start).mp3')
rolling_girl_phase1.set_volume(1)
rolling_girl_phase2 = pygame.mixer.Sound('Rolling Girl (phase 2).mp3')
rolling_girl_phase2.set_volume(1)
rolling_girl_phase3 = pygame.mixer.Sound('Rolling Girl (phase 3).mp3')
rolling_girl_phase3.set_volume(1)

type1 = pygame.mixer.Sound('type.wav')
type2 = pygame.mixer.Sound('type2.wav')
moon_song = pygame.mixer.Sound('moon_song.mp3')
castle_song = pygame.mixer.Sound('WELCOME TO THE CASTLE.mp3')


mus_her = pygame.mixer.Sound('her.mp3')   # Memory transition music
mus_title = pygame.mixer.Sound('Title.mp3')                   # Titlescreen music
mus_boss1 = pygame.mixer.Sound('DJ Dig.mp3')                # Level 1 boss fight music
mus_boss2 = pygame.mixer.Sound('Diva Rejected.mp3')        # Level 2 boss fight music

castle_song.set_volume(0.6)
#my_dear_sister = None
#mus_title = None
#mus_boss1 = None
#mus_boss2 = None

current_music = None

def switch_music(new_track, loops=0):
    global current_music, music_channel
    if new_track is None:
        if current_music is not None:
            music_channel.stop()
            current_music = None
        return
    if current_music is new_track:
        return
    if current_music is not None:
        music_channel.stop()
    current_music = new_track
    if current_music is not None:
        music_channel.play(current_music, loops=loops)


def stop_music():
    global current_music, music_channel
    if current_music is not None:
        music_channel.stop()
        current_music = None


def pause_music():
    global music_channel
    try:
        if music_channel.get_busy():
            music_channel.pause()
        pygame.mixer.music.pause()
    except Exception:
        pass


def resume_music():
    global music_channel
    try:
        if current_music is not None:
            music_channel.unpause()
        pygame.mixer.music.unpause()
    except Exception:
        pass


def get_final_level_phase_from_frame(frame):
    if frame >= FINAL_LEVEL_AUTOSCROLL_START_FRAME + FINAL_LEVEL_PHASE_1_FRAMES + FINAL_LEVEL_PHASE_2_FRAMES:
        return 3
    if frame >= FINAL_LEVEL_AUTOSCROLL_START_FRAME + FINAL_LEVEL_PHASE_1_FRAMES:
        return 2
    return 1


def get_final_level_frame_for_phase(phase):
    if phase == 1:
        return FINAL_LEVEL_AUTOSCROLL_START_FRAME
    if phase == 2:
        return FINAL_LEVEL_AUTOSCROLL_START_FRAME + FINAL_LEVEL_PHASE_1_FRAMES
    if phase == 3:
        return FINAL_LEVEL_AUTOSCROLL_START_FRAME + FINAL_LEVEL_PHASE_1_FRAMES + FINAL_LEVEL_PHASE_2_FRAMES
    return 0


def get_final_level_respawn_position(phase):
    base_y = LEVEL_START_POINTS.get('FINAL', (100, 800))[1] if 'LEVEL_START_POINTS' in globals() else 800
    if phase == 2:
        return (FINAL_LEVEL_PHASE_2_START_X + 100, base_y)
    if phase == 3:
        return (FINAL_LEVEL_PHASE_3_START_X + 100, base_y)
    return (100, base_y)


def create_final_level_dialogue_queue(phase, font):
    if phase == 1:
        return FloatingDialogueQueue([
            {
                'text': "NO, STOP!!!",
                'y': HEIGHT // 2 - 120,
                'speed': 5.0,
                'fade_speed': 2.0,
                'color': DARK_PURPLE,
                'font_size': 50,
                'delay_after': 140,
            },
            {
                'text': "This crash...",
                'y': HEIGHT // 2 - 80,
                'speed': 8.0,
                'fade_speed': 1.5,
                'color': DARK_PURPLE,
                'font_size': 48,
                'delay_after': 120,
            },
            {
                'text': "If yOu diE heRE...iT's OveR... ",
                'y': HEIGHT // 2 - 40,
                'speed': 2.5,
                'fade_speed': 1.0,
                'color': DARK_PURPLE,
                'font_size': 32,
                'delay_after': 10,
            },
            {
                'text': "I can't give up now...",
                'y': HEIGHT // 2 - 30,
                'speed': 4.0,
                'fade_speed': 2.0,
                'font_size': 36,
                'delay_after': 0,
            },
            {
                'text': "I'm not turning back...",
                'y': HEIGHT // 2 + 30,
                'speed': 3.0,
                'fade_speed': 2.0,
                'font_size': 46,
                'delay_after': 120,
            },
        ], font, initial_delay=150, default_delay=120)
    if phase == 2:
        return FloatingDialogueQueue([
            {
                'text': "PlEase, ViO...", #The train speed is picking up
                'y': HEIGHT // 2 - 80,
                'speed': 4.0,
                'fade_speed': 1.4,
                'color': DARK_PURPLE,
                'font_size': 42,
                'delay_after': 150,
            },
            {
                'text': "........",
                'y': HEIGHT // 2 - 40,
                'speed': 4.5,
                'fade_speed': 1.8,
                'font_size': 40,
                'delay_after': 150,
            },
            {
                'text': "PlEase, StOp...",
                'y': HEIGHT // 2 + 20,
                'speed': 4.0,
                'fade_speed': 1.0,
                'color': DARK_PURPLE,
                'font_size': 44,
                'delay_after': 160,
            },
            {
                'text': "You're running into a crash...",
                'y': HEIGHT // 2 + 20,
                'speed': 3.0,
                'fade_speed': 1.2,
                'color': DARK_PURPLE,
                'font_size': 44,
                'delay_after': 80,
            },
            {
                'text': "MOUIKKAI!         MOUIKKAI!",
                'y': HEIGHT // 2 - 20,
                'speed': 6.0,
                'fade_speed': 1.8,
                'color': DARK_PURPLE,
                'font_size': 49,
                'delay_after': 40,
            },
            {
                'text': "Please, it's safer, just let us LOoP aGaiN!",
                'y': HEIGHT // 2 + 20,
                'speed': 5.0,
                'fade_speed': 1.4,
                'color': DARK_PURPLE,
                'font_size': 48,
                'delay_after': 240,
            },
            {
                'text': "Just hold your breath. Stay silent just like we always do...",
                'y': HEIGHT // 2 - 40,
                'speed': 5.0,
                'fade_speed': 1.4,
                'color': DARK_PURPLE,
                'font_size': 42,
                'delay_after': 240,
            },
        ], font, initial_delay=150, default_delay=120)
    if phase == 3:
        return FloatingDialogueQueue([
            {
                'text': "We're going to CRASH! We will DIE...",
                'y': HEIGHT // 2 - 80,
                'speed': 6.0,
                'fade_speed': 2.6,
                'color': DARK_PURPLE,
                'font_size': 58,
                'delay_after': 20,
            },
            {
                'text': "Pull the brakes, turn around, just....STOP.....",
                'y': HEIGHT // 2 - 40,
                'speed': 5.5,
                'fade_speed': 2.5,
                'color': DARK_PURPLE,
                'font_size': 54,
                'delay_after': 40,
            },
            {
                'text': "It's too late. The train is already moving.",
                'y': HEIGHT // 2 + 20,
                'speed': 4.0,
                'fade_speed': 1.6,
                'font_size': 42,
                'delay_after': 30,
            },
            #{
            #    'text': "The train is already moving.",
            #    'y': HEIGHT // 2 + 20,
            #    'speed': 3.5,
             #   'fade_speed': 1.2,
             #   'font_size': 46,
            #    'delay_after': 90,
            #},
            {
                'text': "There's nothing we can do about that.",
                'y': HEIGHT // 2 + 20,
                'speed': 3.8,
                'fade_speed': 1.8,
                'font_size': 50,
                'delay_after': 10,
            },
            {
                'text': "Don't you want to see her too?",
                'y': HEIGHT // 2 + 20,
                'speed': 2.5,
                'fade_speed': 1.0,
                'font_size': 56,
                'delay_after': 30,
            },
            {
                'text': "Just stop talking....",
                'y': HEIGHT // 2 - 20,
                'speed': 2.9,
                'fade_speed': 1.8,
                'color': DARK_PURPLE,
                'font_size': 42,
                'delay_after': 60,
            },
            {
                'text': "There has to be a way...",
                'y': HEIGHT // 2 - 20,
                'speed': 3.3,
                'fade_speed': 2.8,
                'color': DARK_PURPLE,
                'font_size': 42,
                'delay_after': 75,
            },
            {
                'text': "MOUIKKAI !        MOUIKKAI !",
                'y': HEIGHT // 2 - 20,
                'speed': 6.5,
                'fade_speed': 2.0,
                'color': DARK_PURPLE,
                'font_size': 49,
                'delay_after': 40,
            },
            {
                'text': "We must find a way to kEeP looPinG!...right?",
                'y': HEIGHT // 2 - 20,
                'speed': 6.0,
                'fade_speed': 1.8,
                'color': DARK_PURPLE,
                'font_size': 49,
                'delay_after': 40,
            },
            {
                'text': "We... must reach her. I know even you want to see her.",
                'y': HEIGHT // 2 - 30,
                'speed': 5.0,
                'fade_speed': 3.8,
                'font_size': 53,
                'delay_after': 10,
            },
            {
                'text': "Let's face this.",
                'y': HEIGHT // 2 - 30,
                'speed': 5.0,
                'fade_speed': 3.8,
                'font_size': 53,
                'delay_after': 10,
            },
        ], font, initial_delay=150, default_delay=120)


def set_final_level_music_phase(phase):
    global final_level_music_phase
    if phase == final_level_music_phase:
        return
    final_level_music_phase = phase
    #print(f"DEBUG: Switching to final level music phase {phase}")
    if phase == 0:
        stop_music()
        return
    if phase == 1:
        switch_music(rolling_girl_phase1)
    elif phase == 2:
        switch_music(rolling_girl_phase2)
    elif phase == 3:
        switch_music(rolling_girl_phase3)


def update_final_level_music():
    if current_level != 'FINAL' or not final_level_autoscroll:
        return
    phase = get_final_level_phase_from_frame(final_level_frame_count)
    set_final_level_music_phase(phase)


def get_phase_music_progress():
    if current_level != 'FINAL' or floating_dialogue_queue is None:
        return 0.0
    elapsed = getattr(floating_dialogue_queue, 'elapsed_ms', 0)
    total = getattr(floating_dialogue_queue, 'total_duration_ms', 0)
    return min(1.0, elapsed / max(1, total))


def draw_omori_vignette(screen, intensity):
    if intensity <= 0:
        return
    try:
        overlay = shadow_corner_img.copy()
        overlay.set_alpha(int(220 * intensity))
        screen.blit(overlay, (0, 0))
    except NameError:
        pass

# To add future songs, load them above and extend the state logic in update_game_music().

type1.set_volume(0.8)
laser_blast.set_volume(0.5)
snd_hurt.set_volume(0.4)
mois_snd.set_volume(0.8)


moistar_charge_img=pygame.image.load("moistar_charge_img.png").convert_alpha()
donut_img = pygame.image.load("Donut.png").convert_alpha()

boss_neon_wave_img = pygame.image.load('boss_wave.png').convert_alpha()
kira_img = pygame.image.load('Kira.png').convert_alpha()

lever_img = pygame.image.load('lever.png').convert_alpha()
neon_laser_img = pygame.image.load('neon_laser.png').convert_alpha()
try:
    neon_laser_h_img = pygame.image.load('neon_laser_h.png').convert_alpha()
except Exception:
    neon_laser_h_img = pygame.transform.rotate(neon_laser_img, 90)
#laser_warning_img = neon_laser_img.copy()
laser_warning_img = pygame.surface.Surface((TILE_SIZE, HEIGHT)) 
laser_warning_img.fill((255, 20, 147))
laser_warning_img.set_alpha(100)

try:
    shadow_tentacle_img = pygame.image.load('shadow_form2.png').convert_alpha()
    shadow_tentacle_img = pygame.transform.scale(shadow_tentacle_img, (TILE_SIZE * 12, TILE_SIZE * 12))
except Exception:
    shadow_tentacle_img = pygame.Surface((TILE_SIZE * 4, TILE_SIZE * 12), pygame.SRCALPHA)
    pygame.draw.rect(shadow_tentacle_img, (120, 20, 120), shadow_tentacle_img.get_rect())

try:
    shadow_corner_img = pygame.image.load('shadow_corner.png').convert_alpha()
    shadow_corner_img = pygame.transform.smoothscale(shadow_corner_img, (WIDTH, HEIGHT))
except Exception:
    shadow_corner_img = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.circle(shadow_corner_img, (0, 0, 0, 200), (0, 0), 300)
    pygame.draw.circle(shadow_corner_img, (0, 0, 0, 180), (WIDTH, 0), 300)
    pygame.draw.circle(shadow_corner_img, (0, 0, 0, 180), (0, HEIGHT), 300)
    pygame.draw.circle(shadow_corner_img, (0, 0, 0, 200), (WIDTH, HEIGHT), 300)

class DialogueBox:
    def __init__(self, font, text_list, speaker_name="", autoplay=False, auto_delay=120, has_background=True, has_portrait=None, is_passive=False, text_color=(255, 255, 255), is_choice=False):
        self.is_passive = is_passive
        self.text_color = text_color
        self.font = font
        self.text_list = text_list
        self.speaker_name = speaker_name
        self.current_portrait_key = speaker_name 
        self.has_portrait = self.current_portrait_key in PORTRAITS
        self.has_background = has_background
        self.is_choice = is_choice
        self.selection = 0
        self.last_left = False
        self.last_right = False
        # If has_portrait is not specified, determine it based on whether speaker has a portrait
        if has_portrait is None:
            self.has_portrait = self.speaker_name in PORTRAITS
        else:
            self.has_portrait = has_portrait
        
        self.current_sentence = 0
        self.current_text = ""
        self.char_index = 0
        self.timer = 0 # Timer to control text speed
        self.speed = 4  # Lower is faster
        self.finished = False
        self.autoplay = autoplay  # If True, auto-advance to next sentence
        self.auto_delay = auto_delay  # Frames to wait before auto-advancing
        self.auto_timer = 0  # Timer for autoplay
        self.wait_timer = 0

        self.waiting_for_input = False
        self.icon_timer = 0  
        self.z_pressed_last = False

        self.process_current_line()
    def update(self, keys, skip_held=False):
        # Skip entire dialogue if button held (useful for dev testing)
        if keys is None:
            keys = pygame.key.get_pressed()
        is_z_pressed = keys[pygame.K_z] or keys[pygame.K_RETURN] or keys[pygame.K_SPACE]
        controller_confirm = False
        controller_left = False
        controller_right = False
        for joy in joysticks:
            try:
                controller_confirm = controller_confirm or joy.get_button(0) or joy.get_button(1)
                hat = joy.get_hat(0)
                controller_left = controller_left or hat[0] < 0
                controller_right = controller_right or hat[0] > 0
                axis = joy.get_axis(0)
                controller_left = controller_left or axis < -0.5
                controller_right = controller_right or axis > 0.5
            except pygame.error:
                pass
        is_z_pressed = is_z_pressed or controller_confirm
        if skip_held:
            self.finished = True
            return
        
        if self.current_sentence < len(self.text_list):
            target_text = self.text_list[self.current_sentence]

            if self.waiting_for_input:
                if is_z_pressed and not self.z_pressed_last:
                    self.waiting_for_input = False
                self.z_pressed_last = is_z_pressed
                return

            if self.wait_timer > 0:
                self.wait_timer -= 1
                return
            
            if self.char_index < len(target_text):
                
                self.timer += 1
                if self.timer >= self.speed:
                    char = target_text[self.char_index]
                    #play sound every other regular character
                    snd_timer = (2 * self.char_index) // 2
                    if snd_timer % 2 == 0:
                        if char != '.' and char != '|' and char != '*' and char != '>':
                            if self.speaker_name == "Moistar":
                                mois_snd.play()
                            if self.speaker_name == "Captain Vio":
                                type1.play()
                            if self.speaker_name == "???":
                                type2.play()
                            else:
                                type1.play()
                    if char == "|":  # PAUSE TAG
                        self.wait_timer = 30  # Wait for 30 frames
                        self.char_index += 1  # Skip the symbol

                    elif char == "*": 
                        self.waiting_for_input = True
                        self.char_index += 1

                    elif char == ">": # WARP 
                        # Add everything left in the sentence instantly
                        remaining_text = target_text[self.char_index + 1:]
                        self.current_text += remaining_text
                        self.char_index = len(target_text)

                    else:
                        self.current_text += char
                        self.char_index += 1
                        self.timer = 0
            
            
            if self.char_index >= len(target_text):
                # If it's a choice, handle the toggle and the final confirmation
                if self.is_choice and self.current_sentence == len(self.text_list) - 1:
                    # Toggle selection with arrow keys or controller D-pad / stick
                    if ((keys[pygame.K_LEFT] and not self.last_left) or (keys[pygame.K_RIGHT] and not self.last_right)
                        or (controller_left and not self.last_left) or (controller_right and not self.last_right)) and not self.z_pressed_last:
                        self.selection = 1 - self.selection
                        #snd.select
                    self.last_left = keys[pygame.K_LEFT] or controller_left
                    self.last_right = keys[pygame.K_RIGHT] or controller_right
                    # Confirm selection
                    if is_z_pressed and not self.z_pressed_last:
                        self.finished = True
                        return self.selection 
                
                
                #elif is_z_pressed and not self.z_pressed_last:
                    #self.advance_sentence()
                
                if self.autoplay or self.is_passive:
                    self.auto_timer += 1
                    if self.auto_timer >= self.auto_delay:
                        if self.current_sentence < len(self.text_list) - 1:
                            self.advance_sentence()
                            self.auto_timer = 0
                        else:
                            self.finished = True # Signal to BossManager to remove
                elif is_z_pressed and not self.z_pressed_last:
                    self.advance_sentence()
            
            if getattr(self, 'trigger_glitch', False):
                if not hasattr(self, 'glitch_timer'): 
                    self.glitch_timer = 0
                if self.glitch_timer > 15:
                    self.current_sentence += 1
                    self.glitch_timer = 0
                    self.trigger_glitch = False 
                self.glitch_timer += 1

            self.z_pressed_last = is_z_pressed
            #if holding z, faster text speed:
            if is_z_pressed:
                self.timer += self.speed // 0.1  
            

    def process_current_line(self):
        #checks for certain tags at the start of a line
        if self.current_sentence >= len(self.text_list):
            return

        line = self.text_list[self.current_sentence]

        # 1. Handle @ Speaker and Portrait Tags
        if line.startswith("@"):
            parts = line[1:].split(":", 1)
            if len(parts) > 1:
                full_key = parts[0].strip()
                # Set the actual text to be typed (removing the @ stuff)
                self.text_list[self.current_sentence] = parts[1].strip()
                line = self.text_list[self.current_sentence] # Update local line variable

                # Set portrait and display name
                self.current_portrait_key = full_key
                self.speaker_name = full_key.split("_")[0]
                self.has_portrait = self.current_portrait_key in PORTRAITS

        #glitch Tag
        if "~" in line:
            self.trigger_glitch = True
            # Clean the text so the ~ doesn't show up in the typewriter
            self.text_list[self.current_sentence] = line.replace("~", "")
            if not hasattr(self, 'glitch_snd_played'): # Optional: only play once
                glitch_snd.play()
        else:
            self.trigger_glitch = False

    def advance_sentence(self):
        """reset variables for the next sentence."""
        raw_text = "" 
        self.current_sentence += 1
        self.current_text = ""
        self.char_index = 0
        self.timer = 0
        self.auto_timer = 0
        self.wait_timer = 0

        if self.current_sentence < len(self.text_list):
            self.process_current_line()
          
        else:
            self.finished = True
        
    def draw(self, screen, x=0, y=0):
        lines = self.current_text.split('\n')
        line_height = self.font.get_linesize()
        # Draw Name Box 
        if self.is_choice and self.char_index >= len(self.text_list[self.current_sentence]):
                
                yes_color = (255, 255, 0) if self.selection == 0 else (200, 200, 200)
                no_color = (255, 255, 0) if self.selection == 1 else (200, 200, 200)

                yes_surf = self.font.render("[ YES ]", True, yes_color)
                no_surf = self.font.render("[ NO ]", True, no_color)

                screen.blit(yes_surf, (WIDTH // 2 + 50, HEIGHT - 60))
                screen.blit(no_surf, (WIDTH // 2 + 150, HEIGHT - 60))

        if self.is_passive:
            # --- PASSIVE TOP BAR ---
            # Draw at the top of the screen regardless of x, y
            bg_rect = pygame.Rect(0, 0, 1200, 80)
            overlay = pygame.Surface((1200, 80), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180)) 
            screen.blit(overlay, (0, 0))
            
            # Draw text
            text_surf = self.font.render(self.current_text, True, self.text_color)
            screen.blit(text_surf, (50, 25))
            
            # Draw name
            name_surf = self.font.render(f"{self.speaker_name}:", True, (255, 255, 0))
            screen.blit(name_surf, (20, 5))
        else:
            if self.has_background:
                if self.waiting_for_input or (self.current_sentence < len(self.text_list) and self.char_index >= len(self.text_list[self.current_sentence])):
                    self.icon_timer += 0.1
                    # Sine wave 
                    float_y = math.sin(self.icon_timer) * 5 
                    icon_rect = pygame.Rect(x + 460, y + 110 + float_y, 15, 10)
                    pygame.draw.polygon(screen, (255, 255, 255), [
                        (icon_rect.left, icon_rect.top),
                        (icon_rect.right, icon_rect.top),
                        (icon_rect.centerx, icon_rect.bottom)
                    ]) 
                if self.has_portrait and self.current_portrait_key in PORTRAITS:
                    port_rect = pygame.Rect(x + 494, y - 189, 183, 173)
                    pygame.draw.rect(screen, (0, 0, 0), port_rect)
                    pygame.draw.rect(screen, (255, 255, 255), port_rect, 2)
                    
                    portrait_img = pygame.transform.scale(PORTRAITS[self.current_portrait_key], (230, 230))
                    screen.blit(portrait_img, (x + 470, y - 250))
                    
                # Main box background (optional, but looks good)
                #main_bg = pygame.Rect(x - 20, y - 75, 150, 50)
                #pygame.draw.rect(screen, (0, 0, 0), main_bg)
                #pygame.draw.rect(screen, (255, 255, 255), main_bg, 2)

                if self.speaker_name:
                    name_surf = self.font.render(self.speaker_name, True, (255, 255, 255))
                    # Position name box exactly 45 pixels above the main box
                    name_box_rect = pygame.Rect(x - 20, y - 75, name_surf.get_width() + 30, 50)
                    pygame.draw.rect(screen, (0, 0, 0), name_box_rect)
                    pygame.draw.rect(screen, (255, 255, 255), name_box_rect, 2)
                    screen.blit(name_surf, (x - 10, y - 60))

            for i, line in enumerate(lines):
                text_surf = self.font.render(line, True, (255, 255, 255))
                screen.blit(text_surf, (x, y + i * line_height))

    def next_sentence(self):
        if self.current_sentence < len(self.text_list):
            # If current sentence isn't finished, skip to end of it
            if self.char_index < len(self.text_list[self.current_sentence]):
                self.current_text = self.text_list[self.current_sentence]
                self.char_index = len(self.current_text)
            else:
                # Go to next sentence
                self.current_sentence += 1
                self.current_text = ""
                self.char_index = 0

class Particle:
    """Represents a shard/pixel that flies away when the player shatters."""
    def __init__(self, x, y, vel_x, vel_y, size=4, color=(150, 100, 200)):
        self.x = x
        self.y = y
        self.vel_x = vel_x
        self.vel_y = vel_y
        self.size = size
        self.color = color
        self.gravity = 0.3
        self.lifetime = 60  # Frames until particle disappears
        
    def update(self):
        self.x += self.vel_x
        self.y += self.vel_y
        self.vel_y += self.gravity  # Gravity pulls it down
        self.lifetime -= 1

    def draw(self, screen):
        if self.lifetime > 0:
            pygame.draw.rect(screen, self.color, (int(self.x), int(self.y), self.size, self.size))

    def is_alive(self):
        return self.lifetime > 0

class TrailParticle:
    """Represents a trail effect behind the player when dashing."""
    def __init__(self, image, x, y, facing_right):
        self.original_image = image.copy()
        self.x = x
        self.y = y
        self.facing_right = facing_right
        self.alpha = 180  # Start with high opacity
        self.fade_speed = 15  # How fast it fades
        self.lifetime = 12  # Frames until particle disappears
        
    def update(self):
        self.alpha = max(0, self.alpha - self.fade_speed)
        self.lifetime -= 1
    
    def _create_silhouette(self, image):
        silhouette = image.copy()
        # Create a semi-transparent dark overlay that lets the original show through
        overlay = pygame.Surface(silhouette.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))  
        silhouette.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        return silhouette

    def draw(self, screen, camera):
        if self.lifetime > 0 and self.alpha > 0:
            trail_image = self._create_silhouette(self.original_image)
            trail_image.set_alpha(self.alpha)
            trail_rect = trail_image.get_rect(topleft=(self.x, self.y))
            screen.blit(trail_image, camera.apply(trail_rect))

    def is_alive(self):
        return self.lifetime > 0

STAR_IMAGE_CACHE = {}

def create_star_image(size):
    if size in STAR_IMAGE_CACHE:
        return STAR_IMAGE_CACHE[size]
    surf = pygame.Surface((size * 5, size * 5), pygame.SRCALPHA)
    center = (size * 2 + 1, size * 2 + 1)
    base_color = (255, 240, 160)
    glow_color = (255, 235, 140)
    radius = max(1, size)
    
    pygame.draw.line(surf, glow_color, (center[0] - radius, center[1]), (center[0] + radius, center[1]), max(1, size))
    pygame.draw.line(surf, glow_color, (center[0], center[1] - radius), (center[0], center[1] + radius), max(1, size))
    pygame.draw.polygon(surf, base_color, [
        (center[0], center[1] - radius * 2),
        (center[0] + radius, center[1]),
        (center[0], center[1] + radius * 2),
        (center[0] - radius, center[1])
    ])
    pygame.draw.circle(surf, base_color, center, max(1, size // 2))
    return surf

def load_star_frames(filenames):
    for star_filename in filenames:
        try:
            sheet = pygame.image.load(star_filename).convert_alpha()
            width, height = sheet.get_size()
            if width >= height and width % height == 0:
                count = width // height
                return [sheet.subsurface(pygame.Rect(i * height, 0, height, height)).copy() for i in range(count)]
            elif height > width and height % width == 0:
                count = height // width
                return [sheet.subsurface(pygame.Rect(0, i * width, width, width)).copy() for i in range(count)]
            return [sheet]
        except pygame.error:
            continue
    return None

class Star:
    def __init__(self, x, y, size, phase, parallax, frames=None, speed = None):
        self.x = x
        self.y = y
        self.size = size
        self.phase = phase
        self.parallax = parallax
        self.speed = speed 
        if speed is None: 
            self.speed = random.uniform(0.02, 0.14) 
        self.timer = random.uniform(0.0, 2 * math.pi) 
        #self.speed = random.uniform(0.02, 0.14) 
        self.alpha = random.randint(130, 255) 
        self.frames = None 
        self.frame_index = 0
        self.frame_timer = random.uniform(0.0, 1.0)
        self.frame_speed = random.uniform(0.08, 0.22)
        self.base_image = None
        if frames:
            self.frames = [pygame.transform.smoothscale(frame, (self.size * 4, self.size * 4)) for frame in frames]
        else:
            self.base_image = create_star_image(self.size)

    def update(self):
        self.timer += self.speed
        flicker = math.sin(self.timer + self.phase) * 0.5 + 0.5
        self.alpha = int(140 + flicker * 115)
        if self.frames:
            self.frame_timer += self.frame_speed
            self.frame_index = int(self.frame_timer) % len(self.frames)

    def get_image(self):
        if self.frames:
            return self.frames[self.frame_index]
        return self.base_image

    def draw(self, surface, camera):
        screen_x = int(self.x - camera.offset_x * self.parallax)
        screen_y = int(self.y - camera.offset_y * self.parallax)
        if screen_x < -48 or screen_x > WIDTH + 48 or screen_y < -48 or screen_y > HEIGHT + 48:
            return
        image = self.get_image().copy()
        image.set_alpha(self.alpha)
        rect = image.get_rect(center=(screen_x, screen_y))
        surface.blit(image, rect)


#default_pos = (17100, 624) #(switch commenting the one below for just testing the 1st boss)
default_pos = (100, 2724)
# Get initial image from idle animation
LEVEL_START_POINTS = {
    1: default_pos,
    2: (800, 1224),#(20000, 1800))#(14000,900)#
    'FINAL': (100, 800)
}

class Player:
    global default_pos
    def __init__(self, animations):
        self.animations = animations  # Dictionary of animation states to frame lists
        self.current_animation = 'idle'
        self.frame_index = 0
        self.frame_counter = 0
        self.animation_speed = 0.15  # How fast to cycle frames
        
        self.image = self.animations['idle'][0]
        self.draw_rect = self.image.get_rect(topleft=(default_pos))
        self.rect = self.draw_rect.inflate(-10, 0)
        self.hitbox = self.rect.copy()
        self.sync_draw_rect()
        self.spawn_point = (default_pos)
        # State tracking
        self.facing_right = True
        self.is_walking = False

        self.can_move = True
        self.vel_x = 0
        self.vel_y = 0
        self.is_jumping = False
        self.is_dashing = False
        self.dash_timer = 0
        self.dash_cooldown = 0
        self.dash_direction = (0, 0)
        self.dash_spent = False
        self.dash_ready = True
        self.on_wall = None
        self.wall_jump_cooldown = 0
        self.air_control_timer = 0
        self.wall_slide_speed = 2.5

        self.trail_timer = 0  # For dash ghost effect
        self.is_holding_violin = False

        self.health = 3
        self.max_health = 3
        self.invulnerability_timer = 0
        self.is_invincible = False
        self.visible = True
        self.dead_animation_started = False
        
        # Position history for shadow delay
        self.position_history = []
        self.history_length = 320  
        
        # Physics Constants
        self.ACCEL = 0.6     
        self.FRICTION = 0.9  
        self.MAX_WALK = 6     
        self.MAX_RUN = 10     
        self.wall_cling_timer = 0
        self.WALL_CLING_DURATION = 20

        self.cutscene_target_x = None
        self.cutscene_speed = 3

    def reset_for_level(self, spawn_point):
        self.spawn_point = spawn_point
        self.draw_rect.topleft = spawn_point
        self.rect = self.draw_rect.inflate(-10, 0)
        self.hitbox = self.rect.copy()
        self.sync_draw_rect()
        self.vel_x = 0
        self.vel_y = 0
        self.is_jumping = False
        self.is_dashing = False
        self.can_move = True
        self.cutscene_target_x = None
        self.is_holding_violin = False
        self.on_wall = None
        self.wall_jump_cooldown = 0
        self.air_control_timer = 0

    def sync_draw_rect(self):
        if not hasattr(self, 'draw_rect'):
            self.draw_rect = self.image.get_rect()
        self.draw_rect.centerx = self.rect.centerx
        self.draw_rect.bottom = self.rect.bottom

    def update(self, tiles, trail_particles=None, cutscene_mode=False):
        global canSkip 
        if not self.can_move and self.cutscene_target_x is None:
            self.vel_x = 0
        global current_level, final_level_autoscroll
        self.is_walking = False  # Reset walking flag each frame
        self.update_animation()
        if self.cutscene_target_x is not None:
            dist = self.cutscene_target_x - self.rect.centerx
            if abs(dist) < self.cutscene_speed:
                # Snap to exact center and stop
                self.rect.centerx = self.cutscene_target_x
                self.cutscene_target_x = None
                self.vel_x = 0
                self.is_walking = False
            else:
                # Move toward target
                direction = 1 if dist > 0 else -1
                self.rect.x += direction * self.cutscene_speed
                self.vel_x = 1.2 * direction
                self.facing_right = (direction == 1)
                self.is_walking = True

            # Keep visual sprite aligned while cutscene movement is handling the walk
            self.sync_draw_rect()
        self.vel_y += 0.6
        self.rect.y += self.vel_y
        if not self.can_move and self.cutscene_target_x is None:
            # Freeze horizontal movement, but still apply gravity and collision
            self.vel_x = 0

        for tile in tiles:
            if tile.rect.right < self.rect.left - TILE_SIZE * 4 or tile.rect.left > self.rect.right + TILE_SIZE * 4 or tile.rect.bottom < self.rect.top - TILE_SIZE * 4 or tile.rect.top > self.rect.bottom + TILE_SIZE * 4:
                continue
            if tile.type == 'shadow' and getattr(tile, 'alpha', 0) <= 0:
                continue
            if tile.type == 'neon' and not tile.is_active():
                continue
            if self.rect.colliderect(tile.rect):
                if tile.type == 'moonspike':
                    self.take_damage(self.max_health)
                if tile.type == 'shadow':
                    self.take_damage(1)
                if tile.type == 'shockwave':
                    if hasattr(tile, 'boss_managed') and tile.boss_managed:
                        self.take_damage(1)
                    else:
                        self.take_damage(self.max_health)
                elif tile.type == 'neonlaser':
                    laser_hitbox = tile.rect.copy()
                    if tile.orientation == 'V':
                        laser_hitbox.width = 10  # Thin vertical hitbox
                        laser_hitbox.centerx = tile.rect.centerx
                    else:
                        laser_hitbox.height = 10  # Thin horizontal hitbox
                        laser_hitbox.centery = tile.rect.centery
                    if self.rect.colliderect(laser_hitbox):
                        self.take_damage(tile.damage)
                if tile.type == 'platform':
                    if self.vel_y > 0:
                        self.rect.bottom = tile.rect.top
                        self.vel_y = 0
                        self.is_jumping = False
                        self.dash_spent = False
                        self.dash_ready = True
                elif tile.type == 'normal' or tile.type == 'neon' or tile.type == 'invisible':
                    if self.vel_y > 0: 
                        self.rect.bottom = tile.rect.top
                        self.vel_y = 0
                        self.is_jumping = False
                        self.dash_spent = False 
                        self.dash_ready = True
                    elif self.vel_y < 0: 
                        self.rect.top = tile.rect.bottom
                        self.vel_y = 0

        if not self.can_move:
            self.vel_x = 0
            return
        if self.cutscene_target_x is not None or cutscene_mode:
            if self.cutscene_target_x is None:
                self.vel_x = 0 
            return 
        keys = pygame.key.get_pressed()
        controller_x = 0
        controller_y = 0
        dpad_x = 0
        dpad_y = 0
        is_running = keys[pygame.K_x]
        jump_held = keys[pygame.K_z]
        dash_button = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        left_sensor = self.rect.inflate(4, 0).move(-2, 0)
        right_sensor = self.rect.inflate(4, 0).move(2, 0)

        for joy in joysticks:
            try:
                axis_x = joy.get_axis(0)
                axis_y = joy.get_axis(1)
                if abs(axis_x) > 0.15:
                    controller_x = axis_x
                if abs(axis_y) > 0.15:
                    controller_y = axis_y
                hat = joy.get_hat(0)
                if hat[0] != 0:
                    dpad_x = hat[0]
                if hat[1] != 0:
                    dpad_y = hat[1]
            except pygame.error:
                continue

            # Xbox: A=0, B=1 | Switch: B=0, A=1
            if joy.get_button(0) or joy.get_button(1): 
                jump_held = True  
            # Xbox: X=2, Y=3 | Switch: Y=2, X=3
            if joy.get_button(2) or joy.get_button(3):
                is_running = True
            # Shoulder buttons for dash
            if joy.get_button(4) or joy.get_button(5):
                dash_button = True

        if dpad_x != 0:
            controller_x = dpad_x
        if dpad_y != 0:
            controller_y = dpad_y

        def snap_axis(x, y, deadzone=0.3):
            x = x if abs(x) > deadzone else 0
            y = y if abs(y) > deadzone else 0
            if x != 0 and y != 0:
                if abs(x) >= abs(y) * 2:
                    y = 0
                elif abs(y) >= abs(x) * 2:
                    x = 0
            return x, y

        controller_x, controller_y = snap_axis(controller_x, controller_y)

        if self.invulnerability_timer > 0:
            self.invulnerability_timer -= 1
        
        if self.wall_jump_cooldown > 0:
            self.wall_jump_cooldown -= 1
        
        if self.air_control_timer > 0:
            self.air_control_timer -= 1
        
        # --- SINGLE SHORT HOP LOGIC ---
        if self.vel_y < 0 and not jump_held: # this means the player released the jump button while still moving upwards
            self.vel_y *= 0.5 

        # --- DASH LOGIC ---
        input_x = 0
        input_y = 0
        dash_time = DASH_TIME
        dash_speed = DASH_SPEED
        if current_level == 'FINAL' and final_level_autoscroll:
            dash_speed = DASH_SPEED * 1.5
            #dash_time = DASH_TIME * 1.3
        if keys[pygame.K_LEFT] or controller_x < -0.1:
            input_x = -1
        elif keys[pygame.K_RIGHT] or controller_x > 0.1:
            input_x = 1
        if keys[pygame.K_UP] or controller_y < -0.1:
            input_y = -1
        elif keys[pygame.K_DOWN] or controller_y > 0.1:
            input_y = 1

        #==dashing==
        if dash_button and not self.is_dashing and self.dash_cooldown == 0 and self.dash_ready:
            self.is_dashing = True
            self.dash_spent = True 
            self.dash_ready = False 
            self.dash_timer = dash_time
            self.dash_cooldown = DASH_COOLDOWN
            toggle_neon_color()
            if input_x == 0 and input_y == 0:
                self.dash_direction = (1 if self.facing_right else -1, 0)
            else:
                input_length = math.hypot(input_x, input_y)
                self.dash_direction = (input_x / input_length, input_y / input_length)
            self.vel_x = self.dash_direction[0] * dash_speed
            self.vel_y = self.dash_direction[1] * dash_speed
            if self.dash_direction[0] != 0:
                self.facing_right = self.dash_direction[0] > 0
            
            self.trail_timer = 0  # Reset trail timer for dash
        
        #==========
        if self.is_dashing:
            self.dash_timer -= 1
            self.vel_x = self.dash_direction[0] * dash_speed
            self.vel_y = self.dash_direction[1] * dash_speed
            
            # Create dash trail particles every few frames
            self.trail_timer += 1
            if self.trail_timer >= 3:  # Every 3 frames
                if trail_particles is not None:
                    trail_particles.append(TrailParticle(self.image, self.rect.x, self.rect.y, self.facing_right))
                self.trail_timer = 0
            
            if self.dash_timer <= 0:
                self.is_dashing = False
    
        if self.dash_cooldown > 0 and not self.is_dashing:
            self.dash_cooldown -= 1

        # --- HORIZONTAL MOVEMENT ---
        max_speed = self.MAX_RUN if is_running else self.MAX_WALK
        
        if current_level == 'FINAL' and final_level_autoscroll:
            max_speed *= 2.1  
            #DASH_SPEED *= 1.3
            #DASH_TIME = 18
        if not self.is_dashing:
            accel = self.ACCEL
            if self.is_jumping and self.air_control_timer > 0:
                accel *= 2  
            if input_x == -1:
                self.vel_x -= accel
                self.facing_right = False
            elif input_x == 1:
                self.vel_x += accel
                self.facing_right = True
            else:
                # Apply Friction when no keys are pressed
                self.vel_x *= self.FRICTION
                if abs(self.vel_x) < 0.1: self.vel_x = 0
        else:
            # Keep the dash speed locked in while dashing.
            self.vel_x = self.dash_direction[0] * DASH_SPEED

        if not self.is_dashing:
            # Cap the speed so he doesn't accelerate forever
            if self.vel_x > max_speed: self.vel_x = max_speed
            if self.vel_x < -max_speed: self.vel_x = -max_speed
            
        previous_rect = self.rect.copy()  # Save position before horizontal movement
        self.rect.x += self.vel_x
        for tile in tiles:
            if tile.type == 'shadow' and getattr(tile, 'alpha', 0) <= 0:
                continue
            if tile.type == 'neon' and not tile.is_active():
                continue
            if self.rect.colliderect(tile):
                # Platform tiles don't block horizontal movement
                if tile.type == 'platform':
                    continue
                # Wall tiles block from sides
                if tile.type == 'wall':
                    if not previous_rect.colliderect(tile):  # Only resolve if overlap is new
                        if self.vel_x > 0: # Moving right INTO wall
                            self.rect.right = tile.rect.left
                            if self.is_jumping:  # Only set on_wall when in air
                                self.on_wall = 'right'
                        elif self.vel_x < 0: # Moving left INTO wall
                            self.rect.left = tile.rect.right
                            if self.is_jumping:  # Only set on_wall when in air
                                self.on_wall = 'left'
                # Normal tiles block all directions
                elif tile.type == 'normal' or tile.type == 'neon' or tile.type == 'invisible':
                    if not previous_rect.colliderect(tile):  # Only resolve if overlap is new
                        if self.vel_x > 0: # Moving right
                            self.rect.right = tile.rect.left
                            if self.is_jumping:  # Only set on_wall when in air
                                self.on_wall = 'right'
                        elif self.vel_x < 0: # Moving left
                            self.rect.left = tile.rect.right
                            if self.is_jumping:  # Only set on_wall when in air
                                self.on_wall = 'left'
        if current_level == 'FINAL':
            left_limit = camera.offset_x + 10
            right_limit = camera.offset_x + WIDTH - 10
            if self.rect.left < left_limit:
                self.rect.left = left_limit
                self.vel_x = 0
            if self.rect.right > right_limit:
                self.rect.right = right_limit
                self.vel_x = 0

            if final_level_autoscroll and self.rect.left <= left_limit:
                crush_collision = any(
                    tile.type in ('normal', 'neon', 'invisible', 'wall') and self.rect.colliderect(tile.rect)
                    for tile in tiles
                )
                if crush_collision and self.vel_x <= 0:
                    self.take_damage(self.max_health)

        # Wall slide detection using sensors and active input
        # Only engage wall slide if actively pressing toward wall while in air
        wall_touch_right = any(((tile.type in ('wall', 'normal', 'invisible')) or (tile.type == 'neon' and tile.is_active())) and right_sensor.colliderect(tile) 
                               for tile in tiles)
        wall_touch_left = any(((tile.type in ('wall', 'normal', 'invisible')) or (tile.type == 'neon' and tile.is_active())) and left_sensor.colliderect(tile) 
                              for tile in tiles)
        
        # Engage wall slide: must be in air, falling, and actively pressing toward wall
        if self.is_jumping and not self.is_dashing:
            if input_x == 1 and wall_touch_right:
                self.on_wall = 'right'
                self.wall_cling_timer = self.WALL_CLING_DURATION # Refresh timer
            elif input_x == -1 and wall_touch_left:
                self.on_wall = 'left'
                self.wall_cling_timer = self.WALL_CLING_DURATION # Refresh timer
            else:
                # If not pressing toward wall, count down before letting go
                if self.wall_cling_timer > 0:
                    self.wall_cling_timer -= 1
                else:
                    self.on_wall = None
        else:
            self.on_wall = None
            self.wall_cling_timer = 0
        if self.on_wall == 'right' and not wall_touch_right:
            self.on_wall = None
            self.wall_cling_timer = 0
        elif self.on_wall == 'left' and not wall_touch_left:
            self.on_wall = None
            self.wall_cling_timer = 0
       
            

        # Wall sliding slows descent when clinging to a wall
        if self.on_wall and self.vel_y > 0 and not self.is_dashing:
            self.vel_y = min(self.vel_y, self.wall_slide_speed)

        
        
        # Sync visual rectangle with collision hitbox
        self.sync_draw_rect()

        # Record position for shadow delay
        self.position_history.append((self.rect.centerx, self.rect.centery))
        if len(self.position_history) > self.history_length:
            self.position_history.pop(0)
        
        # Update animation based on current state
        

    def update_animation(self):
        """Update the current animation"""
        if hasattr(self, 'is_holding_violin') and self.is_holding_violin:
            new_animation = 'idle'  # Placeholder for violin pose 
    
        keys = pygame.key.get_pressed()
        controller_left = False
        controller_right = False
        for joy in joysticks:
            try:
                hat = joy.get_hat(0)
                controller_left = controller_left or hat[0] < 0
                controller_right = controller_right or hat[0] > 0
                axis = joy.get_axis(0)
                controller_left = controller_left or axis < -0.5
                controller_right = controller_right or axis > 0.5
            except pygame.error:
                pass

        # Determine which animation should play
        if self.is_dashing and self.can_move:
            new_animation = 'dash'
        elif self.is_jumping: #if in air and are pressing against a wall, show climb
            pressing_into_left = (self.on_wall == 'left' and (keys[pygame.K_LEFT] or controller_left))
            pressing_into_right = (self.on_wall == 'right' and (keys[pygame.K_RIGHT] or controller_right))

            if pressing_into_left or pressing_into_right:
                new_animation = 'climb'
            else:
                new_animation = 'jump'
        elif self.can_move and (abs(self.vel_x) > self.MAX_WALK * 0.8):  # Running threshold
            new_animation = 'run'
        elif self.can_move and (abs(self.vel_x) > 1.1 or self.is_walking):  # Walking threshold
            new_animation = 'walk'
        else:
            new_animation = 'idle'
        
        # Reset frame index if animation changed
        if new_animation != self.current_animation:
            self.current_animation = new_animation
            self.frame_index = 0
            self.frame_counter = 0
        
        # Cycle through frames
        self.frame_counter += self.animation_speed
        if self.frame_counter >= 1.0:
            self.frame_counter = 0
            self.frame_index = (self.frame_index + 1) % len(self.animations[self.current_animation])
        
        # Get the current frame and flip if needed
        frame = self.animations[self.current_animation][self.frame_index]
        if not self.facing_right:
            self.image = pygame.transform.flip(frame, True, False)
        else:
            self.image = frame
        if hasattr(self, 'draw_rect'):
            self.draw_rect = self.image.get_rect(center=self.draw_rect.center)
    def jump(self, is_running=False):
        if self.can_move == False or self.cutscene_target_x is not None:
            return False
        keys = pygame.key.get_pressed()
        input_x = 0
        if keys[pygame.K_LEFT]:
            input_x = -1
        elif keys[pygame.K_RIGHT]:
            input_x = 1
        for joy in joysticks:
            try:
                hat = joy.get_hat(0)
                if hat[0] < 0:
                    input_x = -1
                elif hat[0] > 0:
                    input_x = 1
                elif abs(joy.get_axis(0)) > 0.1:
                    input_x = -1 if joy.get_axis(0) < 0 else 1
            except pygame.error:
                pass

        if not self.is_jumping:
            # Normal jump from ground
            force = RUN_JUMP_FORCE if is_running else JUMP_FORCE
            self.vel_y = force
            self.is_jumping = True
            self.air_control_timer = 20
            toggle_neon_color()
            return True
        elif self.on_wall and self.wall_jump_cooldown == 0:
            # Wall jump: require pressing direction away from wall
            if (input_x == -1) or (input_x == 1):
                force = RUN_JUMP_FORCE if is_running else JUMP_FORCE
                self.vel_y = force
                self.is_jumping = True
                self.air_control_timer = 20
                if self.on_wall == 'left':
                    self.vel_x = 10  # Boost right
                    self.facing_right = True
                elif self.on_wall == 'right':
                    self.vel_x = -10  # Boost left
                    self.facing_right = False
                self.on_wall = None
                self.wall_jump_cooldown = 15
                self.dash_spent = False 
                self.dash_ready = True
                toggle_neon_color()
                return True
        return False

    def take_damage(self, amount):
        if amount <= 0 or self.invulnerability_timer >0: #self.is_invincible == True
            return False
        self.health -= amount
        self.invulnerability_timer = 60
        #self.invincible = True
        snd_hurt.play()
        return True

    def reset(self):
        spawn_point = self.spawn_point
        animations = self.animations
        self.__init__(animations)
        self.spawn_point = spawn_point
        self.draw_rect.topleft = spawn_point
        self.rect = self.draw_rect.inflate(-10, 0)
        self.hitbox = self.rect.copy()
        self.sync_draw_rect()

    def die(self):
        self.health = 0
        self.visible = False
        self.dead_animation_started = True
        self.vel_x = 0
        self.vel_y = 0

    def is_dead(self):
        return self.health <= 0


def toggle_neon_color():
    global active_neon_color, neon_toggle_timer
    if neon_toggle_timer <= 0:
        neon_toggle_timer = 10  # Delay toggle by 10 frames

def update_neon_toggle():
    global neon_toggle_timer, active_neon_color
    if neon_toggle_timer > 0:
        neon_toggle_timer -= 1
        if neon_toggle_timer == 0:
            active_neon_color = 'pink' if active_neon_color == 'green' else 'green'

def load_neon_images():
    global neon_images
    try:
        green_on_img = pygame.image.load('green_on_bl.png').convert_alpha()
        pink_on_img = pygame.image.load('pink_off_bl.png').convert_alpha()
    except pygame.error:
        green_on_img = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        green_on_img.fill((0, 255, 0, 200))
        pink_on_img = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        pink_on_img.fill((255, 0, 255, 200))

    green_on_img = pygame.transform.scale(green_on_img, (TILE_SIZE, TILE_SIZE))
    pink_on_img = pygame.transform.scale(pink_on_img, (TILE_SIZE, TILE_SIZE))

    green_off_img = green_on_img.copy()
    green_off_img.set_alpha(90)
    pink_off_img = pink_on_img.copy()
    pink_off_img.set_alpha(90)

    neon_images = {
        'green': {'active': green_on_img, 'inactive': green_off_img},
        'pink': {'active': pink_on_img, 'inactive': pink_off_img}
    }

class Checkpoint:
    def __init__(self, x, y, image):
        self.image = image
        self.rect = self.image.get_rect(topleft=(x, y))
        self.active = False
        self.type = 'checkpoint'

    def update(self, player):
        if not self.active and self.rect.colliderect(player.rect):
            global checkpoint_message, checkpoint_message_timer
            self.active = True
            # Update the player's respawn position to this checkpoint
            player.spawn_point = (self.rect.x, self.rect.y)
            # Optional: Play a sound or visual effect here
            #print("Checkpoint reached!")
            save_game_state()
            checkpoint_message = "Checkpoint reached. Game saved"
            checkpoint_message_timer = 2000


def save_game_state():
    """Save minimal game state to savegame.json (level + player coords)."""
    #try:
    data = {
        'current_level': current_level,
        'x': int(Vio.rect.x),
        'y': int(Vio.rect.y),
        'health': getattr(Vio, 'health', None),
        'holding_violin': getattr(Vio, 'is_holding_violin', False)
    }
    with open('savegame.json', 'w') as f:
        json.dump(data, f)
        #print(f"Game saved: level={data['current_level']} x={data['x']} y={data['y']}")
    #except Exception as e:
        #print(f"Error saving game: {e}")


def load_game():
    """Load game state from savegame.json. Returns True on success, False otherwise."""
    global current_level, active_dialogue, game_state, camera
    if not os.path.exists('savegame.json'):
        #print("No save file found.")
        return False
    try:
        with open('savegame.json', 'r') as f:
            data = json.load(f)
        lvl = data.get('current_level')
        x = data.get('x')
        y = data.get('y')
        if lvl is None or x is None or y is None:
            #print("Save file is missing required fields.")
            return False
        # Load the level then place the player at saved coords
        tiles, checkpoints, decorations_list = load_level(lvl)
        # Place Vio at saved position
        Vio.draw_rect.topleft = (x, y)
        Vio.rect = Vio.draw_rect.inflate(-10, 0)
        Vio.hitbox = Vio.rect.copy()
        Vio.sync_draw_rect()
        Vio.can_move = True
        Vio.visible = True
        active_dialogue = None
        game_state = "PLAYING"
        # Update camera to follow player
        if camera is not None:
            camera.offset_x = max(0, Vio.rect.centerx - WIDTH // 2)
            camera.offset_y = max(0, Vio.rect.centery - HEIGHT * 0.65)
        #print(f"Game loaded: level={lvl} x={x} y={y}")
        return True
    except Exception as e:
        #print(f"Error loading save: {e}")
        return False
class Hazard:
    def update(self, player):
        pass

    def check_player(self, player):
        return self.rect.colliderect(player.rect)

    def on_hit(self, player):
        pass

    def reset(self, player):
        pass

class Shockwave:
    def __init__(self, x, y, image, direction=0, boss_managed=False):
        
        
        self.image = image
        self.image_flipped = pygame.transform.flip(image, True, False)  # Flipped horizontally
        self.rect = self.image.get_rect(topleft=(x, y))
        self.spawn_pos = (x, y)

        self.active = boss_managed
        self.boss_managed = boss_managed
        self.velocity = 0
        self.max_speed = 5 if boss_managed else 13       
        self.accel = 0.1 if boss_managed else 0.3
        self.direction = 0 # Will be 1 (right) or -1 (left)
        self.type = 'shockwave' 
        self.direction = direction 
        self.current_image = self.image_flipped if self.direction == 1 else self.image  # Track which image to draw

    def update(self, player_rect):
        if not self.active:
            # Check distance to player and activate if close enough
            distance = abs(self.rect.centerx - player_rect.centerx)
            if distance < 400:
                self.active = True
                # Move toward player
                self.direction = 1 if player_rect.x > self.rect.x else -1
                # Flip the image based on direction - shockwave should face the direction it's moving
                self.current_image = self.image_flipped if self.direction == 1 else self.image
        else:
            if abs(self.velocity) < self.max_speed:
                self.velocity += self.accel * self.direction
            self.rect.x += self.velocity

    def reset(self):
        """Called when Vio shatters to put the trap back."""
        self.rect.topleft = self.spawn_pos
        self.active = False
        self.velocity = 0
        self.direction = 0
        self.current_image = self.image

class VerticalShockwave:
    def __init__(self, x, y, image, direction="down"):
        self.spawn_pos = (x, y)
        self.direction = direction # "up" or "down"
        
        if direction == "down":
            rotated_img = pygame.transform.rotate(image, -270) # Pointing down
        else:
            rotated_img = pygame.transform.rotate(image, 270)  # Pointing up
            
        self.image = pygame.transform.scale(rotated_img, (40, 60))
        self.rect = self.image.get_rect(topleft=(x, y))
        self.active = False
        self.velocity = 0
        self.max_speed = 62
        self.accel = 2.5
        self.type = 'shockwave'

    def update(self, player_rect):
        if not self.active:
            # Trigger if player is directly above/below within 100px width
            if player_rect:
                if abs(self.rect.centerx - player_rect.centerx) < 100:
                    
                    # Trigger if player is in front of the direction it's facing
                    if self.direction == "down" and player_rect.y > self.rect.y:
                        self.active = True
                    elif self.direction == "up" and player_rect.y < self.rect.y:
                        self.active = True
                
        else:
            self.max_speed = 8
            self.accel = 1.2
            if abs(self.velocity) < self.max_speed:
                self.velocity += self.accel * (1 if self.direction == "down" else -1)
            self.rect.y += self.velocity

    def reset(self):
        self.rect.topleft = self.spawn_pos
        self.active = False
        self.velocity = 0
    def draw(self, screen, camera):
        screen.blit(self.image, camera.apply(self.rect))

def apply_screen_shake(camera, intensity, duration_remaining):
    """Apply a temporary shake to the camera offset."""
    if duration_remaining > 0:
        shake_x = random.randint(-intensity, intensity)
        shake_y = random.randint(-intensity, intensity)
        camera.offset_x += shake_x
        camera.offset_y += shake_y
    return max(0, duration_remaining - 1)


class BouncingWave:
    """A projectile fired by BoomBox speakers that bounces across the screen."""
    def __init__(self, x, y, direction, speed, arena_left, arena_right, image):
        self.image = pygame.transform.scale(image, (TILE_SIZE, TILE_SIZE // 2))

        
        self.rect = self.image.get_rect(topleft=(x, y))
        self.vel_x = speed * direction
        self.arena_left = arena_left
        self.arena_right = arena_right
        self.bounces = 0
        self.max_bounces = 4

    def update(self):
        """Update position and handle bouncing."""
        self.rect.x += self.vel_x
        
        # Check for bounce on arena walls
        if self.rect.left <= self.arena_left:
            self.rect.left = self.arena_left
            self.vel_x *= -1  # Reverse direction
            self.bounces += 1
            self.image = pygame.transform.flip(self.image, True, False)
        elif self.rect.right >= self.arena_right:
            self.rect.right = self.arena_right
            self.vel_x *= -1  # Reverse direction
            self.bounces += 1
            self.image = pygame.transform.flip(self.image, True, False)
        
        return self.bounces >= self.max_bounces  # Return True if should be removed
    
    def draw(self, screen, camera, image):
        """Draw the wave on screen."""
        pos = camera.apply(self.rect)
        # Scale the image to fit the rect size (usually 40x40 or TILE_SIZE)
        
        if abs(self.vel_x) > 10:
            img = pygame.transform.scale(image, (60, 80)) # Thicker slam wave
        else:
            img = pygame.transform.scale(image, (40, 40))
        if self.vel_x > 0:
            img = pygame.transform.flip(img, True, False)
        screen.blit(img, pos)

class BoomBox:
    """A speaker platform that fires BouncingWaves. Has a destructible button on front."""
    def __init__(self, x, y, side, image, shockwave_image=None):
        self.base_y = y  # Base position before falling animation
        self.x = x
        self.y = -200
        self.side = side  # "left" or "right"
        self.shockwave_image = shockwave_image 
        self.image = image
        #self.image = pygame.transform.scale(shockwave_image, (TILE_SIZE * 2, TILE_SIZE * 3))
        orig_w, orig_h = image.get_size()
        self.image = pygame.transform.scale(image, (orig_w * 2, orig_h * 2))
        self.rect = self.image.get_rect()
        self.rect = self.image.get_rect(topleft=(x, y))
        self.is_active = False

        # Button attributes
        self.button_health = 3
        self.button_max_health = 3
        self.button_x = x + (TILE_SIZE if side == "left" else TILE_SIZE)
        self.button_y = y + TILE_SIZE * 2
        self.button_radius = TILE_SIZE // 2
        self.button_is_glowing = False
        self.fight_timer = 0 
        self.has_exploded = False
        #self.glow_timer = 0
        #self.glow_duration = 30  # Frames to show glow as attack tell
        #self.attack_tell_timer = 0  # Glow BEFORE firing as a warning
        

        # State
        self.is_falling = False
        self.fall_speed = 0
        self.fall_accel = 0.5
        self.max_fall_speed = 15
        self.ground_y = 660 # Arena floor level 
        

        # Attack cooldown
        self.attack_cooldown = 0
        
    def start_falling(self):
        """Trigger the BoomBox to fall from the top."""
        self.is_falling = True
        self.y = -self.rect.height  # Start off-screen
        self.rect.y = self.y
        self.fall_speed = 0
    
    def take_damage(self, amount=1):
        """Reduce button health."""
        self.button_health -= amount
        snd_speaker_hurt.play()
        self.button_is_glowing = False
        self.fight_timer = 181
        
        return self.button_health <= 0  # Return True if destroyed
    
    def update(self, player_rect):
        """Update falling animation and cooldowns."""
        self.fight_timer += 1
        fired_wave = None
        # Update falling
        if self.is_falling and self.y < self.ground_y:
            self.fall_speed += self.fall_accel
            if self.fall_speed > self.max_fall_speed:
                self.fall_speed = self.max_fall_speed
            self.y += self.fall_speed
            self.rect.y = self.y
            self.button_y = self.y + TILE_SIZE * 2

        if self.fight_timer % 600 < 180:
            self.button_is_glowing = True
        else:
            self.button_is_glowing = False

        if self.can_fire and self.y >= self.ground_y and self.button_health > 0:
            if self.fight_timer % 180 == 0:
                fired_wave = self.fire_wave(player_rect)
        if self.button_health <=0 and not self.has_exploded:
            snd_speaker_explode.play()
            self.has_exploded = True
        return fired_wave
    
    def can_attack(self):
        """Check if ready to fire a wave - must be landed and not on cooldown."""
        return self.y >= self.ground_y and self.attack_cooldown == 0 and self.button_health > 0
    
    def fire_wave(self, player_rect, speed=8, max_bounces=4):
        """Fire a BouncingWave. Returns the wave object."""

        direction = 1 if self.side == "right" else -1
        wave_x = self.rect.right if self.side == "left" else self.rect.left - 40
        wave_y = max(500, min(player_rect.centery, 820)) 

        self.attack_cooldown = 120  # 2 second cooldown between attacks
        return BouncingWave(wave_x, wave_y, direction, speed, 15000, 15000 + WIDTH, self.shockwave_image)
    
    #def signal_attack_tell(self):
        #"""Start the glow animation as a signal to player that attack is coming."""
        #self.attack_tell_timer = self.glow_duration
    
    def draw(self, screen, camera):
        """Draw the BoomBox and its button."""
        # Draw the speaker
        screen.blit(self.image, camera.apply(self.rect))
        
        # Draw the button (circle)
        
        button_rect = pygame.Rect(self.button_x - self.button_radius, 
                                 self.button_y - self.button_radius, 
                                 self.button_radius * 2, 
                                 self.button_radius * 2)
        button_pos = camera.apply(button_rect)
        
        # Button color based on state
        if self.button_is_glowing:
            pygame.draw.circle(screen, (255, 50, 50), button_pos.center, self.button_radius)
            pygame.draw.circle(screen, (255, 255, 255), button_pos.center, self.button_radius, 2)

        else:
            pygame.draw.circle(screen, (200, 100, 100), button_pos.center, self.button_radius)
            pygame.draw.circle(screen, (255, 255, 255), button_pos.center, self.button_radius, 2)
            button_color = (200, 100, 100)  # Red normally
        
        # Draw health indicator on button
        #if self.button_health > 0:
            #health_text = pygame.font.Font(None, 24).render(str(self.button_health), True, (255, 255, 255))
            #screen.blit(health_text, (button_screen_pos.centerx - 6, button_screen_pos.centery - 12))

class Shadow(Hazard):
    def __init__(self, start_pos=(0, 0)):
        self.start_pos = start_pos
        try:
            self.sprite_sheet = pygame.image.load('shadow_Sheet.png').convert_alpha()
            self.idle_frame = get_image(self.sprite_sheet, 0, 16, 16, SCALE)
        except pygame.error:
            self.idle_frame = pygame.Surface((16 * SCALE, 16 * SCALE), pygame.SRCALPHA)
            self.idle_frame.fill((20, 20, 20, 180))

        self.image = self.idle_frame
        self.rect = self.image.get_rect(topleft=start_pos)
        self.vel_x = 0
        self.vel_y = 0
        self.ACCEL = 0.3
        self.MAX_SPEED = 0.1
        self.FRICTION = 0.85

    def update(self, player):
        global boss_triggered
        # Don't follow player during boss fights
        if boss_triggered:
            return
            
        # Follow player's position with a delay
        if len(player.position_history) >= player.history_length:
            target_x, target_y = player.position_history[0]  # Oldest position
        else:
            # If not enough history, follow current position
            target_x, target_y = player.rect.centerx, player.rect.centery
        
        # Calculate where the target is relative to the shadow.
        dx = target_x - self.rect.centerx
        dy = target_y - self.rect.centery
        
        # Move toward the target smoothly
        if abs(dx) > 4:
            self.vel_x += self.ACCEL if dx > 0 else -self.ACCEL
        else:
            self.vel_x *= self.FRICTION

        if abs(dy) > 4:
            self.vel_y += self.ACCEL if dy > 0 else -self.ACCEL
        else:
            self.vel_y *= self.FRICTION

        if abs(self.vel_x) > self.MAX_SPEED:
            self.vel_x = self.MAX_SPEED if self.vel_x > 0 else -self.MAX_SPEED
        if abs(self.vel_y) > self.MAX_SPEED:
            self.vel_y = self.MAX_SPEED if self.vel_y > 0 else -self.MAX_SPEED

        self.rect.x += self.vel_x
        self.rect.y += self.vel_y

        # Flip the shadow sprite depending on direction.
        if self.vel_x < 0:
            self.image = pygame.transform.flip(self.idle_frame, True, False)
        else:
            self.image = self.idle_frame

    def on_hit(self, player):
        player.take_damage(player.max_health)

    def reset(self, player):
        self.rect.topleft = (player.rect.x - 250, player.rect.y)
        self.vel_x = 0
        self.vel_y = 0

class Spike(Hazard):
    def __init__(self, pos, size=(TILE_SIZE, TILE_SIZE // 2), damage=1):
        self.image = pygame.Surface(size)
        self.image.fill((220, 20, 20))
        self.rect = self.image.get_rect(topleft=pos)
        self.damage = damage

    def update(self, player):
        pass

    def on_hit(self, player):
        player.take_damage(self.damage)

class DJOserBoss:
    def __init__(self, x, y, image, font):
        if image and image.get_width() > 0:
            self.image = image
        else:
            self.image = pygame.Surface((TILE_SIZE * 2, TILE_SIZE * 2))
            self.image.fill((255, 100, 255))  # Magenta for visibility
            pygame.draw.circle(self.image, (255, 255, 0), (TILE_SIZE, TILE_SIZE), TILE_SIZE)  # Yellow circle
        
        self.rect = self.image.get_rect(topleft=(x, y))
        self.base_y = 650 
        self.rect.y = self.base_y
        self.x = x
        self.y = y
        self.vel_x = 0
        self.vel_y = 0
        self.font = font
        self.frames = get_simple_frames("DJ Oser.png", 2, 64, 64, 4) # Adjust size
        self.anim_index = 0
        self.anim_timer = 0

        self.hp = 3
        self.max_hp = 3
        self.state = "INTRO"  # INTRO -> FIGHT -> DAZED -> BONKED
        self.timer = 0
        self.float_offset = 0  # Hovering effect
        self.float_speed = 0.05
        
        # Attack management
        self.current_attack = None
        self.attack_timer = 0
        self.attack_cooldown = 0
        
    def take_damage(self, amount=1):
        """Reduce HP and return True if defeated."""
        self.hp -= amount
        return self.hp <= 0
    
    def update(self, player_rect):
        if hasattr(self, 'is_launched') and self.is_launched:
            target_x = 20000 # Way off to the right
            move_speed = 60  # Super fast!
            self.rect.y -= 15 # Fly upward at an angle
        else:
            move_speed = 5
        
        if self.vel_x != 0:
            self.rect.x += self.vel_x
            self.rect.y += self.vel_y
            self.vel_y += 1.5
            return
        if hasattr(self, 'is_dazed') and self.is_dazed:
            self.rect.y = self.base_y + math.sin(self.timer) * 15 # Just hover gently
            return
        self.timer += 0.05
        self.attack_timer += 1
            #Idle
        if self.attack_timer < 300: 
            target_x = 15000 + 500 
            self.rect.y = self.base_y + math.sin(self.timer) * 15
            #Hunt
        elif 300 <= self.attack_timer < 420:
            target_x = player_rect.centerx
            self.rect.y = self.base_y - 100 
            #Slam
        elif 420 <= self.attack_timer < 450:
            target_x = self.rect.centerx 
            self.rect.y += 25
            if self.rect.y >= 700:
                self.rect.y = 700
                self.hit_ground = True
        else:
            self.hit_ground = False
            target_x = 15000 + 600
            if self.rect.y > self.base_y: self.rect.y -= 5
            if self.attack_timer > 550: self.attack_timer = 0 # Reset cycle

       
        if self.rect.centerx < target_x: 
            self.rect.x += move_speed
        elif self.rect.centerx > target_x: 
            self.rect.x -= move_speed

        if hasattr(self, 'chat_timer') and self.chat_timer > 0:
            self.chat_timer -= 1
        else:
            self.current_chat = ""

    def say(self, text, duration=180):
        self.current_chat = text
        self.chat_timer = duration
    def can_attack(self):
        """Check if boss is ready to perform an attack."""
        return self.state == "FIGHT" and self.attack_cooldown == 0
    
    def start_attack(self):
        """Begin a new attack sequence."""
        self.attack_cooldown = 120  # 2 seconds between attacks
    
    def draw(self, screen, camera):
        """Draw the boss with hovering effect."""
        pos = camera.apply(self.rect)

        self.anim_timer += 1
        if self.anim_timer % 15 == 0:
            self.anim_index = (self.anim_index + 1) % len(self.frames)
        
        current_img = self.frames[self.anim_index]
        screen.blit(current_img, camera.apply(self.rect))
        #chat_surf = self.font.render(self.current_chat, True, (255, 255, 255))
        #chat_pos = camera.apply(self.rect)
        #screen.blit(chat_surf, (chat_pos.centerx - chat_surf.get_width()//2, chat_pos.top - 40))
        # Draw HP indicator (optional)
        if self.state == "FIGHT":
            hp_text = pygame.font.Font(None, 32).render(f"Mo HP: {self.hp}/{self.max_hp}", True, (255, 100, 100))
            screen.blit(hp_text, (WIDTH - 250, 20))

class BossManager:
    global active_dialogue
    """Manages the entire boss fight, including BoomBoxes, waves, and state transitions."""
    def __init__(self, boss, boombox_image, shockwave_image, font):
        self.trail_particles = []

        self.boss = boss
        self.font = font
        self.state = "INTRO"  # INTRO -> FALLING_IN -> FIGHTING -> CLEANUP -> BONK
        self.timer = 0
        self.battle_dialogue = None
        self.said_hint_line = False

        self.moistar_x = 14000  # Start far off-screen to the left
        self.moistar_y = 850
        self.moistar_speed = 45 # Mach speed
        self.moistar_img = moistar_charge_img
        self.donut_img = donut_img
        self.donut_y = -100
        self.donut_visible = False
        self.cleanup_phase = "RANT"
        self.shake_duration = 0

        self.sheet_img = pygame.image.load("Melody1.png").convert_alpha()
        self.sheet_img = pygame.transform.scale(self.sheet_img, (48, 48)) 
        self.sheet_x = self.boss.rect.centerx
        self.sheet_y = -100
        self.sheet_x = 15000 + 600
        self.sheet_visible = False
        self.vio_claiming_sheet = False
        self.violin_started = False
        self.memory_initialized = False
        # BoomBox management
        full_sheet = pygame.image.load("boomBox.png").convert_alpha()
        
        sheet_width, sheet_height = full_sheet.get_size()
        if sheet_width >= 128 and sheet_height >= 128:
            left_img = full_sheet.subsurface(pygame.Rect(0, 0, 64, 128))
            right_img = full_sheet.subsurface(pygame.Rect(64, 0, 64, 128))
        else:
            # Fallback: create colored rectangles if image is too small
            left_img = pygame.Surface((64, 128), pygame.SRCALPHA)
            left_img.fill((255, 0, 0, 128))  # Semi-transparent red
            right_img = pygame.Surface((64, 128), pygame.SRCALPHA)
            right_img.fill((0, 255, 0, 128))  # Semi-transparent green

        self.left_box = BoomBox(15000 + 50, 700, "left", left_img, shockwave_image)
        self.right_box = BoomBox(15000 + 1050, 700, "right", right_img, shockwave_image)
        self.boomboxes = [self.left_box, self.right_box]
        
        # Wave management
        self.waves = []
        self.vertical_waves = []
        self.shockwave_image = shockwave_image
        
        # Screen shake
        self.shake_duration = 0
        self.shake_intensity = 0
        
    def transition_to_falling(self):
        
        self.state = "FALLING_IN"
        self.left_box.start_falling()
        self.right_box.start_falling()
    
    def transition_to_fighting(self):
        """Move from falling in animation to actual combat."""
        self.state = "FIGHTING"
        self.boss.state = "FIGHT"
        self.timer = 0
    
    def trigger_screen_shake(self, intensity=5, duration=15):
        self.shake_duration = duration
        self.shake_intensity = intensity
    
    #def perform_boss_attack(self, attack_type="wave"):
        #"""Execute an attack pattern - signal tell and prepare waves."""
        #if attack_type == "wave":
            # Have both BoomBoxes signal attack tell (glow) BEFORE firing
            #if self.left_box.can_attack() and not self.left_box.button_is_glowing:
                #self.left_box.signal_attack_tell()
            
            #if self.right_box.can_attack() and not self.right_box.button_is_glowing:
                #self.right_box.signal_attack_tell()
    
    def check_wave_player_collision(self, player):
        for wave in self.waves[:]:
            if wave.rect.right < player.rect.left - TILE_SIZE * 4 or wave.rect.left > player.rect.right + TILE_SIZE * 4 or wave.rect.bottom < player.rect.top - TILE_SIZE * 4 or wave.rect.top > player.rect.bottom + TILE_SIZE * 4:
                continue
            if wave.rect.colliderect(player.rect):
                player.take_damage(1)
                #self.waves.remove(wave)
                break
    
    #def check_all_boxes_destroyed(self):
        #"""Return True if both BoomBoxes are destroyed."""
        #return all(box.button_health <= 0 for box in self.boomboxes)
    
    def spawn_vertical_rain(self):
        start_x = 15100
        end_x = 16100
        gap_size = 200
    
        safe_zone_x = random.randint(start_x, end_x - gap_size)
 
        for x in range(start_x, end_x, 120):
  
            if x > safe_zone_x and x < safe_zone_x + gap_size:
                continue
                
            v_wave = VerticalShockwave(x, -100, self.shockwave_image, "down")
            v_wave.active = True
            #v_wave.max_speed = 12 
            self.vertical_waves.append(v_wave)
                #if not hasattr(self, 'talked_once'):
                    #self.boss.say("Feel the might of DJ Oser!")
                    #self.talked_once = True
                #if self.talked_once and not hasattr(self, 'talked_twice'):
                    #self.boss.say("Sure hope you don't dash into the glowing self-destruct buttons.")
                    #self.talked_twice = True
    def update(self, player, keys):
        global boss_finished
        # Update active dialogue
        if self.battle_dialogue:
            self.battle_dialogue.update(keys)
            if self.battle_dialogue.finished:
                self.battle_dialogue = None
        
        # 1. Update Boss (Pass player to handle the Slam Attack!)
        if self.state in ["FALLING_IN", "FIGHTING", "CLEANUP", "BONK_FINISHED", "FINISHED"]:
            old_y = self.boss.rect.y
            self.boss.update(player.rect)
            new_y = self.boss.rect.y
            for box in self.boomboxes:
                box.is_active = True

            if self.state == "FIGHTING":
            
                if not self.said_hint_line:
                    self.battle_dialogue = DialogueBox(
                        self.font, 
                        ["(Sure hope this guy doesn't dash into the \nglowing self-destruct buttons.)"], 
                        speaker_name="DJ Oser", 
                        autoplay=True, 
                        has_background = False,
                        is_passive=True
                    )
                    self.said_hint_line = True
                #if self.battle_dialogue:
                    #self.battle_dialogue.update(keys)
                    #if self.battle_dialogue.finished:
                        #self.battle_dialogue = None

                        
            # Trigger shake if Boss hits ground during slam
                if old_y < 700 and new_y >= 700:
                    self.trigger_screen_shake(10, 15)
                    
                    if random.random() > 0.5:
                        # Spawn the ground waves
                        l_wave = BouncingWave(self.boss.rect.centerx, 740, -1, 12, 15000, 16200, self.shockwave_image)
                        r_wave = BouncingWave(self.boss.rect.centerx, 740, 1, 12, 15000, 16200, self.shockwave_image)
                        l_wave.bounces = 2 # Die faster
                        r_wave.bounces = 2
                        self.waves.extend([l_wave, r_wave])
                        self.boss.hit_ground = False 
                    else:
                    
                        self.spawn_vertical_rain()
            
            # 2. Update BoomBoxes & Collect Waves

            if 300 <= self.boss.attack_timer < 550:
                for box in self.boomboxes:
                    box.can_fire = False
                if 520 == self.boss.attack_timer:
                    for wave in self.waves[:]:
                        self.waves.remove(wave) # Create this variable in BoomBox
            else:
                for box in self.boomboxes:
                    box.can_fire = True
            
            for box in self.boomboxes:
                new_wave = box.update(player.rect)
                if self.state == "FIGHTING" and new_wave:
                    self.waves.append(new_wave)
            
            # 3. Update Bouncing Waves
            for wave in self.waves[:]:
                if wave.update(): # Wave returns True when done bouncing
                    self.waves.remove(wave)
            for v_wave in self.vertical_waves[:]:
                v_wave.update(player.rect)
                if v_wave.rect.y > 800: # Remove when off-screen
                    self.vertical_waves.remove(v_wave)
            for v_wave in self.vertical_waves:
                if v_wave.rect.colliderect(player.rect):
                    player.take_damage(1)
                    #self.vertical_waves.remove(v_wave)
                    break
        # 4. Handle State Transitions
        if self.state == "FALLING_IN":
            if self.left_box.y >= self.left_box.ground_y:
                self.trigger_screen_shake(10, 20)
                self.state = "FIGHTING"
        
        elif self.state == "FIGHTING":
            if all(box.button_health <= 0 for box in self.boomboxes):
                self.state = "CLEANUP"
                self.boss.is_dazed = True
                self.timer = 0

        elif self.state == "CLEANUP":
            self.timer += 1
            if self.cleanup_phase == "RANT":
                player.can_move = False
                if not hasattr(self, 'rant_started'):
                    self.battle_dialogue = DialogueBox(self.font, 
                        ["Not cool, man! You may have destroyed my speakers, \nbut the fight's just getting--"], 
                        "DJ Oser", autoplay=True, auto_delay =40, is_passive=False)
                    self.current_scene_text = self.battle_dialogue
                    self.rant_started = True
                if hasattr(self, 'rant_started') and self.current_scene_text.finished:
                        self.cleanup_phase = "DONUT_FALL"
                        self.donut_visible = True
                        self.timer = 0
            elif self.cleanup_phase == "DONUT_FALL":
                if self.donut_y < self.boss.rect.top+100:
                    self.donut_y += 8
                    self.timer = 0 
                else:
                    # Donut is in hand!
                    if self.timer > 60:
                        if not hasattr(self, 'donut_dialogue_started'):
                                self.battle_dialogue = DialogueBox(self.font, 
                                    ["Huh? What the... a donut?"], 
                                    "DJ Oser", autoplay=True, auto_delay = 40, is_passive=False)
                                self.current_scene_text = self.battle_dialogue
                                self.donut_dialogue_started = True
                                self.timer = 0
                        if hasattr(self, 'donut_dialogue_started') and self.current_scene_text.finished:
                            if self.battle_dialogue is None:
                                self.cleanup_phase = "SHOCK"
                                self.timer = 0
                        

            elif self.cleanup_phase == "SHOCK":
                if not hasattr(self, 'shock_triggered'):
                    # Trigger the "MY DONUT" dialogue
                    self.battle_dialogue = DialogueBox(self.font, ["MY DONUT!!!!!!!!!!"], "Moistar", has_background=True, autoplay=True, is_passive=False)
                    self.shock_triggered = True
                if self.shock_triggered and self.battle_dialogue is None:
                    self.cleanup_phase = "BONK"
                    self.donut_visible = True

            elif self.cleanup_phase == "BONK":
                if self.moistar_x < self.boss.rect.centerx:
                    self.moistar_x += self.moistar_speed
                    self.trail_particles.append([self.moistar_x - 20, self.moistar_y + random.randint(-20, 20), random.randint(4, 8), 255])
                
                    
                if self.moistar_x >= self.boss.rect.centerx:
                    self.trigger_screen_shake(30, 40)
                    self.boss.is_launched = True 
                    self.boss.vel_x = 50 
                    self.boss.vel_y = -30
                    self.state = "BONK" 
                    self.sheet_visible = True
                if self.state == "BONK_FINISHED" and self.battle_dialogue is None:
                    # Trigger the very last cutscene
                    #self.battle_dialogue = DialogueBox(self.font, [
                        #"@Moistar: Mo! You big dummy!| What were you thinking?!",
                        #"Mo: ...|Moistar?| Is that you?",
                    #], "Moistar")
                    self.state ="FINISHED"
                #if self.state == "FINISHED":
                    
                    #self.sheet_visible = True
        if self.sheet_visible:
            if self.sheet_y < 700:
                self.sheet_y += 4
                if not self.vio_claiming_sheet:
                    self.sheet_x += math.sin(pygame.time.get_ticks() * 0.004) * 2
            else:
                
                if player.cutscene_target_x is None and not self.vio_claiming_sheet:
                    player.cutscene_target_x = 15000 + 600  
                    self.vio_claiming_sheet = True
                    player.cutscene_speed = 4.0
        
        if self.vio_claiming_sheet and player.cutscene_target_x is None:
            if self.state != "VIOLIN_PERFORMANCE" and not self.violin_started:
                self.state = "VIOLIN_PERFORMANCE"
                self.violin_started = True
                player.is_holding_violin = True
                # Hide player sprite during the memory performance animation
                try:
                    player.visible = False
                except Exception:
                    pass
                self.performance_timer = 0
                Melody1.play()
            if self.state == "VIOLIN_PERFORMANCE":
                self.performance_timer += 1
                if not hasattr(self, 'memory_fade'):
                    self.memory_fade = 0
                if self.performance_timer > 300:
                    self.memory_fade = min(255, self.memory_fade + 5)
                if self.performance_timer > 460:
                    self.state = "MEMORY_START"
        if self.state == "MEMORY_START":
            player.is_holding_violin = False
            if self.memory_initialized == False:
            
                memory_text = [
                    "(You see a girl boarding a train.)",
                    "(A dark door casts a looming presence...)",
                    "(You raise your hand to open the door.)|",
                    "~",
                    " |(You...| stop thinking about it.)"
        
                ]
                self.battle_dialogue = DialogueBox(self.font, memory_text, is_passive=False)
                self.current_scene_text = self.battle_dialogue
                self.memory_initialized = True
                player.cutscene_target_x = None  # Stop any cutscene movement
                # player.can_move = False  # Handled by cutscene_mode
                return
                #if self.battle_dialogue:
                 #   if "~" in self.battle_dialogue.text_list[self.battle_dialogue.current_sentence]:
                  #      self.is_glitching
            # 2. Check if the memory dialogue is done to return to the arena
            
            if hasattr(self, 'current_scene_text') and self.current_scene_text and self.current_scene_text.finished and self.memory_initialized == True:
                self.state = "MEMORY_END"
                
        elif self.state == "MEMORY_END":
            if not hasattr(self, 'memory_fade'):
                self.memory_fade = 0
            if self.memory_fade > 0:
                self.memory_fade = max(0, self.memory_fade - 5)
            elif not getattr(self, 'post_battle_started', False):
                self.state = "POST_BATTLE_THOUGHTS"
                self.post_battle_started = True
                player.cutscene_target_x = None  
                player.vel_x = 0  
                player.is_dashing = False  
                player.is_jumping = False 
                self.battle_dialogue = DialogueBox(self.font, [
                    "@Captain Vio_Down:.....",
                    "Why....*Why must it continue to haunt me?*\n"
                    "...No. Just continue to the next one. I have to.| \n"
                    "There's no other choice...|right?",
                ], is_passive=False)
                self.current_scene_text = self.battle_dialogue
                # player.can_move = False  # Handled by cutscene_mode

        elif self.state == "POST_BATTLE_THOUGHTS":
            if self.battle_dialogue is None and not getattr(self, 'post_battle_finished', False):
                self.state = "FINISHED"
                boss_finished = True
                self.post_battle_finished = True
                player.can_move = True
                player.cutscene_target_x = None  
                player.vel_x = 0  
                player.is_dashing = False  
                player.is_jumping = False  
                self.memory_fade = 0  # Reset fade to prevent black screen
                #self.vio_claiming_sheet = False  # Reset to prevent retriggering
                self.sheet_visible = False
                player.is_holding_violin = False
                # Restore player visibility after performance
                try:
                    player.visible = True
                except Exception:
                    pass
                
        self.shake_duration = max(0, self.shake_duration - 1)
        for p in self.trail_particles[:]:
                p[0] -= 5      # Move particles left slightly
                p[3] -= 15     # Fade out
                if p[3] <= 0:
                    self.trail_particles.remove(p)
        #print(f"Current State: {self.state} | Dialogue: {self.battle_dialogue}")
    def draw(self, screen, camera):
        
        # Draw BoomBoxes (only if they have health)
        for box in self.boomboxes:
             if box.is_active:
                if box.button_health > 0:
                    box.draw(screen, camera)
        
        # Draw waves
        for wave in self.waves:
            wave.draw(screen, camera, self.shockwave_image)
        for v_wave in self.vertical_waves:
                v_wave.draw(screen, camera)
        # Draw boss
        self.boss.draw(screen, camera)
        if self.donut_visible:
            donut_rect = self.donut_img.get_rect(center=(self.boss.rect.centerx, self.donut_y))
            screen.blit(self.donut_img, camera.apply(donut_rect))

        if self.cleanup_phase == "BONK":
            for p in self.trail_particles:
                star_surf = pygame.Surface((p[2], p[2]))
                star_surf.fill((255, 255, 200)) 
                star_surf.set_alpha(p[3]) 
                
                pos = camera.apply(pygame.Rect(p[0], p[1], p[2], p[2]))
                screen.blit(star_surf, pos)
            ms_rect = self.moistar_img.get_rect(center=(self.moistar_x, self.moistar_y))
            screen.blit(self.moistar_img, camera.apply(ms_rect)) 
        if self.sheet_visible:
            sheet_rect = self.sheet_img.get_rect(center=(self.sheet_x, self.sheet_y))
            screen.blit(self.sheet_img, camera.apply(sheet_rect))

class KiraBossManager:
    def __init__(self, font, arena_origin=(15000, 0), boss_offset=None, arena_size=(WIDTH, HEIGHT), vulnerable_y_offset=300):
        self.font = font
        self.hp = 3  # She takes 3 'major' hits to the shield
        self.state = "SHIELDED"
        self.shield_up = True  # Becomes False when two external lever objects are triggered
        
        self.timer = 0
        self.attack_timer = 0

        self.current_attack = "IDLE"
        #self.state = "INTRO"
        self.font = font
        
        # Arena position data
        self.arena_origin = pygame.Vector2(arena_origin)
        self.arena_width = int(arena_size[0])
        self.arena_height = int(arena_size[1])
        self.boss_offset = pygame.Vector2(boss_offset) if boss_offset is not None else None
        self.vulnerable_offset = pygame.Vector2(0, vulnerable_y_offset)

        # Idle animation
        frame_width = kira_img.get_width() // 2
        frame_height = kira_img.get_height()
        self.kira_frames = []
        for i in range(2):
            frame = kira_img.subsurface(pygame.Rect(i * frame_width, 0, frame_width, frame_height)).copy()
            frame = pygame.transform.scale(frame, (TILE_SIZE * 3, TILE_SIZE * 3))
            self.kira_frames.append(frame)
        self.kira_frame_index = 0
        self.kira_frame_timer = 0
        self.kira_frame_durations = [40, 10]

        # Laser variables
        self.laser_state = None  # "TRACKING", "LOCKED", "FIRING"
        self.laser_type = None  # "H", "V", or "BOTH"
        self.laser_types = []
        self.laser_positions = []
        self.laser_target = pygame.Vector2(0, 0)
        self.laser_alpha = 0
        self.laser_timer = 0
        self.warning_rects = []
        self.laser_shake_timer = 0

        # Laser timing values (frames at 60fps). Change these values to tune attack pacing.
        self.laser_timing = {
            "normal": {"TRACKING": 10, "LOCKED": 75, "FIRING": 30},
            "encore": {"TRACKING": 35, "LOCKED": 60, "FIRING": 30},
        }
        self.laser_grid_segments = 6
        self.boss_wave_ground_offset = TILE_SIZE * 2 + 408
        self.boss_wave_spawn_x_offset = TILE_SIZE * 4
        
        # Vulnerable descent tracking
        self.vulnerable_timer = 0
        self.battle_dialogue = None
        self.fall_velocity = 0
        self.defeat_y = self.arena_height - (TILE_SIZE * 2) - 400

        # Lever and damage tracking
        self.active_levers = 0
        self.hurt_timer = 0
        self.defeat_timer = 0  # Timer before defeat dialogue appears
        self.defeat_dialogue_triggered = False

        # Boss sprite dimensions
        kira_frame = self.kira_frames[0]
        self.kira_width = kira_frame.get_width()
        self.kira_height = kira_frame.get_height()
        if self.boss_offset is None:
            self.boss_offset = pygame.Vector2(
                (self.arena_width - self.kira_width) / 2,
                (self.arena_height - self.kira_height) / 2
            )
        self.kira_frames_flipped = [pygame.transform.flip(frame, True, False) for frame in self.kira_frames]

    def get_kira_rect(self):
        boss_pos = self.arena_origin + self.boss_offset
        if self.state == "VULNERABLE":
            boss_pos = boss_pos + self.vulnerable_offset
        return pygame.Rect(boss_pos.x, boss_pos.y, self.kira_width, self.kira_height)

    def spawn_boss_wave(self, boss_x, boss_y, player_rect):
        """Spawn a boss-managed shockwave from the ground at the edge of the arena."""
        direction = 1 if player_rect.centerx > boss_x else -1
        if direction == 1:
            spawn_x = self.arena_origin.x - self.boss_wave_spawn_x_offset
        else:
            spawn_x = self.arena_origin.x + self.arena_width + self.boss_wave_spawn_x_offset
        spawn_y = self.arena_origin.y + self.arena_height - self.boss_wave_ground_offset
        new_wave = Shockwave(spawn_x, spawn_y, boss_neon_wave_img, direction=direction, boss_managed=True)
        tiles.append(new_wave)

    def clear_boss_weapons(self):
        """Remove active boss lasers and boss-managed waves from the arena."""
        global tiles
        tiles[:] = [tile for tile in tiles if not getattr(tile, 'boss_managed', False)]
        self.current_attack = "IDLE"
        self.laser_state = None
        self.laser_types = []
        self.laser_positions = []
        self.warning_rects = []
        self.laser_timer = 0
        self.attack_timer = 0

    def check_player_damage(self, player, npcs_list):
        """Check if player dashes into Kira while vulnerable and apply damage"""
        if self.state == "VULNERABLE" and not self.shield_up:
            kira_rect = self.get_kira_rect()
            if player.is_dashing and player.rect.colliderect(kira_rect) and self.hurt_timer <= 0:
                self.hp -= 1
                self.hurt_timer = 30
                self.shield_up = True
                self.vulnerable_timer = 0
                self.reset_levers(npcs_list)
                self.active_levers = 0
                if self.hp <= 0:
                    self.state = "DEFEATED"
                    self.clear_boss_weapons()
                    self.fall_velocity = 0
                    self.defeat_timer = 30  # Wait 30 frames (~0.5 seconds) before showing dialogue
                else:
                    self.state = "ENCORE" if self.hp <= 1 else "SHIELDED"

    def _update_warning_rects(self):
        self.warning_rects = []
        grid_width = self.arena_width // self.laser_grid_segments
        grid_height = self.arena_height // self.laser_grid_segments
        if self.state == "ENCORE" and self.laser_positions:
            for laser_type, grid_index in self.laser_positions:
                grid_index = int(max(0, min(self.laser_grid_segments - 1, grid_index)))
                if laser_type == "V":
                    grid_x = self.arena_origin.x + grid_index * grid_width
                    self.warning_rects.append(pygame.Rect(grid_x, self.arena_origin.y, grid_width, self.arena_height))
                else:
                    grid_y = self.arena_origin.y + grid_index * grid_height
                    self.warning_rects.append(pygame.Rect(self.arena_origin.x, grid_y, self.arena_width, grid_height))
        else:
            for laser_type in self.laser_types:
                if laser_type == "V":
                    relative_x = self.laser_target.x - self.arena_origin.x
                    grid_index = int(max(0, min(self.laser_grid_segments - 1, relative_x // grid_width)))
                    grid_x = self.arena_origin.x + grid_index * grid_width
                    self.warning_rects.append(pygame.Rect(grid_x, self.arena_origin.y, grid_width, self.arena_height))
                else:
                    relative_y = self.laser_target.y - self.arena_origin.y
                    grid_index = int(max(0, min(self.laser_grid_segments - 1, relative_y // grid_height)))
                    grid_y = self.arena_origin.y + grid_index * grid_height
                    self.warning_rects.append(pygame.Rect(self.arena_origin.x, grid_y, self.arena_width, grid_height))

    def _choose_encore_laser_positions(self):
        grid_count = self.laser_grid_segments
        count = random.randint(2, min(4, grid_count))
        segments = random.sample(list(range(grid_count)), k=count)
        positions = []
        for segment in segments:
            laser_type = random.choice(["H", "V"])
            positions.append((laser_type, segment))
        return positions

    def handle_spotlight_laser(self, player_rect, player):
        """Manage the spotlight laser attack: Track -> Lock -> Fire"""
        if self.laser_state == "TRACKING":
            if self.state != "ENCORE":
                if "V" in self.laser_types:
                    self.laser_target.x = player_rect.centerx
                if "H" in self.laser_types:
                    self.laser_target.y = player_rect.centery
            self.laser_alpha = 30 + math.sin(pygame.time.get_ticks() * 0.01) * 20  # Low transparency, hard to see
            self._update_warning_rects()
            self.laser_timer += 1
            tracking_duration = self.laser_timing["encore" if self.state == "ENCORE" else "normal"]["TRACKING"]
            if self.laser_timer >= tracking_duration:
                self.laser_state = "LOCKED"
                self.laser_timer = 0

        elif self.laser_state == "LOCKED":
            self.laser_alpha = 80
            self._update_warning_rects()
            self.laser_timer += 1
            locked_duration = self.laser_timing["encore" if self.state == "ENCORE" else "normal"]["LOCKED"]
            if self.laser_timer >= locked_duration:
                self.laser_state = "FIRING"
                self.laser_timer = 0
                self.laser_shake_timer = 10
                grid_width = self.arena_width // self.laser_grid_segments
                grid_height = self.arena_height // self.laser_grid_segments
                if self.state == "ENCORE" and self.laser_positions:
                    for laser_type, grid_index in self.laser_positions:
                        if laser_type == "V":
                            grid_x = self.arena_origin.x + grid_index * grid_width
                            laser = NeonLaserTile(pygame.Rect(grid_x, self.arena_origin.y, grid_width, self.arena_height), 'V', boss_managed=True)
                        else:
                            grid_y = self.arena_origin.y + grid_index * grid_height
                            laser = NeonLaserTile(pygame.Rect(self.arena_origin.x, grid_y, self.arena_width, grid_height), 'H', boss_managed=True)
                        laser.active = True
                        laser.alpha = 255
                        laser.timer = 0
                        tiles.append(laser)
                else:
                    for laser_type in self.laser_types:
                        if laser_type == "V":
                            relative_x = self.laser_target.x - self.arena_origin.x
                            grid_index = int(max(0, min(self.laser_grid_segments - 1, relative_x // grid_width)))
                            grid_x = self.arena_origin.x + grid_index * grid_width
                            laser = NeonLaserTile(pygame.Rect(grid_x, self.arena_origin.y, grid_width, self.arena_height), 'V', boss_managed=True)
                        else:
                            relative_y = self.laser_target.y - self.arena_origin.y
                            grid_index = int(max(0, min(self.laser_grid_segments - 1, relative_y // grid_height)))
                            grid_y = self.arena_origin.y + grid_index * grid_height
                            laser = NeonLaserTile(pygame.Rect(self.arena_origin.x, grid_y, self.arena_width, grid_height), 'H', boss_managed=True)
                        laser.active = True
                        laser.alpha = 255
                        laser.timer = 0
                        tiles.append(laser)

        elif self.laser_state == "FIRING":
            self.laser_timer += 1
            laser_blast.play()
            firing_duration = self.laser_timing["encore" if self.state == "ENCORE" else "normal"]["FIRING"]
            if self.laser_timer >= firing_duration:
                self.clear_boss_weapons()
                self.laser_state = None
                self.current_attack = "IDLE"
                self.attack_timer = 0

    def handle_lasers(self, Vio_rect):
        """Legacy method for compatibility - delegates to handle_spotlight_laser"""
        if self.laser_state is not None:
            self.handle_spotlight_laser(Vio_rect, Vio)
    
    def check_lever_collisions(self, npcs_list, player):
        """Check if player is dashing into levers and activate them"""
        # Reset active lever count
        self.active_levers = 0
        
        # Check all NPCs for levers
        for npc in npcs_list:
            if npc.name == "Lever":
                # If the NPC doesn't have an active property, initialize it
                if not hasattr(npc, 'active'):
                    npc.active = False
                
                # Check if player is dashing and collides with this lever
                if player.is_dashing and player.rect.colliderect(npc.rect):
                    npc.active = True
                
                # Count active levers
                if npc.active:
                    self.active_levers += 1
        
        # If 2 levers are active, set boss to vulnerable
        if self.active_levers >= 2 and self.state not in ["VULNERABLE", "DEFEATED", "DEFEATED_GROUNDED"]:
            self.shield_up = False
            self.state = "VULNERABLE"
            self.clear_boss_weapons()

    def reset_levers(self, npcs_list):
        """Reset all lever states after boss is hit"""
        for npc in npcs_list:
            if npc.name == "Lever":
                npc.active = False
        self.active_levers = 0

    def update(self, player, active_neon_color, npcs_list=None):
        global dialogue_start_timer
        if self.battle_dialogue and self.battle_dialogue.finished:
            self.battle_dialogue = None

        self.timer += 1
        self.attack_timer += 1
        
        if self.hurt_timer > 0:
            self.hurt_timer -= 1
        
        # Enter Encore phase on low HP, but preserve VULNERABLE or defeat state if currently down.
        if self.hp <= 1 and self.state not in ["ENCORE", "VULNERABLE", "DEFEATED", "DEFEATED_GROUNDED"]:
            self.state = "ENCORE"
            self.shield_up = True
            self.vulnerable_timer = 0

        if self.state == "SHIELDED":
            if not self.shield_up:
                # Shield is down - transition to VULNERABLE
                self.state = "VULNERABLE"
        
        if self.state == "VULNERABLE":
            if self.vulnerable_timer == 0:
                self.vulnerable_timer = 300
                self.battle_dialogue = DialogueBox(
                    self.font,
                    ["@Captain Vio: Now she's down, I can dash into her shield."],
                    speaker_name="Captain Vio",
                    is_passive=True
                )
            else:
                self.vulnerable_timer -= 1
                if self.vulnerable_timer <= 0:
                    self.shield_up = True
                    self.reset_levers(npcs_list if npcs_list is not None else [])
                    self.active_levers = 0
                    self.vulnerable_timer = 0
                    self.state = "ENCORE" if self.hp <= 1 else "SHIELDED"

        # Run attacks when shielded or in encore, and continue any in-progress spotlight laser even during VULNERABLE
        if self.state in ["SHIELDED", "ENCORE"] or (self.current_attack == "SPOTLIGHT_LASER" and self.laser_state is not None):
            if self.state == "ENCORE":
                attack_interval = 90
            else:
                attack_interval = 120
            
            if self.current_attack != "SPOTLIGHT_LASER" or self.laser_state is None:
                if self.attack_timer > attack_interval:
                    self.current_attack = random.choice(["SONIC_WAVES", "SPOTLIGHT_LASER"])
                    self.attack_timer = 0

            if self.current_attack == "SONIC_WAVES":
                if self.attack_timer % attack_interval == 0:
                    #print(f"Current State: {self.current_attack}")
                    boss_center = self.arena_origin + self.boss_offset + pygame.Vector2(self.kira_width // 2, self.kira_height // 2)
                    self.spawn_boss_wave(boss_center.x, boss_center.y, player.rect)

            elif self.current_attack == "SPOTLIGHT_LASER":
                if self.laser_state is None and self.state != "VULNERABLE":
                    #print(f"Current State: {self.current_attack}")
                    if self.state == "ENCORE":
                        self.laser_positions = self._choose_encore_laser_positions()
                        self.laser_types = [laser_type for laser_type, _ in self.laser_positions]
                        self.laser_type = "BOTH"
                        self.laser_target = pygame.Vector2(0, 0)
                    else:
                        self.laser_positions = []
                        self.laser_types = [random.choice(["H", "V"])]
                        self.laser_type = self.laser_types[0]
                        self.laser_target = pygame.Vector2(player.rect.centerx, player.rect.centery)
                    self.laser_state = "TRACKING"
                    self.laser_timer = 0
                    self.warning_rects = []
                if self.laser_state is not None:
                    self.handle_spotlight_laser(player.rect, player)

        elif self.state == "HURT":
            pass

        if self.state == "DEFEATED":

            self.fall_velocity += 1.2
            self.boss_offset.y += self.fall_velocity
            if self.boss_offset.y >= self.defeat_y:
                self.boss_offset.y = self.defeat_y
                self.fall_velocity = 0
                self.state = "DEFEATED_GROUNDED"
                global boss2_finished
                boss2_finished = True

        self.kira_frame_timer += 1
        if self.kira_frame_timer >= self.kira_frame_durations[self.kira_frame_index]:
            self.kira_frame_timer = 0
            self.kira_frame_index = (self.kira_frame_index + 1) % len(self.kira_frames)

        if self.laser_shake_timer > 0:
            self.laser_shake_timer -= 1
            camera.shake_x = random.randint(-3, 3)
            camera.shake_y = random.randint(-3, 3)
        else:
            camera.shake_x = 0
            camera.shake_y = 0

    def set_shield_down(self):
        """Called when both lever objects are triggered"""
        self.shield_up = False

    def draw(self, screen, camera, player=None):
        """Draw Kira, her shield, and any visual effects"""
        if self.laser_state in ["TRACKING", "LOCKED"] and self.warning_rects:
            for warning_rect, laser_type in zip(self.warning_rects, self.laser_types):
                if laser_type == "H":
                    warning_img = pygame.transform.scale(neon_laser_h_img, (warning_rect.width, warning_rect.height))
                else:
                    warning_img = pygame.transform.scale(neon_laser_img, (warning_rect.width, warning_rect.height))
                warning_alpha = min(150, max(80, int(self.laser_alpha)))
                warning_img.set_alpha(warning_alpha)
                screen.blit(warning_img, camera.apply(warning_rect))

        kira_rect = self.get_kira_rect()
        flip_left = False
        if player is not None:
            flip_left = player.rect.centerx < kira_rect.centerx
        current_frame = self.kira_frames_flipped[self.kira_frame_index] if flip_left else self.kira_frames[self.kira_frame_index]
        screen.blit(current_frame, camera.apply(kira_rect))

        if self.shield_up and self.state not in ["DEFEATED", "DEFEATED_GROUNDED"]:
            shield_surface = pygame.Surface((kira_rect.width + 24, kira_rect.height + 24), pygame.SRCALPHA)
            pygame.draw.ellipse(shield_surface, (80, 180, 255, 120), shield_surface.get_rect(), 8)
            screen.blit(shield_surface, (camera.apply(kira_rect).x - 12, camera.apply(kira_rect).y - 12))

    def check_wave_player_collision(self, player):
        """Check if player collides with any active shockwave"""
        for tile in tiles:
            if tile.rect.right < player.rect.left - TILE_SIZE * 4 or tile.rect.left > player.rect.right + TILE_SIZE * 4 or tile.rect.bottom < player.rect.top - TILE_SIZE * 4 or tile.rect.top > player.rect.bottom + TILE_SIZE * 4:
                continue
            if isinstance(tile, Shockwave) and tile.active:
                if player.rect.colliderect(tile.rect):
                    player.take_damage(1)
                    tile.active = False

class NPC:
    def __init__(self, x, y, name, dialogue_list, is_item=False, drop_floor=False):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE * 2)
        self.name = name
        self.dialogue_text = dialogue_list 
        self.is_talking = False
        self.is_item = is_item
        self.drop_floor = drop_floor

        self.prompt_timer = 0
        self.talk_cooldown = 0 

        if self.is_item:
            self.knife_image = pygame.image.load("knife.png").convert_alpha()
            self.knife_image = pygame.transform.scale(self.knife_image, (TILE_SIZE, TILE_SIZE))

        self.moistar_image = get_image(pygame.image.load('Moistar.png').convert_alpha(), 0, 35, 35, SCALE)
        self.tv_img = get_image(pygame.image.load('TV.png').convert_alpha(), 0, 80, 60, SCALE)
        if self.name == "Jumbotron":
            self.rect = pygame.Rect(x, y, TILE_SIZE * 4, TILE_SIZE * 6)  
            self.tv_img = pygame.transform.scale(self.tv_img, (TILE_SIZE * 13, TILE_SIZE * 10.8))
            self.kira_portrait1 = pygame.image.load('Kira_Portrait.png').convert_alpha()
            self.kira_portrait1 = pygame.transform.scale(self.kira_portrait1, (TILE_SIZE * 4, TILE_SIZE * 4))
            self.kira_portrait2 = pygame.image.load('Kira_Portrait2.png').convert_alpha()
            self.kira_portrait2 = pygame.transform.scale(self.kira_portrait2, (TILE_SIZE * 4, TILE_SIZE * 4))
            self.portrait_timer = 0
            self.current_portrait = 0
        if self.name == "Lever":
            self.lever_image = pygame.transform.scale(lever_img, (TILE_SIZE, TILE_SIZE * 2))
        if self.name == "Monkey":
            self.monkey_image = pygame.image.load('monkey_npc.png').convert_alpha()
            self.monkey_image = pygame.transform.scale(self.monkey_image, (TILE_SIZE * 2, TILE_SIZE * 3))
            self.rect = self.monkey_image.get_rect(topleft=(x, y))
        if self.name == "Monkey_Dead":
            self.dead_monkey_image = pygame.image.load('monkey_dead_npc.png').convert_alpha()
            self.dead_monkey_image = pygame.transform.scale(self.dead_monkey_image, (TILE_SIZE * 3, TILE_SIZE * 2))
            self.rect = self.dead_monkey_image.get_rect(topleft=(x, y))
    def check_interaction(self, player, confirm_pressed):
        if self.name == "Lever":
            return False
        if self.talk_cooldown > 0:
            self.talk_cooldown -= 1
            return False 

        distance = pygame.math.Vector2(self.rect.center).distance_to(player.center)
        if distance < 80 and confirm_pressed:
            return True

        return False

    def draw_prompt(self, screen, camera, player_rect):
        if self.name == "Lever":
            return
        active_dialogue = False 
        """Draws the floating icon only when near the NPC."""
        dist = pygame.math.Vector2(self.rect.center).distance_to(player_rect.center)
        
        if dist < 80 and not active_dialogue:
            self.prompt_timer += 0.1
            float_y = math.sin(self.prompt_timer) * 5
            
            prompt_pos = camera.apply(self.rect)
            prompt_x = prompt_pos.centerx
            prompt_y = prompt_pos.top - 20 + float_y
            
            pygame.draw.polygon(screen, (255, 255, 255), [
                (prompt_x - 10, prompt_y),
                (prompt_x + 10, prompt_y),
                (prompt_x, prompt_y + 10)
            ])

    def draw(self, screen, camera):

        if self.is_item:
            offset_y = math.sin(pygame.time.get_ticks() * 0.005) * 5 if self.is_item else 0
            screen.blit(self.knife_image, (camera.apply(self.rect).x, camera.apply(self.rect).y + offset_y))
        elif self.name == "Lever":
            screen.blit(self.lever_image, camera.apply(self.rect))
            if hasattr(self, 'active') and self.active:
                glow = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
                glow.fill((0, 255, 0, 80))
                screen.blit(glow, camera.apply(self.rect))
        elif self.name == "Jumbotron":
            tv_pos = camera.apply(self.rect)
            screen.blit(self.tv_img, tv_pos)
           
            self.portrait_timer += 1
            if self.portrait_timer >= 40: 
                self.portrait_timer = 0
                self.current_portrait = 1 - self.current_portrait
            current_portrait = self.kira_portrait1 if self.current_portrait == 0 else self.kira_portrait2
            
            portrait_x = tv_pos.x + 40  
            portrait_y = tv_pos.y + 40
            screen.blit(current_portrait, (portrait_x, portrait_y))
        elif self.name == "Monkey":
            screen.blit(self.monkey_image, camera.apply(self.rect))
        elif self.name == "Monkey_Dead":
            screen.blit(self.dead_monkey_image, camera.apply(self.rect))
        else:
            
            npcs = ["Moistar", "DJ Oser", "???", "Jumbotron", "Knife"]
            if self.name == "Moistar":
                screen.blit(self.moistar_image, camera.apply(self.rect))

class Tile:
    def __init__(self, rect, tile_type='normal', image=None, orientation='up'):
        self.rect = rect
        self.type = tile_type  
        self.image = image
        self.orientation = orientation
        

    def draw(self, screen, camera):
        screen_rect = pygame.Rect(camera.offset_x, camera.offset_y, WIDTH, HEIGHT)
        if self.rect.right < screen_rect.left or self.rect.left > screen_rect.right or self.rect.bottom < screen_rect.top or self.rect.top > screen_rect.bottom:
            return
        if self.image:
            screen.blit(self.image, camera.apply(self.rect))
        else:
            pygame.draw.rect(screen, (100, 100, 100), camera.apply(self.rect))

class ShadowTile(Tile):
    """Invisible shadow obstacle that fades into existence when on screen."""
    def __init__(self, rect, image, fade_delay=None, fade_speed=None, draw_rect=None):
        super().__init__(rect, 'shadow', image=image)
        self.draw_rect = draw_rect.copy() if draw_rect is not None else rect.copy()
        self.alpha = 0
        self.fade_timer = 0
        self.fade_delay = fade_delay if fade_delay is not None else random.randint(1, 5)
        self.fade_speed = fade_speed if fade_speed is not None else random.uniform(8.8, 16.2)
        self.fade_started = False

    def update(self, player_rect):
        # Start fading in once the obstacle enters the visible screen area.
        screen_rect = pygame.Rect(0, 0, WIDTH, HEIGHT)
        if camera.apply(self.draw_rect).colliderect(screen_rect):
            if not self.fade_started:
                self.fade_timer += 1
                if self.fade_timer >= self.fade_delay:
                    self.fade_started = True
            else:
                self.alpha = min(255, self.alpha + self.fade_speed)
        
    def draw(self, screen, camera):
        if self.alpha <= 0:
            return
        screen_rect = pygame.Rect(camera.offset_x, camera.offset_y, WIDTH, HEIGHT)
        if self.draw_rect.right < screen_rect.left or self.draw_rect.left > screen_rect.right or self.draw_rect.bottom < screen_rect.top or self.draw_rect.top > screen_rect.bottom:
            return
        if self.image:
            image = self.image.copy()
            image.set_alpha(int(self.alpha))
            screen.blit(image, camera.apply(self.draw_rect))
        else:
            shadow_surf = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            shadow_surf.fill((255, 255, 255, int(self.alpha)))
            screen.blit(shadow_surf, camera.apply(self.rect))

class Decoration:
    def __init__(self, x, y, image):
        self.image = image
        self.rect = self.image.get_rect(topleft=(x, y))

    def draw(self, screen, camera):
        screen_rect = pygame.Rect(camera.offset_x, camera.offset_y, WIDTH, HEIGHT)
        if self.rect.right < screen_rect.left or self.rect.left > screen_rect.right or self.rect.bottom < screen_rect.top or self.rect.top > screen_rect.bottom:
            return
        #pygame.draw.rect(screen, (255, 0, 0), camera.apply(self.rect), 1)
        screen.blit(self.image, camera.apply(self.rect))

def setup_level(layout, moon_spike_images=None):
    global neon_images, current_level, neon_laser_img, tv_count
    tv_count =0
    shockwave_image = pygame.image.load('shockwave.png').convert_alpha()
    shockwave_image = pygame.transform.scale(shockwave_image, (TILE_SIZE*2, TILE_SIZE))
    
    neon_tile_img = pygame.image.load("neon_bl.png").convert_alpha()
    neon_tile_img = pygame.transform.scale(neon_tile_img, (TILE_SIZE*2, TILE_SIZE*2))

    castle_bl_img = pygame.image.load("castle_bl.png").convert_alpha()
    castle_bl_img = pygame.transform.scale(castle_bl_img, (TILE_SIZE*2, TILE_SIZE*2))

    black_tile_img = pygame.image.load("black_pillar.png").convert_alpha()
    black_tile_img = pygame.transform.scale(black_tile_img, (TILE_SIZE, TILE_SIZE*4))
    neon_light_img = pygame.image.load("neon_bl_lights.png").convert_alpha()
    neon_light_img = pygame.transform.scale(neon_light_img, (TILE_SIZE*4, TILE_SIZE*3))

    neon_spike_r_img = pygame.image.load("neon_spike_r.png").convert_alpha()
    neon_spike_r_img = pygame.transform.scale(neon_spike_r_img, (TILE_SIZE, TILE_SIZE*2))
    neon_spike_l_img = pygame.image.load("neon_spike_l.png").convert_alpha()
    neon_spike_l_img = pygame.transform.scale(neon_spike_l_img, (TILE_SIZE, TILE_SIZE*2))
    neon_spike_u_img = pygame.image.load("neon_spike_u.png").convert_alpha()
    neon_spike_u_img = pygame.transform.scale(neon_spike_u_img, (TILE_SIZE, TILE_SIZE))
    
    
    neon_laser_img = pygame.image.load("neon_laser.png").convert_alpha()
    neon_laser_img = pygame.transform.scale(neon_laser_img, (TILE_SIZE*4, TILE_SIZE*12))
    
    castle_back_img = pygame.image.load("castle_back.png").convert_alpha()
    castle_back_img = pygame.transform.scale(castle_back_img, (TILE_SIZE*3, TILE_SIZE*3))

    castle_back_large_img = pygame.image.load("castle_back.png").convert_alpha()
    castle_back_large_img = pygame.transform.scale(castle_back_large_img, (TILE_SIZE*50, TILE_SIZE*50))

    glass_img = pygame.image.load("neon_glass3.png").convert_alpha()
    glass_img = pygame.transform.scale(glass_img, (TILE_SIZE*3, TILE_SIZE*4))
    K_glass_img = pygame.image.load("kiraWindow.png").convert_alpha()
    K_glass_img = pygame.transform.scale(K_glass_img, (TILE_SIZE*5, TILE_SIZE*9.8))                

    train_int = pygame.image.load("s_train_int.png").convert_alpha()
    train_int = pygame.transform.scale(train_int, (588*4, 207*3.9))  
    train_int2 = pygame.image.load("s_train_int2.png").convert_alpha()
    train_int2 = pygame.transform.scale(train_int2, (588*4, 207*3.9))  
    train_int3 = pygame.image.load("s_train_int3.png").convert_alpha()
    train_int3 = pygame.transform.scale(train_int3, (588*4, 207*3.9))  
    train_int4 = pygame.image.load("s_train_int4.png").convert_alpha()
    train_int4 = pygame.transform.scale(train_int4, (1230, 828)) 
    
    box_img = pygame.image.load("box.png").convert_alpha()
    box_img = pygame.transform.scale(box_img, (TILE_SIZE*2, TILE_SIZE*2))

    shadow_form_img = pygame.image.load('shadow_form1.png').convert_alpha()
    shadow_form_img = pygame.transform.scale(
        shadow_form_img,
        (TILE_SIZE * 2, int(shadow_form_img.get_height() * (TILE_SIZE * 2 / shadow_form_img.get_width())))
    )
    shadow_hand_img = pygame.image.load('shadow_hand.png').convert_alpha()
    shadow_hand_img = pygame.transform.scale(
        shadow_hand_img,
        (TILE_SIZE * 2, int(shadow_hand_img.get_height() * (TILE_SIZE * 2 / shadow_hand_img.get_width())))
    )
    shadow_blob_img = pygame.image.load('shadow_blob.png').convert_alpha()
    shadow_blob_img = pygame.transform.scale(
        shadow_blob_img,
        (TILE_SIZE * 4, int(shadow_blob_img.get_height() * (TILE_SIZE * 4 / shadow_blob_img.get_width())))
    )



    tiles_list = []
    checkpoints = []
    decorations_list = []
    total_level_height = len(layout) * TILE_SIZE
    #tree_img = pygame.image.load('moonTree.png').convert_alpha()
    #tree_img = pygame.transform.scale(tree_img, (TILE_SIZE * 2, TILE_SIZE * 4))
                
    for row_index, row in enumerate(layout):
        for col_index, cell in enumerate(row):
            x = col_index * TILE_SIZE
            y = row_index * TILE_SIZE
            
            if cell == '#':
                # Normal solid tile
                if current_level == 1:
                    new_rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
                    tiles_list.append(Tile(new_rect, 'normal')) # Original Rock
                elif current_level == 2:
                    # Level 2 Neon Trim Tile
                    new_rect = pygame.Rect(x, y, TILE_SIZE*2, TILE_SIZE*2)
                    tiles_list.append(Tile(new_rect, 'normal', image=neon_tile_img))
                elif current_level == 'FINAL':
                    # Final level ground should be invisible; use invisible tile type for collision only.
                    new_rect = pygame.Rect(x, y, TILE_SIZE*500, TILE_SIZE*2)
                    tiles_list.append(Tile(new_rect, 'invisible'))
                else:
                    new_rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
                    tiles_list.append(Tile(new_rect, 'normal', image=glass_img))
            elif cell == 'b':
                if current_level == 2:
                    new_rect = pygame.Rect(x, y, TILE_SIZE*2, TILE_SIZE*2)
                    tiles_list.append(Tile(new_rect, 'normal', image=castle_bl_img))
                if current_level == 'FINAL':
                    new_rect = pygame.Rect(x, y, TILE_SIZE*2, TILE_SIZE*2)
                    tiles_list.append(Tile(new_rect, 'normal', image=box_img))
            elif cell == 'k': # 'k' for Knife
                knife_dialogue = ["A knife lies in front of you...|You look at the knife.* \nYou think about the knife.* You stare at the knife.* \nDo you want to pick it up?"]
                npcs.append(NPC(x, y, "Knife", knife_dialogue, is_item=True))
            
            if cell == 'G':
                # large normal tile
                new_rect = pygame.Rect(x, y, TILE_SIZE*4, TILE_SIZE*4)
                if current_level == 1:
                    tiles_list.append(Tile(new_rect, 'normal'))
                
            elif cell == '$':
                if current_level == 1:
                    # Tall tile (3x height)
                    new_rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE*3)
                    tiles_list.append(Tile(new_rect, 'normal'))
                elif current_level == 2:
                    new_rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE*3)
                    tiles_list.append(Tile(new_rect, 'normal', image=black_tile_img))
            elif cell == 's':
                if current_level == 2:
                    new_rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
                    decorations_list.append(Decoration(x, y, image=neon_light_img))

            elif cell == '2':
                if current_level == 2:
                    new_rect = pygame.Rect(x, y, TILE_SIZE*3, TILE_SIZE*3)
                    decorations_list.append(Decoration(x, y, image=castle_back_img)) 
            elif cell == '3':
                if current_level == 2:
                    new_rect = pygame.Rect(x, y, TILE_SIZE*50, TILE_SIZE*50)
                    decorations_list.append(Decoration(x, y, image=castle_back_large_img)) 
                if current_level == 'FINAL':
                    new_rect = pygame.Rect(x, y, TILE_SIZE*588, TILE_SIZE*207)
                    decorations_list.append(Decoration(x, y, image=train_int))    
            elif cell == '4':  
                if current_level == 'FINAL':
                    new_rect = pygame.Rect(x, y, TILE_SIZE*588, TILE_SIZE*207)
                    decorations_list.append(Decoration(x, y, image=train_int2))       
            elif cell == '5':  
                if current_level == 'FINAL':
                    new_rect = pygame.Rect(x, y, TILE_SIZE*588, TILE_SIZE*207)
                    decorations_list.append(Decoration(x, y, image=train_int3))
            elif cell == '6':  
                if current_level == 'FINAL':
                    new_rect = pygame.Rect(x, y, TILE_SIZE*588, TILE_SIZE*207)
                    decorations_list.append(Decoration(x, y, image=train_int4))   
            elif cell == 'u':
                if current_level == 2:
                    new_rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
                    tiles_list.append(Tile(new_rect, 'moonspike', image=neon_spike_u_img))
            elif cell in ('M', 'D', 'L', 'R', 'm', 'd', 'l', 'r'):
                # Uppercase: regular MoonSpike.png, Lowercase: MoonSpikeDeep.png
                if current_level == 1:
                    orientation_map = {'M': 'up', 'D': 'down', 'L': 'left', 'R': 'right',
                                    'm': 'up', 'd': 'down', 'l': 'left', 'r': 'right'}
                    spike_type = 'deep' if cell.islower() else 'normal'
                    orientation = orientation_map[cell]
                    new_rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
                    tile_img = None
                    if moon_spike_images is not None and spike_type in moon_spike_images:
                        tile_img = moon_spike_images[spike_type].get(orientation)
                    tiles_list.append(Tile(new_rect, 'moonspike', image=tile_img, orientation=orientation))
                elif current_level ==2:
                    
                    if cell == 'r':
                        if current_level == 2:
                            new_rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE*2)
                            tiles_list.append(Tile(new_rect, 'moonspike', image=neon_spike_r_img))
                        
                    elif cell == 'l':
                        if current_level == 2:
                            new_rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE*2)
                            tiles_list.append(Tile(new_rect, 'moonspike', image=neon_spike_l_img))
                    elif cell == 'L':
                        npcs.append(NPC(x, y, "Lever", []))
            
            elif cell == '-':
                # Wide tile (3x width)
                new_rect = pygame.Rect(x, y, TILE_SIZE*3, TILE_SIZE)
                tiles_list.append(Tile(new_rect, 'normal'))
            elif cell == 'P':
                # Platform tile (one-way from top, long and thin)
                new_rect = pygame.Rect(x, y, TILE_SIZE*2, TILE_SIZE)
                tiles_list.append(Tile(new_rect, 'platform'))
            elif cell == 'F':
                if current_level == 'FINAL':
                    new_rect = shadow_form_img.get_rect(topleft=(x, y))
                    tiles_list.append(ShadowTile(new_rect, shadow_form_img))
            elif cell == 'H':
                if current_level == 'FINAL':
                    new_rect = shadow_hand_img.get_rect(topleft=(x, y))
                    tiles_list.append(ShadowTile(new_rect, shadow_hand_img))
            elif cell == 'B':
                if current_level == 'FINAL':
                    # Keep the blob draw position the same but shrink the collision box.
                    padding = 56
                    draw_rect = shadow_blob_img.get_rect(topleft=(x, y))
                    collision_rect = draw_rect.inflate(-padding * 2, -padding * 2)
                    collision_rect.center = draw_rect.center
                    tiles_list.append(ShadowTile(collision_rect, shadow_blob_img, draw_rect=draw_rect))
            #elif cell == 'W':
                # Wall tile (sides only, tall and thin)
                #new_rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE*2)
                #tiles_list.append(Tile(new_rect, 'wall'))
            elif cell == 'S':
                new_wave = Shockwave(x, y, shockwave_image)
                tiles_list.append(new_wave)
            elif cell == 'V':
                new_wave = VerticalShockwave(x, y, shockwave_image, direction="down")
                tiles_list.append(new_wave)
            elif cell == 'v':
                new_wave = VerticalShockwave(x, y, shockwave_image, direction="up")
                tiles_list.append(new_wave)
            elif cell == 'U': #wideMoonRock
                wide_rock_img = pygame.image.load('wideMoonRock.png').convert_alpha()
                wide_rock_img = pygame.transform.scale(wide_rock_img, (TILE_SIZE * 3, TILE_SIZE * 2))
                new_rect = wide_rock_img.get_rect(topleft=(x, y))
                tiles_list.append(Tile(new_rect, 'normal', image=wide_rock_img))
            elif cell == 'g':
                new_rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
                tiles_list.append(NeonTile(new_rect, 'green', neon_images['green']['active'], neon_images['green']['inactive']))
            elif cell == 'p':
                new_rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
                tiles_list.append(NeonTile(new_rect, 'pink', neon_images['pink']['active'], neon_images['pink']['inactive']))
          
            elif cell == 'T': #Jumbotron TV
                drop_floor = False
                #if current_level == 1:
                #    decorations_list.append(Decoration(x, y, tree_img))
                if current_level == 2:
                    tv_count += 1

                    if tv_count == 2:
                        lines = [
                                "@Princess Kira: La dee dummm!",
                                "@Princess Kira: Oh!| A visitor? |Wait...I recognize that posture. \nYou're a musician, are you not?* Hmm...|Hmmmmmmmmm......\nYes, I think you will do. Come meet me for an interview.",  #, yeah yeah, I sing good and stuff.",
                                "@Princess Kira: I hope you don't mind taking the....Fun Route...*\nI can't help pulling the lever, it's just too fun! Wheeeeeeeeeeeeeeeeee!!!!!",
                                "@Captain Vio: . . . "
                            ]
                        drop_floor = True
                    elif tv_count == 3:
                        lines = ["@Princess Kira:Don't mind the neon spikes, but if you can't dodge them, \nyou won't be able to keep up with my singing tempo! OHOHOHOHOHOHHOHOHOHOHOHOHOHOHOHO!!!!!! "]
                    elif tv_count == 4:
                        lines = ["@Princess Kira:I see you've made it this far. Good! \nYou might be able to make it to me after all."]
                    elif tv_count == 5:
                        lines = ["@Princess Kira:Hmm, actually, taking a closer look at you....|\nYour eyes...|You are not an ordinary person, are you?"]
                    else:
                        lines = ["@Princess Kira: ..."]
                npcs.append(NPC(x, y, "Jumbotron", lines, drop_floor=drop_floor))


            elif cell == 'o': #'normal' grey tile, but moonDetail.png
                new_rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
                moon_img = pygame.image.load("moonDetail.png").convert_alpha()
                moon_img = pygame.transform.scale(moon_img, (TILE_SIZE, TILE_SIZE))
                tiles_list.append(Tile(new_rect, 'normal', image=moon_img))
            elif cell == 'Y':
                if current_level == 2:
                    new_rect = pygame.Rect(x, y, TILE_SIZE*4, TILE_SIZE*12)
                    tiles_list.append(NeonLaserTile(new_rect,'neonlaser'))
            elif cell in ('C', 'c'):
                checkpoint_img = pygame.image.load('checkpoint.png').convert_alpha()
                checkpoint_img = pygame.transform.scale(checkpoint_img, (TILE_SIZE*2, TILE_SIZE*2))
                new_checkpoint = Checkpoint(x, y, checkpoint_img)
                checkpoints.append(new_checkpoint)

            elif cell == 'W': # Stained Glass Windows
                if current_level == 2:
                    #new_rect = pygame.Rect(x, y, TILE_SIZE*2, TILE_SIZE*2)
                    decorations_list.append(Decoration(x, y, glass_img))

            elif cell == 'w': # Stained Glass Windows
                if current_level == 2:
                    #new_rect = pygame.Rect(x, y, TILE_SIZE*2, TILE_SIZE*2)
                    decorations_list.append(Decoration(x, y, K_glass_img))

            elif cell == 'N':
                # level 1 NPC #"But all he's doing is just causing desert-related incidents.",
                #"Moistar: Help! Help!",
                 #"Captain Vio: Yeah, yeah, I know. Let's get this over with."
                lines = [
                    "Alas!| There I stoodest, with utmost innocence, partaking in the most \nexquisite of doughy goodness-* a sweet, jelly-filled confection.\nBUT--|all good things must come to an end.*\nAs befittest of a tyrant, which he ISSETH|, Mo......", # and then a sound wave zipped by \nand knocked it out of my hand!| \nCurse you, Mo....",
                    "With his atrocious waves of sound, |didst strike with utmost strength.| \nTHUS--|was my delectable treat flewn into the bottomless cosmos.",  #He found this weird paper.| He calls himself 'DJ Oser' now.\nThinks he's doing everyone a favor by blasting music.",
                    "He's up ahead.* MaKE hIm PaaYyyYy....*\nBeWARrreee tHe SoouuNdd...|",
                    "@Captain Vio: .|.|.|.|.|"
                ]
                npcs.append(NPC(x, y, "Moistar", lines))
            elif cell == 'Q':
                if current_level == 2:
                    lines = [
                        "@Monkey: Finally!* After extensive research, I've discovered how to read \nthe stars!* They say...|'You are the prophetic one, destined to \nsave the world from eEeEeViL...'",
                        "...*Well they either say that or: 'A monkey will slip on a banana \nat 2 A.M.', but I like the first one better.",
                        
                    ]
                    npcs.append(NPC(x, y, "Monkey", lines))
            elif cell == 'q':
                if current_level == 2:

                    lines = [
                        "@:It is not alive.",
                    ]
                npcs.append(NPC(x, y, "Monkey_Dead", lines))
    return tiles_list, checkpoints, decorations_list

class NeonTile(Tile):
    def __init__(self, rect, color, image_active, image_inactive):
        super().__init__(rect, 'neon')
        self.color = color
        self.image_active = image_active
        self.image_inactive = image_inactive
        self.image = image_active

    def is_active(self):
        return active_neon_color == self.color

    def draw(self, screen, camera):
        active_image = self.image_active if self.is_active() else self.image_inactive
        screen.blit(active_image, camera.apply(self.rect))

class NeonLaserTile:
    global neon_laser_img, neon_laser_h_img
    def __init__(self, rect, orientation='V', boss_managed=False):
        self.rect = rect
        self.type = 'neonlaser'
        self.orientation = orientation
        self.alpha = 0
        self.active = False
        self.boss_managed = boss_managed
        self.damage = 1 if boss_managed else 3
        self.timer = 0
        if boss_managed:
            self.active_duration = 40
            self.inactive_duration = 999999
        else:
            self.active_duration = 120  # frames active
            self.inactive_duration = 180  # frames inactive
        self.active_delay_alpha = 140
        self.fade_step = 10
        self.fading_in = False

    def update(self, player_rect=None):
        self.timer += 1
        if self.active:
            self.alpha = min(255, self.alpha + self.fade_step)
            if self.timer >= self.active_duration:
                self.active = False
                self.fading_in = False
                self.timer = 0
        elif self.fading_in:
            self.alpha = min(255, self.alpha + self.fade_step)
            if self.alpha >= self.active_delay_alpha:
                self.active = True
                self.fading_in = False
                self.timer = 0
        else:
            self.alpha = max(0, self.alpha - self.fade_step)
            if not self.boss_managed and self.timer >= self.inactive_duration:
                self.timer = 0
                self.fading_in = True
                self.alpha = 0

        # Ensure boss-managed lasers can be cleared immediately when state changes.
        if self.boss_managed and not self.active:
            self.alpha = 0

    def draw(self, screen, camera):
        if self.alpha > 0:
            if self.orientation == 'H':
                img = pygame.transform.scale(neon_laser_h_img, (self.rect.width, self.rect.height))
            else:
                img = pygame.transform.scale(neon_laser_img, (self.rect.width, self.rect.height))
            img.set_alpha(self.alpha)
            screen.blit(img, camera.apply(self.rect))

    def get_collision_rect(self):
        if self.orientation == 'H':
            thickness = min(16, self.rect.height)
            y = self.rect.centery - thickness // 2
            return pygame.Rect(self.rect.x, y, self.rect.width, thickness)
        else:
            thickness = min(16, self.rect.width)
            x = self.rect.centerx - thickness // 2
            return pygame.Rect(x, self.rect.y, thickness, self.rect.height)

    def check_player(self, player):
        if self.active and self.get_collision_rect().colliderect(player.rect):
            player.take_damage(self.damage)

class Ship:
    def __init__(self, x, y, image=None):
        if image is None:
            self.image = pygame.Surface((TILE_SIZE * 2, TILE_SIZE), pygame.SRCALPHA)
            pygame.draw.polygon(
                self.image,
                (190, 220, 255),
                [(0, TILE_SIZE), (TILE_SIZE * 2, TILE_SIZE), (TILE_SIZE * 1.5, TILE_SIZE // 2), (TILE_SIZE * 0.5, TILE_SIZE // 2)]
            )
        else:
            self.image = image
        self.rect = self.image.get_rect(center=(x, y))
        self.active = False
        self.taking_off = False
        self.target_level = None
        self.transition_fade = 0
        self.takeoff_speed = 8
        self.state = "IDLE"
    def activate(self):
        self.active = True
        self.taking_off = False

    def start_takeoff(self, target):
        self.taking_off = True
        self.target_level = target
        self.rumble_timer = 60 

    def update(self):
        if not self.taking_off:
            return False
        if self.rumble_timer > 0:
            self.rumble_timer -= 1
            # Add small jitter to the ship's position
            self.rect.x += random.randint(-2, 2)
            return False
        self.rect.y -= self.takeoff_speed // 2
        self.rect.x += self.takeoff_speed * 2
        if self.rect.y < -300:
            return True
        return False

    def draw(self, screen, camera):
        if not self.active:
            return
        if hasattr(self, 'transition_fade') and self.transition_fade > 0:
            fade_surf = pygame.Surface((WIDTH, HEIGHT))
            fade_surf.fill((0, 0, 0))
            fade_surf.set_alpha(self.transition_fade)
            screen.blit(fade_surf, (0, 0))
        
        shake_offset = (0, 0)
        if self.taking_off and self.transition_fade < 100:
            shake_offset = (random.randint(-4, 4), random.randint(-4, 4))

        # Apply the shake to your camera or blit position
        screen.blit(self.image, (camera.apply(self.rect).x + shake_offset[0], 
                                camera.apply(self.rect).y + shake_offset[1]))

def handle_ship_scene():
    global ship_scene_state, active_dialogue, Vio, font, melody3_img, the_melody_img, melody3_alpha, the_melody_alpha, melody_glow_alpha, performing_img, performing_alpha, performing_timer, performing_sound_started, door_img, door_alpha, door_fade_out
    global tiles, checkpoints, decorations_list, flash_lights_active, flash_lights_timer, flash_lights_intensity, ship_to_final_transition
    #print(f"DEBUG: ship_scene_state={ship_scene_state}")
    if ship_scene_state == "INTRO":
        # Automatically start dialogue when entering ship
        if active_dialogue is None:
            active_dialogue = DialogueBox(font, [
                "@Captain Vio:On my way.* That place is where the final melody is.|\nI wonder if this time will be different.| If--|If I can do it this time.|\nBut...| every time... ",
                "@Captain Vio_Down:.....",
                "...Every time...|How come every time...|My cowardly shadow \ntakes over?!* I.....|",
                "I just want to see you again, Lin.| Why does that blasted door taunt \nme so much...?| I just tremble.| I feel like I may not even be conscious.* \nWhy have I failed to enter that wretched place so many times?",
                "And...|every time I fail, she...|",
                "@???:.... ",
                "Do you...| remember?* There is an easier way to end this, to see her...|\nPlease... just let me stop your pain. Let me...",
                "@Captain Vio_Down:I...|* I can't just give up...|right?| I...|have to continue.",
                "I have to keep going."
            
            ],  autoplay=False)
            ship_scene_state = "DIALOGUE_1"
    elif ship_scene_state == "DIALOGUE_1":
        #print(f"DEBUG: In DIALOGUE_1, active_dialogue.finished={active_dialogue.finished if active_dialogue else 'None'}")
        
        if active_dialogue is None or (active_dialogue and active_dialogue.finished):
            Vio.cutscene_target_x = 550  
            Vio.cutscene_speed = 4.0
            ship_scene_state = "MOVING_TO_CONSOLE"
    elif ship_scene_state == "MOVING_TO_CONSOLE":
        if Vio.cutscene_target_x is None:  # Finished moving
            # Start next dialogues
            active_dialogue = DialogueBox(font, [
                "Well, the next melody is waiting.| Maybe this'll be the time...|",
                "@Captain Vio_Down:But...| I really don't know how much longer I can do this...|Just going \nin circles, causing both of us pain and suffering.",
                ".....",
                "@Captain Vio_Surprised:.....!",
                "T-There's a light!* Is that...?",
                "No...|It can't be...|",
                #"Placeholder: Here you can control the ship.",
                #"Placeholder: End of placeholder scene."
            ], speaker_name="Captain Vio")
            ship_scene_state = "DIALOGUE_2"
    elif ship_scene_state == "DIALOGUE_2":
        if active_dialogue is None or (active_dialogue and active_dialogue.finished):
            ship_scene_state = "SHOW_MELODY3"
    elif ship_scene_state == "SHOW_MELODY3":
        # Load and show Melody3 on the right side
        if melody3_img is None:
            try:
                melody3_img = pygame.image.load('Melody3.png').convert_alpha()
            except FileNotFoundError:
                melody3_img = pygame.Surface((50, 50))
                melody3_img.fill((255, 0, 0))  # Red placeholder
        melody3_alpha = min(255, melody3_alpha + 5)  # Fade in
        if melody3_alpha >= 255 and Vio.cutscene_target_x is None:
            # Start moving Vio towards Melody3
            melody3_x = 1000  # Adjust this x-coordinate for Melody3 position
            Vio.cutscene_target_x = melody3_x - 50  # Position near Melody3
            Vio.cutscene_speed = 2.0
            ship_scene_state = "MOVING_TO_MELODY3"
    elif ship_scene_state == "MOVING_TO_MELODY3":
        if Vio.cutscene_target_x is None:  # Reached
            # Trigger dialogue for Melody3
            active_dialogue = DialogueBox(font, [
                "@Captain Vio_Surprised:....",
                "No...",
                "This can't be possible...|right?* This has never happened before...",
                "Have...|Have my prayers been answered?",
                "The third melody..."
            ], speaker_name="Captain Vio")
            ship_scene_state = "MELODY3_DIALOGUE"
    elif ship_scene_state == "MELODY3_DIALOGUE":
        if active_dialogue is None or (active_dialogue and active_dialogue.finished):
            ship_scene_state = "COMBINE_MELODIES"
    elif ship_scene_state == "COMBINE_MELODIES":
        # Fade out Melody3, fade in The Melody in center with glow
        melody3_alpha = max(0, melody3_alpha - 5)
        the_melody_alpha = min(255, the_melody_alpha + 5)
        melody_glow_alpha = min(100, melody_glow_alpha + 2)  # Glow effect
        if the_melody_alpha >= 255 and Vio.cutscene_target_x is None:
            # Load The Melody if not loaded
            if the_melody_img is None:
                try:
                    the_melody_img = pygame.image.load('The Melody.png').convert_alpha()
                except FileNotFoundError:
                    the_melody_img = pygame.Surface((100, 100))
                    the_melody_img.fill((0, 255, 0))  # Green placeholder
            # Move Vio to The Melody
            the_melody_x = 600  # Center x, adjust as needed
            Vio.cutscene_target_x = the_melody_x
            ship_scene_state = "MOVING_TO_THE_MELODY"
    elif ship_scene_state == "MOVING_TO_THE_MELODY":
        if Vio.cutscene_target_x is None:  # Reached
            performing_alpha = 0
            performing_timer = 0
            performing_sound_started = False
            Vio.can_move = False
            ship_scene_state = "PERFORMING"
    elif ship_scene_state == "PERFORMING":
        Vio.is_holding_violin = True
        # Hide the regular Vio sprite while the performing animation plays
        Vio.visible = False
        performing_alpha = min(255, performing_alpha + 5)
        if performing_alpha >= 255 and not performing_sound_started:
            #try:
            The_Melody.play()
            #except FileNotFoundError:
                #print("Sound file not found")
            performing_sound_started = True
        if performing_sound_started:
            performing_timer += 1
            if performing_timer >= 1140:
                #active_dialogue = DialogueBox(font, [
                    #"Placeholder: The song finishes with a flash.",
                    #"(You're back...|)"
                    #"(A white door casts a looming presence.)"
               # ], speaker_name=None)
               ship_scene_state = "FLASHING_LIGHTS"
    elif ship_scene_state == "FLASHING_LIGHTS":
        Vio.is_holding_violin = False
        Vio.visible = True
        # Flashing lights transition effect
        global flash_lights_active, flash_lights_timer, flash_lights_intensity
        if not flash_lights_active:
            flash_lights_active = True
            flash_lights_timer = 0
        flash_lights_timer += 1
        # Create a pulsing effect
        flash_lights_intensity = abs(math.sin(flash_lights_timer * 0.15)) * 200
        if flash_lights_timer > 120:  # About 2 seconds of flashing
            ship_scene_state = "DOOR_FADE_IN"
            flash_lights_active = False
    elif ship_scene_state == "DOOR_FADE_IN":
        if door_img is None:
            try:
                door_img = pygame.image.load('The Door.png').convert_alpha()
            except FileNotFoundError:
                door_img = pygame.Surface((200, 300), pygame.SRCALPHA)
                pygame.draw.rect(door_img, (180, 180, 255), door_img.get_rect(), border_radius=20)
        door_alpha = min(255, door_alpha + 10)
        if door_alpha >= 255 and (active_dialogue is None or (active_dialogue and active_dialogue.finished)):
            active_dialogue = DialogueBox(font, [
                "(You're back...)",
                "(A dark door casts a looming presence.)",
                "(You...|feel repelled.* You...|feel dizzy.)",
                "(You...|feel like you might pass out...)",
                "(You...|want to turn around and run away...|\nBut...|You feel like you may be forgetting something.* Something \nimportant.* You find yourself staring at the door, unable to move.)",
                "...",
                #"(...You hear a girl calling your name.)",
                "@???:Don't go through the door...|Stay...|Who knows what's waiting on the \nother side?",                                                                      # Stay where it's safe...|Just let me hold your breath...*",
                "@Captain Vio_Down:.....",
                "N-No...|I-Is this how it ends again?| I-I have to open the door.| I can't \nfail again.| But...|Why won't my hands move?",
                ".....",
                "@:(The clock is ticking.)",
                ".....",
                ".| .| .| .| .|",
                "(Soon, the train will leave.* It will leave you behind.)",
                "....................",
                "(Your hand slowly reaches out.)",
                "@Captain Vio_Down:She's on the other side of this door...| I'm almost there.",
                "......",
                "@???:You are going to fail.| If you open the door...",
                "@:(A...|sudden warmth comes upon you.| A light appears.)",
                "(The door begins to open!)",




            ], speaker_name=None)
            ship_scene_state = "DOOR_DIALOGUE"
    elif ship_scene_state == "DOOR_DIALOGUE":
        if active_dialogue is None or (active_dialogue and active_dialogue.finished):
            ship_scene_state = "DOOR_FADE_OUT"
            ship_scene_state = "READY_FOR_FINAL"
            global ship_to_final_transition
            ship_to_final_transition = True
    elif ship_scene_state == "DOOR_FADE_OUT":
        door_alpha = max(0, door_alpha - 10)
        if door_alpha <= 0:
            ship_scene_state = "READY_FOR_FINAL"
    
    elif ship_scene_state == "READY_FOR_FINAL":
        # Set flag for main loop to handle transition
        #Vio.is_holding_violin = False
        ship_scene_state = None
        Vio.can_move = True
        # Restore Vio's normal sprite visibility when leaving the ship scene
       #Vio.visible = True
    elif ship_scene_state == "FINAL_DIALOGUE":
        if active_dialogue and active_dialogue.finished:
            ship_scene_state = None  # End scene

def load_level(level_number):
    global current_level, LEVEL_MAP, tiles, checkpoints, decorations_list, font
    global npcs, hazards, boss_triggered, boss_finished, boss_manager
    global boss_state, boss_first_entry, active_dialogue, ship, shadow, camera
    global moon_spike_images, Vio, LEVEL_START_POINTS, neon_images, active_neon_color, neon_toggle_timer
    global ship_scene_state, ship_img, ship_image
    #print(f"DEBUG: Starting load_level({level_number})")
    current_level = level_number
    #Vio = Player(animations)
    if level_number == 'SHIP':
        active_neon_color = 'green'
        LEVEL_MAP = []

        if 'tiles' in globals(): tiles.clear()
        if 'checkpoints' in globals(): checkpoints.clear()
        if 'decorations_list' in globals(): decorations_list.clear()

        npcs.clear()
        if hazards:
            hazards.clear()
        if shadow is not None:
            hazards = [shadow]
        else:
            hazards = []

        tiles = [
            Tile(pygame.Rect(0, 400, 1200, 200), 'normal'),  # Floor
            #Tile(pygame.Rect(500, 200, 200, 200), 'normal'),  # Box in center
        ]
        checkpoints = []
        decorations_list = []

        # Add NPC for ship dialogue
        ship_dialogue = [
            "Placeholder: Welcome to the ship!",
            "Placeholder: This is where the story continues.",
            "Placeholder: Let's move to the console."
        ]
        npcs.append(NPC(600, 100, "Ship Console", ship_dialogue))

        Vio.reset_for_level((100, 300))  # Spawn point inside the ship
        Vio.visible = True
        Vio.can_move = True
        Vio.health = Vio.max_health
        Vio.invulnerability_timer = 0
        camera.offset_x = 0
        camera.offset_y = 0

        ship_image = pygame.image.load('Allegro_Int.png').convert_alpha()
        ship_image = pygame.transform.scale(ship_image, (1200, 800))
        ship_scene_state = "INTRO"

        boss_triggered = False
        boss2_triggered = False
        boss_finished = False
        boss2_finished = False
        boss_manager = None
        kira_boss_manager = None
        boss_state = None
        boss2_state = None
        boss_first_entry = True
        active_dialogue = None

        if ship:
            ship.active = True
            ship.taking_off = False
            ship.transition_fade = 0
            ship.target_level = None
        else:
            # Create ship for SHIP level
            ship = Ship(600, 3050, ship_img)  # Position it in the ship level
            ship.active = True

        #print("DEBUG: Loaded SHIP level")
        return tiles, checkpoints, decorations_list

    if level_number == 'FINAL':
        active_neon_color = 'green'
        LEVEL_MAP = LEVEL_FIN_MAP
        # Placeholder intro dialogue for final level
        global final_level_frame_count, final_level_autoscroll
        #print("DEBUG: Loading FINAL level")
        final_level_frame_count = 0
        final_level_autoscroll = False  # Don't autoscroll during intro dialogue
    elif level_number == 2:
        active_neon_color = 'green'
        LEVEL_MAP = LEVEL2_MAP
        #active_dialogue = DialogueBox(font, ["Princess Kira's Castle"], autoplay=True, has_background=False, is_passive=True, text_color=(255, 0, 255))
        
    elif level_number == 1:
        LEVEL_MAP = LEVEL1_MAP
    #else:
        #LEVEL_MAP = LEVEL1_MAP


    if 'tiles' in globals(): tiles.clear()
    if 'checkpoints' in globals(): checkpoints.clear()
    if 'decorations_list' in globals(): decorations_list.clear()

    npcs.clear()
    if shadow is None:
        shadow = Shadow((0, 0))
    else:
        shadow.reset(Vio)

    
    #print("DEBUG: NPCs cleared, resetting Vio")

    hazards = [shadow]
    boss_triggered = False
    boss2_triggered = False
    boss_finished = False
    boss_manager = None
    boss_state = None
    boss_first_entry = True
    active_dialogue = None

    #current_fade = ship.transition_fade if ship is not None else 0
    start_pos = LEVEL_START_POINTS.get(level_number, (100, 2724))
    
    Vio.reset_for_level(start_pos)

    level_width = max(len(row) for row in LEVEL_MAP) * TILE_SIZE
    if current_level == 1:
        ship_x = min(level_width - TILE_SIZE * 2 - 50, BOSS_ARENA1_START_X + 2500)
        ship_y = min(HEIGHT + 120, 760)
    elif current_level == 2:
        ship_x = min(level_width - TILE_SIZE * 2 - 50, BOSS2_ARENA_LEFT + 2500)
        ship_y = min(HEIGHT + 1420, 3060)
    elif current_level == 'FINAL':
        ship_x = min(level_width - TILE_SIZE * 2 - 50, 1000)
        ship_y = min(HEIGHT + 120, 800)
    else:
        ship_x = TILE_SIZE * 2
        ship_y = HEIGHT
    ship_img = pygame.image.load("Allegro(open).png").convert_alpha()
    ship = Ship(ship_x, ship_y, ship_img)
    #ship.transition_fade = current_fade
    #ship.active = True 

    if camera is not None:
        camera.offset_x = max(0, Vio.rect.centerx - WIDTH // 2)
        camera.offset_y = max(0, Vio.rect.centery - HEIGHT * 0.65)
    
    #print("DEBUG: About to call setup_level")

    tiles, checkpoints, decorations_list = setup_level(LEVEL_MAP, moon_spike_images)
   # print(f"--- Level {level_number} Loading Report ---")
    #print(f"Total tiles created: {len(tiles)}")
    
    #print("DEBUG: setup_level FINISHED")
    #if len(tiles) > 0:
        # Find the very first solid tile to see its coordinates
        #first_tile = tiles[0]
        #print(f"First tile found at: x={first_tile.rect.x}, y={first_tile.rect.y}")
        #print(f"Vio starting at: x={Vio.rect.x}, y={Vio.rect.y}")
    #else:
        #print("CRITICAL ERROR: No tiles were created! Check your LEVEL2_MAP string.")

    return tiles, checkpoints, decorations_list
    #return tiles, checkpoints, decorations_list

def load_ship_level():
    return load_level('SHIP')


def draw_moon_spike(surface, rect, orientation='up'):
    color = (200, 200, 255)
    if orientation == 'up':
        points = [(rect.left, rect.bottom), (rect.centerx, rect.top), (rect.right, rect.bottom)]
    elif orientation == 'down':
        points = [(rect.left, rect.top), (rect.centerx, rect.bottom), (rect.right, rect.top)]
    elif orientation == 'left':
        points = [(rect.right, rect.top), (rect.left, rect.centery), (rect.right, rect.bottom)]
    else:  # 'right'
        points = [(rect.left, rect.top), (rect.right, rect.centery), (rect.left, rect.bottom)]
    pygame.draw.polygon(surface, color, points)

def get_image(sheet, frame, width, height, scale):
    image = pygame.Surface((width, height), pygame.SRCALPHA).convert_alpha()
    image.blit(sheet, (0, 0), ((frame * width), 0, width, height))
    image = pygame.transform.scale(image, (width * scale, height * scale))
    return image

def load_spritesheet(filename, frame_w, frame_h, scale):
    """Load spritesheet and extract animation frames scaled to the given scale factor."""
    sheet = pygame.image.load(filename).convert_alpha()
    
    walk_frames = extract_frames(sheet, 0, 3, 3, frame_w, frame_h, scale)

    animations = {
        "idle":  extract_frames(sheet, 0, 0, 3, frame_w, frame_h, scale),
        "jump":  extract_frames(sheet, 1, 0, 2, frame_w, frame_h, scale),
        "dash":  extract_frames(sheet, 1, 2, 2, frame_w, frame_h, scale),
        "climb": extract_frames(sheet, 1, 4, 2, frame_w, frame_h, scale),
        "run":   extract_frames(sheet, 2, 0, 6, frame_w, frame_h, scale)
    }
    animations["walk"] = [walk_frames[0], walk_frames[1], walk_frames[2], walk_frames[1]]
    return animations

def extract_frames(sheet, row, start_col, num_frames, w, h, scale):
    """Extract and scale individual frames from a spritesheet."""
    frames = []
    for i in range(num_frames):
        # Get the source rectangle from the spritesheet
        rect = pygame.Rect((start_col + i) * w, row * h, w, h)
        frame = sheet.subsurface(rect).copy()
        # Scale the frame
        frame = pygame.transform.scale(frame, (w * scale, h * scale))
        frames.append(frame)
    return frames


class SpriteAnimator:
    """Simple sprite animator with per-frame durations and horizontal flip support."""
    def __init__(self, frames, durations=None, loop=True):
        # frames: list of Surfaces
        # durations: list of milliseconds per frame (or single value applied to all)
        self.frames = frames or []
        if durations is None:
            # default 200ms per frame
            self.durations = [200] * len(self.frames)
        elif isinstance(durations, (int, float)):
            self.durations = [int(durations)] * len(self.frames)
        else:
            self.durations = [int(d) for d in durations]
        self.loop = loop
        self.index = 0
        self.timer = 0
        self.playing = True
        self.finished = False
        self.flip_horizontal = False

    def reset(self):
        self.index = 0
        self.timer = 0
        self.playing = True
        self.finished = False

    def update(self, dt):
        if not self.playing or self.finished or len(self.frames) == 0:
            return
        # dt in milliseconds expected
        self.timer += dt
        while self.timer >= self.durations[self.index]:
            self.timer -= self.durations[self.index]
            self.index += 1
            if self.index >= len(self.frames):
                if self.loop:
                    self.index = 0
                else:
                    self.index = len(self.frames) - 1
                    self.finished = True
                    break

    def get_current(self):
        if not self.frames:
            return None
        frame = self.frames[self.index]
        if self.flip_horizontal:
            return pygame.transform.flip(frame, True, False)
        return frame


def get_simple_frames(filename, num_frames, frame_w, frame_h, scale):
    """Extracts a simple horizontal row of frames."""
    try:
        sheet = pygame.image.load(filename).convert_alpha()
        sheet_width, sheet_height = sheet.get_size()
        
        frames = []
        for i in range(num_frames):
            rect_x = i * frame_w
            rect_y = 0
            
            # Check if the rectangle fits within the sheet
            if rect_x + frame_w <= sheet_width and rect_y + frame_h <= sheet_height:
                rect = pygame.Rect(rect_x, rect_y, frame_w, frame_h)
                frame = sheet.subsurface(rect).copy()
                frame = pygame.transform.scale(frame, (int(frame_w * scale), int(frame_h * scale)))
                frames.append(frame)
            else:
                # Create a fallback frame if out of bounds
                frame = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
                frame.fill((255, 255, 0, 128))  # Semi-transparent yellow
                frame = pygame.transform.scale(frame, (int(frame_w * scale), int(frame_h * scale)))
                frames.append(frame)
        
        return frames
    except (pygame.error, FileNotFoundError):
        # If file doesn't exist or can't be loaded, return fallback frames
        frames = []
        for i in range(num_frames):
            frame = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
            frame.fill((255, 0, 255, 128))  # Semi-transparent magenta
            frame = pygame.transform.scale(frame, (int(frame_w * scale), int(frame_h * scale)))
            frames.append(frame)
        return frames

def handle_player_death(player, hazards, tiles, camera, particles, trail_particles=None):
    """Reset everything when the player dies."""
    global boss_triggered, boss_manager, mo_boss, active_dialogue, boss2_triggered, kira_boss_manager, current_level, ship, final_level_frame_count, floating_dialogue, floating_dialogue_queue, tentacle_attacks, final_level_tentacle_schedule, final_level_dialogue_queues, final_level_dialogue_queue_phase
    global transition_started, transition_fading, transition_fade_alpha, transition_fade_in, memory_started, sheet_spawned, sheet_visible, violin_timer, boss2_defeated, boss2_finished, boss2_state, fading, fade_alpha, final_level_music_phase

    # During boss fights, respawn before the boss arena so player must walk back
    if boss_triggered:
        # Reset player to BEFORE the boss arena
        player.rect.x = BOSS_ARENA1_START_X - 1000  # Spawn well before the trigger point
        player.rect.y = 740  # Same Y as normal spawn
        player.spawn_point = (player.rect.x, player.rect.y)
        player.vel_x = 0
        player.vel_y = 0
        player.health = player.max_health
        player.invulnerability_timer = 120  # 2 seconds of invulnerability
        player.visible = True
        player.dead_animation_started = False
        player.can_move = True
        player.cutscene_target_x = None
        
        # RESET boss_triggered so camera unfreezes and follows player normally again
        boss_triggered = False
        
        # Reset camera to normal following mode
        camera.__init__(WIDTH, HEIGHT)
   
        # Clear particles and trails
        particles.clear()
        if trail_particles is not None:
            trail_particles.clear()
            
        # Reset boss manager waves but keep state
        if boss_manager:
            tiles[:] = [tile for tile in tiles if not getattr(tile, 'boss_managed', False)]
            boss_manager = None

        # Reset any pending transitions
        transition_started = False
        transition_fading = False
        transition_fade_alpha = 0
        transition_fade_in = False
        memory_started = False
        sheet_spawned = False
        sheet_visible = False
        violin_timer = 0
        boss2_defeated = False
        boss2_finished = False
        boss2_state = None
        fading = False
        fade_alpha = 0
        active_dialogue = None
        return
    
    # During level 2 boss fight
    if boss2_triggered:
        player.rect.x = 21000  
        player.rect.y = 740  
        player.spawn_point = (player.rect.x, player.rect.y)
        player.vel_x = 0
        player.vel_y = 0
        player.health = player.max_health
        player.invulnerability_timer = 120  
        player.visible = True
        player.dead_animation_started = False
        player.can_move = True
        player.cutscene_target_x = None
        
        boss2_triggered = False
        
        # Clear particles and trails
        particles.clear()
        if trail_particles is not None:
            trail_particles.clear()
            
        # Reset kira boss manager and flag so intro plays again on re-entry
        if kira_boss_manager:
            tiles[:] = [tile for tile in tiles if not getattr(tile, 'boss_managed', False)]
            kira_boss_manager = None
        
        # Reset transition flags to prevent triggering on death
        transition_started = False
        transition_fading = False
        transition_fade_alpha = 0
        transition_fade_in = False
        memory_started = False
        sheet_spawned = False
        sheet_visible = False
        violin_timer = 0
        boss2_defeated = False
        boss2_finished = False
        boss2_state = None
        fading = False
        fade_alpha = 0
        active_dialogue = None
        return

    # Generic death reset for any other level (including SHIP)
    final_level_respawn_phase = None
    if current_level == 'FINAL':
        final_level_respawn_phase = get_final_level_phase_from_frame(final_level_frame_count)
       # print(f"DEBUG: Dying in final level, frame={final_level_frame_count}, camera.offset_x={camera.offset_x}, phase={final_level_respawn_phase}")

    player.reset_for_level(player.spawn_point)
    player.health = player.max_health
    player.invulnerability_timer = 120
    player.visible = True
    player.dead_animation_started = False
    player.can_move = True
    player.cutscene_target_x = None
    player.vel_x = 0
    player.vel_y = 0

    if ship:
        ship.taking_off = False

    particles.clear()
    if trail_particles is not None:
        trail_particles.clear()

    if current_level == 'SHIP':
        camera.offset_x = 0
        camera.offset_y = 0
    else:
        camera.__init__(WIDTH, HEIGHT)

    if current_level == 'FINAL':
        phase = final_level_respawn_phase if final_level_respawn_phase is not None else get_final_level_phase_from_frame(final_level_frame_count)
        respawn_pos = get_final_level_respawn_position(phase)
       # print(f"DEBUG: Final respawn phase={phase}, respawn_pos={respawn_pos}")
        player.rect.topleft = respawn_pos
        player.spawn_point = respawn_pos
        player.hitbox = player.rect.copy()
        if hasattr(player, 'sync_draw_rect'):
            player.sync_draw_rect()
        final_level_frame_count = get_final_level_frame_for_phase(phase)
        floating_dialogue = None
        final_level_dialogue_queues[phase] = create_final_level_dialogue_queue(phase, font)
        floating_dialogue_queue = final_level_dialogue_queues[phase]
        final_level_dialogue_queue_phase = phase
        tentacle_attacks.clear()
        final_level_tentacle_schedule = []
        final_cutscene_triggered = False
        final_cutscene_state = None
        final_level_music_phase = 0
        stop_music()
        final_phase_shake_timer = 0
        final_phase_shake_offset = (0, 0)
        floating_dialogue_queue = None  # Reset so tentacle schedule reinitializes on respawn
        camera.offset_x = max(0, respawn_pos[0] - 100)
        camera.offset_y = 390

    transition_started = False
    transition_fading = False
    transition_fade_alpha = 0
    transition_fade_in = False
    memory_started = False
    sheet_spawned = False
    sheet_visible = False
    violin_timer = 0
    boss2_defeated = False
    boss2_finished = False
    boss2_state = None
    fading = False
    fade_alpha = 0
    active_dialogue = None
    return
def main():
    global boss_triggered, boss2_triggered, boss_manager, Vio, shadow, ship, current_level, moon_spike_images, active_dialogue, hazards, LEVEL_MAP, npcs, sheet_visible, violin_timer, memory_started, sheet_spawned, font, screen, game_state, tiles, checkpoints, decorations_list
    global ship_img, boss2_finished
    
    LEVEL_MAP = LEVEL1_MAP  # Initialize level map
    #current_level = 1

    if DEBUG_LEVEL_2:
        tiles, checkpoints, decorations_list = load_level(2)
        game_state = "LEVEL_START_ANIMATION"
        ship.rect.y = -500 

    # World starfield for the background
    max_world_width = max(len(row) for row in LEVEL_MAP) * TILE_SIZE
    max_world_height = len(LEVEL_MAP) * TILE_SIZE
    star_frames = load_star_frames(('Star.png', 'star.png', 'star_sheet.png', 'starsheet.png', 'starfield.png', 'Starfield.png'))
    stars = [Star(
        random.randint(0, max_world_width),
        random.randint(0, max_world_height),
        random.choice([2, 3, 4, 5, 6]),
        random.uniform(0, 2 * math.pi),
        random.uniform(0.18, 0.5),
        frames=star_frames
    ) for _ in range(260)]
    if current_level == 'FINAL':
        stars = [Star(
        random.randint(0, max_world_width),
        random.randint(0, max_world_height),
        random.choice([2, 3, 4, 5, 6]),
        random.uniform(0, 2 * math.pi),
        random.uniform(0.18, 0.5),
        frames=star_frames
    ) for _ in range(60)]

    # Load all animations
    try:
        animations = load_spritesheet('Captain_Vio_Sheet.png', 48, 52, SCALE //1.5)
    except pygame.error:
       # print("Error: Could not load Captain_Vio_Sheet.png")
        animations = None
        return
    
    

    Vio = Player(animations)
    particles = []
    trail_particles = []

    # --- Cockpit cutscene assets & animators ---
    try:
        lin_sheet = pygame.image.load('Lin.png').convert_alpha()
    except Exception:
        lin_sheet = None

    try:
        vio_violin_sheet = pygame.image.load('Vio(Violin).png').convert_alpha()
    except Exception:
        vio_violin_sheet = None

    # Helper to extract row frames when rows may have different counts
    def extract_row_frames_dynamic(sheet, row, num_frames, scale):
        if sheet is None:
            return []
        sw, sh = sheet.get_size()
        # Assume the row uses up to num_frames columns, frame width is sw // max_columns
        frame_w = sw // max(1, num_frames)
        frame_h = sh // max(1, (sh // frame_w)) if frame_w else sh
        return extract_frames(sheet, row, 0, num_frames, frame_w, frame_h, scale)

    # Default scale: reuse SCALE where appropriate; fall back to 2
    _sheet_scale = SCALE if 'SCALE' in globals() else 2
    
    lin_idle_frames = extract_row_frames_dynamic(lin_sheet, 0, 2, _sheet_scale)
    lin_perform_frames = extract_row_frames_dynamic(lin_sheet, 1, 3, _sheet_scale)
    vio_violin_frames = extract_row_frames_dynamic(vio_violin_sheet, 0, 5, _sheet_scale)
    vio_violin_anim = SpriteAnimator(vio_violin_frames, durations=150, loop=True) if vio_violin_frames else None
    #now let's scale it so that the vio_violin animation matches the size of Vio's normal poses
    #VIO_OVERLAY_DEBUG = True  # Set True to log overlay draws and draw debug rect (prints once per hold)
    VIO_OVERLAY_DEBUG = False



    # Sprite animators will be created in final level section when needed

    
    # Moon spike image loading and rotated variants
    moon_spike_images = {}
    try:
        moon_spike_base = pygame.image.load('MoonSpike.png').convert_alpha()
        moon_spike_base = pygame.transform.scale(moon_spike_base, (TILE_SIZE, TILE_SIZE))
    except pygame.error:
        moon_spike_base = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        pygame.draw.polygon(moon_spike_base, (200, 200, 255), [(0, TILE_SIZE), (TILE_SIZE * 0.25, TILE_SIZE * 0.4), (TILE_SIZE * 0.5, TILE_SIZE), (TILE_SIZE * 0.75, TILE_SIZE * 0.4), (TILE_SIZE, TILE_SIZE)])

    moon_spike_images['normal'] = {}
    moon_spike_images['normal']['up'] = moon_spike_base
    moon_spike_images['normal']['down'] = pygame.transform.rotate(moon_spike_base, 180)
    moon_spike_images['normal']['left'] = pygame.transform.rotate(moon_spike_base, 90)
    moon_spike_images['normal']['right'] = pygame.transform.rotate(moon_spike_base, -90)
    
    try:
        moon_spike_deep = pygame.image.load('MoonSpikeDeep.png').convert_alpha()
        moon_spike_deep = pygame.transform.scale(moon_spike_deep, (TILE_SIZE, TILE_SIZE))
    except pygame.error:
        moon_spike_deep = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        pygame.draw.polygon(moon_spike_deep, (100, 150, 255), [(0, TILE_SIZE), (TILE_SIZE * 0.25, TILE_SIZE * 0.4), (TILE_SIZE * 0.5, TILE_SIZE), (TILE_SIZE * 0.75, TILE_SIZE * 0.4), (TILE_SIZE, TILE_SIZE)])

    moon_spike_images['deep'] = {}
    moon_spike_images['deep']['up'] = moon_spike_deep
    moon_spike_images['deep']['down'] = pygame.transform.rotate(moon_spike_deep, 180)
    moon_spike_images['deep']['left'] = pygame.transform.rotate(moon_spike_deep, 90)
    moon_spike_images['deep']['right'] = pygame.transform.rotate(moon_spike_deep, -90)

    load_neon_images()
    # Do not auto-load any level while on the title screen. Levels will be loaded
    # when the player selects New Game or Load Game.
    #tiles, checkpoints, decorations_list = load_level(current_level)
    tiles = []
    checkpoints = []
    decorations_list = []

    # Boss assets - will be loaded when needed
    try:
        mo_boss_img = pygame.image.load('DJ Oser.png').convert_alpha()
        mo_boss_img = pygame.transform.scale(mo_boss_img, (TILE_SIZE * 2, TILE_SIZE * 2))
    except pygame.error:
        mo_boss_img = pygame.Surface((TILE_SIZE * 2, TILE_SIZE * 2))
        mo_boss_img.fill((100, 200, 255))
    
    try:
        boombox_img = pygame.image.load('boomBox.png').convert_alpha()
    except pygame.error:
        boombox_img = None
    
    try:
        shockwave_img = pygame.image.load('shockwave.png').convert_alpha()
    except pygame.error:
        shockwave_img = None
    
    active_dialogue = None
    title_buttons = ["New Game", "Load Game"]
    title_selected = 0
    try:
        title_image = pygame.image.load("titlescreen.png").convert_alpha()
        title_image = pygame.transform.scale(title_image, (WIDTH, HEIGHT))
    except pygame.error:
        title_image = pygame.Surface((WIDTH, HEIGHT))
        title_image.fill((12, 12, 24))

    # Scan for any controllers already plugged in
    for i in range(pygame.joystick.get_count()):
        joy = pygame.joystick.Joystick(i)
        joy.init()
        joysticks.append(joy)

    fading = False
    fade_alpha = 0
    fade_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    font = pygame.font.Font(None, 30)

    # Game state
    game_state = "TITLE"

    # Intro setup
    opening_text = [
        "One more time. Just one more time.|\nI can't give up...|right?",
        "You're just rolling in circles.| A failure.",
        #"....|I....",
        "(Suppress it.| Just suppress it....)",
        "The Moon...|where the first melody is..."
    ]
    intro_dialogue = DialogueBox(font, opening_text, autoplay = True, has_background = False)

    z_was_held = False
    talking_npc = None
    
    floor_falling = False
    kira_is_dropping_floor = False
    
    # Cutscene sprite animators and fade (initialized on demand in final level)
    lin_idle_anim = None
    lin_perform_anim = None
    # Scaling tweaks for violin overlays
    VIO_OVERLAY_SCALE = 1.5  # Multiplier for in-play overlay size (1.0 = match Vio.draw_rect)
    VIO_CUTSCENE_SCALE = 1.5  # Multiplier for final-cutscene performing scale
    cockpit_fade_alpha = 0
    
    # Fullscreen state
    is_fullscreen = False
    base_width, base_height = WIDTH, HEIGHT
    fullscreen_scale = 1.0

    while True:
        global boss_manager, boss_state, boss_first_entry, button_is_glowing, boss2_first_time, tv_count, has_not_dropped_floor, boss_finished, boss2_state
        global transition_started, transition_fade_in, transition_fading, transition_fade_alpha, DARK_PURPLE, final_level_frame_count, final_level_autoscroll, final_level_autoscroll_speed, floating_dialogue, floating_dialogue_queue, tentacle_attacks, final_level_tentacle_schedule, final_cutscene_triggered, final_cutscene_state, final_cutscene_trigger_x, final_intro_dialogue_not_started, final_phase_shake_timer, final_phase_shake_offset, credits_y, credits_speed, checkpoint_message, checkpoint_message_timer, is_paused, pause_selected, esc_hold_timer
        
        dt = clock.tick(60)
        interaction_performed = False
        keys = pygame.key.get_pressed()
        confirm_keys_held = keys[pygame.K_z] or keys[pygame.K_RETURN] or keys[pygame.K_SPACE]
        confirm_buttons_held = any(joy.get_button(0) or joy.get_button(1) for joy in joysticks)
        z_currently_held = confirm_keys_held or confirm_buttons_held
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return

            # Handle controller connection/disconnection
            if event.type == pygame.JOYDEVICEADDED:
                joy = pygame.joystick.Joystick(event.device_index)
                joy.init()
                joysticks.append(joy)
              #  print(f"Controller connected: {event.device_index}")
                continue
            if event.type == pygame.JOYDEVICEREMOVED:
                removed_id = getattr(event, 'instance_id', None)
                if removed_id is not None:
                    joysticks[:] = [joy for joy in joysticks if joy.get_instance_id() != removed_id]
                else:
                    joysticks[:] = [joy for joy in joysticks if joy.get_id() != event.device_index]
               # print(f"Controller disconnected: {removed_id if removed_id is not None else event.device_index}")
                continue
            
            # Handle fullscreen toggle (F4)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F4:
                    is_fullscreen = not is_fullscreen
                    if is_fullscreen:
                        screen = pygame.display.set_mode((base_width, base_height), pygame.FULLSCREEN | pygame.SCALED)
                        desktop_width, desktop_height = pygame.display.get_window_size()
                        fullscreen_scale = min(desktop_width / base_width, desktop_height / base_height)
                    #    print(f"Fullscreen enabled (game scale: {fullscreen_scale:.2f})")
                    else:
                        screen = pygame.display.set_mode((base_width, base_height))
                        fullscreen_scale = 1.0
                     #   print(f"Fullscreen disabled")

            # Handle input events
            if game_state == "TITLE":
                if active_dialogue:
                    active_dialogue.update(keys)
                    if active_dialogue.finished:
                        active_dialogue = None

                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_LEFT, pygame.K_UP):
                        title_selected = (title_selected - 1) % len(title_buttons)
                    elif event.key in (pygame.K_RIGHT, pygame.K_DOWN):
                        title_selected = (title_selected + 1) % len(title_buttons)
                    elif event.key in (pygame.K_z, pygame.K_RETURN, pygame.K_SPACE):
                        if title_selected == 0:
                            # Reset all game variables and start a new game
                            #Vio = None
                            tiles = []
                            checkpoints = []
                            decorations_list = []
                            hazards = []
                            npcs = []
                            boss_manager = None
                            kira_boss_manager = None
                            ship = None
                            active_dialogue = None
                            boss_triggered = False
                            boss2_triggered = False
                            boss_finished = False
                            boss2_finished = False
                            current_level = None
                            fading = False
                            sheet_visible = False
                            transition_started = False
                            final_cutscene_triggered = False
                            final_cutscene_state = None
                            is_paused = False
                            pause_selected = 0
                            esc_hold_timer = 0
                            # Start a new game: load level 1 now (but don't auto-save yet)
                            load_level(1)
                            opening_text = [
                                "One more time. Just one more time.|\nI can't give up...|right?",
                                "You're just rolling in circles.| A failure.",
                                "(Suppress it.| Just suppress it....)",
                                "The Moon...|where the first melody is..."
                            ]
                            intro_dialogue = DialogueBox(font, opening_text, autoplay=True, has_background=False)
                            active_dialogue = None
                            game_state = "INTRO"
                        elif title_selected == 1:
                            if not load_game():
                                active_dialogue = DialogueBox(font, ["No save file found."], speaker_name="System")
                elif event.type == pygame.JOYHATMOTION and event.hat == 0:
                    if event.value[0] < 0:
                        title_selected = (title_selected - 1) % len(title_buttons)
                    elif event.value[0] > 0:
                        title_selected = (title_selected + 1) % len(title_buttons)
                elif event.type == pygame.JOYBUTTONDOWN:
                    if event.button in (0, 1):
                        if title_selected == 0:
                            # Reset all game variables and start a new game via controller... 
                            #Vio = None
                            tiles = []
                            checkpoints = []
                            decorations_list = []
                            hazards = []
                            npcs = []
                            boss_manager = None
                            kira_boss_manager = None
                            ship = None
                            active_dialogue = None
                            boss_triggered = False
                            boss2_triggered = False
                            boss_finished = False
                            boss2_finished = False
                            current_level = None
                            fading = False
                            sheet_visible = False
                            transition_started = False
                            final_cutscene_triggered = False
                            final_cutscene_state = None
                            # Start a new game via controller: load level 1 now
                            load_level(1)
                            opening_text = [
                                "One more time. Just one more time.|\nI can't give up...|right?",
                                "You're just rolling in circles.| A failure.",
                                "(Suppress it.| Just suppress it....)",
                                "The Moon...|where the first melody is..."
                            ]
                            intro_dialogue = DialogueBox(font, opening_text, autoplay=True, has_background=False)
                            active_dialogue = None
                            game_state = "INTRO"
                        elif title_selected == 1:
                            if not load_game():
                                active_dialogue = DialogueBox(font, ["No save file found."], speaker_name="System")
            
            if game_state == "PLAYING":
                can_jump = not active_dialogue or (active_dialogue and active_dialogue.is_passive)
                if event.type == pygame.KEYDOWN:
                    # Debug buttons (easily disablable)
                    if DEBUG_ENABLED:
                        if event.key == pygame.K_1:
                            Vio.rect.x -= 1000
                            if current_level == 'FINAL':
                                frame_shift = 5000 // max(1, final_level_autoscroll_speed)
                                final_level_frame_count = max(0, final_level_frame_count - frame_shift)
                            camera.offset_x = max(0, Vio.rect.centerx - WIDTH // 2)
                        #    print(f"Debug warp left! X: {Vio.rect.x}, frame {final_level_frame_count}")
                        elif event.key == pygame.K_2:
                            if current_level != 'FINAL':
                                Vio.rect.x += 1000
                            if current_level == 'FINAL':
                                Vio.rect.x += 5000
                                frame_shift = 5000 // max(1, final_level_autoscroll_speed)
                                final_level_frame_count += frame_shift
                            camera.offset_x = max(0, Vio.rect.centerx - WIDTH // 2)
                        #    print(f"Debug warp right! X: {Vio.rect.x}, frame {final_level_frame_count}")
                        elif event.key == pygame.K_3:
                            Vio.rect.x += 15000
                            frame_shift = 15000 // max(1, final_level_autoscroll_speed)
                            final_level_frame_count += frame_shift
                            camera.offset_x = max(0, Vio.rect.centerx - WIDTH // 2)
                        if active_dialogue and active_dialogue.is_choice:
                            # Check if the text is done and they are confirming a choice
                            if active_dialogue.char_index >= len(active_dialogue.text_list[active_dialogue.current_sentence]):
                                if active_dialogue.selection == 0: # YES
                                    Vio.has_knife = True
                                    npcs = [n for n in npcs if n.name != "Knife"] 
                                    
                                    # Trigger the reaction
                                    active_dialogue = DialogueBox(font, [
                                        "@Captain Vio: . . . !",
                                        "I just heard someone's voice.| I have not heard it before.\n(I...don't know what to do...What if it can help?)",
                                        "@???:Yeah, right. No one else knows. No one can help. \nThey will just hinder our mission. \nWho knows what they will do?",
                                        "@Captain Vio:(Maybe...it's right. Who knows what that voice was? \nMaybe I should just....forget about it.)",
                                        #"But a knife's a knife."
                                    ], speaker_name="Captain Vio")
                                else: # NO
                                    active_dialogue = None 
                                continue # Skip the rest of the key logic
                        for npc in npcs:
                            if not active_dialogue and npc.check_interaction(Vio.rect, True):
                                active_dialogue = DialogueBox(font, npc.dialogue_text, 
                                                            speaker_name=npc.name, 
                                                            is_choice=npc.is_item)
                                npc.talk_cooldown = 30
                                talking_npc = npc
                                interaction_performed = True
                                break    
                        if interaction_performed:
                            continue


                    # Pause with P key
                    if event.key == pygame.K_p:
                        is_paused = not is_paused
                        pause_selected = 0
                        if is_paused:
                            pause_music()
                        else:
                            resume_music()
                    # Pause menu navigation
                    elif is_paused:
                        if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                            pause_selected = (pause_selected + 1) % 2
                        elif event.key in (pygame.K_z, pygame.K_RETURN, pygame.K_SPACE):
                            if pause_selected == 0:
                                # Continue game
                                is_paused = False
                                resume_music()
                            elif pause_selected == 1:
                                # Exit program
                                return
                    elif event.key == pygame.K_z and can_jump:
                        is_running = keys[pygame.K_x] and abs(Vio.vel_x) > WALK_SPEED
                        Vio.jump(is_running)
                    # ESC key hold for 3 seconds to exit
                    elif event.key == pygame.K_ESCAPE:
                        esc_hold_timer = 180  # 3 seconds at 60 FPS
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_ESCAPE:
                        esc_hold_timer = 0
                elif event.type == pygame.JOYBUTTONDOWN:
                    if event.button in (0, 1):
                        for npc in npcs:
                            if not active_dialogue and npc.check_interaction(Vio.rect, True):
                                active_dialogue = DialogueBox(font, npc.dialogue_text, speaker_name=npc.name, is_choice=npc.is_item)
                                talking_npc = npc
                                npc.talk_cooldown = 30
                                interaction_performed = True
                                break
                        if interaction_performed:
                            continue
                        if can_jump:
                            is_running = False
                            for joy in joysticks:
                                try:
                                    if (joy.get_button(2) or joy.get_button(3)) and abs(Vio.vel_x) > WALK_SPEED:
                                        is_running = True
                                        break
                                except pygame.error:
                                    continue
                            Vio.jump(is_running)
        
        # ESC hold timer countdown
        if esc_hold_timer > 0:
            esc_hold_timer -= 1
            if esc_hold_timer <= 0:
                return  # Exit program
        
        # Controller pause button (try button 6 and 7 which are often +/-)
        for joy in joysticks:
            try:
                # Button 6 or 7 is often START/+ or - button
                if (joy.get_button(6) or joy.get_button(7)) and game_state == "PLAYING":
                    is_paused = not is_paused
                    pause_selected = 0
                    if is_paused:
                        pause_music()
                    else:
                        resume_music()
                # Pause menu navigation with controller
                if is_paused and game_state == "PLAYING":
                    # Check directional buttons for pause menu nav
                    if joy.get_hat(0)[0] != 0:  # D-pad horizontal
                        pause_selected = (pause_selected + 1) % 2
                    # A button (0) to confirm pause menu selection
                    if joy.get_button(0):
                        if pause_selected == 0:
                            is_paused = False
                            resume_music()
                        elif pause_selected == 1:
                            return
            except pygame.error:
                pass
        
        # Music state manager
        if not is_paused:
            if game_state == "TITLE":
                switch_music(mus_title, -1)
            elif game_state == "INTRO":
                stop_music()
            elif game_state == "MEMORY_TRANSITION":
                switch_music(mus_her, -1)
            elif game_state == "PLAYING":
                if current_level == 1:
                    if boss_triggered and boss_manager and boss_manager.state in ("FIGHTING", "FALLING_IN"):
                        switch_music(mus_boss1, -1)
                    elif boss_triggered:
                        stop_music()
                    else:
                        switch_music(moon_song, -1)
                elif current_level == 2:
                    if boss2_triggered and boss2_state == "FIGHTING":
                        switch_music(mus_boss2, -1)

                    elif boss2_triggered:
                        stop_music()
                    else:
                        switch_music(castle_song, -1)
                elif current_level == 'FINAL':
                    update_final_level_music()
                else:
                    stop_music()
            else:
                stop_music()

        if game_state == "PLAYING" and not is_paused:
            if active_dialogue:
                
                skip = (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) and canSkip
                active_dialogue.update(keys, skip_held=skip)
                if active_dialogue.finished:
                    # Check if this was the boss intro dialogue
                    if boss_triggered and boss_manager and boss_manager.state == "INTRO":
                        boss_manager.transition_to_falling()
                    
                    # Check if this was boss2 intro dialogue
                    if boss2_triggered and boss2_state == "INTRO":
                        boss2_state = "FIGHTING"
                        if kira_boss_manager and kira_boss_manager.state == "INTRO":
                            kira_boss_manager.state = "SHIELDED"
                            kira_boss_manager.current_attack = "IDLE"
                            kira_boss_manager.attack_timer = 0
                            kira_boss_manager.shield_up = True
                        
                    active_dialogue = None
                    if talking_npc:
                        if getattr(talking_npc, 'drop_floor', False):
                            kira_is_dropping_floor = True
                            has_not_dropped_floor = False
                        talking_npc = None
            if boss_triggered and not boss_finished:
                # Set the limits (Leave a little padding so Vio doesn't touch the literal edge)
                min_x = 15000 + 10
                max_x = 15000 + 1200 - Vio.rect.width - 10
                
                # If Vio tries to go past, snap him back
                if Vio.rect.x < min_x:
                    Vio.rect.x = min_x
                elif Vio.rect.x > max_x:
                    Vio.rect.x = max_x

            else:
                # NPC dialogue is handled directly in the input event loop.
                pass
                    
        if not is_paused and game_state == "PLAYING" and active_dialogue is None and kira_is_dropping_floor:
            # Trigger the platform drop once after the TV dialogue finishes.
            floor_falling = True
            kira_is_dropping_floor = False
            #Vio.can_move = False
        
        if not is_paused and game_state == "PLAYING" and floor_falling:
            drop_zone = pygame.Rect(Vio.rect.left - TILE_SIZE, Vio.rect.bottom, Vio.rect.width + TILE_SIZE * 2, TILE_SIZE)
            for tile in tiles:
                if hasattr(tile, 'rect') and tile.rect.colliderect(drop_zone):
                    tile.rect.y += 1415
            
            if Vio.rect.y > HEIGHT + 100:
                #snd
                floor_falling = False
                Vio.can_move = True
        # Update based on game state
        if game_state == "TITLE":
            if active_dialogue:
                active_dialogue.update(keys)
                if active_dialogue.finished:
                    active_dialogue = None
        elif game_state == "INTRO":
            # Skip intro dialogue by holding Shift (for dev testing)
            skip_held = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
            intro_dialogue.update(keys, skip_held=skip_held)
            if intro_dialogue.finished:
                game_state = "PLAYING"
                # Save game now that the level has actually started (overwrite previous save)
                #try:
                    #save_game_state()
                #except Exception:
                   # pass
        elif game_state == "PLAYING" and not is_paused:
            global flash_lights_active, flash_lights_timer, flash_lights_intensity
            if ship.taking_off:
                camera.update(ship.rect)
            else:
                camera.update(Vio.rect)

            # Only lock controls if dialogue is NOT passive or if cutscene target is set
            cutscene_mode = (active_dialogue and not getattr(active_dialogue, 'is_passive', False)) or Vio.cutscene_target_x is not None
            Vio.update(tiles, trail_particles, cutscene_mode=cutscene_mode)
            if getattr(Vio, 'is_holding_violin', False) and vio_violin_anim is not None:
                vio_violin_anim.update(dt)
            # Handle ship scene if in ship level
            if current_level == 'SHIP':
                handle_ship_scene()
            
            # Check if transitioning from ship to final level
            global ship_to_final_transition
            if ship_to_final_transition:
                tiles, checkpoints, decorations_list = load_level('FINAL')
                save_game_state()  
                #print("DEBUG: active_dialogue being made")

                #active_dialogue = DialogueBox(font, [
                #    "You stand at the precipice of eternity.",
                #    "The melody awaits.",
                #    "Will you finally play it right?"
                #], speaker_name="???", autoplay=False, has_background=True)
                ship_to_final_transition = False
                flash_lights_active = False
            
            # Final level updates
            if current_level == 'FINAL':
                #final_level_frame_count += 1
                if active_dialogue is None and not final_level_autoscroll and final_level_frame_count == 0 and final_intro_dialogue_not_started:
                    active_dialogue = DialogueBox(font, [
                    "@Captain Vio_Surprised:It...|The door just opened...* I'm here.| I'm actually here, Lin! I'm \ncoming!",
                    "@???:Did you forget?| This train will crash.| You will die a horrible death. |\nBut you can still leave.| ",
                    "@Captain Vio:I will continue.| I'm here now.* This has been \na long time waiting.",
                    "@Captain Vio_Joy:I'm coming for you, Lin!"
                    #"The melody awaits.",
                    #Will you finally play it right?"
                        ], autoplay=False, has_background=True)
                    final_intro_dialogue_not_started = False
                # Start autoscroll when intro dialogue finishes
                if active_dialogue is None and not final_level_autoscroll and final_level_frame_count < 90:
                    final_level_frame_count += 1

                if final_level_frame_count >= 90 and not final_cutscene_triggered:
                    final_level_frame_count += 1
                    final_level_autoscroll = True

                if final_level_autoscroll and floating_dialogue_queue is None:
                    final_level_dialogue_queues[1] = create_final_level_dialogue_queue(1, font)
                    final_level_dialogue_queues[2] = create_final_level_dialogue_queue(2, font)
                    final_level_dialogue_queues[3] = create_final_level_dialogue_queue(3, font)
                    floating_dialogue_queue = final_level_dialogue_queues[1]
                    final_level_dialogue_queue_phase = 1

                    # Initialize sprite animators for cutscene (only once per run)
                    try:
                        lin_sheet = pygame.image.load('Lin.png').convert_alpha()
                        # Lin.png: 192x168, 2 rows. Row 0: 2 frames (64px each). Row 1: 3 frames (64px each). Height: 84px per row.
                        lin_idle_frames = extract_frames(lin_sheet, 0, 0, 2, lin_sheet.get_width() // 3, lin_sheet.get_height() // 2, 2)
                        lin_perform_frames = extract_frames(lin_sheet, 1, 0, 3, lin_sheet.get_width() // 3, lin_sheet.get_height() // 2, 2)
                    except Exception as e:
                        lin_idle_frames = []
                        lin_perform_frames = []
                       # print(f"Warning: Could not load Lin.png: {e}")

                    try:
                        vio_violin_sheet = pygame.image.load('Vio(Violin).png').convert_alpha()
                        vio_violin_frames = extract_frames(vio_violin_sheet, 0, 0, 5, vio_violin_sheet.get_width() // 5, vio_violin_sheet.get_height(), 2)
                    except Exception as e:
                        vio_violin_frames = []
                        #print(f"Warning: Could not load Vio(Violin).png: {e}")

                    lin_idle_anim = SpriteAnimator(lin_idle_frames, durations=300, loop=True)
                    lin_perform_anim = SpriteAnimator(lin_perform_frames, durations=[200, 200, 200], loop=True)
                    vio_violin_anim = SpriteAnimator(vio_violin_frames, durations=150, loop=True)

                    final_level_tentacle_schedule = [
                        {'frame': 5640, 'direction': 'RIGHT', 'tracking_frames': 65, 'locked_frames': 20, 'strike_frames': 30, 'delay_after': 0, 'triggered': False},
                        {'frame': 5990, 'direction': 'TOP', 'tracking_frames': 45, 'locked_frames': 38, 'strike_frames': 28, 'delay_after': 0, 'triggered': False},
                        {'frame': 6190, 'direction': 'LEFT', 'tracking_frames': 50, 'locked_frames': 52, 'strike_frames': 32, 'delay_after': 0, 'triggered': False},
                        {'frame': 6350, 'direction': 'BOTTOM', 'tracking_frames': 35, 'locked_frames': 38, 'strike_frames': 26, 'delay_after': 0, 'triggered': False},
                        {'frame': 6540, 'direction': 'LEFT', 'tracking_frames': 35, 'locked_frames': 65, 'strike_frames': 24, 'delay_after': 0, 'triggered': False},
                        {'frame': 6740, 'direction': 'BOTTOM', 'tracking_frames': 25, 'locked_frames': 55, 'strike_frames': 24, 'delay_after': 0, 'triggered': False},
                        {'frame': 6740, 'direction': 'LEFT', 'tracking_frames': 35, 'locked_frames': 75, 'strike_frames': 24, 'delay_after': 0, 'triggered': False},
                        {'frame': 7500, 'direction': 'LEFT', 'tracking_frames': 45, 'locked_frames': 48, 'strike_frames': 28, 'delay_after': 0, 'triggered': False},
                        {'frame': 7500, 'direction': 'BOTTOM', 'tracking_frames': 45, 'locked_frames': 48, 'strike_frames': 28, 'delay_after': 0, 'triggered': False},
                        {'frame': 7800, 'direction': 'RIGHT', 'tracking_frames': 35, 'locked_frames': 50, 'strike_frames': 28, 'delay_after': 0, 'triggered': False},
                        {'frame': 7950, 'direction': 'LEFT', 'tracking_frames': 50, 'locked_frames': 85, 'strike_frames': 28, 'delay_after': 0, 'triggered': False},
                        #{'frame': 7850, 'direction': 'LEFT', 'tracking_frames': 35, 'locked_frames': 55, 'strike_frames': 24, 'delay_after': 0, 'triggered': False},
                        {'frame': 8200, 'direction': 'RIGHT', 'tracking_frames': 50, 'locked_frames': 50, 'strike_frames': 30, 'delay_after': 0, 'triggered': False},
                        {'frame': 8200, 'direction': 'TOP', 'tracking_frames': 55, 'locked_frames': 70, 'strike_frames': 28, 'delay_after': 0, 'triggered': False},
                        {'frame': 8400, 'direction': 'RIGHT', 'tracking_frames': 50, 'locked_frames': 50, 'strike_frames': 30, 'delay_after': 0, 'triggered': False},
                        {'frame': 8500, 'direction': 'BOTTOM', 'tracking_frames': 30, 'locked_frames': 40, 'strike_frames': 28, 'delay_after': 0, 'triggered': False},
                        {'frame': 8600, 'direction': 'BOTTOM', 'tracking_frames': 30, 'locked_frames': 40, 'strike_frames': 28, 'delay_after': 0, 'triggered': False},
                        {'frame': 8700, 'direction': 'BOTTOM', 'tracking_frames': 30, 'locked_frames': 40, 'strike_frames': 28, 'delay_after': 0, 'triggered': False},
                        {'frame': 8800, 'direction': 'BOTTOM', 'tracking_frames': 30, 'locked_frames': 40, 'strike_frames': 28, 'delay_after': 0, 'triggered': False},
                        {'frame': 8900, 'direction': 'BOTTOM', 'tracking_frames': 30, 'locked_frames': 40, 'strike_frames': 28, 'delay_after': 0, 'triggered': False},
                        #{'frame': 9000, 'direction': 'BOTTOM', 'tracking_frames': 30, 'locked_frames': 40, 'strike_frames': 28, 'delay_after': 0, 'triggered': False},
                        #{'frame': 8600, 'direction': 'TOP', 'tracking_frames': 45, 'locked_frames': 20, 'strike_frames': 28, 'delay_after': 0, 'triggered': False},
                        #{'frame': 8400, 'direction': 'RIGHT', 'tracking_frames': 50, 'locked_frames': 50, 'strike_frames': 30, 'delay_after': 0, 'triggered': False},
                    ]

                if final_level_autoscroll:
                    current_final_phase = get_final_level_phase_from_frame(final_level_frame_count)
                    if final_level_dialogue_queue_phase != current_final_phase:
                        if final_level_dialogue_queues.get(current_final_phase) is None:
                            final_level_dialogue_queues[current_final_phase] = create_final_level_dialogue_queue(current_final_phase, font)
                        floating_dialogue_queue = final_level_dialogue_queues[current_final_phase]
                        final_level_dialogue_queue_phase = current_final_phase

                if final_level_autoscroll and final_level_tentacle_schedule:
                    for entry in final_level_tentacle_schedule:
                        if not entry.get('triggered', False) and final_level_frame_count >= entry['frame']:
                            tentacle_attacks.append(TargetedTentacleStrike(
                                entry['direction'], Vio, font,
                                tracking_frames=entry['tracking_frames'],
                                locked_frames=entry['locked_frames'],
                                strike_frames=entry['strike_frames'],
                                image=shadow_tentacle_img,
                                screen_padding=30,
                            ))
                            entry['triggered'] = True

                if final_level_autoscroll and not final_cutscene_triggered and camera.offset_x >= final_cutscene_trigger_x:
                    #print(f"DEBUG: Triggering final cutscene at frame {final_level_frame_count}, camera.offset_x={camera.offset_x}")
                    final_cutscene_triggered = True
                    final_cutscene_state = 'TALKING'
                    final_level_autoscroll = False
                    #Vio.can_move = False
                    final_cutscene_timer = 0
                    final_cutscene_music_stopped = False
                    final_cutscene_dialogue_started = False
                    # Initialize cutscene dialogue
                    if active_dialogue is None:
                        active_dialogue = DialogueBox(font, [
                            "@Captain Vio_Joy:.....Lin!",
                            "@Captain Vio_Surprised:What's going on?",
                            "@Lin:Vio! H-Help! I heard a strange noise. I decided to check it out. But...|\nThe Conductor seems unconscious. And the train is going \nout of control.",
                            "I'm trying to figure out what's going on, but the terminal is \njust showing errors.| At this rate....|We're going to crash!",
                             "I found this old...|resonance device. It might help controlling the \ntrain, but it needs a 'two-part harmonic balance' or something.", 
                            "Who ever thought of this old machinery, anyway?",
                            "@Captain Vio_Joy:.......",
                            "Alright, sounds easy. We both already have our instruments, right?"
                        ], autoplay=False, has_background=True)
                #now, when the current line is 3, Vio will walk right, but I have to make sure it's indented where it should be, so that it works:
                
                if floating_dialogue_queue is not None:
                    floating_dialogue_queue.update(dt)
                
                
                if final_cutscene_triggered and final_cutscene_state == 'TALKING':
                    
                    try:
                        current_line_idx = active_dialogue.current_sentence if active_dialogue is not None else 0
                    except Exception:
                        current_line_idx = 0
                    if hasattr(lin_idle_anim, 'flip_horizontal'):
                        lin_idle_anim.flip_horizontal = (current_line_idx in (2, 3))

                    if current_line_idx >= 2 and Vio.cutscene_target_x is None and Vio.rect.centerx < 165000:
                        Vio.can_move = False
                        Vio.cutscene_target_x = 165000
                    
                    # Update animator
                    if hasattr(lin_idle_anim, 'update'):
                        lin_idle_anim.update(dt)
                    
                    # Transition to PERFORMING when dialogue finishes
                    if active_dialogue is None or (active_dialogue and active_dialogue.finished):
                        final_cutscene_state = 'PERFORMING'
                        if hasattr(lin_perform_anim, 'reset'):
                            lin_perform_anim.reset()
                        if hasattr(vio_violin_anim, 'reset'):
                            vio_violin_anim.reset()
                        # Hide the regular Vio sprite while the cutscene performing animation shows
                        try:
                            Vio.visible = False
                        except Exception:
                            pass
                        final_cutscene_timer = 0
                        # Stop background music and start duet
                        stop_music()
                        #try:
                        pygame.mixer.music.load('Their Duet.mp3')
                        pygame.mixer.music.play(0)
                        #except Exception as e:

                        #    print(f"Warning: Could not play Their Duet.mp3: {e}")
                        active_dialogue = None

                elif final_cutscene_triggered and final_cutscene_state == 'PERFORMING':
                    # Update performing animators
                    if hasattr(lin_perform_anim, 'update'):
                        lin_perform_anim.update(dt)
                    if hasattr(vio_violin_anim, 'update'):
                        vio_violin_anim.update(dt)
                    
                    final_cutscene_timer += dt
                    # After 12 seconds (12000ms), transition to FADE_TO_BLACK
                    if final_cutscene_timer >= 12000:
                        final_cutscene_state = 'FADE_TO_BLACK'
                        cockpit_fade_alpha = 0  # Initialize fade

                elif final_cutscene_triggered and final_cutscene_state == 'FADE_TO_BLACK':
                    # Fade to black over 2 seconds (2000ms)
                    rate = 255.0 / 2000.0
                    cockpit_fade_alpha = min(255, cockpit_fade_alpha + dt * rate)
                    
                    # Stop music and show placeholder when fully faded
                    if cockpit_fade_alpha >= 255:
                        try:
                            pygame.mixer.music.stop()
                        except Exception:
                            pass
                        if active_dialogue is None:
                            after_dialogue = [
                        
                                #"@Lin:Um, Vio? Why do you look suddenly older?| And, your eyes...\nwhat happened?",
                                #"@Captain Vio:.....Umm..."
                                "@Lin:Can you hear that? Do you hear the audiance?* There are so \nmany people.",
                                "Your hands are shaking again...",
                                "@Captain Vio:I-It's fine.| I'm fine now.",
                                "Let's play now. Together.",
                               
                               # "@Captain Vio:Lin,| I have something to tell you..."
                                #"Or some time later, another memory. Maybe they play the recital"

                               # "You find yourself back in the place where you first met Lin.| But something feels different.",
                                
                                ]
                            active_dialogue = DialogueBox(font, after_dialogue, autoplay=False, has_background=True)
                        # Restore Vio visibility once the cutscene has faded to the "To be continued" screen
                        try:
                            Vio.visible = True
                        except Exception:
                            pass
                        final_cutscene_state = 'CUTSCENE_DONE'
                if final_cutscene_state == 'CUTSCENE_DONE' and active_dialogue is None:
                    game_state = "CREDITS"
                    credits_y = HEIGHT
                    final_cutscene_triggered = False
                if final_level_autoscroll:
                    if current_final_phase == 1:
                        Vio.max_health =5
                        #Vio.health = Vio.max_health 
                        
                    if current_final_phase == 2:
                        #Vio.max_health += 1
                        #Vio.health = Vio.max_health + 2
                        Vio.max_health =6
                    if current_final_phase == 3:
                        Vio.max_health =7
                        #Vio.health = Vio.max_health + 3
                if final_level_autoscroll and current_final_phase >= 3 or final_cutscene_triggered:
                    if final_phase_shake_timer <= 0 and random.random() < 0.03:
                        final_phase_shake_timer = random.randint(5, 12)
                        final_phase_shake_offset = (random.randint(-6, 6), random.randint(-4, 4))
                    if final_cutscene_triggered: #more rigerous camera shake
                        if final_phase_shake_timer <= 0 and random.random() < 0.05:
                            final_phase_shake_timer = random.randint(5, 12)
                            final_phase_shake_offset = (random.randint(-8, 8), random.randint(-5, 5))
                    if final_phase_shake_timer > 0:
                        final_phase_shake_timer -= 1
                        if final_phase_shake_timer <= 0:
                            final_phase_shake_offset = (0, 0)
                

                if final_cutscene_state == 'BOUNDARY_DIALOGUE' and active_dialogue is None:
                    #final_level_autoscroll = True
                    Vio.can_move = True
                    final_cutscene_state = 'BOUNDARY_DONE'

                for attack in tentacle_attacks[:]:
                    attack.update()
                    if attack.finished:
                        tentacle_attacks.remove(attack)
            
            # Update trail particles and remove dead ones
            for trail in trail_particles[:]:
                trail.update()
                if not trail.is_alive():
                    trail_particles.remove(trail)
            
            update_neon_toggle()
            
            #if active_dialogue:
                #Vio.update_animation()
            
            for cp in checkpoints:
                cp.update(Vio)
            for hazard in hazards:
                if not active_dialogue and not (boss_triggered and isinstance(hazard, Shadow)):
                    hazard.update(Vio)
                if not fading and not (boss_triggered and isinstance(hazard, Shadow)) and hazard.check_player(Vio):
                    hazard.on_hit(Vio)
            for tile in tiles:
                if hasattr(tile, 'update'):
                    tile.update(Vio.rect)
                if hasattr(tile, 'check_player') and not fading:
                    tile.check_player(Vio)
            if Vio.rect.y > HEIGHT + 10000 and not fading:
                Vio.take_damage(Vio.max_health)
            if Vio.is_dead() and not fading:
                fading = True
                Vio.vel_x = 0  
                Vio.vel_y = 0  
                if not Vio.dead_animation_started:
                    Vio.die()
                    for _ in range(20):
                       
                        angle = random.uniform(0, 2 * math.pi)
                        speed = random.uniform(2, 8)
                        vx = math.cos(angle) * speed
                        vy = math.sin(angle) * speed
                        color = (200, 100, 255)
                        particles.append(Particle(Vio.rect.centerx, Vio.rect.centery, vx, vy, random.randint(2, 4), color))


            #========LEVEL 1 BOSS=====================================
            if current_level == 1 and boss_triggered and boss_manager:
                if ship and not ship.active:
                        ship.activate()
                if ship and ship.active:
                    if Vio.rect.colliderect(ship.rect) and not ship.taking_off and current_level == 1:
                        if z_currently_held and not z_was_held:
                            Vio.visible = False 
                            Vio.can_move = False 
                            
                            ship.start_takeoff(2)

                    if ship.update() and current_level == 1:
                        game_state = "MEMORY_TRANSITION" 
                        memory_text = [
                            "@Lin:Wait, Vio! You're playing too fast again! We can't play like that \nat our performance.",
                            ".....",
                            "@Lin:...I'm sorry.| It's just, I get nervous, and I really want it to be perfect.| \nI worked really hard composing this piece.* But maybe \nI'm pushing you too hard.",
                            "@Captain Vio (young)_Young: Yeah. You're right...|I'm playing too fast.* \nI'm really trying though. Let's try again.", # I just hope I can stand up to you when we play at the same time. It's harder to hear my mistakes when you're playing too. ",
                            #"@: ",
                            #"@: "
                        ]
                        
                        active_dialogue= DialogueBox(font, memory_text, autoplay = False, has_background=True, is_passive=False)
                        #if ship.target_level is not None:
                            #load_level(ship.target_level)
            
            # Level 2 ship interaction
            if current_level == 2 and ship and ship.active:
                if Vio.rect.colliderect(ship.rect) and not ship.taking_off:
                    if z_currently_held and not z_was_held:
                        Vio.visible = False
                        Vio.can_move = False  
                        ship.start_takeoff('SHIP')
                if ship.update():
                    game_state = "MEMORY_TRANSITION"
                    if ship.target_level == 'SHIP':
                        memory_text = [
                            "@Captain Vio:....|One more...|One more melody.* Then I get another chance...",
                            "@Captain Vio_Down:........"
                            #"@Lin:I can see that you're trembling...|"
                            #""
                        
                        ]
                    if current_level == 2:
                            memory_text = [
                                        "@Lin:Wow, can you believe it, Vio?| Tomorrow's the day.* We've worked \nreally hard for this, and we've made a lot of progress.",
                                        "@Captain Vio (young)_Young:Yeah, but...| We've never been on the Space Express before.| \nYou...aren't scared at all?| I'm...terrified.",
                                        "@Lin:Of course I'm scared. I've never been on the train either.| But \ndon't worry.| I know you don't like to be alone, I'll be with you the \nwhole time.* Our song...is only complete if we play it together.",
                                        "@Captain Vio (young)_Young:Y-Yeah, let's just focus on playing, and we should be fine.* \nIt's just another method of transportation, right?| \nE-Everything is going to be okay...* I won't let you down."
                                    ]
                    else:
                        #switch_music(mus_her)
                        memory_text = [
                            "@Lin:Wait, Vio! You're playing too fast again! We can't play like that at our \nperformance.",
                            "@Lin:...Sorry. I'm just nervous. I want it to be perfect. \nI worked really hard composing this piece.",
                            "@Captain Vio (young)_Young:No. You're right. I'm trying my hardest though. Let's try again, \none more time, from the start. And don't worry, we will get this piece \nright.",
                            "@???:~",
                            "But...| You left her behind. And now you're trying in vain to chase \nafter times that will never come back. You just can't save her. When \nwill you come to your senses, and let me...|.|.|.",
                            "@Captain Vio:...No...|No I can't...|I can't give up. Even if I have \nto....|go to that place again. "

                        ]
                    active_dialogue = DialogueBox(font, memory_text, autoplay=False, has_background=True, is_passive=False)
            
            # Ship level takeoff
            if current_level == 'SHIP' and ship and ship.taking_off:
                if ship.update():
                    
                    fading = True 
            
            if not boss_triggered and Vio.rect.x > BOSS_ARENA1_START_X and Vio.rect.x <17000 and current_level==1:
                
                boss_triggered = True
                # Create the boss and manager
                mo_boss = DJOserBoss(15000 + WIDTH // 2 - TILE_SIZE, 780, mo_boss_img, font)
                boss_manager = BossManager(mo_boss, boombox_img, shockwave_img, font)
                boss_state = "INTRO"
                
                
                if boss_first_entry:
                    active_dialogue = DialogueBox(
                        font, 
                        [
                            "YO! YO! YO! What up, Captain? Wanna jam with good ol' DJ Oser?",
                            "@Captain Vio:The music sheet, Mo.* Now. ",
                            "@DJ Oser:GASP! Mo? I'm DJ Oser now! See, I used to be just an unconscious \nmeteor, but now,--",
                            "@Captain Vio_Down: ......",
                            "@DJ Oser:Uh...what's that look for? \nYer ruining the good vibes. I should teach you a lesson. \nOHHOHOHOHOHOHOHHOHOHOHOHOHOOO!!!"
                        ],
                        speaker_name="DJ Oser",
                        has_background=True
                    )
                    boss_first_entry = False
                    
            
                else:    
                    boss_manager.transition_to_falling()
                    boss_state = "FIGHTING"
                    active_dialogue = None
            if active_dialogue and boss_state == "INTRO":
                #Vio.vel_x =0
                if active_dialogue.current_sentence == 3: 
                    if Vio.cutscene_target_x is None: # Only set it once
                        Vio.cutscene_target_x = 15000 + 100
                        Vio.cutscene_speed = 1.0
            # Update boss manager if active
            if boss_manager:
                boss_manager.update(Vio, keys)
                if boss_manager.battle_dialogue:
                    active_dialogue = boss_manager.battle_dialogue
                # Check for wave collisions with player
                boss_manager.check_wave_player_collision(Vio)
                
                # Check for player attacks on BoomBox buttons
                if Vio.is_dashing:  # Player can attack buttons while dashing
                    for box in boss_manager.boomboxes:
                        button_rect = pygame.Rect(box.button_x - box.button_radius, 
                                                box.button_y - box.button_radius, 
                                                box.button_radius * 2, box.button_radius * 2)
                        if Vio.rect.colliderect(button_rect):
                            if box.button_is_glowing:
                                if box.take_damage(1):
                                    # Box destroyed - could add explosion effect here
                                    pass
                            else:
                                pass
                # Apply screen shake from boss manager
                if boss_manager.shake_duration > 0:
                    camera.shake_x = random.randint(-boss_manager.shake_intensity, boss_manager.shake_intensity)
                    camera.shake_y = random.randint(-boss_manager.shake_intensity, boss_manager.shake_intensity)
                else:
                    camera.shake_x = 0
                    camera.shake_y = 0
                
                # Check for boss fight completion
                if boss_manager.state == "BONK":
                    # Trigger final cutscene
                    active_dialogue = DialogueBox(
                        font,
                        [
                           "My precious delight! My...my precious......."
                        ],
                        speaker_name="Moistar", autoplay= True, auto_delay = 50,
                        has_background=True
                    )
                    boss_manager.state = "FINISHED"

          #  if boss_manager and boss_manager.state == "FINISHED" and current_level == 1:
          #      if ship and not ship.active:
          #          ship.activate()
            #if ship and ship.active:
             #   if Vio.rect.colliderect(ship.rect) and not ship.taking_off:
              #      if z_currently_held and not z_was_held:
               #         Vio.visible = False 
                #        Vio.can_move = False 
                        
                 #       ship.start_takeoff(2)

          #          memory_text = [
          #              "@Lin:Wait, Vio! You're playing too fast again! We can't play like that at our \nperformance.",
          #              "@Lin:...Sorry. I'm just nervous. I want it to be perfect. \nI worked really hard composing this piece.",
          #              "@Captain Vio_Young: Yeah. You're right. I'm trying my hardest though. Let's try again, \none more time, from the start. And don't worry, we will get this piece \nright.",
          #              "@???:~",
          #              "But...| You left her behind. And now you're trying in vain to chase \nafter times that will never come back. You just can't save her. When \nwill you come to your senses, and let me...|.|.|.",
          #              "@Captain Vio:...No...|No I can't...|I can't give up. Even if I have \nto....|go to that place again. "
          #          ]
          #      active_dialogue = DialogueBox(font, memory_text, autoplay=False, has_background=True, is_passive=False)
                #if ship.target_level is not None:
                    #load_level(ship.target_level)
        
                #boss_triggered = False
            #DRAW===================================

            #======LEVEL 2 BOSS==============================
            if Vio.rect.x > BOSS2_ARENA_LEFT and Vio.rect.x < BOSS2_ARENA_LEFT + BOSS2_ARENA_WIDTH and current_level==2 and not boss2_triggered and not boss2_finished:
                
                kira_boss_manager = KiraBossManager(
                    font,
                    arena_origin=(BOSS2_ARENA_LEFT, -HEIGHT + 1500),
                    boss_offset=(1000, 980), #1480
                    arena_size=(WIDTH*2, HEIGHT*2 + 400),
                    vulnerable_y_offset=300,
                )
                boss2_triggered = True
                if boss2_first_time == True:
                    boss2_state = "INTRO"
                    boss2_dialogue = ["@Princess Kira:Yay! You're finally here! |Sorry about making you go through the... \n'Fun Route', but now I know your capabilites. |Welcome to the stage! \nSo, let's really see if you're worthy to sing with me.| \nLet's start with--",
                                      "@Captain Vio:No.* I just want the music sheet.",
                                      "@Princess Kira:H-How do you know anything about that?| And seriously, \nwhat is that look on your face?| No one comes to my stage \nand orders me around! You saw the dangers in this castle, so why \nprovoke me? You really are strange...",
                                      "I felt alone. Waiting...|After what happened to--",
                                      "@Captain Vio:...I will take it by force if I have to. \nI know that asking for it is useless. You won't give it to me. \nJust fight me already.",
                                      "@Princess Kira: ...No, you WILL stay, even if I DO have to knock some sense into you. \n(I was probably going to shoot lasers at you just for fun anyway!)"
                                      
                                      ]
                    boss2_first_time = False
                    active_dialogue = DialogueBox(font, boss2_dialogue, speaker_name="Princess Kira")
                else: 
                    boss2_state = "FIGHTING"
            if boss2_triggered:
                if boss2_state == "INTRO":
                    if active_dialogue:

                        if active_dialogue.current_sentence == 1: 
                            if Vio.cutscene_target_x is None:
                                Vio.cutscene_target_x = 22000 +100
                                Vio.cutscene_speed = 1.0
                        if active_dialogue.current_sentence == 4: 
                            if Vio.cutscene_target_x is None:
                                Vio.cutscene_target_x = 22000 +200
                                Vio.cutscene_speed = 1.0
                #game_state = "BOSS2_FIGHT"
                kira_boss_manager.update(Vio, active_neon_color, npcs)
                if boss2_state == "FIGHTING":
                    kira_boss_manager.check_lever_collisions(npcs, Vio)
                    if kira_boss_manager.battle_dialogue and active_dialogue is None:
                        active_dialogue = kira_boss_manager.battle_dialogue
                    kira_boss_manager.check_player_damage(Vio, npcs)

                if not boss2_finished:
                    min_x = BOSS2_ARENA_LEFT + 10
                    max_x = BOSS2_ARENA_LEFT + BOSS2_ARENA_WIDTH - Vio.rect.width - 10
                    min_y = BOSS2_ARENA_TOP
                    max_y = BOSS2_ARENA_TOP + BOSS2_ARENA_HEIGHT - Vio.rect.height

                    if Vio.rect.x < min_x:
                        Vio.rect.x = min_x
                    elif Vio.rect.x > max_x:
                        Vio.rect.x = max_x
                    if Vio.rect.y < min_y:
                        Vio.rect.y = min_y
                    elif Vio.rect.y > max_y:
                        Vio.rect.y = max_y
                if kira_boss_manager.state == "DEFEATED_GROUNDED" and not kira_boss_manager.defeat_dialogue_triggered:
                    boss2_state = None
                    #stop_music()
                    active_dialogue = DialogueBox(font, ["@Princess Kira: ....S-Stop!| That's enough.| Take your precious music sheet...|\nWe both know there's something clearly missing about it.",
                                                         "But, I can see that looks in your eyes.| \nYou know full well what it sounds like.", # probably unused: if you ever have the time, come back, won't you? Please, I'm so lonely...", #You Well, fine, just take it already..."
                                                         "@Captain Vio: (...So predictable. But it's not like she'll say something \ndifferent this time.)",
                                                         "@Princess Kira: What am I supposed to do now?| I can't just abondon my castle.",
                                                         "But..| I am getting tired of singing alone. |\nAnd I'm hungry. Hmmmmm.......What to do..."
                                                         #"If...If you find the time...|"


                                                         ], speaker_name="Princess Kira")
                    kira_boss_manager.defeat_dialogue_triggered = True
                    global boss2_defeated
                    boss2_defeated = True
                    
            # Debug ship spawn
            if DEBUG_SHIP_SPAWN and current_level == 2 and not ship:
                ship = Ship(21000, 2200, ship_img)
                ship.activate()
            
            # Level 2 boss defeat transition
            if boss2_defeated and active_dialogue is None and not transition_started:
                # Spawn Melody2 sheet beside Kira
                kira_pos = kira_boss_manager.arena_origin + kira_boss_manager.boss_offset
                sheet_x = kira_pos.x + 100 #23000 # Beside Kira (x=23000+100=23100, y=2172)
                sheet_y = kira_pos.y        #2172
                sheet_img = pygame.image.load("Melody2.png").convert_alpha()
                sheet_img = pygame.transform.scale(sheet_img, (48, 48))
                sheet_visible = True
                sheet_spawned = True
                # Auto-walk Vio to the sheet
                Vio.cutscene_target_x = sheet_x
                Vio.can_move = False
                transition_started = True
            if transition_started:

                if sheet_visible:
                    sheet_rect = pygame.Rect(sheet_x, sheet_y, 48, 48)
                    if Vio.rect.colliderect(sheet_rect):
                        # Collection: Start violin state
                        Vio.is_holding_violin = True
                        # Hide regular Vio while the violin animation plays
                        try:
                            Vio.visible = False
                        except Exception:
                            pass
                        violin_timer = 8 * 60  # 8 seconds at 60 FPS
                        Melody2.play()
                        sheet_visible = False  # Hide sheet
                        Vio.cutscene_target_x = None

                if violin_timer > 0:
                    violin_timer -= 1
                    if violin_timer <= 0:
                        transition_fading = True
                
                if transition_fading: #=====THE SECOND MELODY MEMORY=======
                    transition_fade_alpha = min(255, transition_fade_alpha + 5)
                    
                    if transition_fade_alpha >= 255 and not memory_started:
                        #game_state = "MEMORY_TRANSITION"
                        #switch_music(mus_her)
                        active_dialogue = DialogueBox(font, [
                            "Are you still here?* Do you even play with meaning anymore?",
                            "Or is the right question: With what meaning do you now play?",

                          #"@Lin:Wow, can you believe it, Vio?| Tomorrow's the day.* We've worked \nreally hard for this, and we've made a lot of progress.",
                          #  "@Captain Vio (young)_Young:Yeah, but...| We've never been on the Space Express before.| \nYou...aren't scared at all?| I'm...terrified.",
                          #  "@Lin:Of course I'm scared. I've never been on the train either.| But \ndon't worry.| I know you don't like to be alone, I'll be with you the \nwhole time.* Our song...is only complete if we play it together.",
                          #  "@Captain Vio (young)_Young:Y-Yeah, let's just focus on playing, and we should be fine.* \nIt's just another method of transportation, right?| \nE-Everything is going to be okay...* I won't let you down."
                        ], )
                        
                        memory_started = True
                    #elif transition_fade_alpha == 255:
                        #switch_music(mus_her)
                    if memory_started and active_dialogue is None and not transition_fade_in:
                        transition_fade_in = True
                        transition_fading = False
                
                if transition_fade_in:
                    transition_fade_alpha = max(0, transition_fade_alpha - 5)
                    if transition_fade_alpha <= 0:
                        transition_fade_in = False
                        # Spawn ship
                        ship.rect.centerx = sheet_x + 200
                        ship.rect.bottom = sheet_y + 48
                        ship.active = True
                        Vio.can_move = True
                        Vio.cutscene_target_x = None
                        # Ensure Vio's normal sprite is visible again after the transition
                        try:
                            Vio.visible = True
                        except Exception:
                            pass
                    



            if current_level == 'SHIP':
                screen.fill((0, 0, 0))
            else:
                screen.fill((124, 57, 103))

            for star in stars:
                if not (is_paused and game_state == "PLAYING"):
                    star.update()
                if current_level == 'SHIP':
                    star.x -= 0.8  # Move left
                    star.y += 0.3  # Move down slightly
                    star.speed = 32
                    # Wrap around if star goes off screen
                    if star.x < 100:
                        star.x = max_world_width - 100
                    if star.y > max_world_height + 100:
                        star.y = -100
                if current_level == 'FINAL' and final_level_autoscroll and not (is_paused and game_state == "PLAYING"):
                    star.x -= 15.8
                    star.y += 0.3
                    star.speed = 32
                    screen_x = int(star.x - camera.offset_x * star.parallax)
                    screen_y = int(star.y - camera.offset_y * star.parallax)
                    if screen_x < -100:
                        star.x = camera.offset_x * star.parallax + WIDTH + 100
                    if screen_y > HEIGHT + 48:
                        star.y = camera.offset_y * star.parallax - 48
                star.draw(screen, camera)

            for decoration in decorations_list:
                decoration.draw(screen, camera) 

            # Draw sheet after decorations to avoid being behind
            if sheet_visible:
                screen.blit(sheet_img, camera.apply(pygame.Rect(sheet_x, sheet_y, 48, 48))) 

            for hazard in hazards:
                
                screen.blit(hazard.image, camera.apply(hazard.rect))
            if current_level == 'SHIP' and ship_image:
                screen.blit(ship_image, (0 - camera.offset_x, -300 - camera.offset_y))
            for tile in tiles:
                # Draw different colors based on tile type
                if tile.type == 'shockwave':
                    tile.update(Vio.rect)
                if tile.type == 'normal':
                    color = (155, 173, 183)  # grey
                    #if current_level != 'FINAL':
                    if not tile.image:
                        pygame.draw.rect(screen, color, camera.apply(tile.rect))
                    if tile.image:
                        screen.blit(tile.image, camera.apply(tile.rect))
                elif tile.type == 'platform':
                    # Platform: draw thin horizontally (half height)
                    color = (10, 200, 255)  # Light blue
                    visual_rect = tile.rect.copy()
                    visual_rect.height = TILE_SIZE // 2
                    pygame.draw.rect(screen, color, camera.apply(visual_rect))
                elif tile.type == 'wall':
                    # Wall: draw a thin side wall to show one-way collision
                    color = (150, 100, 200)  # Purple
                    visual_rect = tile.rect.copy()
                    visual_rect.width = max(4, TILE_SIZE // 5)
                    visual_rect.centerx = tile.rect.centerx
                    pygame.draw.rect(screen, color, camera.apply(visual_rect))
                elif tile.type == 'neon':
                    tile.draw(screen, camera)
                elif tile.type == 'neonlaser':
                    tile.draw(screen, camera)
                elif tile.type == 'moonspike' or tile.type == 'shockwave':
                    if tile.type == 'shockwave' and hasattr(tile, 'current_image'):
                        screen.blit(tile.current_image, camera.apply(tile.rect))
                    elif tile.image:
                        screen.blit(tile.image, camera.apply(tile.rect))
                    else:
                        color = (220, 220, 220)
                        pygame.draw.rect(screen, color, camera.apply(tile.rect))
                elif tile.type == 'shadow':
                    tile.draw(screen, camera)
                elif tile.type == 'invisible':
                    pass
                else:
                    color = (150, 150, 150)  # Gray fallback
                    pygame.draw.rect(screen, color, camera.apply(tile.rect))

        
        # Fade to black and restart (only in playing state)
        if game_state == "PLAYING" and fading:
            fade_alpha += 5  # Fade speed
            if fade_alpha >= 255:
                # Restart everything
                handle_player_death(Vio, hazards, tiles, camera, particles, trail_particles)
                fade_alpha = 0
                fading = False
            else:
                fade_surface.fill((0, 0, 0, fade_alpha))
                screen.blit(fade_surface, (0, 0))
                # Draw particles on top of fade
                for particle in particles:
                    particle.draw(screen)
                    

        if game_state == "TITLE":
            screen.blit(title_image, (0, 0))
            button_width = 260
            button_height = 70
            gap = 30
            total_width = button_width * len(title_buttons) + gap * (len(title_buttons) - 1)
            start_x = WIDTH // 2 - total_width // 2
            y = HEIGHT - 120
            for idx, text in enumerate(title_buttons):
                rect = pygame.Rect(start_x + idx * (button_width + gap), y, button_width, button_height)
                pygame.draw.rect(screen, (0, 0, 0), rect)
                pygame.draw.rect(screen, (255, 255, 255), rect, 3)
                label = font.render(text, True, (255, 255, 255))
                label_rect = label.get_rect(center=rect.center)
                screen.blit(label, label_rect)
                if idx == title_selected:
                    indicator_rect = rect.inflate(14, 14)
                    pygame.draw.rect(screen, (255, 255, 255), indicator_rect, 3)
            if active_dialogue:
                active_dialogue.draw(screen, WIDTH // 2 - 200, HEIGHT // 2)
        elif game_state == "INTRO":
            screen.fill((0, 0, 0))
            intro_dialogue.draw(screen, WIDTH // 2 - 200, HEIGHT // 2)
        elif game_state == "PLAYING":
            health_text = font.render(f"Health: {Vio.health}", True, (255, 255, 255))
            screen.blit(health_text, (10, 10))
            if checkpoint_message_timer > 0:
                checkpoint_message_timer -= dt
                message_surface = font.render(checkpoint_message, True, (255, 255, 255))
                screen.blit(message_surface, (20, HEIGHT - 40))
                if checkpoint_message_timer <= 0:
                    checkpoint_message = ""
            for cp in checkpoints:
                screen.blit(cp.image, camera.apply(cp.rect))
            for npc in npcs:
                npc.draw(screen, camera)
                npc.draw_prompt(screen, camera, Vio.rect)

            # Draw boss manager if active
            if boss_manager:
                boss_manager.draw(screen, camera)

            # Draw Kira boss if active
            if boss2_triggered and kira_boss_manager:
                        kira_boss_manager.draw(screen, camera, Vio)
            if ship:
                ship.draw(screen, camera)
                if ship.active and not ship.taking_off and Vio.rect.colliderect(ship.rect):
                    prompt_text = font.render("Z", True, (255, 255, 255))
                    prompt_pos = camera.apply(pygame.Rect(Vio.rect.centerx - 80, Vio.rect.top - 40, 160, 20))
                    screen.blit(prompt_text, (prompt_pos.x, prompt_pos.y))

            if Vio.visible:
                for trail in trail_particles:
                    trail.draw(screen, camera)
                draw_image = Vio.image
                if not Vio.invulnerability_timer >0 or (pygame.time.get_ticks() // 50) % 2 == 0:
                    screen.blit(draw_image, camera.apply(Vio.draw_rect))
                    

            # Draw ship scene elements
            if current_level == 'SHIP':
                if melody3_img and melody3_alpha > 0:
                    melody3_surf = melody3_img.copy()
                    melody3_surf.set_alpha(melody3_alpha)
                    screen.blit(melody3_surf, (1000, 300))  # Adjust position as needed
                if the_melody_img and the_melody_alpha > 0:
                    the_melody_surf = the_melody_img.copy()
                    the_melody_surf.set_alpha(the_melody_alpha)
                    # Glow effect
                    glow_surf = pygame.Surface(the_melody_img.get_size(), pygame.SRCALPHA)
                    glow_surf.fill((255, 255, 255, melody_glow_alpha))
                    screen.blit(glow_surf, (600 - the_melody_img.get_width() // 2, 300 - the_melody_img.get_height() // 2))
                    screen.blit(the_melody_surf, (600 - the_melody_img.get_width() // 2, 300 - the_melody_img.get_height() // 2))  # Center
                if not getattr(Vio, 'is_holding_violin', False) and performing_img is not None and performing_alpha > 0:
                    performing_surf = performing_img.copy()
                    performing_surf.set_alpha(performing_alpha)
                    performing_x = 600 - performing_img.get_width() // 2
                    performing_y = 200 - performing_img.get_height() // 2
                    screen.blit(performing_surf, (performing_x, performing_y))
                if ship_scene_state in ('DOOR_FADE_IN', 'DOOR_DIALOGUE', 'DOOR_FADE_OUT') and door_img is not None:
                    black_surf = pygame.Surface((WIDTH, HEIGHT))
                    black_surf.fill((0, 0, 0))
                    black_surf.set_alpha(door_alpha)
                    screen.blit(black_surf, (0, 0))
                    door_surf = door_img.copy()
                    door_surf.set_alpha(door_alpha)
                    door_x = WIDTH // 2 - door_img.get_width() // 2
                    door_y = HEIGHT // 2 - door_img.get_height() // 2
                    screen.blit(door_surf, (door_x, door_y))
                if ship_scene_state == "FLASHING_LIGHTS" and flash_lights_active:
                    # White flashing lights effect
                    flash_surf = pygame.Surface((WIDTH, HEIGHT))
                    flash_surf.fill((255, 255, 255))
                    flash_intensity = max(0, min(255, flash_lights_intensity))
                    flash_surf.set_alpha(flash_intensity)
                    screen.blit(flash_surf, (0, 0))
            
            # Unconditional violin overlay draw (runs every frame during PLAYING)
            # Clear per-hold debug flag when not holding
            if not getattr(Vio, 'is_holding_violin', False) and hasattr(Vio, '_violin_debug_shown'):
                try:
                    delattr(Vio, '_violin_debug_shown')
                except Exception:
                    try:
                        del Vio._violin_debug_shown
                    except Exception:
                        pass

            # Warn if holding but animator missing (log once)
            if getattr(Vio, 'is_holding_violin', False) and vio_violin_anim is None:
                if not hasattr(Vio, '_violin_anim_missing_logged'):
                    try:
                        print("DEBUG WARNING: Vio.is_holding_violin is True but vio_violin_anim is None")
                    except Exception:
                        pass
                    Vio._violin_anim_missing_logged = True

            if getattr(Vio, 'is_holding_violin', False) and vio_violin_anim is not None:
                violin_frame = vio_violin_anim.get_current()
                if violin_frame:
                    vio_screen_rect = camera.apply(Vio.draw_rect)
                    # Apply overlay scale multiplier
                    target_w = max(1, int(vio_screen_rect.width * VIO_OVERLAY_SCALE))
                    target_h = max(1, int(vio_screen_rect.height * VIO_OVERLAY_SCALE))
                    try:
                        vf_scaled = pygame.transform.scale(violin_frame, (target_w, target_h))
                    except Exception:
                        vf_scaled = violin_frame
                    # Center the overlay on Vio.draw_rect
                    draw_x = vio_screen_rect.x + (vio_screen_rect.width - vf_scaled.get_width()) // 2
                    draw_y = vio_screen_rect.y + (vio_screen_rect.height - vf_scaled.get_height()) // 2
                    screen.blit(vf_scaled, (draw_x, draw_y))
                    if VIO_OVERLAY_DEBUG:
                        debug_rect = pygame.Rect(draw_x, draw_y, vf_scaled.get_width(), vf_scaled.get_height())
                        pygame.draw.rect(screen, (255, 0, 0), debug_rect, 2)
                        #if not getattr(Vio, '_violin_debug_shown', False):
                         #   try:
                          #      print(f"DEBUG: violin overlay at {debug_rect} target_size=({target_w},{target_h}) frame_size={violin_frame.get_size()}")
                           # except Exception:
                            #    pass
                            #Vio._violin_debug_shown = True

        if game_state == "CREDITS":
            screen.fill((0, 0, 0))
            line_height = 40
            for index, line in enumerate(CREDITS_TEXT):
                text_surf = font.render(line, True, (255, 255, 255))
                text_rect = text_surf.get_rect(center=(WIDTH // 2, credits_y + index * line_height))
                screen.blit(text_surf, text_rect)
            credits_y -= credits_speed
            if credits_y + len(CREDITS_TEXT) * line_height < 0:
                credits_y = HEIGHT
                game_state = "TITLE"
                # Do NOT reset variables here; they'll be reset when "New Game" is pressed

        # Pause screen overlay (renders on top of game)
        if is_paused and game_state == "PLAYING":
            # Semi-transparent black overlay
            pause_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pause_overlay.fill((0, 0, 0, 128))  # 50% black transparency
            screen.blit(pause_overlay, (0, 0))
            
            # "PAUSED" text
            pause_text = font.render("PAUSED", True, (255, 255, 255))
            pause_text_rect = pause_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))
            screen.blit(pause_text, pause_text_rect)
            
            # Pause menu buttons
            button_width = 260
            button_height = 70
            gap = 30
            total_width = button_width * 2 + gap
            start_x = WIDTH // 2 - total_width // 2
            button_y = HEIGHT // 2 + 20
            
            pause_buttons = ["Continue", "Exit"]
            for idx, button_text in enumerate(pause_buttons):
                button_rect = pygame.Rect(start_x + idx * (button_width + gap), button_y, button_width, button_height)
                pygame.draw.rect(screen, (0, 0, 0), button_rect)
                pygame.draw.rect(screen, (255, 255, 255), button_rect, 3)
                label = font.render(button_text, True, (255, 255, 255))
                label_rect = label.get_rect(center=button_rect.center)
                screen.blit(label, label_rect)
                
                # Highlight selected button
                if idx == pause_selected:
                    indicator_rect = button_rect.inflate(14, 14)
                    pygame.draw.rect(screen, (255, 255, 255), indicator_rect, 3)

        #boss1 cutscene
        if boss_manager and hasattr(boss_manager, 'memory_fade') and boss_manager.memory_fade > 0:
            fade_surf = pygame.Surface((WIDTH, HEIGHT))
            fade_surf.fill((0, 0, 0)) # Pure black
            fade_surf.set_alpha(boss_manager.memory_fade)
            screen.blit(fade_surf, (0, 0))
            
    
        # If we are in the memory state, keep the screen black and show text
        if game_state == "MEMORY_TRANSITION":
            if active_dialogue:
                active_dialogue.update(keys)
                screen.fill((0, 0, 0))
            if active_dialogue is None or active_dialogue.finished:
                active_dialogue = None
                if ship and getattr(ship, 'target_level', None) == 'SHIP':
                    tiles, checkpoints, decorations_list = load_level('SHIP')
                elif current_level == 1:
                    tiles, checkpoints, decorations_list = load_level(2)
                game_state = "LEVEL_START_ANIMATION"
                if ship:
                    ship.taking_off = False
                    ship.rect.y = -500
                    ship.rect.x = 200
                    ship.transition_fade = 255
                    ship.target_level = None
                #Vio.rect.topleft = (-1000, -1000)
                # Reset Vio's visibility for the new level
                #Vio.visible = True
                #Vio.can_move = True
                # Set a new starting position for Level 2 balcony
                #Vio.rect.topleft = (100, 300)
                #active_dialogue.draw(screen)
            # Once the dialogue is finished, transition to level 2
            #if active_dialogue and active_dialogue.finished:
                #load_level(2)
                #game_state = "PLAYING"
                #active_dialogue = None
        BALCONY_Y = 500

        if game_state == "LEVEL_START_ANIMATION" and ship:
            # Fade the black out
        
            ship.transition_fade = max(0, ship.transition_fade - 5)
            
            ship.rect.y += ship.takeoff_speed
            ship.rect.x += ship.takeoff_speed // 2 # Reverse the diagonal drift
        
            camera.update(ship.rect)
        
            if ship.rect.y >= BALCONY_Y:
                ship.rect.y = BALCONY_Y
                game_state = "PLAYING"
                Vio.visible = True
                Vio.can_move = True
                Vio.rect.center = ship.rect.center
            #    DRAW  SHIP===

        if transition_fading or transition_fade_in:
                fade_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                fade_surf.fill((0, 0, 0))
                fade_surf.set_alpha(transition_fade_alpha)
                screen.blit(fade_surf, (0, 0))
        
        if ship and ship.active and ship.transition_fade > 0:
            fade_surf = pygame.Surface((WIDTH, HEIGHT))
            fade_surf.fill((0, 0, 0))
            fade_surf.set_alpha(ship.transition_fade)
            screen.blit(fade_surf, (0, 0))

        
        

        if current_level == 'FINAL':
            phase = get_final_level_phase_from_frame(final_level_frame_count)
            #if phase >= 3:
                #intensity = get_phase_music_progress()
                #draw_omori_vignette(screen, intensity)
            
            # --- Draw cutscene sprites ---
            if final_cutscene_triggered:
                LIN_WORLD_POS = (165550, 830)
                VIO_WORLD_POS = (165000, 846)
                
                if final_cutscene_state == 'TALKING' and lin_idle_anim:
                    frame = lin_idle_anim.get_current()
                    if frame:
                        screen_pos = camera.apply(pygame.Rect(LIN_WORLD_POS[0], LIN_WORLD_POS[1], frame.get_width(), frame.get_height()))
                        screen.blit(frame, (screen_pos.x, screen_pos.y))
                
                elif final_cutscene_state == 'PERFORMING' and lin_perform_anim and vio_violin_anim:
                    lin_frame = lin_perform_anim.get_current()
                    vio_frame = vio_violin_anim.get_current()
                    if lin_frame:
                        lin_screen_pos = camera.apply(pygame.Rect(LIN_WORLD_POS[0], LIN_WORLD_POS[1], lin_frame.get_width(), lin_frame.get_height()))
                        screen.blit(lin_frame, (lin_screen_pos.x, lin_screen_pos.y))
                    if vio_frame:
                        # Use Vio's regular on-screen draw_rect size but apply an extra
                        # multiplier so the final-cutscene performing pose looks larger.
                        vio_screen_pos = camera.apply(pygame.Rect(VIO_WORLD_POS[0], VIO_WORLD_POS[1], Vio.draw_rect.width, Vio.draw_rect.height))
                        target_w = max(1, int(vio_screen_pos.width * VIO_CUTSCENE_SCALE))
                        target_h = max(1, int(vio_screen_pos.height * VIO_CUTSCENE_SCALE))
                        try:
                            vio_scaled = pygame.transform.scale(vio_frame, (target_w, target_h))
                        except Exception:
                            vio_scaled = vio_frame
                        # Center scaled frame on the original world position
                        draw_x = vio_screen_pos.x + (vio_screen_pos.width - vio_scaled.get_width()) // 2
                        draw_y = vio_screen_pos.y + (vio_screen_pos.height - vio_scaled.get_height()) // 2
                        screen.blit(vio_scaled, (draw_x, draw_y))
                
                elif final_cutscene_state in ('FADE_TO_BLACK', 'CUTSCENE_DONE') and cockpit_fade_alpha > 0:
                    fade_surf = pygame.Surface((WIDTH, HEIGHT))
                    fade_surf.fill((0, 0, 0))
                    fade_surf.set_alpha(min(255, int(cockpit_fade_alpha)))
                    screen.blit(fade_surf, (0, 0))

        if final_phase_shake_offset != (0, 0):
            screen_copy = screen.copy()
            screen.fill((0, 0, 0))
            screen.blit(screen_copy, final_phase_shake_offset)

        if tentacle_attacks:
            for attack in tentacle_attacks:
                attack.draw(screen)
        
        if active_dialogue:
            if not active_dialogue.is_passive:
                box_x = WIDTH // 2 - 350
                box_y = HEIGHT - 150
                pygame.draw.rect(screen, (0, 0, 0), (box_x, box_y, 700, 150)) # Black box
                pygame.draw.rect(screen, (255, 255, 255), (box_x, box_y, 700, 150), 2) # White border
                active_dialogue.draw(screen, box_x + 20, box_y + 20)
            else:
                # Passive dialogue draws itself at the top
                active_dialogue.draw(screen)
        
        
        if floating_dialogue_queue is not None:
            floating_dialogue_queue.draw(screen)

        if active_dialogue and getattr(active_dialogue, 'trigger_glitch', False):
            screen_copy = screen.copy()
            screen.fill((255, 255, 255))
            for i in range(0, HEIGHT, 6): # Adjust '4' for thicker/thinner scanlines
                offset = random.randint(-20, 20)
                screen.blit(screen_copy, (offset, i), (0, i, WIDTH, 4))
        #pygame.draw.rect(screen, (255, 0, 0), (Vio.rect.x - camera_x, Vio.rect.y, Vio.rect.width, Vio.rect.height), 2)
        
        z_was_held = z_currently_held
        pygame.display.flip()
        if Vio is not None:
            pygame.display.set_caption(f" X: {Vio.rect.x} Y: {Vio.rect.y} game_state: {game_state} current_level: {current_level} camera_x: {camera.offset_x} camera_y: {camera.offset_y}")
        else:
            pygame.display.set_caption(f"game_state: {game_state}")
LEVEL1_MAP = [
    '........................................................................................................................................................................................................................................G..GG...G...G...G...G...G...G...G...G...G..G..G...G...G...G...G...GG...G...G...G..G...GG...',
    '.................................................................................................................................................................................................................................................................................................................................',
    '.................................................................................................................................................................................................................................................................................................................................',
    '.......................................................................................................................................................................................................................................G...GG...G...G...G...G...G...G...G...G...G...G..G...G...G...G...G...G...G...G...G...G...G..G...G...G...G..G...G...G...G..G...G...G...G..G...G...G...G..G...G...G...G.',
    '....................................................................................................................................................................................................................................................................................................................................................................$',
    '...........................................................................................................................................................................................................................................G.....................................................................................',
    '.......................................................................................................................................................................................................................................G...G.........................................................................................$....................................',
    '......................................................................................................................................................................................G...G...G...G...G...G...G...G...G...G...G...G........GG...dddddddddddddddddddddddddd#############################################ddddd.........$$..............$.$...................................',
    '...............................................................................................................................................................................................................................................r..........................d########G...G...G...G..G..$G...G...G...G..$$.........................................................................................',
    '.......................................................................................................................................................................................................................................G...G...$...........................d####G....................$G...G...G...G..$$...................................................................................',
    '......................................................................................................................................................................................G...G...G...G...G...G...G...G...G...G...G...G.........................................d###.....................................$$................................................................................',
    '...............................................................................................................................................................................................................................................$.............................d##.....................................................................................................................',
    '.......................................................................................................................................................................................................................................G...G...#..............................d#.........................................................................................................................',
    '......................................................................................................................................................................................G...G...G...G...G...G...G...G...G...G...G...G............#..........#########.......................................................................................................................................................',
    '...............................................................................................................................................................................................................................................$..........#########.................c.....................................................................................................................................',
    '.......................................................................................................................................................................................................................................G...G..............lG...G..........................................................................................................................................................',
    '......................................................................................................................................................................................G...G...G...G...G...G...G...G...G...G...G...G.......................lG...G....MMmmmmmmMGGGGGGGGGGGGGGGGGGGGGGGGGG..G..G..G.............................................................................................................',
    '...............................................................................................................................................................................................................................................$..........lG...G....G...G...G.G...#....#GGGGGGoGGGGGGG..................................................................................................................',
    '.......................................................................................................................................................................................................................................G...G..............lG...G..................l....#GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG................',
    '......................................................................................................................................................................................G...G...G...G...G...G...G...G...G...G...G...G......,,,..............lG...G..................lG...#GGGGGGGGGGGGGG....................................................................................................................',
    '......................................................................................................................................................................................G...G...G...G...G...G...G...G...G...G...G...G............$..........lG...G....G...G...G.G...l....#GGGGGGGGGGGGGG....................................................................................................................',
    '.......................................................................................................................................................................................................................................G...G..............lG...G...r..............l....#GGGGGGGGGGGGGG....................................................................................................................',
    '......................................................................................................................................................................................G...G...G...G...G...G...G...G...G...G...G...G...F........$..........lG...G...r..............lG...rGGGGGGGGGGGGGG....................................................................................................................',
    '.............................................................................................................................................................................G...#####..............................................G.....................lG...G...r..............l....rGGGGGGGGGGGGGG....................................................................................................................',
    '.............................................................................................................................................................................G...#####G...G...G...G...G...G...G...G...G...G...G...G.G...G..G..............lG...G...r..............l....rGGGGGGGGGGGGGG....................................................................................................................',
    '.............................................................................................................................................................................G...#####.........................................................r..........lG...G...r..............lG...rGGGGGGGGGGGGGG....................................................................................................................',
    '.............................................................................................................................................................................G...#####.........................................................#r.........$G...G...r..............l....rGGGGGGGGGGGGGG....................................................................................................................',
    '.............................................................................................................................................................................G...#####.........................................................##r.........G...G...r..............lG...rGGGGGGGGGGGGGG....................................................................................................................',
    '...............................................................mm............................................................................................................G...#G...ddddddddddddddddddddddddddddddddddddddddd###################r........G...G...r..............l....rGGGGGGGGGGGGGG....................................................................................................................',
    '............................................VVVV..............L##R...........................................................................................................G...#............VVV..............................D###################r......lG...G...r..............l....rGGGGGGGGGGGGGG....................................................................................................................',
    '..............................................................L##R...........................................................................................................G...#..............................................Ddd#####Go#####G...r......lG...G...r..............lG...rGGGGGGGGGGGGGG....................................................................................................................',
    '..............................................................L##R...........................................................................................................G...#G..................................................L#########G...r......lG...G...r..............l....rGGGGGGGGGGGGGG....................................................................................................................',
    '..............................................................L##R...........................................................................................................G...#....................................................l########G...r......lG...G...r..............l....rGGGGGGGGGGGGGG....................................................................................................................',
    '..............................................................L##R...........................................................................................................G...#.....................................................l#######G...r......$G...G...r..............lG...rGGGGGGGGGGGGGG....................................................................................................................',
    '..............................................................L##R...........................................................................................................G...#G.....................................................#######G...r.......G...G...r..............l....rGGGGGGGGGGGGGG....................................................................................................................',
    '..............................................................L##R...........................................................................................................G...#.......................................................DddddDG...r.......G...G...r..............lG...r..................................................................................................................................',
    '..............................................................L##R...........................................................................................................G...#.............................................................G...r......lG...G...r..............l....r..................................................................................................................................',
    '..............................................................L##R...........................................................................................................G...#G............................................................G...$......lG...G...r..............l....r..............GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG',
    '..............................................................L##R...........................................................................................................G...#........................................................................lG...G...r..............lG...r',
    '..............................................................L##R...........................................................................................................G...#.......................l###########.....................................lG...G...r..............l....r',
    '..............................................................L##R...........................................................................................................G...#G......................l##Go########................S............#......lG...G...r..............l....r',
    '..............................................................L##R...........................................................................................................G...#...........#######.....l#############................S..................lG...G...r..............lG...r',
    '...........................................................U..L##R.......................................................G...G...G...G...G...G...G...G...G...G...G...G...G...G...#..........Sl#####r.....l###Go#########..................................lG...G...r..............l....r',
    '..........................................MGGGGGGGG.......GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG......G...G...G...G...G...G...G...G...G...G...G...G...G...G...G...........l#####r.....l###############....mmmmmmmm.....................lG...G...r..............l....r',
    '..........................................$$$....................................................................................................................................#...r.......l#####r.....l#####################Go####Go######Go####################r..............lG...r.',
    '...............................lmr........$-o.....................---............................................................................................................#...r.......l#####r.....l#########################################################r..............l....r..',
    '...............................l#r........$$$....................................................................................................................................#...r......Sl#####r.....l#########################################################r..............l....r..',
    '...............................l#r........$$$...................M.......................................................#########ddddddddddddddddddddddddddddddddddddddddddddddddddddd.......l#####r.....l#########################################################r..............lG...r.',
    '...............................l#r......MM$$$..................LR........................................................G...G..#............................................................l#####r.....l#########################################################r..............l....r...',
    '...............................l#r......$$$.....................LR..............................................................#............................................................l#####r.....l#########################################################r..............l....r.',
    '...............................l#r......$$$......................LR---................---.......................................#............................................................l#####r.....l#########################################################r..............lG...r....',
    '...............................l#r......$$$......................LRG...G...G...G...G...Go..G...G...G...G...G...G...G.G...G...G..#............................................................l#####r.....l#########################################################r..............l....r...' ,
    '...............................ldr......$$$.....................LR..............................................................#............................................................l#####r.....l#########################################################r..............l....r..',
    '......................###...............$$$...........$$$$$$$...LR........................................-..--.................#................................................#####.......l#####r.....l#########################################################r..............lG...r...',
    '......................-#o...............$$$U.........GGGGGGGGGGGGGGGGGGGGGGGG...#####GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG..G...G...#................................................l###r.......l#####r.....l#########################################################r..............l####r...',
    '.................---..###.............MM$$$$$$$$$$......o.......................#-o##.....................x.....................#.....................................####.......l###r.......l###r.......l#####r.....l##########################################################mmmmmmmmmmmmmm######..',
    '.................$$$$$$$$.............$$$G..G...$$..............-.....-..-......#####...........................................#.....................C...............l##r.......l###r.......l###r.......l#####r.....l##############################################################################.',
    '.........N.......$$$$$..........M.......G.......................................ddddd...........................................#.....................................l##r.......l###r.......l###r.......l#####r.....l##############################################################################',
    '...............................L#R..........................................................dddddd................................................###.U...#####,,,,,,,l##r.......l###r.......l###r.......l#####r.....l#########################################################################################################################################################################..',
    '##Go#########....#########MMMMG##oMMMM$$$.G..G..$$..................................................................S.............................l###...#####r.......l##r.......l###r.......l#####r.....l#########################################################################################################################################################################...........',
    '#####Go######MMMM#########G.G..G..G..G...G..G...$$................................................................................................l###########r.......l##r.......l###r.......#######.....l#########################################################################################################################################################################..................................................',
    '#Go##########Go###########..G...G...G...G...G.....................................................................................................l############mmmmmmm####mmmmmmm#####mmmmmmm#######mmmmm##########################################################################################################################################################################.........................................',
    '######Go##################..G...G...G...G...G......U..............................S..................S............................................l################################################################################################################################################################################################################################',
    'G...G...G...G...G...G...G...G...G...G...G...G...GGGGGGGGGGGoGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG..#G...G...G...G...G...G...G...G...G...G.#######################################################################################################################################################################################################################',
    'G...G...G...G...G..G...G...G...GW..G...G...G...G.....................................................................#',
    '..............................W.................G...G...G...G...G...G...G..G...G...G...G...G...G...G...G...G...G...G...G...G...GG...G...G...G...G...G...GG...G...G...G...G...G...GG...G...G...G...G...G...GG...G...G...G...G...G...GG...G...G...G...G...G...GG...G...G...G...G...G...GG...G...G...G...G...G...GG...G...G...G...G...G...GG...G...G...G...G...G...GG...G...G...G...G...G...G........................................#',
    'W..............................WW....................................................................................#',

]

LEVEL2_MAP = [
    '.............................................................................3................................................................3..................................................................................................3.................................................3.................................................3.................................................3..............uuuuuuuuuub........................3.................................................3......................................................',
    '................................................................................................................................................................................................................................................................................................................................................................................................................................l',
    '................................................................................................................................................................................................................................................................................................................................................................................................................................l',
    '.............................................................................2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2...................................................................................................................................................................................................................................................................................l',
    '................................................................................................................................................................................................................................................................................................................................................................................................................................l',
    '..........................................................................................................................u.....................................................................................................................................................................................................................................................................................................l',
    '.............................................................................2..2..2..2..2..2..2..2..2..2..2..2..2..2..2.l2r.2..2..2..2..2..2...................................................................................................................................................................................................................................................................................l...................................................................................................................................................................................................',
    '.........................................................................................................................l.r....................................................................................................................................................................................................................................................................................................l...................................................................................................................................',
    '.........................................................................................................................l.r....................................................................................................................................................................................................................................................................................................l...................................................................................................................................',
    '.............................................................................2..2..2..2..2..2..2..2..2..2..2..2..2..2..2.l2r.2..2..2..2..2..2......................................................................................................................................................................................................................................................................Y............l........................................................................................................................................................',
    '.........................................................................................................................l.r...........................................................................................................................................................................................................................................................lr.......................................l........................................................................................................',
    '.........................................................................................................................l.r.......................................................................................................................................................................................W...................................................................pg.......................................l............................................................................................................',
    '.............................................................................2..2..2..2..2..2..2..2..2..2..2..2..2..2..2.l2r.2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2................................................................................................................................................................................................lr..........pg.......................................l...........................................................................................................................................................................',
    '.........................................................................................................................l.r...............................................................................................................................................................................................................................................pg..........pg...........uuuuuu##....................l.................................................................................................................................................',
    '.........................................................................................................................l.r...............................................................................................................................................................................................................................................pg..........lg..........l#.#.#.##............gg.....l.............................................................................................................................................',
    '.............................................................................2..2..2..2..2....W...2..2..2..2..2..2..2..2.l2r.2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..................................................................................................................................................T..............................pg..........lg..........l.......#............lr.....l....................................................................................................................................',
    '.........................................................................................................................l.r...............................................................................................................................................................................................................................................pg..........pg..........l#.#.#.##.............r.....l..........................................................................................................................................',
    '.........................................................................................2........2..2..2..2..2..2..2..2.l2r.2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2...........................................................................................................................................s.....................................pg..........gg..........l.......#.............r.....l.............................................................................................................................................',
    '.............................................................................2..2..2..2..................................l.r........................................................................................................................................................................................................................q...........c..........pg..........pg..........l#.#.#.##.............r.....l.................................................................................................................................................',
    '.........................................................................................2..2..2..2..2..2.T2..2..2..2..2.l2r.2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2.................................................................................................................................................................................lr..........lr..........l.......#.............r.....l.................................................................................................................................................',
    '.........................................................................................................................l.r........................................................................................................................................................................#.#.#.##.ppppppgggggggggppp#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#...................................................r.....l..............................................................................................................................................................',
    '...........s..................s.................s............................2..2..2..2..2..2..2..2..2..2..2..2..2..2..2.l2r.2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2............................................................................lb.b.b.b...................b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.r...................................................r.....l..............................................................................................................................................................',
    '................c.........................................................................................................l.r........................................................................................................................................................................l................................................................r...................................................r.....l.............................................................................................................................................................................................................................',
    '.............................................................................2..2..2..2..2..2..2..2..2..2..2..2..2..2..2.l2r.2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2.....................................................................................lb.b.b.b.uuuuuuuuuuuuuuuuuub.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.r...................................................r.....l.................................................................................................................................................................................................................................................................',
    '.........#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.ggg.....gggg.........ppppppppp#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#........................................................................................................................................................................l................................................................r...................................................r.....l.............................................................................................................................................................................................................................',
    '.........b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b...............................b.b.b.b.b.b.b.b.b.b.b.......b.b.b.b.b.b.b........................................................................................................................................................................lb.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.r...................................................r.....l.............................................................................................................................................................................................................................',
    '..........................................................................2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2............................................................................................................p...l................................................................r...................................................r.....l.............................................................................................................................................................................................................................',
    '................................................................................................................................................................................................................................................................................................p...lb.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.r...................................................r.....l.............................................................................................................................................................................................................................',
    '..........................................................................2..2..2..2..2..2..2.2..2..2..2r.2..2..l2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2...................................................................................................p...l................................................................r.uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuur.....luuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuu.......................................................................................................................................................................................................................',
    '........................................................................................................r.......................................................................................................................................................................................p...lb.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.r...................................................r.....l#######################################................................................................................................................................................................................................................................................',
    'uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuu2..2..2..2..2..2..2..2..2..2.l2..2..2..2..2.2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2.2.2.2.2.2.2.2.2..2..2..2..2..2..2..2..2..2..2..2..2..2................................................p...l................................................................r..................................................#r.....l#######################################.....p..L...........................................................................................................................................................................................................................................................................',
    '......................................................................................................b.r......................................................................................................3....................................................................................lb.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b3b.b.b.b.b.b.b.b.r...............................3.................b.r.....l.......................3....................p.........................................................................................................................................................................................',
    '...................................................................................3..2..2..2..2..2..2..2..2..2.l.......................................................................................................................................................................g...........l................................................................r.................................................b.r.....l............................................p.....................................................................................................................................................................................................',
    '......................................................................................................b.r.......l2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2.2.....g...........lb.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.r.................................................b.r.....l............................................p.....g.........................................................................................................................................................................................................................',
    '...................................................................................2..2..2..2..2..2..2..2..2..2.........................................................................................................................................................................p...........l................................................................r.................................................b.r.....l..................................................g............................................................................................................................................................................................................................................................................',
    '......................................................................................................b.r.......l2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2.2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2.....p...........lb.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.r.................................................b.r.....l..................................................g......................................L..p...................................................................................................................................................................................',
    '...................................................................................2..2..2..2..2..2..2.2..2..2.............................................................................................................W............................................................g...........l................................................................r.................................................b.r.....l..................................................g.........................................p...............................................................................................................................................',
    '......................................................................................................b.r.......l.......................................................................................................................................................................g...........lb.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.r.................................................b.r.....l............................................p.....g.........................................p...................................................................................................................................................',
    '...................................................................................2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2.2..2..2..2..2..2.2..2..2.2..2..2.2..2..2.2..2..2..2..2..2..2..2..2.2..2..2.2..2..2.2..2.......2..2.2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2.....g.......p...l................................................................r.................................................b.r.....l............................................p...............................................p........................................................................................................................................................................',
    '......................................................................................................b.r.......l........................................................................................................................T..........Y..W....Y...........................Y.......p...lb.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.r.................................................b.r.....l............................................p........w.................w....................p..................................................................................................................................................................',
    '...................................................................................2..2..2..2..2..2..2..2..2..2.................................................................................................................................................................................p...l................................................................r.................................................b.r.....l............................................p...............................................p...............................................................................................................................................',
    '......................................................................................................b.r.......l2..2..2..2..2..2.2..2..2..2..2..2.2..2..2.2..2..2.2..2..2.2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2........2..2.2..2..2..2..2..2..2............p...lb.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.r.................................................b.r.....l............................................p...............................................p..........................................................................................................................................................................',
    '...................................................................................2..2..2..2..2..2..2..2..2..2.................................................................................................................................................................................p...l................................................................r.................................................b.r.....l............................................p..........................................pppppp................................................................................................................................................................',
    '......................................................................................................b.r.......l...............................................................................................................................................................................p...lb.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.r.................................................b.r.....l............................................p...............................................p..................................................................................................................................................',
    '...................................................................................2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2.2..2..2..2..2..2.2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2k.2..2..2..2..2..2..2..2..2..2..2..2..2.2..2..2..2..2..2................l................................................................r.................................................b.r.......................................................................................gggg.............................................................................................................................................................................',
    '......................................................................................................b.r.......l...............................................................p..2..2..2..2..2..2..2..2..2..2..2..2..2..######################ggggggggppppppp######################...............lb.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.r.................................................b.r...................................................................................................................................................................................................................................................................................................',
    '...................................................................................2..2..2..2..2..2..2..2..2..2.................................................................p.......g.................g.......p2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2.................l................................................................r.................................................b.r..................................................................................................................................................................................................................................................................',
    '......................................................................................................b.r........2..2..2..2..2..2.2..2..2.2..2..2.2..2..2.2..2..2.2..2..2..2..2.p2......g........p........g.......p.................................................................................lb.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.r.................................................b.r....c......................................................................................................................................................................................................................................',
    '...................................................................................2..2..2..2..2..2..22..2..2..2..2..2..2.2..2..2.2..2..2.2..2..2.2..2..2.2..2..2.2..2..2..2..2.p2.2..2.g2..2..2.p2..2..2.g2..2..2p.2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2................l................................................................r.................................................b.r......................................................................................................................................................................................................................................................',
    '......................................................................................................b.r...................................Q...................................p.......g........p........g.......p.................................................................................lb.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.r.................................................b.b#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.pppppgggggggggppp#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#.#............................................................................................................................................................................................................',
    '........................................................................................................2.c.2...........................................................................g........p........g..........................................................................................................................................................r.................................................b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.bb....................b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.............................................................................................................................................................................................................................................................',
    '...................................................................................2..2..2..2..2..2..2b.2..2..2..2..2..2..2..2.2..2..2..2..2..2.2..2..2..2..2..2.2..2..2..2..2..2..2..2..2..2..2.p2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.br....................................................................................................................................uuuuuuuuuuuuuuuuu..................................................................................................................................................',
    '........................................................................................................2#################################################################...........................................................................................................................................................................................r...............................................................................................................................................................................................................................................................................................................................',
    '......................................................................................................b..b3.b2.b2.b2.b2.b2.b..b..b..b..b..b.b.b2b.b.b2.b2.b2.b.b2.b2.b2.b2.32..2..2..2..3..2..2..2..2..2..2..2..2..2..2..2.32..2..2..2..2..2..2..2..2..2..2.32..2..2..2..2..2..2..2..2..2..2..2..2.3b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.br...........................................................................................................................................................................................................................................................................................................................................',
    '...................................................................................2..2..2..2..2..2..22..2...........................................................................................................................................................................................................................................................r...................................................................................................................................................................................................................................................................................................................',
    '......................................................................................................2.2.2..2..2.2..2..2.2..2..2.2..2..2.2..2..2.2..2..2.2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.br..............................................................................................................................................................................................................................................................................................................',
    '.....................................................................................................................................................................................................................................................................................................................................................................r....................................................................................................................................................................................................................................................................................................................................................',
    '..........................................................................................................2..2..2.2..2..2.2..2..2.2..2..2.2..2..2.2..2..2.2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.2..2..2..2..2..2..2..2..2..2........................................................................................................................................................................................................................................................................',
    '........................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................',
    '..........................................................................................................2..2..2.2..2..2.2..2..2.2..2..2.2..2..2.2..2..2.2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..2..b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b.b................................................................................uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuu..........................................................................................................................................................................',


]

LEVEL_FIN_MAP = [
'....................................................................................................................................................................................................................',
'....................................................................................................................................................................................................................',
'....................................................................................................................................................................................................................',
'....................................................................................................................................................................................................................',
'....................................................................................................................................................................................................................',
'....................................................................................................................................................................................................................',
'....................................................................................................................................................................................................................',
'....................................................................................................................................................................................................................',
'3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3...............................................3................................................3................................................4................................................4................................................4................................................4................................................4................................................4................................................4................................................4................................................4................................................4................................................4................................................4................................................4................................................4................................................4................................................4................................................4................................................4................................................4................................................4................................................4................................................5................................................5................................................5................................................5................................................5................................................5................................................5................................................5................................................5................................................5................................................5................................................5................................................5................................................5................................................5................................................5................................................5................................................5................................................5................................................5................................................5................................................5................................................5................................................5................................................5................................................5................................................5................................................5................................................5................................................6.........................................................6.........................................5................................................5................................................5................................................5................................................4................................................4................................................4................................................4................................................4................................................4................................................3................................................4................................................4................................................4................................................4................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................3................................................................................................................................................................',
'#..................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................#..................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................#..................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................#..................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................#..................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................#.......................................................................................................................................FFFF.......................................................................................................................................................................................................................................................................................................................................................................#..................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................#..................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................#..................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................#..............................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................',
'........................................................B...B...B...................F..F.F.FF..F..........................................................................................................................................................................................................................................F...............................F.........................F.........................F................................................................................................................................................................................................................FF...............................................................................B...........................................................................F..F..................................................................................................................................................................................................................................................................................................F..F...............................................................................................................................................................................................b......................................................HH......................................FFFFFFF.......................................H.H................................................................................................................F....................................b......................b.b.b...b.....................................................................FFF.........................................................................................................................................................................................................................................FF..FF...................FFFFFFFFFFFF........................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................b.............................................................................................................b...............................................................................................................................................................................................b...................................................................................................................................................................................................................................Fb....................................................................................FF........................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................',
'.....................................................................F...........................F............................................................................................................................F.......................F......................................................................................................................................................................................................................................................................................................................................................................................F...F....................................F..........F...........................................................................................................FF..........B.................................................................................................................................F................................................................................................................................B......................FF........................................................................................................FFF..........................................................................................................................................F....F...................................................................................................................................................................................................b...................................................................b.....................................................................................................................................................................................................................................................................................................................FF................................................................................................................................................................................................................b........................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................B....................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................b..........................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................',
'......................................................F............F..........................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................F............................................................................................................................................................................................................................................F.....................................................................................................................................................................................................................................................B...........................H.H..............................B......................F.....................................................FFFF...................................................................................FFF.....................................................................................................................................................b...........................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................b...............................................................................................................................................................................................b.................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................',
'.............................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................B................................................................................................................................................................................................................................................................................................................................................................................................................................H...........................................................................................................................................................................................................................................................................................................................................................b....................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................b........................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................F....................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................b.....................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................',
'.............................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................FFFF............................................................................................b.........................................................................................................................................................................................b.......................................................................................................................................................b.......................................b.b............................................................................................................H.........................................................b..............................................................................................................................................................................................................................................................F......................................................................................b.b............................................................................................................................................................................................bBb.............................................................................................................................................................................................B....H...........................................................................................................................F...............................................................................................................................................................................................F................................................................b.b.b................................................................................................................................................................................................F..................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................',
'.....................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................B.......................................................................................................................................B..................................................................................................B...............................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................HH.................................................................................................................................................................................................................................................................................b...................................................................................................................b.b.b..........................................................................................B.........................................B......................................................................................................................................................................................................................................................................b................................H......................................b.b.b.b........................................................................................................................................................................................................................................................................................................................................................................................................b.b..B.....H..H....................................b.b.b.......................................................................b...........................................................................................................................................................................................................................................................................B...................................................................................................................................................................b..........................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................',
'.............................................................................................................................................................................B...............................B.........................H.......................H.....................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................H.H......................................................................................................F......................................................................................................................................................................................................................................................................................................................H................b....................................................h.............................b.................................H...........B.....b...H...............................HH....................b................................................................................H.H........................B...................b...........................b.............................................................b...b.b.bB....................................................b..................................b....b.b......................................................................................................................................................................b............................................................................................................................................................................................................................................................................................................................B...B...B...B..........B..B..B..................................................................................................................................................................................B...B...B........................................................................................................................................................................................b............BH....................................b.b...HHHH..b.............................H........................................................................................................................................HHHH.............................................................................................................................................................b..b.b..b...................................................................................................................................................................................................................................................b.......................................................B..............................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................',
'.....................................H.................................................H.................................H.H...................H.H.....................................................................................H.......................H...................................................................................................................................................................................................................................................................................................................................H..........................................HH..........................................HHH.................H.H...................................................H.H.H......................................H............................B.......................H........H.H....................................................H.............................................................................................................................................................................H.H.H.................H........................H..........................................................................H.H............................B..............................................................H.H.....................H................................................................................H....................................BH...............H.........................................................................................................................................b.............................................HHHHHHHHHHHHHH................H..........................HHHHHHHHHHHHHHHHHHHHHHHHHHHHHHHH............................................................................B..HH...................................B...B..HHHHHHHHHH..............................................HH.........................HHHH......................................H....................................................................................................................................b................................b...............................................................................................................................................................................................................................................B........................................................................................................................................................................................................B.......B...B............................B..........b.b.b.b.............................HH..................................b..................................................................................................HHHH.....HH............................................................................................................................................................B..B............................................................................................................HHHHHHHHHH................................HH.................................................................................................................................................b.HHHHHHH................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................',
'..........................................................................................................................................................................................................................................................................................................................................H...........................H..........................H..........................H........................H.......................H.................................................................................................................................................................................................................................H.............................................................................................HH......................................................H......H...H.........................................................................H.................H............................................................................................................H............................................................................................................................b.HHH..................H..............................F............................b.....................................b.b.b.........b.....B.............................FF..................b.F.b.........................b..............b.b...................................FFF........................B...................b...........................bB.....................................b......................b.b.b.b.b.....................................................b..................................b....b..FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF.......................................................................................................................................b..........................................HH..HH...................HHHH....HHHH.........................H..................H...............................................................................................................................................................................................B.............B.......B...B...B...B.......................................................................................................................................................................................................................................................................................................................................................................b.b.b.b.b.......B.........B..................B...B.........b.bFFFFFFFFFb.b........................F..F........................................................................................................................................................................................................................................................................B..............................b..B....B....b................................................................................................................................................b....................................H...........H......................................b.......b......b...........................................b.b.b.b.b.............................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................',
'...................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................FFFFFF........................................................................................................................B............B......................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................B.................................................................................................................................................................................................................................................................................................................b................................b...........................................................................................................................................................................................................................................................................................................................................................................................................................................................................b.b.b.b.b.b.b........................................................FF..................................b...................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................',
'#..................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................#..................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................#..................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................#..................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................#..................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................#..................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................#..................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................#..................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................#...................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................#....................................................................................................................................................................................................................',
'.............................................................................................................................................................................................................................................................................................................................',
'....................................................................................................................................................................................................................',
'....................................................................................................................................................................................................................',
'....................................................................................................................................................................................................................',
'....................................................................................................................................................................................................................................................................................................',








]


















if __name__ == "__main__": main()
