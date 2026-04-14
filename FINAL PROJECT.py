import pygame
import math
#for now, z is jump, x is run, and shift is dash
#and for joystick, A/B is jump, X/Y is run, and shoulder buttons are dash

pygame.joystick.init()

# Keep track of controllers
joysticks = []
# Constants
WIDTH, HEIGHT = 800, 600
SCALE = 3
TILE_SIZE = 16 * SCALE
GRAVITY = 0.8
WALK_SPEED = 4
RUN_SPEED = 8  
JUMP_FORCE = -16
RUN_JUMP_FORCE = -18
DASH_SPEED = 18
DASH_TIME = 10
DASH_COOLDOWN = 20


class Player:
    def __init__(self):

        self.sprite_sheet = pygame.image.load('kris_sheet.png').convert_alpha()
        
      
        self.idle_frame = get_image(self.sprite_sheet, 0, 16, 16, SCALE)
        
        self.image = self.idle_frame
        self.rect = self.image.get_rect(topleft=(100, 300))
        
        # State tracking
        self.facing_right = True 
        self.frame_index = 0
        self.animation_speed = 0.15 
        
         
        self.vel_x = 0
        self.vel_y = 0
        self.is_jumping = False
        self.is_dashing = False
        self.dash_timer = 0
        self.dash_cooldown = 0
        self.dash_direction = (0, 0)
        
        # Physics Constants
        self.ACCEL = 0.6     
        self.FRICTION = 0.9  
        self.MAX_WALK = 6     
        self.MAX_RUN = 10     

    def update(self, tiles):
        keys = pygame.key.get_pressed()
        controller_x = 0
        controller_y = 0
        is_running = keys[pygame.K_x]
        jump_held = keys[pygame.K_z]
        dash_button = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]

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

        # --- SINGLE SHORT HOP LOGIC ---
        if self.vel_y < 0 and not jump_held:
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

        if dash_button and not self.is_dashing and self.dash_cooldown == 0:
            self.is_dashing = True
            self.dash_timer = DASH_TIME
            if input_x == 0 and input_y == 0:
                self.dash_direction = (1 if self.facing_right else -1, 0)
            else:
                input_length = math.hypot(input_x, input_y)
                self.dash_direction = (input_x / input_length, input_y / input_length)
            self.vel_x = self.dash_direction[0] * DASH_SPEED
            self.vel_y = self.dash_direction[1] * DASH_SPEED
            if self.dash_direction[0] != 0:
                self.facing_right = self.dash_direction[0] > 0

        if self.is_dashing:
            self.dash_timer -= 1
            self.vel_x = self.dash_direction[0] * DASH_SPEED
            self.vel_y = self.dash_direction[1] * DASH_SPEED
            if self.dash_timer <= 0:
                self.is_dashing = False
                self.dash_cooldown = DASH_COOLDOWN

        if self.dash_cooldown > 0 and not self.is_dashing:
            self.dash_cooldown -= 1

        # --- HORIZONTAL MOVEMENT ---
        max_speed = self.MAX_RUN if is_running else self.MAX_WALK
        
        if not self.is_dashing:
            if input_x == -1:
                self.vel_x -= self.ACCEL
                self.facing_right = False
            elif input_x == 1:
                self.vel_x += self.ACCEL
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

        self.rect.x += self.vel_x
        for tile in tiles:
            if self.rect.colliderect(tile):
                if self.vel_x > 0: # Moving right
                    self.rect.right = tile.left
                elif self.vel_x < 0: # Moving left
                    self.rect.left = tile.right

        if not self.is_dashing:
            self.vel_y += GRAVITY
        self.rect.y += self.vel_y
        
        for tile in tiles:
            if self.rect.colliderect(tile):
                if self.vel_y > 0: 
                    self.rect.bottom = tile.top
                    self.vel_y = 0
                    self.is_jumping = False
                elif self.vel_y < 0: 
                    self.rect.top = tile.bottom
                    self.vel_y = 0

        if self.facing_right:
           
            self.image = self.idle_frame
        else:
        
            self.image = pygame.transform.flip(self.idle_frame, True, False)
    def jump(self, is_running=False):
        if not self.is_jumping:
            force = RUN_JUMP_FORCE if is_running else JUMP_FORCE
            self.vel_y = force
            self.is_jumping = True

class Shadow:
    def __init__(self, start_pos=(0, 0)):
        self.start_pos = start_pos
        try:
            self.sprite_sheet = pygame.image.load('Dark_Kris_Sheet.png').convert_alpha()
            self.idle_frame = get_image(self.sprite_sheet, 0, 36, 36, SCALE)
        except pygame.error:
            self.idle_frame = pygame.Surface((36 * SCALE, 36 * SCALE), pygame.SRCALPHA)
            self.idle_frame.fill((20, 20, 20, 180))

        self.image = self.idle_frame
        self.rect = self.image.get_rect(topleft=start_pos)
        self.vel_x = 0
        self.vel_y = 0
        self.ACCEL = 0.3
        self.MAX_SPEED = 5
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

    def check_player(self, player):
        return self.rect.colliderect(player.rect)

    def reset(self, player):
        self.rect.topleft = (player.rect.x - 250, player.rect.y)
        self.vel_x = 0
        self.vel_y = 0

class Camera:
    def __init__(self, width, height):
        self.offset_x = 0
        self.width = width
        self.height = height

    def apply(self, entity_rect):
     
        return entity_rect.move(-self.offset_x, 0)

    def update(self, target_rect):
    
        self.offset_x = target_rect.centerx - int(WIDTH / 2)
        
        self.offset_x = max(0, self.offset_x)

class Tile(pygame.sprite.Sprite):
    def __init__(self, pos, size):
        super().__init__()
        self.image = pygame.Surface((size, size))
        self.image.fill((139, 69, 19)) 
        self.rect = self.image.get_rect(topleft=pos)
def setup_level(layout):
    tiles_list = []
    for row_index, row in enumerate(layout):
        for col_index, cell in enumerate(row):
            if cell == '#':
                x = col_index * TILE_SIZE
                y = row_index * TILE_SIZE
            
                new_tile = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
                tiles_list.append(new_tile)
            if cell == '$':
                x = col_index * TILE_SIZE
                y = row_index * TILE_SIZE
                
                new_tile = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE*3)
                tiles_list.append(new_tile)
            if cell == '-':
                x = col_index * TILE_SIZE
                y = row_index * TILE_SIZE
                
                new_tile = pygame.Rect(x, y, TILE_SIZE*3, TILE_SIZE)
                tiles_list.append(new_tile)
    return tiles_list 
def get_image(sheet, frame, width, height, scale):
    image = pygame.Surface((width, height), pygame.SRCALPHA).convert_alpha()
    image.blit(sheet, (0, 0), ((frame * width), 0, width, height))
    image = pygame.transform.scale(image, (width * scale, height * scale))
    return image


def main():
    pygame.init()
    pygame.joystick.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    camera = Camera(WIDTH, HEIGHT)
    Kris = Player()
    shadow = Shadow((Kris.rect.x - 250, Kris.rect.y))

    # Scan for any controllers already plugged in
    for i in range(pygame.joystick.get_count()):
        joy = pygame.joystick.Joystick(i)
        joy.init()
        joysticks.append(joy)

    tiles = setup_level(LEVEL_MAP)
    fading = False
    fade_alpha = 0
    fade_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    while True:
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return

            
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
            # --- JUMP LOGIC (Initial Press) ---
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



        Kris.update(tiles)
        shadow.update(Kris)
        camera.update(Kris.rect)
        
        # If the shadow catches the player, start the fade restart.
        if shadow.check_player(Kris) and not fading:
            fading = True

        # Check for out of bounds (falling off screen)
        if Kris.rect.y > HEIGHT + 100 and not fading:
            fading = True
        
        screen.fill((107, 140, 255)) 
        draw_image = Kris.image
        
        screen.blit(shadow.image, camera.apply(shadow.rect))
        screen.blit(draw_image, camera.apply(Kris.rect))
        for tile in tiles:
            pygame.draw.rect(screen, (139, 69, 19), camera.apply(tile))
        
        #fade to black and restart
        if fading:
            fade_alpha += 5  # Fade speed
            if fade_alpha >= 255:
                # Restart
                Kris.__init__()
                shadow.reset(Kris)
                camera.__init__(WIDTH, HEIGHT)
                fade_alpha = 0
                fading = False
            else:
                fade_surface.fill((0, 0, 0, fade_alpha))
                screen.blit(fade_surface, (0, 0))
        
        pygame.display.flip()
        clock.tick(60)
LEVEL_MAP = [
    '.......................................',
    '##......................................',
    '........................................',
    '........-.............................',
    '......................###...............',
    '.............-........................',
    '.................---...............................',
    '.............--..............................$$',
    '.........................................',
    '........................................',
    '#######.....##################$$....$...$$...$$$$$$$$$$$$$$$$$$$$$$$$####################',
    '#######.....###################.............................................',
    '#######.....###################..##................................',
    '###################################................................',

]
if __name__ == "__main__": main()
