import pygame


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

class Player:
    def __init__(self):
        # 1. Load the sheet
        self.sprite_sheet = pygame.image.load('kris_sheet.png').convert_alpha()
        
        # 2. Extract frames (assuming 16x16 pixels per frame)
        self.idle_frame = get_image(self.sprite_sheet, 0, 16, 16, SCALE)
        
        self.image = self.idle_frame
        self.rect = self.image.get_rect(topleft=(100, 300))
        
        # State tracking
        self.facing_right = True # Your image faces left, so False is default
        self.frame_index = 0
        self.animation_speed = 0.15 
        
        # Physics (keeping your existing variables)
        self.vel_x = 0
        self.vel_y = 0
        self.is_jumping = False
        
        # Physics Constants
        self.ACCEL = 0.6      # How fast he starts moving
        self.FRICTION = 0.9   # How fast he slows down (lower = more slippery)
        self.MAX_WALK = 6     # Top speed walking
        self.MAX_RUN = 10     # Top speed running

    def update(self, tiles):
        keys = pygame.key.get_pressed()
        controller_x = 0
        is_running = keys[pygame.K_x]
        jump_held = keys[pygame.K_z]

        for joy in joysticks:
            try:
                axis_x = joy.get_axis(0)
                if abs(axis_x) > 0.1:
                    controller_x = axis_x

                # Xbox: A=0, B=1 | Switch: B=0, A=1
                if joy.get_button(0) or joy.get_button(1):
                    jump_held = True
                # Xbox: X=2, Y=3 | Switch: Y=2, X=3
                if joy.get_button(2) or joy.get_button(3):
                    is_running = True
            except pygame.error:
                # The device was removed while we were polling it.
                continue

        # --- SINGLE SHORT HOP LOGIC ---
        if self.vel_y < 0 and not jump_held:
            self.vel_y *= 0.5 

        # --- HORIZONTAL MOVEMENT ---
        max_speed = self.MAX_RUN if is_running else self.MAX_WALK
        
        if keys[pygame.K_LEFT] or controller_x < -0.1:
            self.vel_x -= self.ACCEL
        elif keys[pygame.K_RIGHT] or controller_x > 0.1:
            self.vel_x += self.ACCEL
        else:
            # Apply Friction when no keys are pressed
            self.vel_x *= self.FRICTION
            if abs(self.vel_x) < 0.1: self.vel_x = 0

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

        # 2. Gravity & Vertical Movement
        self.vel_y += GRAVITY
        self.rect.y += self.vel_y
        
        # Ground Collision (Keep your current logic)
        for tile in tiles:
            if self.rect.colliderect(tile):
                if self.vel_y > 0: # Falling down
                    self.rect.bottom = tile.top
                    self.vel_y = 0
                    self.is_jumping = False
                elif self.vel_y < 0: # Jumping up (hitting head)
                    self.rect.top = tile.bottom
                    self.vel_y = 0

        if self.facing_right:
            # If moving right, use the original image
            self.image = self.idle_frame
        else:
            # If moving left, flip the original image
            self.image = pygame.transform.flip(self.idle_frame, True, False)
    def jump(self):
        if not self.is_jumping:
            self.vel_y = JUMP_FORCE
            self.is_jumping = True
class Camera:
    def __init__(self, width, height):
        self.offset_x = 0
        self.width = width
        self.height = height

    def apply(self, entity_rect):
        # Shift the entity's position by the camera offset for drawing
        return entity_rect.move(-self.offset_x, 0)

    def update(self, target_rect):
        # Keep Kris in the center (or left-center) of the screen
        # We subtract half the screen width to center him
        self.offset_x = target_rect.centerx - int(WIDTH / 2)
        
        # Stop the camera from scrolling off the left edge (0)
        self.offset_x = max(0, self.offset_x)

class Tile(pygame.sprite.Sprite):
    def __init__(self, pos, size):
        super().__init__()
        self.image = pygame.Surface((size, size))
        self.image.fill((139, 69, 19)) # Brown for dirt/bricks
        self.rect = self.image.get_rect(topleft=pos)
def setup_level(layout):
    tiles_list = [] = []
    for row_index, row in enumerate(layout):
        for col_index, cell in enumerate(row):
            if cell == '#':
                x = col_index * TILE_SIZE
                y = row_index * TILE_SIZE
                # Create a simple Rect for each block
                new_tile = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
                tiles_list.append(new_tile)
            if cell == '$':
                x = col_index * TILE_SIZE
                y = row_index * TILE_SIZE
                # Create a simple Rect for each block
                new_tile = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE*3)
                tiles_list.append(new_tile)
            if cell == '-':
                x = col_index * TILE_SIZE
                y = row_index * TILE_SIZE
                # Create a simple Rect for each block
                new_tile = pygame.Rect(x, y, TILE_SIZE*3, TILE_SIZE)
                tiles_list.append(new_tile)
    return tiles_list # <--- This is the crucial part!
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

    # Scan for any controllers already plugged in
    for i in range(pygame.joystick.get_count()):
        joy = pygame.joystick.Joystick(i)
        joy.init()
        joysticks.append(joy)

    # Create a long floor to test scrolling
    tiles = setup_level(LEVEL_MAP)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return

            # Handle Controller Connections
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
                if event.key == pygame.K_z: Kris.jump()
            
            if event.type == pygame.JOYBUTTONDOWN:
                # 0 is B, 1 is A on Switch controllers
                if event.button == 0 or event.button == 1: 
                    Kris.jump()



        Kris.update(tiles)
        camera.update(Kris.rect)
        screen.fill((107, 140, 255)) # Sky Blue
        draw_image = Kris.image
        
        # Draw Kris using the camera offset
        screen.blit(draw_image, camera.apply(Kris.rect))
        for tile in tiles:
            pygame.draw.rect(screen, (139, 69, 19), camera.apply(tile))
        
        pygame.display.flip()
        clock.tick(60)
LEVEL_MAP = [
    '.......................................',
    '##......................................',
    '........................................',
    '........-.............................',
    '......................###...............',
    '.............-........................',
    '..................................................',
    '.............--..............................$$',
    '.........................................',
    '........................................',
    '#######.....##################$$....$...$$...$$$$$$$$$$$$$$$$$$$$$$$$####################',
    '#######.....###################.............................................',
    '#######.....###################..##................................',
    '###################################................................',

]
if __name__ == "__main__": main()