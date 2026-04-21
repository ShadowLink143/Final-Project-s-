import pygame, random, math
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
    def __init__(self, font, text_list, speaker_name="", autoplay=False, auto_delay=120, has_background=True):
        self.font = font
        self.text_list = text_list
        self.speaker_name = speaker_name
        self.has_background = has_background
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

    def update(self, keys, skip_held=False):
        # Skip entire dialogue if button held (useful for dev testing)
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
                    if char == "|":  # PAUSE TAG
                        self.wait_timer = 30  # Wait for 30 frames
                        self.char_index += 1  # Skip the symbol

                    elif char == "*": # NEW: WAIT FOR INPUT TAG
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
                if self.autoplay:
                    self.auto_timer += 1
                    if self.auto_timer >= self.auto_delay:
                        self.advance_sentence()
                elif is_z_pressed and not self.z_pressed_last:
                    self.advance_sentence()
            
            self.z_pressed_last = is_z_pressed
            #if you're holding z, the text will proceed twice as fast:
            if is_z_pressed:
                self.timer += self.speed // 0.1  # Speed up text when holding Z
        else:
            self.finished = True

    def advance_sentence(self):
        """reset variables for the next sentence."""
        self.current_sentence += 1
        self.current_text = ""
        self.char_index = 0
        self.timer = 0
        self.auto_timer = 0
        self.wait_timer = 0

        if self.current_sentence < len(self.text_list):
            next_line = self.text_list[self.current_sentence]
            if next_line.startswith("@"):
                parts = next_line[1:].split(":", 1)
                if len(parts) > 1:
                    self.speaker_name = parts[0]
                    self.text_list[self.current_sentence] = parts[1]

    def draw(self, screen, x, y):
        lines = self.current_text.split('\n')
        line_height = self.font.get_linesize()
        # Draw Name Box 
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
        self.image = image.copy()
        self.x = x
        self.y = y
        self.facing_right = facing_right
        self.alpha = 180  # Start with high opacity
        self.fade_speed = 15  # How fast it fades
        self.lifetime = 12  # Frames until particle disappears
        
    def update(self):
        self.alpha = max(0, self.alpha - self.fade_speed)
        self.lifetime -= 1

    def draw(self, screen, camera):
        if self.lifetime > 0 and self.alpha > 0:
            trail_image = self.image.copy()
            trail_image.set_alpha(self.alpha)
            screen_x = int(self.x - camera.offset_x)
            screen_y = int(self.y - camera.offset_y)
            screen.blit(trail_image, (screen_x, screen_y))

    def is_alive(self):
        return self.lifetime > 0


def create_star_image(size):
    surf = pygame.Surface((size * 5, size * 5), pygame.SRCALPHA)
    center = (size * 2 + 1, size * 2 + 1)
    base_color = (255, 240, 160)
    glow_color = (255, 235, 140)
    radius = max(1, size)
    # draw small diamond shape and cross arms
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

class Player:
    def __init__(self, animations):
        self.animations = animations  # Dictionary of animation states to frame lists
        self.current_animation = 'idle'
        self.frame_index = 0
        self.frame_counter = 0
        self.animation_speed = 0.15  # How fast to cycle frames
        default_pos = (100, 2724)

        # Get initial image from idle animation
        self.image = self.animations['idle'][0]
        self.rect = self.image.get_rect(topleft=(default_pos)) 
        self.hitbox = self.rect.inflate(-10, 0) 
        self.rect = self.hitbox.copy()
        self.spawn_point = (default_pos)
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
    def update(self, tiles, trail_particles=None):
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
            
            # Create dash trail particles
            if trail_particles is not None:
                trail_particles.append(TrailParticle(self.image, self.rect.x, self.rect.y, self.facing_right))
        
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
                if tile.type == 'moonspike' or tile.type == 'shockwave':
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
        self.rect = self.image.get_rect(topleft=(x, y))
        self.spawn_pos = (x, y)

        self.active = False
        self.velocity = 0
        self.max_speed = 13       
        self.accel = 0.3
        self.direction = 0 # Will be 1 (right) or -1 (left)
        self.type = 'shockwave' 

    def update(self, player_rect):
        if not self.active:
            # Check distance to player and activate if close enough
            distance = abs(self.rect.centerx - player_rect.centerx)
            if distance < 400:
                self.active = True
                # Move toward player
                self.direction = 1 if player_rect.x > self.rect.x else -1
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

class VerticalShockwave:
    def __init__(self, x, y, image, direction="down"):
        self.spawn_pos = (x, y)
        self.direction = direction # "up" or "down"
        
        if direction == "down":
            self.image = pygame.transform.rotate(image, -270) # Pointing down
        else:
            self.image = pygame.transform.rotate(image, 270)  # Pointing up
            
        self.rect = self.image.get_rect(topleft=(x, y))
        self.active = False
        self.velocity = 0
        self.max_speed = 62
        self.accel = 2.5
        self.type = 'shockwave'

    def update(self, player_rect):
        if not self.active:
            # Trigger if player is directly above/below within 100px width
            if abs(self.rect.centerx - player_rect.centerx) < 100:
                
                # Trigger if player is in front of the direction it's facing
                if self.direction == "down" and player_rect.y > self.rect.y:
                    self.active = True
                elif self.direction == "up" and player_rect.y < self.rect.y:
                    self.active = True
        else:
            if abs(self.velocity) < self.max_speed:
                self.velocity += self.accel * (1 if self.direction == "down" else -1)
            self.rect.y += self.velocity

    def reset(self):
        self.rect.topleft = self.spawn_pos
        self.active = False
        self.velocity = 0

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
        self.MAX_SPEED = 4.1
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
        # Placeholder for NPC: A bright yellow square

        npcs = ["Moistar", "DJ Oser", "???"]
        Moistar_image = get_image(pygame.image.load('Moistar4.png').convert_alpha(), 0, 35, 35, SCALE)
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

npcs = []

def setup_level(layout, moon_spike_images=None):
    shockwave_image = pygame.image.load('shockwave.png').convert_alpha()
    shockwave_image = pygame.transform.scale(shockwave_image, (TILE_SIZE*2, TILE_SIZE))
    tiles_list = []
    checkpoints = []
    decorations_list = []
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
                tree_img = pygame.image.load('moonTree.png').convert_alpha()
                tree_img = pygame.transform.scale(tree_img, (TILE_SIZE * 2, TILE_SIZE * 4))
                # Position it slightly higher so it "sits" on the ground
                decorations_list.append(Decoration(x, y - TILE_SIZE, tree_img))
            elif cell in ('C', 'c'):
                # Checkpoint: A floating piano or stand
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
                    "@Captain Vio: .|.|.|.|.|(Why did I talk to this guy again?)"
                ]
                npcs.append(NPC(x, y, "Moistar", lines))

    return tiles_list, checkpoints, decorations_list


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


def handle_player_death(player, hazards, tiles, camera, particles, trail_particles=None):
    """Reset everything when the player dies."""
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
    pygame.init()
    pygame.joystick.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    camera = Camera(WIDTH, HEIGHT)
    
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
    shadow = Shadow((Vio.rect.x - 250, Vio.rect.y))
    hazards = [shadow, Spike((500, 520), damage=1)] 
    particles = []
    trail_particles = []
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

    moon_spike_images['normal'] = {}
    moon_spike_images['normal']['up'] = moon_spike_base
    moon_spike_images['normal']['down'] = pygame.transform.rotate(moon_spike_base, 180)
    moon_spike_images['normal']['left'] = pygame.transform.rotate(moon_spike_base, 90)
    moon_spike_images['normal']['right'] = pygame.transform.rotate(moon_spike_base, -90)
    

       # Load deep MoonSpikeDeep.png
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

    tiles, checkpoints, decorations_list = setup_level(LEVEL_MAP, moon_spike_images)

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
            if game_state == "PLAYING" and not active_dialogue:
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
                skip = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
                active_dialogue.update(keys, skip_held=skip)
                if active_dialogue.finished:
                    active_dialogue = None
                    npc.talk_cooldown = 30
            else:
                if z_currently_held and not z_was_held:
            
                    for npc in npcs:
                        if npc.check_interaction(Vio.rect, keys):
                            active_dialogue = DialogueBox(font, npc.dialogue_text, speaker_name="Moistar")

        

        # Update based on game state
        if game_state == "INTRO":
            # Skip intro dialogue by holding Shift (for dev testing)
            skip_held = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
            intro_dialogue.update(keys, skip_held=skip_held)
            if intro_dialogue.finished:
                game_state = "PLAYING"
        elif game_state == "PLAYING":
            
            if not active_dialogue:
                 Vio.update(tiles)
            if active_dialogue:
                Vio.vel_x = 0
                Vio.vel_y = 0
                Vio.update_animation()
            for cp in checkpoints:
                cp.update(Vio)
            for hazard in hazards:
                if not active_dialogue:
                    hazard.update(Vio)
                if not fading and hazard.check_player(Vio):
                    hazard.on_hit(Vio)
            camera.update(Vio.rect)

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

            for particle in particles[:]:
                particle.update()
                if not particle.is_alive():
                    particles.remove(particle)

            # Update trail particles
            for trail in trail_particles[:]:
                trail.update()
                if not trail.is_alive():
                    trail_particles.remove(trail)

        # Draw based on game state
        
        if game_state == "INTRO":
            screen.fill((0, 0, 0))  # Pure black
            intro_dialogue.draw(screen, WIDTH // 2 - 200, HEIGHT // 2)
        elif game_state == "PLAYING":
            screen.fill((124, 57, 103))  # Dark purple background
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
                    if tile.image:
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
                    

        if game_state == "PLAYING":
            health_text = font.render(f"Health: {Vio.health}", True, (255, 255, 255))
            screen.blit(health_text, (10, 10))
            for cp in checkpoints:
                screen.blit(cp.image, camera.apply(cp.rect))
            for npc in npcs:
                npc.draw(screen, camera)
                npc.draw_prompt(screen, camera, Vio.rect)
            if Vio.visible:
                for trail in trail_particles:
                    trail.draw(screen, camera)
                draw_image = Vio.image
                screen.blit(draw_image, camera.apply(Vio.rect))
        

        if active_dialogue:
            # Draw a simple box background for the text
            pygame.draw.rect(screen, (0, 0, 0), (50, 450, 700, 150)) # Black box
            pygame.draw.rect(screen, (255, 255, 255), (50, 450, 700, 150), 2) # White border
            active_dialogue.draw(screen, 70, 470)


        pygame.display.flip()
        clock.tick(60)
LEVEL_MAP = [
    '........................................................................................................................................................................................................................................G..GG...G...G...G...G...G...G...G...G...G..G..G...G...G...G...G...GG...G...G...G..G...GG...',
    '.................................................................................................................................................................................................................................................................................................................................',
    '.................................................................................................................................................................................................................................................................................................................................',
    '.......................................................................................................................................................................................................................................G...GG...G...G...G...G...G...G...G...G...G...G..G...G...G...G...G...G...G...G...G...G...G.',
    '.................................................................................................................................................................................................................................................................................................................................',
    '...........................................................................................................................................................................................................................................G.....................................................................................',
    '.......................................................................................................................................................................................................................................G...G.....................................................................................',
    '...........................................................................................................................................................................................................................................GG...dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd',
    '...............................................................................................................................................................................................................................................r..........................d######..###.#.#.#####.###.#.............................................................................................................................',
    '.......................................................................................................................................................................................................................................G...G...$...........................d#####...#..#.#.#.#.#.###.#.......................................................................................................................',
    '............................................................................................................................................................................................................................................................................d####..##..###.#.#.#.#.........................................................................................................................',
    '...............................................................................................................................................................................................................................................$.............................d###....................#......................................................................................................................',
    '.......................................................................................................................................................................................................................................G...G...#..............................d##........................................................................................................................',
    '...............................................................................................................................................................................................................................................#..........#########.......................................................................................................................................................',
    '...............................................................................................................................................................................................................................................$..........#########.......................................................................................................................................................',
    '.......................................................................................................................................................................................................................................G...G..............lG...G...r......................................................................................................................................................',
    '..........................................................................................................................................................................................................................................................lG...G...rMMmmmmmmMGGGGGGGGGGGGGGGGGGGGGGGGG....................................................................................................................',
    '...............................................................................................................................................................................................................................................$..........lG...G...rG...G...G.G...#....#GGGGGGGGGGGGGG....................................................................................................................',
    '.......................................................................................................................................................................................................................................G...G..............lG...G...r..............l....rGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGggg....................................................................................................................',
    '..........................................................................................................................................................................................................................................................lG...G...r..............lG...rGGGGGGGGGGGGGG....................................................................................................................',
    '...............................................................................................................................................................................................................................................$..........lG...G...rG...G...G.G...l....rGGGGGGGGGGGGGG....................................................................................................................',
    '.......................................................................................................................................................................................................................................G...G..............lG...G...r..............l....rGGGGGGGGGGGGGG....................................................................................................................',
    '...............................................................................................................................................................................................................................................$..........lG...G...r..............lG...rGGGGGGGGGGGGGG....................................................................................................................',
    '.............................................................................................................................................................................G...#####..............................................G.....................lG...G...r..............l....rGGGGGGGGGGGGGG....................................................................................................................',
    '.............................................................................................................................................................................G...#####G...G...G...G...G...G...G...G...G...G...G...G.G...G..G..............lG...G...r..............l....rGGGGGGGGGGGGGG....................................................................................................................',
    '.............................................................................................................................................................................G...#####.........................................................r..........lG...G...r..............lG...rGGGGGGGGGGGGGG....................................................................................................................',
    '.............................................................................................................................................................................G...#####.........................................................#r.........$G...G...r..............l....rGGGGGGGGGGGGGG....................................................................................................................',
    '.............................................................................................................................................................................G...#####.........................................................##r.........G...G...r..............lG...rGGGGGGGGGGGGGG....................................................................................................................',
    '.............................................................................................................................................................................G...#G...ddddddddddddddddddddddddddddddddddddddddd###################r........G...G...r..............l....rGGGGGGGGGGGGGG....................................................................................................................',
    '............................................VVVV.............................................................................................................................G...#............VVV..............................D###################r......lG...G...r..............l....rGGGGGGGGGGGGGG....................................................................................................................',
    '.............................................................................................................................................................................G...#..............................................Ddd############G...r......lG...G...r..............lG...rGGGGGGGGGGGGGG....................................................................................................................',
    '.............................................................................................................................................................................G...#G..................................................L#########G...r......lG...G...r..............l....rGGGGGGGGGGGGGG....................................................................................................................',
    '.............................................................................................................................................................................G...#....................................................l########G...r......lG...G...r..............l....rGGGGGGGGGGGGGG....................................................................................................................',
    '..............................................................LMMR...........................................................................................................G...#.....................................................l#######G...r......$G...G...r..............lG...rGGGGGGGGGGGGGG....................................................................................................................',
    '..............................................................L##R...........................................................................................................G...#G.....................................................#######G...r.......G...G...r..............l....rGGGGGGGGGGGGGG....................................................................................................................',
    '..............................................................L##R...........................................................................................................G...#.......................................................DddddDG...r.......G...G...r..............lG...r..................................................................................................................................',
    '..............................................................L##R...........................................................................................................G...#.............................................................G...r......lG...G...r..............l....r..................................................................................................................................',
    '..............................................................L##R...........................................................................................................G...#G............................................................G...$......lG...G...r..............l....r..............GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG',
    '..............................................................L##R...........................................................................................................G...#........................................................................lG...G...r..............lG...r',
    '..............................................................L##R...........................................................................................................G...#.......................l###########.....................................lG...G...r..............l....r',
    '..............................................................L##R...........................................................................................................G...#G......................l############................S............#......lG...G...r..............l....r',
    '..............................................................L##R...........................................................................................................G...#...........#######.....l#############................S..................lG...G...r..............lG...r',
    '..............................................................L##R.......................................................G...G...G...G...G...G...G...G...G...G...G...G...G...G...#..........Sl#####r.....l##############..................................lG...G...r..............l....r',
    '..........................................MGGGGGGGG.......GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG......G...G...G...G...G...G...G...G...G...G...G...G...G...G...G...........l#####r.....l###############....mmmmmmmm.....................lG...G...r..............l....r',
    '..........................................$$$....................................................................................................................................#...r.......l#####r.....l#########################################################r..............lG...r.',
    '...............................lmr........$$$.....................---............................................................................................................#...r.......l#####r.....l#########################################################r..............l....r..',
    '...............................l#r........$$$....................................................................................................................................#...r......Sl#####r.....l#########################################################r..............l....r..',
    '...............................l#r........$$$...................M.......................................................#########ddddddddddddddddddddddddddddddddddddddddddddddddddddd.......l#####r.....l#########################################################r..............lG...r.',
    '...............................l#r......MM$$$..................LR........................................................G...G..#............................................................l#####r.....l#########################################################r..............l....r...',
    '...............................l#r......$$$.....................LR..............................................................#............................................................l#####r.....l#########################################################r..............l....r.',
    '...............................l#r......$$$......................LR---................---.......................................#............................................................l#####r.....l#########################################################r..............lG...r....',
    '...............................l#r......$$$......................LRG...G...G...G...G...G...G...G...G...G...G...G...G.G...G...G..#............................................................l#####r.....l#########################################################r..............l....r...' ,
    '...............................ldr......$$$.....................LR..............................................................#............................................................l#####r.....l#########################################################r..............l....r..',
    '......................###...............$$$...........$$$$$$$...LR........................................-..--.................#................................................#####.......l#####r.....l#########################################################r..............lG...r...',
    '......................###...............$$$U.........GGGGGGGGGGGGGGGGGGGGGGGG...#####GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG..G...G...#................................................l###r.......l#####r.....l#########################################################r..............l####r...',
    '.................---..###.............MM$$$$$$$$$$..............................#####.....................x.....................#.....................................####.......l###r.......l#####r.....l##########################################################mmmmmmmmmmmmmm######..',
    '.................$$$$$$$$.............$$$.......$$..............-.....-..-......#####...........................................#......................C..............l##r.......l###r.......l#####r.....l##############################################################################.',
    '.........N.......$$$$$..........M...............................................ddddd...........................................#.....................................l##r.......l###r.......l#####r.....l##############################################################################',
    '...............................L#R..........................................................dddddd................................................###.U...#####,,,,,,,l##r.......l###r.......l#####r.....l#########################################################################################################################################################################..',
    '#############....#########MMMMM###MMMM$$$.......$$..................................................................S.............................l###...#####r.......l##r.......l###r.......l#####r.....l#########################################################################################################################################################################...........',
    '#############MMMM#########......................$$................................................................................................l###########r.......l##r.......l###r.......#######.....l#########################################################################################################################################################################..................................................',
    '##########################........................................................................................................................l############mmmmmmm####mmmmmmm#####mmmmmmm#######mmmmm##########################################################################################################################################################################.........................................',
    '##########################.........................U..............................S..................S............................................l################################################################################################################################################################################################################################',
    '................................................GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG...#G...G...G...G...G...G...G...G...G...G.#######################################################################################################################################################################################################################',
    'W..............................WW....................................................................................#',
    '..............................W......................................................................................#',
    'W..............................WW....................................................................................#',

]
if __name__ == "__main__": main()
