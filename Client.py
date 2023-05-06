import asyncio
import pygame
import json
import random
import hashlib
import math
import struct
from functools import lru_cache

# Define some colors
BLACK = (0, 0, 0)
LIGHT_GREY = (200, 200, 200)
GREY = (125, 125, 125)
DARK_GREY = (75, 75, 75)
WHITE = (255, 255, 255)
DARK_BLUE = (0, 0, 100)
STAR_COLORS = [(128, 0, 0), (255, 220, 97), (255, 255, 221), (255, 157, 82), (255, 50, 80), (176, 196, 222), (255, 170, 50), (251, 176, 59)]
PLANET_COLORS = [(20, 160, 180), (219, 219, 159), (65, 74, 76), (108, 122, 137), (238, 169, 73), (123, 36, 28), (65, 131, 215), (40, 55, 71)]
MOON_COLORS = [(180, 180, 200), (125, 125, 140), (95, 95, 105)]
LASER = (130, 180, 255)
TRANSPARENT = (0, 0, 0, 0)

THE_GOLDEN_PALETTE = [(255, 238, 153), (237, 197, 49), (164, 126, 27)]
THE_GOLDEN_NUMBER = 7777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777777

# Set up the display window
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
CELL_SIZE = 40
STAR_FREQUENCY = 110000000000000
SPEED = 10

# Set the title of the window
pygame.display.set_caption("Legend of the Golden Star")

# Set up the camera position
camera_x = 0
camera_y = 0

# Store previously calculated star values
MAX_MEMORY = 4000
star_values = {}
star_group = pygame.sprite.Group()
#bullet_group = pygame.sprite.Group()
bullet_groups = {}

star_objects = {}

# Set selected star position
selected_x = None
selected_y = None

# Set ship variables
SHIP_ROTATION_SPEED = 6 *2
SHIP_THRUST = 0.1 *2
SHIP_LENGTH = 14

# Set bullet variables
BULLET_WIDTH = 5
BULLET_HEIGHT = 5
BULLET_SPEED = 5 *2
BULLET_EXPIRE = 50 //2

# Choose a font and font size
pygame.font.init()
font = pygame.font.Font("fonts\LoSumires-2X8l.ttf", 28)

# Set up the clock for the game loop
clock = pygame.time.Clock()

# Define a class for the stars
class Star(pygame.sprite.Sprite):
    def __init__(self, x, y, star_val):
        super().__init__()
        size = get_star_size(star_val)
        shade = STAR_COLORS[int((721*star_val) % 8)]
        half_size = size // 2
        self.image = pygame.Surface([size, size]).convert_alpha()
        self.image.fill((0, 0, 0, 0))
        pygame.draw.circle(self.image, shade, (half_size, half_size), half_size)
        self.rect = self.image.get_rect()
        self.rect.centerx = x + (CELL_SIZE // 2)
        self.rect.centery = y + (CELL_SIZE // 2)
        self.radius = half_size

# Define a class for the Golden Star
class Golden_Star(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        size = 40
        THE_GOLDEN_PALETTE
        self.image = pygame.Surface([size, size]).convert_alpha()
        self.image.fill(BLACK)
        self.image.set_colorkey(BLACK)
        points = []
        # get all points
        for i in range(6):
            angle_deg = 60 * i + 90
            ax = (size/2) * math.cos(math.radians(angle_deg)) + (size/2)
            ay = 20 * math.sin(math.radians(angle_deg)) + (size/2) - 0.6
            points.append((ax, ay))
            angle_deg = 60 * i + 120
            ax = ((size/2)*0.7) * math.cos(math.radians(angle_deg)) + (size/2)
            ay = ((size/2)*0.7) * math.sin(math.radians(angle_deg)) + (size/2) - 0.6
            points.append((ax, ay))
        # draw main shape
        pygame.draw.polygon(self.image, THE_GOLDEN_PALETTE[1], points)

        # draw highlights
        highlight_points = [points[4], points[5], points[6], ((size/2), (size/2))]
        pygame.draw.polygon(self.image, THE_GOLDEN_PALETTE[0], highlight_points)
        highlight_points = [points[2], points[3], ((size/2), (size/2))]
        pygame.draw.polygon(self.image, THE_GOLDEN_PALETTE[0], highlight_points)
        highlight_points = [points[7], points[8], ((size/2), (size/2))]
        pygame.draw.polygon(self.image, THE_GOLDEN_PALETTE[0], highlight_points)

        # draw shadows
        shadow_points = [points[10], points[11], points[0], ((size/2), (size/2))]
        pygame.draw.polygon(self.image, THE_GOLDEN_PALETTE[2], shadow_points)
        shadow_points = [points[8], points[9], ((size/2), (size/2))]
        pygame.draw.polygon(self.image, THE_GOLDEN_PALETTE[2], shadow_points)
        shadow_points = [points[1], points[2], ((size/2), (size/2))]
        pygame.draw.polygon(self.image, THE_GOLDEN_PALETTE[2], shadow_points)

        self.rect = self.image.get_rect()
        self.rect.x = x + (CELL_SIZE // 2) - (size // 2)
        self.rect.y = y + (CELL_SIZE // 2) - (size // 2)

# Define a class for a ship
class Ship(pygame.sprite.Sprite):
    def __init__(self, ship_length, screen_width, screen_height):
        super().__init__()
        self.ship_length = ship_length
        self.screen_width = screen_width
        self.screen_height = screen_height

        # create a surface for the ship
        self.image = pygame.Surface((self.ship_length*2, self.ship_length*2), pygame.SRCALPHA).convert_alpha()
        self.rect = self.image.get_rect(center=(self.screen_width//2, self.screen_height//2))

        # draw the ship on the surface
        ship_surface = pygame.Surface((self.ship_length, self.ship_length), pygame.SRCALPHA).convert_alpha()
        offset = 1
        ship_points = ((self.ship_length/2, 0), (0, self.ship_length), (self.ship_length/2, self.ship_length/2), (self.ship_length, self.ship_length))
        pygame.draw.polygon(ship_surface, WHITE, ship_points, 1)
        ship_points = ((self.ship_length//2, offset), (offset, self.ship_length - offset), (self.ship_length//2, self.ship_length//2), (self.ship_length - offset, self.ship_length - offset))
        pygame.draw.polygon(ship_surface, WHITE, ship_points, 1)
        self.radius = self.ship_length / 2

        # blit the ship surface onto the image surface
        self.image.blit(ship_surface, (self.ship_length//2, self.ship_length//2))

    def update(self, ship_angle):
        # rotate the ship image and update the rect
        rotated_surface = pygame.transform.rotate(self.image, -ship_angle)
        self.rect = rotated_surface.get_rect(center=self.rect.center)
        screen.blit(rotated_surface, self.rect)

# Define a class for a ship
class Enemy_Ship(pygame.sprite.Sprite):
    def __init__(self, ship_length, x, y):
        super().__init__()
        self.ship_length = ship_length
        self.x = x
        self.y = y

        # create a surface for the ship
        self.image = pygame.Surface((self.ship_length*2, self.ship_length*2), pygame.SRCALPHA).convert_alpha()
        self.rect = self.image.get_rect(center=(self.x, self.y))

        # draw the ship on the surface
        ship_surface = pygame.Surface((self.ship_length, self.ship_length), pygame.SRCALPHA).convert_alpha()
        offset = 1
        ship_points = ((self.ship_length/2, 0), (0, self.ship_length), (self.ship_length/2, self.ship_length/2), (self.ship_length, self.ship_length))
        pygame.draw.polygon(ship_surface, WHITE, ship_points, 1)
        ship_points = ((self.ship_length//2, offset), (offset, self.ship_length - offset), (self.ship_length//2, self.ship_length//2), (self.ship_length - offset, self.ship_length - offset))
        pygame.draw.polygon(ship_surface, WHITE, ship_points, 1)
        self.radius = self.ship_length / 2

        # blit the ship surface onto the image surface
        self.image.blit(ship_surface, (self.ship_length//2, self.ship_length//2))

    def update(self, ship_angle):
        # rotate the ship image and update the rect
        rotated_surface = pygame.transform.rotate(self.image, -ship_angle)
        self.rect = rotated_surface.get_rect(center=self.rect.center)
        screen.blit(rotated_surface, self.rect)

# Define a class for a bullet
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, ship_angle, ship_velocity):
        super().__init__()
        self.image = pygame.Surface((BULLET_WIDTH, BULLET_HEIGHT)).convert_alpha()
        self.image.fill(WHITE)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.radius = BULLET_WIDTH / 2
        self.angle = ship_angle - 90
        self.timer = BULLET_EXPIRE
        self.velocity = [BULLET_SPEED * math.cos(math.radians(self.angle)) + ship_velocity[0],
                         BULLET_SPEED * math.sin(math.radians(self.angle)) + ship_velocity[1]]

    def update(self, move_x, move_y):
        self.timer -= 1
        self.rect.x += self.velocity[0] - move_x
        self.rect.y += self.velocity[1] - move_y
        if self.timer <= 0:
            self.kill()
        if self.rect.x < -BULLET_WIDTH or self.rect.x > SCREEN_WIDTH or \
                self.rect.y < -BULLET_HEIGHT or self.rect.y > SCREEN_HEIGHT:
            self.kill()

# Draw lightning between bullets
def draw_lightning(bullet_group):
    if len(bullet_group) > 1:
        for j in range(len(bullet_group)-1):
            start = bullet_group.sprites()[j].rect.center
            end = bullet_group.sprites()[j+1].rect.center
            pygame.draw.line(screen, LASER, start, end, 2)


# Star size equation
def get_star_size(star_val_section):
    size = (star_val_section % 947)*(CELL_SIZE/947) + 2
    return size

# Get all the cell coordinates on screen
# Cache up to 600 entries
@lru_cache(maxsize=600)
def get_all_cell_coords(camera_x, camera_y):
    cell_coords = []
    left_border = -(camera_x % CELL_SIZE)
    top_border = -(camera_y % CELL_SIZE)
    
    # iterate over all pixels outside the screen with a step length of cell_size
    for x in range(left_border - CELL_SIZE, SCREEN_WIDTH + CELL_SIZE, CELL_SIZE):
        for y in range(top_border - CELL_SIZE, SCREEN_HEIGHT + CELL_SIZE, CELL_SIZE):
            cell_x, cell_y = pixel_to_cell(x, y, camera_x, camera_y)
            cell_coords.append((cell_x, cell_y))
    
    return cell_coords

# Cache up to 1000 entries
@lru_cache(maxsize=1000)
def calculate_star_value(cell_x, cell_y):
    return two_seeded_random(cell_x, cell_y)

# Draws all the stars in the cells
def draw_all_cells(camera_x, camera_y, cell_coords):
    existing_coords = set(star_objects.keys()) # Set of cell coordinates with existing star objects
    new_coords = set(cell_coords) - existing_coords # Set of cell coordinates with new star objects
    deleted_coords = existing_coords - set(cell_coords) # Set of cell coordinates with deleted star objects
    
    # Update positions of existing star objects
    for cell_x, cell_y in cell_coords:
        if (cell_x, cell_y) in star_objects:
            star = star_objects[(cell_x, cell_y)]
            star.rect.centerx, star.rect.centery = cell_to_pixel(cell_x, cell_y, camera_x - CELL_SIZE//2, camera_y - CELL_SIZE//2)
    
    # Add new star objects
    for cell_x, cell_y in new_coords:
        if (cell_x, cell_y) not in star_values:
            full_star_val = calculate_star_value(cell_x, cell_y)
            star_val = int(str(full_star_val)[:15])
            star_values[(cell_x, cell_y)] = star_val
            if len(star_values) > MAX_MEMORY:
                oldest_key = next(iter(star_values))
                del star_values[oldest_key]
        else:
            star_val = star_values[(cell_x, cell_y)]
            full_star_val = star_val
        if star_val < STAR_FREQUENCY:
            pixel_x, pixel_y = cell_to_pixel(cell_x, cell_y, camera_x, camera_y)
            star = Star(pixel_x, pixel_y, star_val)
            star_group.add(star)
            star_objects[(cell_x, cell_y)] = star
        elif star_val == 777777777777777:
            if full_star_val == THE_GOLDEN_NUMBER:
                star_values[(cell_x, cell_y)] = full_star_val
                pixel_x, pixel_y = cell_to_pixel(cell_x, cell_y, camera_x, camera_y)
                star = Golden_Star(pixel_x, pixel_y)
                screen.blit(star.image, star.rect)
    
    # Delete deleted star objects
    for cell_x, cell_y in deleted_coords:
        star = star_objects[(cell_x, cell_y)]
        star_group.remove(star)
        del star_objects[(cell_x, cell_y)]
    
    # Draw all the stars on the screen
    star_group.draw(screen)
    
    return star_group

# Convert pixel coordinates to cell coordinates
def pixel_to_cell(x, y, camera_x, camera_y):
    cell_x = ( (x + camera_x) - (SCREEN_WIDTH // 2) ) // CELL_SIZE
    cell_y = ( -(y + camera_y) + (SCREEN_HEIGHT // 2) ) // CELL_SIZE
    return (cell_x, cell_y)

# Convert cell coordinates to pixel coordinates
def cell_to_pixel(cell_x, cell_y, camera_x, camera_y):
    x = (cell_x * CELL_SIZE) + (SCREEN_WIDTH // 2) - camera_x
    y = -((cell_y * CELL_SIZE) - (SCREEN_HEIGHT // 2) + camera_y)
    return (x, y)

# A one seeded random function
def one_seeded_random(x):
    # generate a unique seed
    x = f'{x}'.encode('utf-8')
    hashval = hashlib.sha256(x).hexdigest()
    seed = int(hashval, 16) / 2**256
    random.seed(seed)
    return random.random()

# The SHAKE function
# Cache up to 100 entries
@lru_cache(maxsize=100)
def SHAKE(input):
    shake256 = hashlib.shake_256()
    byte_length = (input.bit_length() + 8) // 8  # number of bytes needed to represent x
    input_bytes = input.to_bytes(byte_length, byteorder='big', signed=True)
    shake256.update(input_bytes)
    digest = shake256.digest(8)
    seed = int.from_bytes(digest, byteorder='big', signed=True)
    return seed

# A two seeded random function
# Cache up to 100 entries
@lru_cache(maxsize=100)
def two_seeded_random(x, y):
    seed = struct.pack('qqqq', SHAKE(x), SHAKE(y), 0, 0)
    digest = hashlib.sha512(seed).digest()
    int_value = int.from_bytes(digest, byteorder='big')
    return int_value

# Move the ship
def move_ship(velocity, move_x, move_y):
    # Update the camera position based on the ship's velocity
    move_x += velocity[0]
    move_y += velocity[1]
    return move_x, move_y

# Calculate velocity resulting from acceleration
def apply_acceleration(ship_angle,ship_thrust, velocity_vector):
    sin = (math.sin(math.radians(ship_angle)))
    cos = (-math.cos(math.radians(ship_angle)))
    dec_ship_thrust = (ship_thrust)
    acceleration_vector = ((sin * dec_ship_thrust), (cos * dec_ship_thrust))
    velocity_vector[0] += acceleration_vector[0]
    velocity_vector[1] += acceleration_vector[1]
    return velocity_vector

# WARP prompt
def get_WARP():
    box = pygame.Rect(SCREEN_WIDTH//2 - 110, 300, 210, 120)
    pygame.draw.rect(screen, WHITE, box)
    box = pygame.Rect(SCREEN_WIDTH//2 - 80, 310, 150, 32)
    pygame.draw.rect(screen, LIGHT_GREY, box)

    text = font.render(f'Enter your WARP destination:', True, WHITE)
    screen.blit(text, (SCREEN_WIDTH//2 - 150, 250))


    x = get_user_input_x()
    y = get_user_input_y()
    return int(x), int(y)

# X WARP input
def get_user_input_x():
    input_box1 = pygame.Rect(SCREEN_WIDTH//2 - 80, 310, 150, 32)
    input1 = ''
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return input1
                elif event.key == pygame.K_BACKSPACE:
                    input1 = input1[:-1]
                else:
                    input1 += event.unicode

        # Draw the input box and text surface
        text1 = font.render(input1, True, DARK_GREY)
        pygame.draw.rect(screen, LIGHT_GREY, input_box1)
        screen.blit(text1, (input_box1.x + 5, input_box1.y + 5))

        pygame.display.update()
        clock.tick(30)

# Y WARP input
def get_user_input_y():
    input_box1 = pygame.Rect(SCREEN_WIDTH//2 - 80, 360, 150, 32)
    input1 = ''
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return input1
                elif event.key == pygame.K_BACKSPACE:
                    input1 = input1[:-1]
                else:
                    input1 += event.unicode

        # Draw the input box and text surface
        text1 = font.render(input1, True, DARK_GREY)
        pygame.draw.rect(screen, LIGHT_GREY, input_box1)
        screen.blit(text1, (input_box1.x + 5, input_box1.y + 5))

        pygame.display.update()
        clock.tick(30)

# Mouse hover icon
def star_hover(cell_pos, camera_x, camera_y):
    # check if there is a star
    full_star_val = two_seeded_random(cell_pos[0], cell_pos[1])
    star_val = int(str(full_star_val)[:15])
    if star_val < STAR_FREQUENCY:
        x, y = cell_to_pixel(cell_pos[0], cell_pos[1], camera_x, camera_y)

        # draw the highlight
        highlighter = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(screen, WHITE, highlighter, width=1, border_radius=4)

        # erase sections of the highlight
        pygame.draw.line(screen, TRANSPARENT, (x + 9, y), (x + CELL_SIZE - 10, y))
        pygame.draw.line(screen, TRANSPARENT, (x + 9, y + CELL_SIZE - 1), (x + CELL_SIZE - 10, y + CELL_SIZE - 1))
        pygame.draw.line(screen, TRANSPARENT, (x, y + 9), (x, y + CELL_SIZE - 10))
        pygame.draw.line(screen, TRANSPARENT, (x + CELL_SIZE - 1, y + 9), (x + CELL_SIZE - 1, y + CELL_SIZE - 10))

# Star system viewer
def star_system_display(x, y, star_val):
    # draw the menu background, set the clipping space to inside the blue
    blue_rect = pygame.Rect(5, SCREEN_HEIGHT//2 + 2, SCREEN_WIDTH - 10, SCREEN_HEIGHT//2 - 7)
    border_rect = pygame.Rect(3, SCREEN_HEIGHT//2, SCREEN_WIDTH - 6, SCREEN_HEIGHT//2 - 3)
    pygame.draw.rect(screen, GREY, border_rect)
    pygame.draw.rect(screen, DARK_BLUE, blue_rect)
    screen.set_clip(blue_rect)

    # more random values
    re_star_val = one_seeded_random(star_val)
    rand_x = one_seeded_random(x)
    rand_y = one_seeded_random(y)

    # draw the star
    star_size = get_star_size(star_val)
    star_shade = STAR_COLORS[int((721*star_val) % 8)]
    pygame.draw.circle(screen, star_shade, (60 - star_size, (3*SCREEN_HEIGHT)//4), star_size * 8)

    # get planet count
    planet_count = round( (re_star_val**4) * 8 + 0.48 )

    # draw the planets
    total_planet_distance = (60 - star_size) + (star_size * 8) + 100
    for i in range(planet_count):
        # get planet val
        planet_seed = i + re_star_val + rand_x + rand_y
        planet_val = one_seeded_random(planet_seed)

        # draw the planet
        planet_size = (planet_val % 0.01)*4000 + 2
        planet_shade = PLANET_COLORS[int((947*planet_val) % 8)]
        pygame.draw.circle(screen, planet_shade, (total_planet_distance + 20 + (planet_size), (3*SCREEN_HEIGHT)//4), planet_size)

        # get moon count
        moon_count = round( ((planet_size / 12) * (planet_val + 0.5)) * planet_val )

        # draw the moons
        total_moon_distance = (planet_size) + 20 + (3*SCREEN_HEIGHT)//4
        for i in range(moon_count):
            # get moon val
            moon_seed = i + planet_val + rand_x + rand_y
            moon_val = one_seeded_random(moon_seed)
            #one_seeded_random(one_seeded_random((one_seeded_random(two_seeded_random(x, y)) + one_seeded_random(x) + one_seeded_random(y))) + one_seeded_random(x) + one_seeded_random(y))

            # draw the moon
            moon_size = (moon_val % 0.01)*1000 + 2
            moon_shade = MOON_COLORS[int((1669*moon_val) % 3)]
            pygame.draw.circle(screen, moon_shade, (total_planet_distance + 20 + (planet_size), total_moon_distance + 10 + moon_size), moon_size)

            # add to total moon distance
            total_moon_distance += 10 + (moon_size * 2)

        # add to total planet distance
        total_planet_distance += 20 + (planet_size * 2)

    # clear the clipping area
    screen.set_clip(None)

    # Add text
    text = font.render(f"X:", True, WHITE)
    screen.blit(text, (2, SCREEN_HEIGHT//2 - 66))
    text = font.render(f"{x}", True, WHITE)
    screen.blit(text, (35, SCREEN_HEIGHT//2 - 66))
    text = font.render(f"Y:", True, WHITE)
    screen.blit(text, (2, SCREEN_HEIGHT//2 - 44))
    text = font.render(f"{y - 1}", True, WHITE)
    screen.blit(text, (35, SCREEN_HEIGHT//2 - 44))
    text = font.render(f"Planets at this star: {planet_count}", True, WHITE)
    screen.blit(text, (2, SCREEN_HEIGHT//2 - 22))

# Camera movement in the Man loop
def Man_camera(keys, ship_thrust, ship_angle, camera_x, camera_y):
    if keys[pygame.K_UP]:
        ship_thrust = SHIP_THRUST
    if keys[pygame.K_LEFT]:
        ship_angle -= SHIP_ROTATION_SPEED
    if keys[pygame.K_RIGHT]:
        ship_angle += SHIP_ROTATION_SPEED
    if keys[pygame.K_w]:
        camera_x, camera_y = get_WARP()
        camera_x *= CELL_SIZE
        camera_y *= -CELL_SIZE
    
    return ship_thrust, ship_angle, camera_x, camera_y




enemies = {}

# Send info to the server
async def send_position(position, writer):
    # send position as a string with format "<x>,<y>"
    message = f"{position[0]},{position[1]},{position[2]}"
    writer.write(message.encode())
    await writer.drain()
    
# Get info from the server
async def receive_positions(position, screen, reader):
    global enemies
    # receive positions of all clients as a JSON string
    response = await reader.read(1024)
    positions_str = response.decode().strip()
    enemies = json.loads(positions_str)

# Main loop
async def main():
    pygame.init()
    reader, writer = await asyncio.open_connection('127.0.0.1', 8888)
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    screen.fill(BLACK)
    pygame.display.set_caption("Legend of the Golden Star")
    clock = pygame.time.Clock()

    ship = Ship(SHIP_LENGTH, SCREEN_WIDTH, SCREEN_HEIGHT)
    ship_angle = 0
    velocity_vector = [0, 0]
    move_x = 0
    move_y = 0

    ship_rect = ship.rect
    collision_range = pygame.Rect(ship_rect.x - SHIP_LENGTH*2, ship_rect.y - SHIP_LENGTH*2, SHIP_LENGTH*4, SHIP_LENGTH*4)

    max_bullet_groups = 2
    bullet_groups = {}
    next_bullet_group = 0

    # Set up the camera position
    camera_x = 0
    camera_y = 0

    #bullet_group = pygame.sprite.Group()
    bullet_groups = {}

    while True:
        # Limit the frame rate
        clock.tick(30)

        ship_thrust = 0.0
        move_x = move_x - round(move_x)
        move_y = move_y - round(move_y)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                        # Create a new group for this shot
                        bullet_groups[next_bullet_group] = pygame.sprite.Group()
                        # Create the bullets and add them to the group
                        for i in range(3):
                            bullet = Bullet(SCREEN_WIDTH//2, SCREEN_HEIGHT//2, ship_angle - 10 + 10*i, velocity_vector)
                            bullet_groups[next_bullet_group].add(bullet)
                        next_bullet_group = (next_bullet_group + 1) % max_bullet_groups

        # Move the camera
        ship_thrust, ship_angle, camera_x, camera_y = Man_camera(pygame.key.get_pressed(), ship_thrust, ship_angle, camera_x, camera_y)

        # Calculate the new velocity
        velocity_vector = apply_acceleration(ship_angle, ship_thrust, velocity_vector)

        # Move the ship
        move_x, move_y = move_ship(velocity_vector, move_x, move_y)
        camera_x += round(move_x)
        camera_y += round(move_y)

        # Clear the screen
        screen.fill(BLACK)

        # Get cell coordinates and draw all outlines
        cell_coords = get_all_cell_coords(camera_x, camera_y)
        stars = draw_all_cells(camera_x, camera_y, cell_coords)

        # Draw the ship
        ship.update(ship_angle)

        for star in stars:
            if star.rect.colliderect(collision_range):
                if pygame.sprite.collide_circle(ship, star):
                    camera_x = camera_y = 0
                    move_x = move_y = 0
                    velocity_vector = [0, 0]
                    for i in range(len(bullet_groups)):
                        bullet_group = bullet_groups[i]
                        bullet_group.empty()
        
        for i in range(len(bullet_groups)):
            # Get the group for this shot
            bullet_group = bullet_groups[i]
            bullet_group.update(move_x, move_y)
            bullet_group.draw(screen)
            # Update and draw the bullets in this group
            for bullet in bullet_group:
                for star in stars:
                    if pygame.sprite.collide_circle(bullet, star):
                        bullet.kill()
            # Draw the lightning between bullets in this group
            draw_lightning(bullet_group)

        # create a text surface object with the cell position
        cell_pos = pixel_to_cell(SCREEN_WIDTH//2, SCREEN_HEIGHT//2, camera_x, camera_y)
        text = font.render("X:", True, WHITE)
        screen.blit(text, (2, 25))
        text = font.render(f"{cell_pos[0]}", True, WHITE)
        screen.blit(text, (27, 25))
        text = font.render("Y:", True, WHITE)
        screen.blit(text, (2, 47))
        text = font.render(f"{cell_pos[1]}", True, WHITE)
        screen.blit(text, (27, 47))
        text = font.render(f'Press "W" to WARP', True, WHITE)
        screen.blit(text, (2, 3))

        # extract positions from dictionary and update screen
        for player, pos in enemies.items():
            x, y, theta = pos
            x -= camera_x - SCREEN_WIDTH//2
            y -= camera_y - SCREEN_HEIGHT//2
            enemy_ship = Enemy_Ship(SHIP_LENGTH, x, y)
            enemy_ship.update(theta)

        pygame.display.update()

        tasks = [
            send_position((camera_x, camera_y, ship_angle), writer),
            receive_positions((camera_x, camera_y), screen, reader)
        ]
        await asyncio.gather(*tasks)

asyncio.run(main())
