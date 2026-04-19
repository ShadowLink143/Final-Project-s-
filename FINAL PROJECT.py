import pygame
import math
#for now, z is jump, x is run, and shift is dash. to wall jump, be in air, press the other direction, and jump. (oh and I temporarily lowered gravity and made the shadow very slow to test wall jumping)
#and for joystick, A/B is jump, X/Y is run, and shoulder buttons are dash

pygame.joystick.init()

# Keep track of controllers
joysticks = []
# Constants
WIDTH, HEIGHT = 800, 600
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



class DialogueBox:
    def __init__(self, font, text_list, autoplay=False, auto_delay=120):
        self.font = font
        self.text_list = text_list
        self.current_sentence = 0
        self.current_text = ""
        self.char_index = 0
        self.timer = 0
        self.speed = 3  # Lower is faster
        self.finished = False
        self.autoplay = autoplay  # If True, auto-advance to next sentence
        self.auto_delay = auto_delay  # Frames to wait before auto-advancing
        self.auto_timer = 0  # Timer for autoplay
        self.wait_timer = 0
    def update(self, keys, skip_held=False):
        # Skip entire dialogue if button held (useful for dev testing)
        keys = pygame.key.get_pressed()
        if skip_held:
            self.finished = True
            return
        
        if self.current_sentence < len(self.text_list):
            target_text = self.text_list[self.current_sentence]

            if self.wait_timer > 0:
                self.wait_timer -= 1
                return
            
            if self.char_index < len(target_text):
                self.timer += 1
                if self.timer >= self.speed:
                    char = target_text[self.char_index]
                    if char == "|":  # PAUSE TAG
                        self.wait_timer = 30  # Wait for 30 frames
                        self.char_index += 1  # Skip the symbol
                    elif char == ">": # WARP 
                        # Add everything left in the sentence instantly
                        remaining_text = target_text[self.char_index + 1:]
                        self.current_text += remaining_text
                        self.char_index = len(target_text)
                    elif pygame.KEYUP in keys and (keys[pygame.K_z] or keys[pygame.K_RETURN] or keys[pygame.K_SPACE]):
                        # If player releases advance button, skip to end of sentence
                        self.current_text = target_text
                        self.char_index = len(target_text)
                    else:
                        self.current_text += char
                        self.char_index += 1
                    

            else:
                # Text is fully typed
                if self.autoplay:
                    self.auto_timer += 1
                    if self.auto_timer >= self.auto_delay:
                        self.advance_sentence()
                else:
                    # Wait for input to advance
                    if keys[pygame.K_z] or keys[pygame.K_RETURN] or keys[pygame.K_SPACE]:
                        self.advance_sentence()
        else:
            self.finished = True

    def advance_sentence(self):
        """Helper to reset variables for the next sentence."""
        self.current_sentence += 1
        self.current_text = ""
        self.char_index = 0
        self.timer = 0
        self.auto_timer = 0
        self.wait_timer = 0
    def draw(self, screen, x, y):
        lines = self.current_text.split('\n')
        line_height = self.font.get_linesize()
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


class Player:
    def __init__(self, animations):
        self.animations = animations  # Dictionary of animation states to frame lists
        self.current_animation = 'idle'
        self.frame_index = 0
        self.frame_counter = 0
        self.animation_speed = 0.15  # How fast to cycle frames
        
        # Get initial image from idle animation
        self.image = self.animations['idle'][0]
        self.rect = self.image.get_rect(topleft=(100, 2300)) 
        self.hitbox = self.rect.inflate(-10, 0) 
        self.rect = self.hitbox.copy()
        # State tracking
        self.facing_right = True
        
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

        self.health = 3
        self.max_health = 3
        self.invulnerability_timer = 0
        self.visible = True
        self.dead_animation_started = False
        
        # Physics Constants
        self.ACCEL = 0.6     
        self.FRICTION = 0.9  
        self.MAX_WALK = 6     
        self.MAX_RUN = 10     
        self.wall_cling_timer = 0
        self.WALL_CLING_DURATION = 20
    def update(self, tiles):
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
        #==========
        if self.is_dashing:
            self.dash_timer -= 1
            self.vel_x = self.dash_direction[0] * DASH_SPEED
            self.vel_y = self.dash_direction[1] * DASH_SPEED
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
        if not self.is_dashing:
            self.vel_y += GRAVITY

        # Wall sliding slows descent when clinging to a wall
        if self.on_wall and self.vel_y > 0 and not self.is_dashing:
            self.vel_y = min(self.vel_y, self.wall_slide_speed)

        self.rect.y += self.vel_y
        
        for tile in tiles:
            if self.rect.colliderect(tile.rect):
                # Moon spike kills on touch regardless of collision direction
                if tile.type == 'moonspike':
                    self.take_damage(self.max_health)
                # Platform tiles only block from TOP (vel_y > 0)
                if tile.type == 'platform':
                    if self.vel_y > 0:  # Falling onto platform
                        self.rect.bottom = tile.rect.top
                        self.vel_y = 0
                        self.is_jumping = False
                        self.dash_spent = False
                        self.dash_ready = True
                    # Platform lets you pass through from below/sides
                # Wall tiles don't block vertical movement
                elif tile.type == 'wall':
                    # Walls allow pass-through from top/bottom
                    continue
                # Normal tiles block all directions
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
                        self.on_wall = None
        
        # Update animation based on current state
        self.update_animation()

    def update_animation(self):
        """Update the current animation based on player state and cycle frames."""
        keys = pygame.key.get_pressed()
        # Determine which animation should play
        if self.is_dashing:
            new_animation = 'dash'
        elif self.is_jumping: #if in air and are pressing against a wall, show climb
            pressing_into_left = (self.on_wall == 'left' and keys[pygame.K_LEFT])
            pressing_into_right = (self.on_wall == 'right' and keys[pygame.K_RIGHT])

            if pressing_into_left or pressing_into_right:
                new_animation = 'climb'
            else:
                new_animation = 'jump'
        elif abs(self.vel_x) > self.MAX_WALK * 0.8:  # Running threshold
            new_animation = 'run'
        elif abs(self.vel_x) > 1.1:  # Walking threshold
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
        if amount <= 0 or self.invulnerability_timer > 0:
            return False
        self.health -= amount
        self.invulnerability_timer = 30
        return True

    def die(self):
        self.health = 0
        self.visible = False
        self.dead_animation_started = True

    def is_dead(self):
        return self.health <= 0

class Hazard:
    def update(self, player):
        pass

    def check_player(self, player):
        return self.rect.colliderect(player.rect)

    def on_hit(self, player):
        pass

    def reset(self, player):
        pass

class Shadow(Hazard):
    def __init__(self, start_pos=(0, 0)):
        self.start_pos = start_pos
        try:
            self.sprite_sheet = pygame.image.load('Dark_Kris_Sheet.png').convert_alpha()
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
        self.FRICTION = 0.82

    def update(self, player):
        # Calculate where the player is relative to the shadow.
        dx = player.rect.centerx - self.rect.centerx # Horizontal distance
        dy = player.rect.centery - self.rect.centery # Vertical distance
    
        # Move toward the player smoothly
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

class Camera:
    def __init__(self, width, height):
        self.offset_x = 0
        self.offset_y = 0
        self.width = width
        self.height = height

    def apply(self, entity_rect):
        return entity_rect.move(-self.offset_x, -self.offset_y)

    def update(self, target_rect):
        self.offset_x = target_rect.centerx - int(WIDTH / 2 - 20)
        self.offset_y = target_rect.centery - int(HEIGHT * 0.65)
        
        self.offset_x = max(0, self.offset_x)
        self.offset_y = max(-10000000, self.offset_y) 

class NPC:
    def __init__(self, x, y, name, dialogue_list):
        self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE * 2)
        self.name = name
        self.dialogue_text = dialogue_list 
        self.is_talking = False
    
    def check_interaction(self, player, keys):
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

    def draw(self, screen, camera):
        # Placeholder for NPC: A bright yellow square
        npcs = ["Moistar", "DJ Oser", "???"]
        Moistar_image = get_image(pygame.image.load('Moistar.png').convert_alpha(), 0, 16, 32, SCALE)
        screen.blit(Moistar_image, camera.apply(self.rect))

class Tile:
    def __init__(self, rect, tile_type='normal', image=None, orientation='up'):
        self.rect = rect
        self.type = tile_type  # 'normal', 'platform', 'wall', or 'moonspike'
        self.image = image
        self.orientation = orientation

npcs = []

def setup_level(layout, moon_spike_images=None):
    tiles_list = []
    total_level_height = len(layout) * TILE_SIZE
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
            elif cell == 'M':
                # Moon spike tile: kills on touch, rendered with a PNG
                new_rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
                tile_img = None
                if moon_spike_images is not None:
                    tile_img = moon_spike_images.get('up')
                tiles_list.append(Tile(new_rect, 'moonspike', image=tile_img, orientation='up'))
            elif cell == 'N':
                # level 1 NPC 
                lines = [
                    "Moistar: Help! Help!",
                    "So there I was, enjoying my donut,| and then a sound wave zipped by \nand knocked it out of my hand!| \nCurse you, Mo....",
                    "He found this weird paper.| He calls himself 'DJ Oser' now.\nThinks he's doing everyone a favor by blasting music.",
                    "But all he's doing is just causing desert-related incidents.",
                    "He's up ahead.| MaKE hIm PaaYyyYy....",
                    "Captain Vio: Yeah, yeah, I know. Let's get this over with."
                ]
                npcs.append(NPC(x, y, "Moistar", lines))

    return tiles_list 
def get_image(sheet, frame, width, height, scale):
    image = pygame.Surface((width, height), pygame.SRCALPHA).convert_alpha()
    image.blit(sheet, (0, 0), ((frame * width), 0, width, height))
    image = pygame.transform.scale(image, (width * scale, height * scale))
    return image


def load_spritesheet(filename, frame_w, frame_h, scale):
    """Load spritesheet and extract animation frames scaled to the given scale factor."""
    sheet = pygame.image.load(filename).convert_alpha()
    
    
    
    animations = {
        "idle":  extract_frames(sheet, 0, 0, 3, frame_w, frame_h, scale),
        "walk":  extract_frames(sheet, 0, 3, 3, frame_w, frame_h, scale),
        "jump":  extract_frames(sheet, 1, 0, 2, frame_w, frame_h, scale),
        "dash":  extract_frames(sheet, 1, 2, 2, frame_w, frame_h, scale),
        "climb": extract_frames(sheet, 1, 4, 2, frame_w, frame_h, scale),
        "run":   extract_frames(sheet, 2, 0, 6, frame_w, frame_h, scale)
    }
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


def main():
    pygame.init()
    pygame.joystick.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    camera = Camera(WIDTH, HEIGHT)
    
    # Load all animations
    try:
        animations = load_spritesheet('Captain_Vio_Sheet.png', 48, 52, SCALE //1.5)
    except pygame.error:
        print("Error: Could not load Captain_Vio_Sheet.png")
        animations = None
        return
    
    Kris = Player(animations)
    shadow = Shadow((Kris.rect.x - 250, Kris.rect.y))
    hazards = [shadow, Spike((500, 520), damage=1)] 
    particles = []
    active_dialogue = None
    # Scan for any controllers already plugged in
    for i in range(pygame.joystick.get_count()):
        joy = pygame.joystick.Joystick(i)
        joy.init()
        joysticks.append(joy)

    # Moon spike image loading and rotated variants
    moon_spike_images = {}
    try:
        moon_spike_base = pygame.image.load('MoonSpike.png').convert_alpha()
        moon_spike_base = pygame.transform.scale(moon_spike_base, (TILE_SIZE, TILE_SIZE))
    except pygame.error:
        moon_spike_base = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        pygame.draw.polygon(moon_spike_base, (200, 200, 255), [(0, TILE_SIZE), (TILE_SIZE * 0.25, TILE_SIZE * 0.4), (TILE_SIZE * 0.5, TILE_SIZE), (TILE_SIZE * 0.75, TILE_SIZE * 0.4), (TILE_SIZE, TILE_SIZE)])

    moon_spike_images['up'] = moon_spike_base
    moon_spike_images['down'] = pygame.transform.rotate(moon_spike_base, 180)
    moon_spike_images['left'] = pygame.transform.rotate(moon_spike_base, 90)
    moon_spike_images['right'] = pygame.transform.rotate(moon_spike_base, -90)

    tiles = setup_level(LEVEL_MAP, moon_spike_images)
    fading = False
    fade_alpha = 0
    fade_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    font = pygame.font.Font(None, 30)

    # Game state
    game_state = "INTRO"

    # Intro setup
    opening_text = [
        "One more time. One more time.",
        "These three melodies can turn back the very hands of time.",
        "I will get you back, Lena. Just wait.",
        "The Moon...where the first melody is..."
        "Let's do this."
    ]
    intro_dialogue = DialogueBox(font, opening_text, autoplay = True)

    while True:
        keys = pygame.key.get_pressed()
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
            if game_state == "PLAYING" and not active_dialogue:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_z: 
                        is_running = keys[pygame.K_x] and abs(Kris.vel_x) > WALK_SPEED
                        Kris.jump(is_running)
                
                if event.type == pygame.JOYBUTTONDOWN:
                    if event.button == 0 or event.button == 1: 
                        is_running = False
                        for joy in joysticks:
                            try:
                                if joy.get_button(2) or joy.get_button(3) and abs(Kris.vel_x) > WALK_SPEED:
                                    is_running = True
                                    break
                            except pygame.error:
                                continue
                        Kris.jump(is_running)
        if game_state == "PLAYING":
            if active_dialogue:
                skip = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
                active_dialogue.update(keys, skip_held=skip)
                if active_dialogue.finished:
                    active_dialogue = None
            else:
                if keys[pygame.K_z] or keys[pygame.K_RETURN] or keys[pygame.K_SPACE] or (joysticks and any(joy.get_button(0) or joy.get_button(1) for joy in joysticks)):
            
                    for npc in npcs:
                        if npc.check_interaction(Kris.rect, keys):
                            active_dialogue = DialogueBox(font, npc.dialogue_text)

        # Update based on game state
        if game_state == "INTRO":
            # Skip intro dialogue by holding Shift (for dev testing)
            skip_held = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
            intro_dialogue.update(keys, skip_held=skip_held)
            if intro_dialogue.finished:
                game_state = "PLAYING"
        elif game_state == "PLAYING":
            if not active_dialogue:
                Kris.update(tiles)
            for hazard in hazards:
                if not active_dialogue:
                    hazard.update(Kris)
                if not fading and hazard.check_player(Kris):
                    hazard.on_hit(Kris)
            camera.update(Kris.rect)

            if Kris.rect.y > HEIGHT + 10000 and not fading:
                Kris.take_damage(Kris.max_health)

            if Kris.is_dead() and not fading:
                fading = True
                Kris.vel_x = 0  # Stop horizontal movement
                Kris.vel_y = 0  # Stop falling
                if not Kris.dead_animation_started:
                    Kris.die()
                    for _ in range(20):
                        import random
                        angle = random.uniform(0, 2 * math.pi)
                        speed = random.uniform(2, 8)
                        vx = math.cos(angle) * speed
                        vy = math.sin(angle) * speed
                        color = (200, 100, 255)
                        particles.append(Particle(Kris.rect.centerx, Kris.rect.centery, vx, vy, random.randint(2, 4), color))

            for particle in particles[:]:
                particle.update()
                if not particle.is_alive():
                    particles.remove(particle)

        # Draw based on game state
        if game_state == "INTRO":
            screen.fill((0, 0, 0))  # Pure black
            intro_dialogue.draw(screen, WIDTH // 2 - 200, HEIGHT // 2)
        elif game_state == "PLAYING":
            screen.fill((124, 57, 103))  # Dark purple background
            if Kris.visible:
                draw_image = Kris.image
                screen.blit(draw_image, camera.apply(Kris.rect))
            for hazard in hazards:
                screen.blit(hazard.image, camera.apply(hazard.rect))
            for tile in tiles:
                # Draw different colors based on tile type
                if tile.type == 'normal':
                    color = (155, 173, 183)  # grey
                    pygame.draw.rect(screen, color, camera.apply(tile.rect))
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
                elif tile.type == 'moonspike':
                    if tile.image:
                        screen.blit(tile.image, camera.apply(tile.rect))
                    else:
                        color = (220, 220, 220)
                        pygame.draw.rect(screen, color, camera.apply(tile.rect))
                else:
                    color = (150, 150, 150)  # Gray fallback
                    pygame.draw.rect(screen, color, camera.apply(tile.rect)) 
        
        # Fade to black and restart (only in playing state)
        if game_state == "PLAYING" and fading:
            fade_alpha += 5  # Fade speed
            if fade_alpha >= 255:
                # Restart
                Kris.__init__(animations)
                for hazard in hazards:
                    hazard.reset(Kris)
                camera.__init__(WIDTH, HEIGHT)
                fade_alpha = 0
                fading = False
                particles.clear()  # Clear all particles on reset
            else:
                fade_surface.fill((0, 0, 0, fade_alpha))
                screen.blit(fade_surface, (0, 0))
                # Draw particles on top of fade
                for particle in particles:
                    particle.draw(screen)
                    

        if game_state == "PLAYING":
            health_text = font.render(f"Health: {Kris.health}", True, (255, 255, 255))
            screen.blit(health_text, (10, 10))
        for npc in npcs:
            if game_state == "PLAYING":
                npc.draw(screen, camera)

        if active_dialogue:
            # Draw a simple box background for the text
            pygame.draw.rect(screen, (0, 0, 0), (50, 400, 700, 150)) # Black box
            pygame.draw.rect(screen, (255, 255, 255), (50, 400, 700, 150), 2) # White border
            active_dialogue.draw(screen, 70, 420)


        pygame.display.flip()
        clock.tick(60)
LEVEL_MAP = [
    '..................................................................................................................................................................',
    '.......................................................................................................................................................................',
    '.......................................................................................................................................................',
    '...................................................................................................................................................................',
    '..................................................................................................................................................................',
    '.......................................................................................................................................................................',
    '.......................................................................................................................................................',
    '...................................................................................................................................................................',
    '..................................................................................................................................................................',
    '.......................................................................................................................................................................',
    '.......................................................................................................................................................',
    '..................................................................................................................................................................',
    '.......................................................................................................................................................................',
    '.......................................................................................................................................................',
    '...................................................................................................................................................................',
    '..................................................................................................................................................................',
    '.......................................................................................................................................................................',
    '.......................................................................................................................................................',
    '...................................................................................................................................................................',
    '..................................................................................................................................................................',
    '.......................................................................................................................................................................',
    '..................................................................................................................................................................',
    '.......................................................................................................................................................................',
    '.......................................................................................................................................................',
    '..................................................................................................................................................................',
    '.......................................................................................................................................................................',
    '.......................................................................................................................................................',
    '..............................................................G.....................................................................................................',
    '..................................................................................................................................................................',
    '.......................................................................................................................................................................',
    '..............................................................G.........................................................................................',
    '...................................................................................................................................................................',
    '..................................................................................................................................................................',
    '.......................................................................................................................................................................',
    '..............................................................G....................................................................................................',
    '.......................................................................................................................................................................',
    '..........................................MGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG..........................................................................................................',
    '..........................................$$$.........................................................................................................................',
    '...............................MMM........$$$....................---......................................................',
    '...............................MMM........$$$.......................................................................................................................',
    '...............................MMM........$$$........................................................................................................................',
    '...............................MMM......MM$$$........---..........................................................................................'
    '...............................MMM......$$$.......................................................................................................',
    '##.............................MMM......$$$.....................---................---...........................................',
    '...............................MMM......$$$..........................................................................' ,
    '........-......................MMM......$$$....',
    '........-.............###...............$$$...........$$$$$$$..............................................-..--...............',
    '......................###...............$$$..........GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG.......................................................................................',
    '.................---..###.............MM$$$$$$$$$$..................................................................................................',
    '.................$$$$$$$$.............$$$.......$$..............-.....-..-..-..-.--..-.............W.......................WW...............................PP',
    '.................$$$$$..........M.....................................................................................W..........................PPPPPPPPPP.....',
    '........N......................MMM..............................................................W.......................WW.............',
    '#############....#########MMMMMMMM....$$$...$$$$$$$$$$$$$$$$$$$$$$$$####################.........................................',
    '#############MMMM#########.................................................................................................',
    '##########################.......................................................................................................................',
    '##########################........MMMM.........................................................................................',
    '',
    'W..............................WW............................PP',
    '..............................W..................PPPPPP',
    'W..............................WW',

]
if __name__ == "__main__": main()
