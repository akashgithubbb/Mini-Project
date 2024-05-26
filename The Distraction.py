import pygame
from pygame.locals import *
from pygame import mixer
import pickle
from os import path

# Initialize Pygame and mixer
pygame.mixer.pre_init(44100, -16, 2, 512)
mixer.init()
pygame.init()

# Set up clock
clock = pygame.time.Clock()
fps = 60

# Get display resolution
info = pygame.display.Info()
screen_width = info.current_w
screen_height = info.current_h

# Set the game window size
aspect_ratio = 4 / 3
if screen_width / screen_height >= aspect_ratio:
    game_width = screen_height * aspect_ratio
    game_height = screen_height
else:
    game_width = screen_width
    game_height = screen_width / aspect_ratio

screen = pygame.display.set_mode((int(game_width), int(game_height)), pygame.FULLSCREEN)
pygame.display.set_caption('The Distraction')

# Define fonts and colors
game_font = pygame.font.SysFont('Bauhaus', 70)
blue = (0, 0, 255)

# Load images
bg_img = pygame.image.load('Brick Wall.jpg')
restart_img = pygame.image.load('restart_btn.png')
start_img = pygame.image.load('start_btn.png')
exit_img = pygame.image.load('exit_btn.png')



# Load sounds
pygame.mixer.music.load('music.wav')
pygame.mixer.music.play(-1, 0.0, 5000)
jump_fx = pygame.mixer.Sound('jump.wav')
jump_fx.set_volume(0.5)
game_over_fx = pygame.mixer.Sound('game_over.wav')
game_over_fx.set_volume(0.5)

# Game variables
tile_size = 50
game_over = 0
main_menu = True
level = 3
max_level = 3

# Define function to draw text
def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))

# Function to reset level
def reset_level(level):
    player.reset(100, screen_height - 130)
    insta_group.empty()
    platform_group.empty()
    football_group.empty()
    exit_group.empty()
    mobile_group.empty()

    # Load level data and create world
    if path.exists(f'level{level}_data'):
        with open(f'level{level}_data', 'rb') as pickle_in:
            world_data = pickle.load(pickle_in)
    world = World(world_data)
    return world

# Button class
class Button():
    def __init__(self, x, y, image):
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.clicked = False

    def draw(self):
        action = False
        pos = pygame.mouse.get_pos()

        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0] == 1 and not self.clicked:
                action = True
                self.clicked = True

        if pygame.mouse.get_pressed()[0] == 0:
            self.clicked = False

        screen.blit(self.image, self.rect)
        return action

# Player class
class Player():
    def __init__(self, x, y):
        self.reset(x, y)

    def update(self, game_over):
        dx = 0
        dy = 0
        walk_cooldown = 5
        col_thresh = 20

        if game_over == 0:
            key = pygame.key.get_pressed()
            if key[pygame.K_SPACE] and not self.jumped and not self.in_air:
                jump_fx.play()
                self.vel_y = -15
                self.jumped = True
            if not key[pygame.K_SPACE]:
                self.jumped = False
            if key[pygame.K_LEFT]:
                dx -= 5
                self.counter += 1
                self.direction = -1
            if key[pygame.K_RIGHT]:
                dx += 5
                self.counter += 1
                self.direction = 1
            if not (key[pygame.K_LEFT] or key[pygame.K_RIGHT]):
                self.counter = 0
                self.index = 0
                if self.direction == 1:
                    self.image = self.images_right[self.index]
                elif self.direction == -1:
                    self.image = self.images_left[self.index]

            if self.counter > walk_cooldown:
                self.counter = 0
                self.index += 1
                if self.index >= len(self.images_right):
                    self.index = 0
                if self.direction == 1:
                    self.image = self.images_right[self.index]
                elif self.direction == -1:
                    self.image = self.images_left[self.index]

            self.vel_y += 1
            if self.vel_y > 10:
                self.vel_y = 10
            dy += self.vel_y

            self.in_air = True
            for tile in world.tile_list:
                if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                    dx = 0
                if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                    if self.vel_y < 0:
                        dy = tile[1].bottom - self.rect.top
                        self.vel_y = 0
                    elif self.vel_y >= 0:
                        dy = tile[1].top - self.rect.bottom
                        self.vel_y = 0
                        self.in_air = False

            if pygame.sprite.spritecollide(self, insta_group, False) or \
               pygame.sprite.spritecollide(self, mobile_group, False) or \
               pygame.sprite.spritecollide(self, football_group, False):
                game_over = -1
                game_over_fx.play()

            if pygame.sprite.spritecollide(self, exit_group, False):
                game_over = 1

            for platform in platform_group:
                if platform.rect.colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                    dx = 0
                if platform.rect.colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                    if abs((self.rect.top + dy) - platform.rect.bottom) < col_thresh:
                        self.vel_y = 0
                        dy = platform.rect.bottom - self.rect.top
                    elif abs((self.rect.bottom + dy) - platform.rect.top) < col_thresh:
                        self.rect.bottom = platform.rect.top - 1
                        self.in_air = False
                        dy = 0
                    if platform.move_x != 0:
                        self.rect.x += platform.move_direction

            self.rect.x += dx
            self.rect.y += dy

        elif game_over == -1:
            self.image = self.distracted_image
            draw_text('DISTRACTED!', game_font, blue, (screen_width // 2) - 200, screen_height // 2)
            if self.rect.y > 200:
                self.rect.y -= 5

        screen.blit(self.image, self.rect)
        return game_over

    def reset(self, x, y):
        self.images_right = []
        self.images_left = []
        self.index = 0
        self.counter = 0
        for num in range(1, 5):
            img_right = pygame.image.load(f'guy{num}.png')
            img_right = pygame.transform.scale(img_right, (40, 80))
            img_left = pygame.transform.flip(img_right, True, False)
            self.images_right.append(img_right)
            self.images_left.append(img_left)
        self.distracted_image = pygame.image.load('ghost.png')
        self.image = self.images_right[self.index]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.vel_y = 0
        self.jumped = False
        self.direction = 0
        self.in_air = True

# World class
class World():
    def __init__(self, data):
        self.tile_list = []
        dirt_img = pygame.image.load('dirt.png')
        grass_img = pygame.image.load('grass.png')

        row_count = 0
        for row in data:
            col_count = 0
            for tile in row:
                if tile == 1:
                    img = pygame.transform.scale(dirt_img, (tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile = (img, img_rect)
                    self.tile_list.append(tile)
                if tile == 2:
                    img = pygame.transform.scale(grass_img, (tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile = (img, img_rect)
                    self.tile_list.append(tile)
                if tile == 3:
                    football = Football(col_count * tile_size, row_count * tile_size + 15)
                    football_group.add(football)
                if tile == 4:
                    platform = Platform(col_count * tile_size, row_count * tile_size, 1, 0)
                    platform_group.add(platform)
                if tile == 5:
                    platform = Platform(col_count * tile_size, row_count * tile_size, 0, 1)
                    platform_group.add(platform)
                if tile == 6:
                    insta = Insta(col_count * tile_size, row_count * tile_size + 9)
                    insta_group.add(insta)
                if tile == 7:
                    mobile = Mobile(col_count * tile_size, row_count * tile_size + 5)
                    mobile_group.add(mobile)
                if tile == 8:
                    exit = Exit(col_count * tile_size, row_count * tile_size - (tile_size // 2))
                    exit_group.add(exit)

                col_count += 1
            row_count += 1

    def draw(self):
        for tile in self.tile_list:
            screen.blit(tile[0], tile[1])

# Define enemy and object classes
class Insta(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.image.load('instagram enemy.png')
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.move_direction = 1
        self.move_counter = 0

    def update(self):
        self.rect.x += self.move_direction
        self.move_counter += 1
        if abs(self.move_counter) > 50:
            self.move_direction *= -1
            self.move_counter *= -1

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, move_x, move_y):
        super().__init__()
        img = pygame.image.load('platform.png')
        self.image = pygame.transform.scale(img, (tile_size, tile_size // 2))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.move_counter = 0
        self.move_direction = 1
        self.move_x = move_x
        self.move_y = move_y

    def update(self):
        self.rect.x += self.move_direction * self.move_x
        self.rect.y += self.move_direction * self.move_y
        self.move_counter += 1
        if abs(self.move_counter) > 50:
            self.move_direction *= -1
            self.move_counter *= -1

class Football(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.image.load('football1.png')
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.move_direction = 1
        self.move_counter = 0

    def update(self):
        self.rect.x += self.move_direction
        self.move_counter += 1
        if abs(self.move_counter) > 50:
            self.move_direction *= -1
            self.move_counter *= -1

class Mobile(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.image.load('Mobile.png')
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.move_direction = 1
        self.move_counter = 0

    def update(self):
        self.rect.x += self.move_direction
        self.move_counter += 1
        if abs(self.move_counter) > 50:
            self.move_direction *= -1
            self.move_counter *= -1

class Exit(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        img = pygame.image.load('exit.png')
        self.image = pygame.transform.scale(img, (tile_size, int(tile_size * 1.5)))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

# Initialize player and sprite groups
player = Player(100, screen_height - 130)
insta_group = pygame.sprite.Group()
platform_group = pygame.sprite.Group()
football_group = pygame.sprite.Group()
mobile_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()

# Load in level data and create world
if path.exists(f'level{level}_data'):
    with open(f'level{level}_data', 'rb') as pickle_in:
        world_data = pickle.load(pickle_in)
world = World(world_data)

# Create buttons
restart_button = Button(int(game_width // 2) - 50, int(game_height // 2) + 100, restart_img)
start_button = Button(int(game_width // 2) - 350, int(game_height // 2), start_img)
exit_button = Button(int(game_width // 2) + 100, int(game_height // 2), exit_img)

# Main game loop
run = True
while run:
    clock.tick(fps)
    screen.blit(bg_img, (0, 0))

    if main_menu:
        if exit_button.draw():
            run = False
        if start_button.draw():
            main_menu = False
    else:
        world.draw()
        if game_over == 0:
            insta_group.update()
            platform_group.update()
            football_group.update()
            mobile_group.update()

        insta_group.draw(screen)
        football_group.draw(screen)
        mobile_group.draw(screen)
        exit_group.draw(screen)
        platform_group.draw(screen)

        game_over = player.update(game_over)

        if game_over == -1:
            if restart_button.draw():
                world_data = []
                world = reset_level(level)
                game_over = 0

        if game_over == 1:
            level += 1
            if level <= max_level:
                world_data = []
                world = reset_level(level)
                game_over = 0
            else:
                draw_text('YOU WIN!', game_font, blue, (screen_width // 2) - 140, screen_height // 2)
                if restart_button.draw():
                    level = 1
                    world_data = []
                    world = reset_level(level)
                    game_over = 0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    pygame.display.update()

pygame.quit()
