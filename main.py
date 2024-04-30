import pygame
import random
import sys
from pygame.math import Vector2

# Basic setup
pygame.init()

# Font
title_font = pygame.font.Font(None, 60)  # None = default
score_font = pygame.font.Font(None, 40)

# Colors
BLUE = (170, 204, 249)
WHITE = (255, 255, 255)
DARKBLUE = (131, 171, 240)

cell_size = 30
number_of_cells = 25

OFFSET = 75


class Food:
    def __init__(self, snake_body):
        self.position = self.generate_random_pos(snake_body)

    def draw(self):
        # An invisible square to contains food
        food_rect = pygame.Rect(OFFSET + self.position.x * cell_size, OFFSET + self.position.y * cell_size,
                                cell_size, cell_size)  # x, y coordinate; width height

        # Draw food (using the loaded image)
        screen.blit(food_surface, food_rect)

    def generate_random_cell(self):
        x = random.randint(0, number_of_cells - 1)  # Make sure it won't out of range
        y = random.randint(0, number_of_cells - 1)
        return Vector2(x, y)

    def generate_random_pos(self, snake_body):
        position = self.generate_random_cell()  # x, y random coordinates of the food
        while position in snake_body:  # Ensure that the food doesn't generate on the snake's body
            position = self.generate_random_cell()
        return position


class Snake:
    def __init__(self):
        self.body = [Vector2(6, 9), Vector2(5, 9), Vector2(4, 9)]  # [Head, tail...]
        # To know which direction is moving
        self.direction = Vector2(1, 0)  # Moving right by default
        self.add_segment = False
        self.direction_changed = False
        self.eat_sound = pygame.mixer.Sound("Sounds/eat.mp3")
        self.wall_hit_sound = pygame.mixer.Sound("Sounds/wall.mp3")

    def draw(self, color):
        for segment in self.body:
            # Snake's position and size -> [x, y, width, height]
            # Adding OFFSET shifts the snake's position by 75 pixels (OFFSET) from the screen edge,
            # so the actual x, y coordinates become (75 + 6 * 30, 75 + 9 * 30).
            # This means the snake will start counting from the inside of the grid, not the edge of the screen.
            segment_rect = (OFFSET + segment.x * cell_size, OFFSET + segment.y * cell_size, cell_size, cell_size)
            pygame.draw.rect(screen, color, segment_rect, 0, 7)

    def update(self):
        # self.body[0] the current position of the snake's head
        # self.direction (Vector2(1, 0)) the direction in which the snake is moving to the right (moving one unit at a time)
        # Adding these two results in a new head position
        self.body.insert(0, self.body[0] + self.direction)
        # Insert to the head of the snake; self.body[0] + self.direction = Vector2(6, 9) + self.direction -> Adding element to the right side of current head
        # self.direction will be updated based on user's keyboard

        # 在蛇身體列表的開頭插入新的頭部位置。self.body[0] 是當前頭部的位置，self.direction 是蛇的移動方向
        # 通過將這兩個 Vector2 物件相加，計算出新的頭部位置。例如，如果 self.body[0] 是 Vector2(6, 9)
        # 且 self.direction 是 Vector2(1, 0)，新的頭部位置將是 Vector2(7, 9)，代表蛇向右移動了一格

        # Check if the snake has just eaten food and needs to grow. If it has just eaten, won't remove the tail
        if self.add_segment:
            self.add_segment = False
        else:
            self.body = self.body[:-1]  # Remove the last element (The tail of the snake)

    # Reset to the original body list and direction attributes when the game is over
    def reset(self):
        self.body = [Vector2(6, 9), Vector2(5, 9), Vector2(4, 9)]
        self.direction = Vector2(1, 0)


class Game:
    def __init__(self):
        self.snake = Snake()
        self.food = Food(self.snake.body)
        # Check if the game is over or running
        self.state = True
        self.score = 0
        self.second_snake_threshold = 5  # When will the second snake show up
        self.second_snake = None

    def draw(self):
        self.food.draw()
        self.snake.draw(WHITE)
        # Check if the second snake has been created. If it has, draw it on the screen.
        # Once created, the second snake is always drawn, no need to check the score.
        if self.second_snake:
            self.second_snake.draw(DARKBLUE)

    def update(self):
        # Update the game state if the game is not over
        if self.state:
            self.snake.update()
            self.check_collision_with_food(self.snake)
            self.check_collision_with_edges(self.snake)
            self.check_collision_with_tail(self.snake)
            self.snake.direction_changed = False
            self.create_second_snake()  # Attempt to create the second snake if conditions are met

            if self.second_snake:
                self.second_snake.update()
                self.check_collision_with_food(self.second_snake)
                self.check_collision_with_edges(self.second_snake)
                self.check_collision_with_tail(self.second_snake)
                self.check_collision_with_other_snake(self.snake, self.second_snake)
                self.snake.direction_changed = False

    def check_collision_with_food(self, snake):
        # Check if the snake’s head cell and the food cell are the same for every update of the game
        if snake.body[0] == self.food.position:
            self.food.position = self.food.generate_random_pos(self.snake.body)
            snake.add_segment = True
            self.score += 1
            self.snake.eat_sound.play()

    def check_collision_with_edges(self, snake):
        # if (it has gone past the right edge of the grid or it has gone past the left edge of the grid)
        # self.snake.body[0].x = (Vector2(6, 9) -> 6)
        if snake.body[0].x == number_of_cells or snake.body[0].x == -1:
            self.game_over()

        # if (it has gone past the top edge of the grid or it has gone past the bottom edge of the grid)
        if snake.body[0].y == number_of_cells or snake.body[0].y == -1:
            self.game_over()

    def check_collision_with_tail(self, snake):
        # Ensure the snake object is not None before accessing its properties
        # This check is crucial because, after a game over, the second snake is set to None
        # Without this check, attempting to access the 'body' attribute of a NoneType
        # (when the second snake hits the edge and this method is called) would raise an AttributeError
        if snake is not None:
            headless_body = snake.body[1:]  # Snake body without head
            if snake.body[0] in headless_body:  # Check if the head hit the tail
                self.game_over()

    def check_collision_with_other_snake(self, snake1, snake2):
        if snake1 is not None and snake2 is not None:
            if snake1.body[0] in snake2.body or snake2.body[0] in snake1.body:
                self.game_over()


    def game_over(self):
        self.snake.reset()
        # Reset the food's position
        self.food.position = self.food.generate_random_pos(self.snake.body)
        self.state = False
        self.score = 0
        self.snake.wall_hit_sound.play()
        self.second_snake = None
        print("Press any key to restart the game.")

    def score_reached_for_second_snake(self):
        return self.score >= self.second_snake_threshold

    def create_second_snake(self):
        # 只有當第二條蛇不存在且分數達到 threshold 時才創建
        # not self.second_snake = not None(the default is None) = True
        # In other words, if not self.second_snake is True, it means second snake has not yet been created
        if not self.second_snake and self.score_reached_for_second_snake():
            self.second_snake = Snake()


def draw_table():
    for x in range(number_of_cells):
        for y in range(number_of_cells):
            rect = pygame.Rect(OFFSET + x * cell_size, OFFSET + y * cell_size, cell_size, cell_size)
            pygame.draw.rect(screen, (255, 255, 255), rect, 1)


screen = pygame.display.set_mode(
    (2 * OFFSET + cell_size * number_of_cells, 2 * OFFSET + cell_size * number_of_cells))  # (750, 750)

pygame.display.set_caption("Snake Game")

# Set the game icon
icon = pygame.image.load('./Graphics/snake.png')
pygame.display.set_icon(icon)

clock = pygame.time.Clock()  # Set the FPS

# Create objects
game = Game()

# Food image
food_surface = pygame.image.load("./Graphics/food.png")

SNAKE_UPDATE = pygame.USEREVENT  # USEREVENT can be used to create custom events
# It is used to create an event that will be triggered every time the snake's position needs to be updated
pygame.time.set_timer(SNAKE_UPDATE,
                      200)  # Slow down the snake's moving speed; Trigger the SNAKE_UPDATE event every 200 milliseconds

table_drew = False

# Game Loop
while True:
    for event in pygame.event.get():
        # Check if the event is a SNAKE_UPDATE event, which occurs every 200 milliseconds to update the snake's position
        if event.type == SNAKE_UPDATE:
            game.update()

        # Quit the game
        if event.type == pygame.QUIT:  # if quit
            pygame.quit()
            sys.exit()  # close the program completely
        if event.type == pygame.KEYDOWN:  # check for key press
            if event.key == pygame.K_RETURN:  # check if the key is ESC
                pygame.quit()
                sys.exit()  # close the program completely
            if event.key == pygame.K_p:  # If press p, draw the table
                table_drew = not table_drew

            if not game.state:
                game.state = True

        # Check user's key press to change snake's direction
        if event.type == pygame.KEYDOWN:
            # To ensure that the snake cannot move in the opposite direction of its current movement
            # Only allow the snake to change its direction upwards only if it is not moving downwards
            if event.key == pygame.K_UP and game.snake.direction != Vector2(0, 1) and not game.snake.direction_changed:
                game.snake.direction = Vector2(0, -1)  # Up
                game.snake.direction_changed = True
            if event.key == pygame.K_DOWN and game.snake.direction != Vector2(0, -1) and not game.snake.direction_changed:
                game.snake.direction = Vector2(0, 1)  # Down
                game.snake.direction_changed = True
            if event.key == pygame.K_LEFT and game.snake.direction != Vector2(1, 0) and not game.snake.direction_changed:
                game.snake.direction = Vector2(-1, 0)  # Left
                game.snake.direction_changed = True
            if event.key == pygame.K_RIGHT and game.snake.direction != Vector2(-1, 0) and not game.snake.direction_changed:
                game.snake.direction = Vector2(1, 0)  # Right
                game.snake.direction_changed = True

        if game.score_reached_for_second_snake():
            # second_snake
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_w and game.second_snake.direction != Vector2(0, 1) and not game.snake.direction_changed:
                    game.second_snake.direction = Vector2(0, -1)  # Up
                    game.second_snake.direction_changed = True
                if event.key == pygame.K_s and game.second_snake.direction != Vector2(0, -1) and not game.snake.direction_changed:
                    game.second_snake.direction = Vector2(0, 1)  # Down
                    game.second_snake.direction_changed = True
                if event.key == pygame.K_a and game.second_snake.direction != Vector2(1, 0) and not game.snake.direction_changed:
                    game.second_snake.direction = Vector2(-1, 0)  # Left
                    game.second_snake.direction_changed = True
                if event.key == pygame.K_d and game.second_snake.direction != Vector2(-1, 0) and not game.snake.direction_changed:
                    game.second_snake.direction = Vector2(1, 0)  # Right
                    game.second_snake.direction_changed = True

    if table_drew:
        screen.fill(BLUE)
        draw_table()
    else:
        screen.fill(BLUE)

    pygame.draw.rect(screen, WHITE,
                     (OFFSET - 5, OFFSET - 5, cell_size * number_of_cells + 10, cell_size * number_of_cells + 10), 5)
    game.draw()

    # Title and Score
    title_surface = title_font.render("Snake Game", True, WHITE)
    score_surface = score_font.render("Score: " + str(game.score), True, WHITE)
    screen.blit(title_surface, (OFFSET - 5, 20))
    screen.blit(score_surface, (OFFSET - 5, OFFSET + cell_size * number_of_cells + 10))

    pygame.display.update()
    clock.tick(60)  # Set FPS to 60
