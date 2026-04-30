import pygame, random, math
import math
#for now, z is jump, x is run, and shift is dash. to wall jump, be in air, press the other direction, and jump. 
#and for joystick, A/B is jump, X/Y is run, and shoulder buttons are dash


pygame.display.init()
# some lists and stuff
joysticks = []
npcs = []

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
canSkip = False
active_dialogue=None
boss_triggered = False
boss_finished = False
boss_manager = None  # Will be initialized when boss is triggered
boss_state = None  # Can be "INTRO", "FIGHTING", "DAZED", "BONKED"
boss_first_entry = True  # Track first entry vs re-entry to skip dialogue

# Level state
current_level = 1

ship = None
shadow = None
moon_spike_images = None

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

    def  update(self, target_rect):
        global boss_triggered, boss_finished
        if boss_triggered and not boss_finished:
            # Lock the camera to the arena coordinates
            self.offset_x = 15000 
            

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

BOSS_ARENA1_START_X = (15000)

PORTRAITS = {
    "Captain Vio": pygame.image.load("Vio_Portrait.png").convert_alpha(),
    "Captain Vio_Down": pygame.image.load("Vio_Down.png").convert_alpha(),
    #"Moistar": pygame.image.load("moistar_portrait.png").convert_alpha(),
    #"DJ Oser": pygame.image.load("mo_portrait.png").convert_alpha(),
    #"???": pygame.image.load("unknown_portrait.png").convert_alpha()
}

pygame.mixer.init()
mois_snd = pygame.mixer.Sound('Mois_bytes.wav')
snd_hurt = pygame.mixer.Sound('snd_hurt.wav')
snd_speaker_explode =pygame.mixer.Sound('snd_speaker_explode.wav')
snd_speaker_hurt =pygame.mixer.Sound('snd_speaker_hurt.wav')
glitch_snd = pygame.mixer.Sound('glitch_snd.wav')

snd_hurt.set_volume(0.3)
mois_snd.set_volume(0.3)


moistar_charge_img=pygame.image.load("moistar_charge_img.png").convert_alpha()
donut_img = pygame.image.load("Donut.png").convert_alpha()



class DialogueBox:
    def __init__(self, font, text_list, speaker_name="", autoplay=False, auto_delay=120, has_background=True, has_portrait=None, is_passive=False):
        self.is_passive = is_passive
        self.font = font
        self.text_list = text_list
        self.speaker_name = speaker_name
        self.current_portrait_key = speaker_name 
        self.has_portrait = self.current_portrait_key in PORTRAITS
        self.has_background = has_background
        
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
        if self.is_passive:
            # --- PASSIVE TOP BAR ---
            # Draw at the top of the screen regardless of x, y
            bg_rect = pygame.Rect(0, 0, 1200, 80)
            overlay = pygame.Surface((1200, 80), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180)) 
            screen.blit(overlay, (0, 0))
            
            # Draw text
            text_surf = self.font.render(self.current_text, True, (255, 255, 255))
            screen.blit(text_surf, (50, 25))
            
            # Draw name
            name_surf = self.font.render(f"{self.speaker_name}:", True, (255, 255, 0))
            screen.blit(name_surf, (20, 5))
        else:
            if self.has_background:
                if self.waiting_for_input or (self.current_sentence < len(self.text_list) and self.char_index >= len(self.text_list[self.current_sentence])):
                    self.icon_timer += 0.1
                    # Sine wave for smooth floating: math.sin(time) * amplitude
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


def create_star_image(size):
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
    def __init__(self, x, y, size, phase, parallax, frames=None):
        self.x = x
        self.y = y
        self.size = size
        self.phase = phase
        self.parallax = parallax
        self.timer = random.uniform(0.0, 2 * math.pi)
        self.speed = random.uniform(0.02, 0.14)
        self.alpha = random.randint(130, 255)
        self.frames = None
        self.frame_index = 0
        self.frame_timer = random.uniform(0.0, 1.0)
        self.frame_speed = random.uniform(0.08, 0.22)
        if frames:
            self.frames = [pygame.transform.smoothscale(frame, (self.size * 4, self.size * 4)) for frame in frames]

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
        return create_star_image(self.size)

    def draw(self, surface, camera):
        screen_x = int(self.x - camera.offset_x * self.parallax)
        screen_y = int(self.y - camera.offset_y * self.parallax)
        if screen_x < -48 or screen_x > WIDTH + 48 or screen_y < -48 or screen_y > HEIGHT + 48:
            return
        image = self.get_image().copy()
        image.set_alpha(self.alpha)
        rect = image.get_rect(center=(screen_x, screen_y))
        surface.blit(image, rect)


default_pos = (17100, 624) #(switch commenting the one below for just testing the 1st boss)
#default_pos = (100, 2724)
# Get initial image from idle animation
LEVEL_START_POINTS = {
    1: default_pos,
    2: (100, 2724)
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
        self.rect = self.image.get_rect(topleft=(default_pos)) 
        self.hitbox = self.rect.inflate(-10, 0) 
        self.rect = self.hitbox.copy()
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
        self.rect.topleft = spawn_point
        self.hitbox = self.rect.inflate(-10, 0)
        self.rect = self.hitbox.copy()
        self.vel_x = 0
        self.vel_y = 0
        self.is_jumping = False
        self.is_dashing = False
        self.can_move = True
        self.cutscene_target_x = None
        self.on_wall = None
        self.wall_jump_cooldown = 0
        self.air_control_timer = 0

    def update(self, tiles, trail_particles=None, cutscene_mode=False):
        global canSkip 
        if not self.can_move and self.cutscene_target_x is None:
            self.vel_x = 0
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
            
        if not self.can_move:
            self.vel_x = 0
            self.vel_y = 0
            return
            
        self.vel_y += 0.6
        self.rect.y += self.vel_y
            
        for tile in tiles:
            if self.rect.colliderect(tile.rect):
                if tile.type == 'moonspike' or tile.type == 'shockwave':
                    self.take_damage(self.max_health)
                if tile.type == 'platform':
                    if self.vel_y > 0:
                        self.rect.bottom = tile.rect.top
                        self.vel_y = 0
                        self.is_jumping = False
                        self.dash_spent = False
                        self.dash_ready = True
                elif tile.type == 'normal':
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
        is_running = keys[pygame.K_x]
        jump_held = keys[pygame.K_z]
        dash_button = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        left_sensor = self.rect.inflate(4, 0).move(-2, 0)
        right_sensor = self.rect.inflate(4, 0).move(2, 0)
        for joy in joysticks:
            if abs(joy.get_axis(0)) > 0.1:
                controller_x = joy.get_axis(0)
            if abs(joy.get_axis(1)) > 0.1:
                controller_y = joy.get_axis(1)
            
            # Xbox: A=0, B=1 | Switch: B=0, A=1
            if joy.get_button(0) or joy.get_button(1): 
                jump_held = True  
            # Xbox: X=2, Y=3 | Switch: Y=2, X=3
            if joy.get_button(2) or joy.get_button(3):
                is_running = True
            # Shoulder buttons for dash
            if joy.get_button(4) or joy.get_button(5):
                dash_button = True

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
            self.dash_timer = DASH_TIME
            self.dash_cooldown = DASH_COOLDOWN
            if input_x == 0 and input_y == 0:
                self.dash_direction = (1 if self.facing_right else -1, 0)
            else:
                input_length = math.hypot(input_x, input_y)
                self.dash_direction = (input_x / input_length, input_y / input_length)
            self.vel_x = self.dash_direction[0] * DASH_SPEED
            self.vel_y = self.dash_direction[1] * DASH_SPEED
            if self.dash_direction[0] != 0:
                self.facing_right = self.dash_direction[0] > 0
            
            self.trail_timer = 0  # Reset trail timer for dash
        
        #==========
        if self.is_dashing:
            self.dash_timer -= 1
            self.vel_x = self.dash_direction[0] * DASH_SPEED
            self.vel_y = self.dash_direction[1] * DASH_SPEED
            
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
        
        if not self.is_dashing:
            accel = self.ACCEL
            if self.is_jumping and self.air_control_timer > 0:
                accel *= 2  # Extra air control
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
                elif tile.type == 'normal':
                    if not previous_rect.colliderect(tile):  # Only resolve if overlap is new
                        if self.vel_x > 0: # Moving right
                            self.rect.right = tile.rect.left
                            if self.is_jumping:  # Only set on_wall when in air
                                self.on_wall = 'right'
                        elif self.vel_x < 0: # Moving left
                            self.rect.left = tile.rect.right
                            if self.is_jumping:  # Only set on_wall when in air
                                self.on_wall = 'left'

        # Wall slide detection using sensors and active input
        # Only engage wall slide if actively pressing toward wall while in air
        wall_touch_right = any(tile.type in ('wall', 'normal') and right_sensor.colliderect(tile) 
                               for tile in tiles)
        wall_touch_left = any(tile.type in ('wall', 'normal') and left_sensor.colliderect(tile) 
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

        
        
        # Record position for shadow delay
        self.position_history.append((self.rect.centerx, self.rect.centery))
        if len(self.position_history) > self.history_length:
            self.position_history.pop(0)
        
        # Update animation based on current state
        

    def update_animation(self):
        """Update the current animation"""
        #if hasattr(self, 'is_holding_violin') and self.is_holding_violin:
            #new_animation = 'violin_pose' 
    
        keys = pygame.key.get_pressed()
        # Determine which animation should play
        if self.is_dashing and self.can_move:
            new_animation = 'dash'
        elif self.is_jumping: #if in air and are pressing against a wall, show climb
            pressing_into_left = (self.on_wall == 'left' and keys[pygame.K_LEFT])
            pressing_into_right = (self.on_wall == 'right' and keys[pygame.K_RIGHT])

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
    def jump(self, is_running=False):
        keys = pygame.key.get_pressed()
        input_x = 0
        if keys[pygame.K_LEFT]:
            input_x = -1
        elif keys[pygame.K_RIGHT]:
            input_x = 1
        # Add controller input here if needed
              
        if not self.is_jumping:
            # Normal jump from ground
            force = RUN_JUMP_FORCE if is_running else JUMP_FORCE
            self.vel_y = force
            self.is_jumping = True
            self.air_control_timer = 20
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
        self.rect.topleft = spawn_point

    def die(self):
        self.health = 0
        self.visible = False
        self.dead_animation_started = True
        self.vel_x = 0
        self.vel_y = 0

    def is_dead(self):
        return self.health <= 0

class Checkpoint:
    def __init__(self, x, y, image):
        self.image = image
        self.rect = self.image.get_rect(topleft=(x, y))
        self.active = False
        self.type = 'checkpoint'

    def update(self, player):
        if not self.active and self.rect.colliderect(player.rect):
            self.active = True
            # Update the player's respawn position to this checkpoint
            player.spawn_point = (self.rect.x, self.rect.y)
            # Optional: Play a sound or visual effect here
            print("Checkpoint reached!")

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
    def __init__(self, x, y, image):
        self.image = image
        self.image_flipped = pygame.transform.flip(image, True, False)  # Flipped horizontally
        self.rect = self.image.get_rect(topleft=(x, y))
        self.spawn_pos = (x, y)

        self.active = False
        self.velocity = 0
        self.max_speed = 13       
        self.accel = 0.3
        self.direction = 0 # Will be 1 (right) or -1 (left)
        self.type = 'shockwave' 
        self.current_image = self.image  # Track which image to draw

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
        self.button_health = 1
        self.button_max_health = 1
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
        self.MAX_SPEED = 7.1
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
                self.performance_timer = 0
                # melody1_snd.play()
            if self.state == "VIOLIN_PERFORMANCE":
                self.performance_timer += 1
                if not hasattr(self, 'memory_fade'):
                    self.memory_fade = 0
                if self.performance_timer > 120:
                    self.memory_fade = min(255, self.memory_fade + 5)
                if self.performance_timer > 280:
                    self.state = "MEMORY_START"
        if self.state == "MEMORY_START":
            if self.memory_initialized == False:
        
                memory_text = [
                    "(You see a girl boarding a train.)",
                    "(A white door casts a looming presence...)",
                    "(You raise your hand to open the door.|)",
                    "~",
                    " (|You...| stop thinking about it.)"
        
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
                
        self.shake_duration = max(0, self.shake_duration - 1)
        for p in self.trail_particles[:]:
                p[0] -= 5      # Move particles left slightly
                p[3] -= 15     # Fade out
                if p[3] <= 0:
                    self.trail_particles.remove(p)
        print(f"Current State: {self.state} | Dialogue: {self.battle_dialogue}")
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

class NPC:
    def __init__(self, x, y, name, dialogue_list):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE * 2)
        self.name = name
        self.dialogue_text = dialogue_list 
        self.is_talking = False

        self.prompt_timer = 0
        self.talk_cooldown = 0 
    def check_interaction(self, player, keys):
        if self.talk_cooldown > 0:
            self.talk_cooldown -= 1
            return False # Can't talk yet!

        distance = pygame.math.Vector2(self.rect.center).distance_to(player.center)
        
        # Check keyboard or controller
        joy_press = False
        if joysticks:
            for joy in joysticks:
                if joy.get_button(0) or joy.get_button(1):
                    joy_press = True
                    break
                    
        if distance < 60 and (keys[pygame.K_z] or joy_press):
            return True
            
        return False

    def draw_prompt(self, screen, camera, player_rect):
        active_dialogue = False 
        """Draws the floating icon only when near the NPC."""
        dist = pygame.math.Vector2(self.rect.center).distance_to(player_rect.center)
        
        # Show prompt if player is close but not currently in dialogue
        if dist < 80 and not active_dialogue:
            self.prompt_timer += 0.1
            # Sine wave for the bobbing effect
            float_y = math.sin(self.prompt_timer) * 5
            
            # Position it above the NPC's head
            # apply() ensures it follows the camera properly
            prompt_pos = camera.apply(self.rect)
            prompt_x = prompt_pos.centerx
            prompt_y = prompt_pos.top - 20 + float_y
            
            # Draw a simple white triangle or use your 'checkpoint' icon scaled down
            pygame.draw.polygon(screen, (255, 255, 255), [
                (prompt_x - 10, prompt_y),
                (prompt_x + 10, prompt_y),
                (prompt_x, prompt_y + 10)
            ])

    def draw(self, screen, camera):

        npcs = ["Moistar", "DJ Oser", "???"]
        Moistar_image = get_image(pygame.image.load('Moistar.png').convert_alpha(), 0, 35, 35, SCALE)
        screen.blit(Moistar_image, camera.apply(self.rect))

class Tile:
    def __init__(self, rect, tile_type='normal', image=None, orientation='up'):
        self.rect = rect
        self.type = tile_type  # 'normal', 'platform', 'wall', or 'moonspike'
        self.image = image
        self.orientation = orientation
        

    def draw(self, screen, camera):
        if self.image:
            # Draw the PNG if it exists
            screen.blit(self.image, camera.apply(self.rect))
        else:
            # Fallback to gray square if image is missing
            pygame.draw.rect(screen, (100, 100, 100), camera.apply(self.rect))

class Decoration:
    def __init__(self, x, y, image):
        self.image = image
        self.rect = self.image.get_rect(topleft=(x, y))

    def draw(self, screen, camera):
        screen.blit(self.image, camera.apply(self.rect))


def setup_level(layout, moon_spike_images=None):
    shockwave_image = pygame.image.load('shockwave.png').convert_alpha()
    shockwave_image = pygame.transform.scale(shockwave_image, (TILE_SIZE*2, TILE_SIZE))
    tiles_list = []
    checkpoints = []
    decorations_list = []
    total_level_height = len(layout) * TILE_SIZE
    tree_img = pygame.image.load('moonTree.png').convert_alpha()
    tree_img = pygame.transform.scale(tree_img, (TILE_SIZE * 2, TILE_SIZE * 4))
                
    for row_index, row in enumerate(layout):
        for col_index, cell in enumerate(row):
            x = col_index * TILE_SIZE
            y = row_index * TILE_SIZE
            
            if cell == '#':
                # Normal solid tile
                new_rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
                tiles_list.append(Tile(new_rect, 'normal'))
            if cell == 'G':
                #large normal tile
                new_rect = pygame.Rect(x, y, TILE_SIZE*4, TILE_SIZE*4)
                tiles_list.append(Tile(new_rect, 'normal'))
            elif cell == '$':
                # Tall tile (3x height)
                new_rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE*3)
                tiles_list.append(Tile(new_rect, 'normal'))
            elif cell == '-':
                # Wide tile (3x width)
                new_rect = pygame.Rect(x, y, TILE_SIZE*3, TILE_SIZE)
                tiles_list.append(Tile(new_rect, 'normal'))
            elif cell == 'P':
                # Platform tile (one-way from top, long and thin)
                new_rect = pygame.Rect(x, y, TILE_SIZE*2, TILE_SIZE)
                tiles_list.append(Tile(new_rect, 'platform'))
            elif cell == 'W':
                # Wall tile (sides only, tall and thin)
                new_rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE*2)
                tiles_list.append(Tile(new_rect, 'wall'))
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
          
            elif cell == 'T': #moonTree
                decorations_list.append(Decoration(x, y, tree_img))

            elif cell == 'o': #'normal' grey tile, but moonDetail.png
                moon_img = pygame.image.load("moonDetail.png").convert_alpha()
                moon_img = pygame.transform.scale(moon_img, (TILE_SIZE, TILE_SIZE))
                tiles_list.append(Tile(new_rect, 'normal', image=moon_img))
            elif cell in ('C', 'c'):
                checkpoint_img = pygame.image.load('checkpoint.png').convert_alpha()
                checkpoint_img = pygame.transform.scale(checkpoint_img, (TILE_SIZE*2, TILE_SIZE*2))
                new_checkpoint = Checkpoint(x, y, checkpoint_img)
                checkpoints.append(new_checkpoint)
            elif cell in ('M', 'D', 'L', 'R', 'm', 'd', 'l', 'r'):
                # Uppercase: regular MoonSpike.png, Lowercase: MoonSpikeDeep.png
                orientation_map = {'M': 'up', 'D': 'down', 'L': 'left', 'R': 'right',
                                   'm': 'up', 'd': 'down', 'l': 'left', 'r': 'right'}
                spike_type = 'deep' if cell.islower() else 'normal'
                orientation = orientation_map[cell]
                new_rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
                tile_img = None
                if moon_spike_images is not None and spike_type in moon_spike_images:
                    tile_img = moon_spike_images[spike_type].get(orientation)
                tiles_list.append(Tile(new_rect, 'moonspike', image=tile_img, orientation=orientation))

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

    return tiles_list, checkpoints, decorations_list


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

    def start_takeoff(self, next_level):
        self.taking_off = True
        self.target_level = next_level
        self.active = True

    def update(self):
        if not self.active:
            return False
        if self.taking_off:
            self.rect.y -= self.takeoff_speed
            if self.rect.y < -200:
                if not hasattr(self, 'transition_fade'):
                    self.transition_fade = 0
                self.transition_fade = min(255, self.transition_fade + 5)
            if self.transition_fade >= 255:
                self.state = "SHIP_MEMORY"
                return True
            #if self.rect.bottom < 0:
                #self.active = False
            
    
        return False

    def draw(self, screen, camera):
        if not self.active:
            return
        if hasattr(self, 'transition_fade') and self.transition_fade > 0:
            fade_surf = pygame.Surface((WIDTH, HEIGHT))
            fade_surf.fill((0, 0, 0))
            fade_surf.set_alpha(self.transition_fade)
            screen.blit(fade_surf, (0, 0))
        screen.blit(self.image, camera.apply(self.rect))


def load_level(level_number):
    global current_level, LEVEL_MAP, tiles, checkpoints, decorations_list
    global npcs, hazards, boss_triggered, boss_finished, boss_manager
    global boss_state, boss_first_entry, active_dialogue, ship, shadow, camera
    global moon_spike_images, Vio, LEVEL_START_POINTS

    current_level = level_number
    if level_number == 1:
        LEVEL_MAP = LEVEL1_MAP
    elif level_number == 2:
        LEVEL_MAP = LEVEL2_MAP
    else:
        LEVEL_MAP = LEVEL1_MAP

    npcs.clear()
    if shadow is None:
        shadow = Shadow((0, 0))
    else:
        shadow.reset(Vio)

    hazards = [shadow]
    boss_triggered = False
    boss_finished = False
    boss_manager = None
    boss_state = None
    boss_first_entry = True
    active_dialogue = None

    start_pos = LEVEL_START_POINTS.get(level_number, (100, 2724))
    Vio.reset_for_level(start_pos)

    level_width = max(len(row) for row in LEVEL_MAP) * TILE_SIZE
    ship_x = min(level_width - TILE_SIZE * 2 - 50, 15000 + 2500)
    ship_y = min(HEIGHT + 120, 760)
    ship = Ship(ship_x, ship_y)

    if camera is not None:
        camera.offset_x = max(0, Vio.rect.centerx - WIDTH // 2)
        camera.offset_y = max(0, Vio.rect.centery - HEIGHT * 0.65)

    tiles, checkpoints, decorations_list = setup_level(LEVEL_MAP, moon_spike_images)
    return tiles, checkpoints, decorations_list


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
    global boss_triggered, boss_manager, mo_boss, active_dialogue
    
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
            boss_manager.waves.clear()
            boss_manager.state = "INTRO"  # Goes straight to FALLING_IN on re-entry
            boss_manager.said_hint_line = False
            boss_manager.battle_dialogue = None
        return
    
    # Normal death handling (not during boss fight)
    # Reset player while preserving the current spawn point.
    player.reset()
    
    # Reset all hazards
    for hazard in hazards:
        hazard.reset(player)
    
    # Reset shockwaves and other resettable tiles
    for tile in tiles:
        if hasattr(tile, 'reset'):
            tile.reset()
    
    # Reset camera
    camera.__init__(WIDTH, HEIGHT)
    
    # Clear particles
    particles.clear()

    if trail_particles is not None:
        trail_particles.clear()

def main():
    global boss_triggered, boss_manager, Vio, shadow, ship, current_level, moon_spike_images, active_dialogue, hazards
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
    # Load all animations
    try:
        animations = load_spritesheet('Captain_Vio_Sheet.png', 48, 52, SCALE //1.5)
    except pygame.error:
        print("Error: Could not load Captain_Vio_Sheet.png")
        animations = None
        return
    
    

    Vio = Player(animations)
    particles = []
    trail_particles = []
    
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

    tiles, checkpoints, decorations_list = load_level(current_level)

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
    game_state = "INTRO"

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


    while True:
        global boss_manager, boss_state, boss_first_entry, button_is_glowing
        keys = pygame.key.get_pressed()
        z_currently_held = keys[pygame.K_z] or keys[pygame.K_RETURN] or keys[pygame.K_SPACE] or (joysticks and any(joy.get_button(0) or joy.get_button(1) for joy in joysticks))
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return

            # Handle controller connection/disconnection
            if event.type == pygame.JOYDEVICEADDED:
                joy = pygame.joystick.Joystick(event.device_index)
                joy.init()
                joysticks.append(joy)
                print(f"Controller connected: {event.device_index}")
            if event.type == pygame.JOYDEVICEREMOVED:
                removed_id = getattr(event, 'instance_id', None)
                if removed_id is not None:
                    joysticks[:] = [joy for joy in joysticks if joy.get_instance_id() != removed_id]
                else:
                    joysticks[:] = [joy for joy in joysticks if joy.get_id() != event.device_index]
                print(f"Controller disconnected: {removed_id if removed_id is not None else event.device_index}")

            # Jump logic only in playing state
            # Allow jump input if no dialogue, or if dialogue is passive
            can_jump = not active_dialogue or (active_dialogue and active_dialogue.is_passive)
            if game_state == "PLAYING" and can_jump:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_z: 
                        is_running = keys[pygame.K_x] and abs(Vio.vel_x) > WALK_SPEED
                        Vio.jump(is_running)
                
                if event.type == pygame.JOYBUTTONDOWN:
                    if event.button == 0 or event.button == 1: 
                        is_running = False
                        for joy in joysticks:
                            try:
                                if joy.get_button(2) or joy.get_button(3) and abs(Vio.vel_x) > WALK_SPEED:
                                    is_running = True
                                    break
                            except pygame.error:
                                continue
                        Vio.jump(is_running)
        if game_state == "PLAYING":
            if active_dialogue:
                
                skip = [keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]] and canSkip == True
                active_dialogue.update(keys, skip_held=skip)
                if active_dialogue.finished:
                    # Check if this was the boss intro dialogue
                    if boss_triggered and boss_manager and boss_manager.state == "INTRO":
                        boss_manager.transition_to_falling()
                        
                    active_dialogue = None
                    npc.talk_cooldown = 30
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
                if z_currently_held and not z_was_held:
            
                    for npc in npcs:
                        if npc.check_interaction(Vio.rect, keys) and not active_dialogue:
                            active_dialogue = DialogueBox(font, npc.dialogue_text, speaker_name="Moistar")

        

        # Update based on game state
        if game_state == "INTRO":
            # Skip intro dialogue by holding Shift (for dev testing)
            skip_held = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
            intro_dialogue.update(keys, skip_held=skip_held)
            if intro_dialogue.finished:
                game_state = "PLAYING"
        elif game_state == "PLAYING":
            camera.update(Vio.rect)
           
            # Only lock controls if dialogue is NOT passive
            cutscene_mode = active_dialogue and not getattr(active_dialogue, 'is_passive', False)
            Vio.update(tiles, trail_particles, cutscene_mode=cutscene_mode)
            
            #if active_dialogue:
                #Vio.update_animation()
            
            for cp in checkpoints:
                cp.update(Vio)
            for hazard in hazards:
                if not active_dialogue and not (boss_triggered and isinstance(hazard, Shadow)):
                    hazard.update(Vio)
                if not fading and not (boss_triggered and isinstance(hazard, Shadow)) and hazard.check_player(Vio):
                    hazard.on_hit(Vio)
            if Vio.rect.y > HEIGHT + 10000 and not fading:
                Vio.take_damage(Vio.max_health)
            if Vio.is_dead() and not fading:
                fading = True
                Vio.vel_x = 0  # Stop horizontal movement
                Vio.vel_y = 0  # Stop falling
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
            #if ship and not ship.active:
                    #ship.activate()
            #if ship and ship.active:
                #if Vio.rect.colliderect(ship.rect) and not ship.taking_off:
                    #if z_currently_held and not z_was_held:
                        #Vio.visible = False 
                        #Vio.can_move = False 
                        #ship.start_takeoff(2)

                #if ship.update():
                 #   game_state = "MEMORY_TRANSITION" 
                  #  memory_text = [
                    #    "Lin: You're playing too fast again, Vio.",
                    #    "Lin: If you rush the ending... | you'll miss the best part of the song.",
                    #    "Vio: The best part?",
                    #    "Lin: The part where we're playing together. | Don't leave me behind, okay?"
                  #  ]
                    
                  #  active_dialogue= DialogueBox(font, memory_text, autoplay = True, is_passive=False)
                    #if ship.target_level is not None:
                        #load_level(ship.target_level)
            if not boss_triggered and Vio.rect.x > BOSS_ARENA1_START_X and Vio.rect.x <17000:
                
                boss_triggered = True
                # Create the boss and manager
                mo_boss = DJOserBoss(15000 + WIDTH // 2 - TILE_SIZE, 780, mo_boss_img, font)
                boss_manager = BossManager(mo_boss, boombox_img, shockwave_img, font)
                boss_state = "INTRO"
                s
                
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

            if boss_manager and boss_manager.state == "FINISHED":
                if ship and not ship.active:
                    ship.activate()

                if ship and ship.active:
                    if Vio.rect.colliderect(ship.rect) and not ship.taking_off:
                        if z_currently_held and not z_was_held:
                            Vio.visible = False 
                            Vio.can_move = False 
                            ship.start_takeoff(2)

                    if ship.update():
                        if ship.target_level is not None:
                            load_level(ship.target_level)



            #DRAW===================================
            screen.fill((124, 57, 103))
            for star in stars:
                star.update()
                star.draw(screen, camera)
                
            for hazard in hazards:
                
                screen.blit(hazard.image, camera.apply(hazard.rect))
            for tile in tiles:
                # Draw different colors based on tile type
                if tile.type == 'shockwave':
                    tile.update(Vio.rect)
                if tile.type == 'normal':
                    color = (155, 173, 183)  # grey
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
                elif tile.type == 'moonspike' or tile.type == 'shockwave':
                    if tile.type == 'shockwave' and hasattr(tile, 'current_image'):
                        screen.blit(tile.current_image, camera.apply(tile.rect))
                    elif tile.image:
                        screen.blit(tile.image, camera.apply(tile.rect))
                    else:
                        color = (220, 220, 220)
                        pygame.draw.rect(screen, color, camera.apply(tile.rect))
                else:
                    color = (150, 150, 150)  # Gray fallback
                    pygame.draw.rect(screen, color, camera.apply(tile.rect))
                for decoration in decorations_list:
                    decoration.draw(screen, camera) 
        
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
                    

        if game_state == "INTRO":
            screen.fill((0, 0, 0))
            intro_dialogue.draw(screen, WIDTH // 2 - 200, HEIGHT // 2)
        elif game_state == "PLAYING":
            health_text = font.render(f"Health: {Vio.health}", True, (255, 255, 255))
            screen.blit(health_text, (10, 10))
            for cp in checkpoints:
                screen.blit(cp.image, camera.apply(cp.rect))
            for npc in npcs:
                npc.draw(screen, camera)
                npc.draw_prompt(screen, camera, Vio.rect)

            # Draw boss manager if active
            if boss_manager:
                boss_manager.draw(screen, camera)

            if ship:
                ship.draw(screen, camera)
                if ship.active and not ship.taking_off and Vio.rect.colliderect(ship.rect):
                    prompt_text = font.render("Press Z to board the ship", True, (255, 255, 255))
                    prompt_pos = camera.apply(pygame.Rect(Vio.rect.centerx - 80, Vio.rect.top - 40, 160, 20))
                    screen.blit(prompt_text, (prompt_pos.x, prompt_pos.y))

            if Vio.visible:
                for trail in trail_particles:
                    trail.draw(screen, camera)
                draw_image = Vio.image
                if not Vio.invulnerability_timer >0 or (pygame.time.get_ticks() // 50) % 2 == 0:
                    screen.blit(draw_image, camera.apply(Vio.rect))

        #boss1 cutscene
        if boss_manager and hasattr(boss_manager, 'memory_fade') and boss_manager.memory_fade > 0:
            fade_surf = pygame.Surface((WIDTH, HEIGHT))
            fade_surf.fill((0, 0, 0)) # Pure black
            fade_surf.set_alpha(boss_manager.memory_fade)
            screen.blit(fade_surf, (0, 0))
            
        #    DRAW  SHIP===
        if ship.active and ship.transition_fade > 0:
            fade_surf = pygame.Surface((WIDTH, HEIGHT))
            fade_surf.fill((0, 0, 0))
            fade_surf.set_alpha(ship.transition_fade)
            screen.blit(fade_surf, (0, 0))

        # If we are in the memory state, keep the screen black and show text
        if game_state == "MEMORY_TRANSITION":
            screen.fill((0, 0, 0))
            # Draw your Lin memory text here!
            # Once the player presses Z to skip or timer ends:
            # load_level(2)
            # game_state = "PLAYING"

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
        if active_dialogue and getattr(active_dialogue, 'trigger_glitch', False):
    
            screen_copy = screen.copy()
            screen.fill((255, 255, 255))
            for i in range(0, HEIGHT, 6): # Adjust '4' for thicker/thinner scanlines
                offset = random.randint(-20, 20)
                screen.blit(screen_copy, (offset, i), (0, i, WIDTH, 4))
        
        pygame.display.flip()
        clock.tick(60)
        pygame.display.set_caption(f" X: {Vio.rect.x} Y: {Vio.rect.y}")
LEVEL1_MAP = [
    '........................................................................................................................................................................................................................................G..GG...G...G...G...G...G...G...G...G...G..G..G...G...G...G...G...GG...G...G...G..G...GG...',
    '.................................................................................................................................................................................................................................................................................................................................',
    '.................................................................................................................................................................................................................................................................................................................................',
    '.......................................................................................................................................................................................................................................G...GG...G...G...G...G...G...G...G...G...G...G..G...G...G...G...G...G...G...G...G...G...G..G...G...G...G..G...G...G...G..G...G...G...G..G...G...G...G..G...G...G...G.',
    '....................................................................................................................................................................................................................................................................................................................................................................$',
    '...........................................................................................................................................................................................................................................G.....................................................................................',
    '.......................................................................................................................................................................................................................................G...G.........................................................................................$....................................',
    '......................................................................................................................................................................................G...G...G...G...G...G...G...G...G...G...G...G........GG...dddddddddddddddddddddddddd#############################################ddddd.........$$..............$.$...................................',
    '...............................................................................................................................................................................................................................................r..........................d######..G...G...G...G..G..$G...G...G...G..$$.........................................................................................',
    '.......................................................................................................................................................................................................................................G...G...$...........................d#####..G...G...G...G..G..$G...G...G...G..$$...................................................................................',
    '......................................................................................................................................................................................G...G...G...G...G...G...G...G...G...G...G...G.........................................d####....................................$$................................................................................',
    '...............................................................................................................................................................................................................................................$.............................d###....................................................................................................................',
    '.......................................................................................................................................................................................................................................G...G...#..............................d##........................................................................................................................',
    '......................................................................................................................................................................................G...G...G...G...G...G...G...G...G...G...G...G............#..........#########.......................................................................................................................................................',
    '...............................................................................................................................................................................................................................................$..........#########.......................................................................................................................................................',
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
    '.........N.......$$$$$..........M.......G.......................................ddddd...........................................#..................S..................l##r.......l###r.......l###r.......l#####r.....l##############################################################################',
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
    '........................................................................................................................................................................................................................................G..GG...G...G...G...G...G...G...G...G...G..G..G...G...G...G...G...GG...G...G...G..G...GG...',
    '.................................................................................................................................................................................................................................................................................................................................',
    '.................................................................................................................................................................................................................................................................................................................................',
    '.......................................................................................................................................................................................................................................G...GG...G...G...G...G...G...G...G...G...G...G..G...G...G...G...G...G...G...G...G...G...G..G...G...G...G..G...G...G...G..G...G...G...G..G...G...G...G..G...G...G...G.',
    '....................................................................................................................................................................................................................................................................................................................................................................$',
    '...........................................................................................................................................................................................................................................G.....................................................................................',
    '.......................................................................................................................................................................................................................................G...G.........................................................................................$....................................',
    '......................................................................................................................................................................................G...G...G...G...G...G...G...G...G...G...G...G........GG...dddddddddddddddddddddddddd#############################################ddddd.........$$..............$.$...................................',
    '...............................................................................................................................................................................................................................................r..........................d######..G...G...G...G..G..$G...G...G...G..$$.........................................................................................',
    '.......................................................................................................................................................................................................................................G...G...$...........................d#####..G...G...G...G..G..$G...G...G...G..$$...................................................................................',
    '......................................................................................................................................................................................G...G...G...G...G...G...G...G...G...G...G...G.........................................d####....................................$$................................................................................',
    '...............................................................................................................................................................................................................................................$.............................d###....................................................................................................................',
    '.......................................................................................................................................................................................................................................G...G...#..............................d##........................................................................................................................',
    '......................................................................................................................................................................................G...G...G...G...G...G...G...G...G...G...G...G............#..........#########.......................................................................................................................................................',
    '...............................................................................................................................................................................................................................................$..........#########.......................................................................................................................................................',
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
    '..NNNNN...............---..###.............MM$$$$$$$$$$......o.......................#-o##.....................x.....................#.....................................####.......l###r.......l###r.......l#####r.....l##########################################################mmmmmmmmmmmmmm######..',
    '.................$$$$$$$$.............$$$G..G...$$..............-.....-..-......#####...........................................#.....................C...............l##r.......l###r.......l###r.......l#####r.....l##############################################################################.',
    '.........N.......$$$$$..........M.......G.......................................ddddd...........................................#..................S..................l##r.......l###r.......l###r.......l#####r.....l##############################################################################',
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

LEVEL_MAP = LEVEL1_MAP
if __name__ == "__main__": main()
