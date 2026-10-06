import asyncio  # Added for browser compatibility
import random
import pygame

# 1. Initialize Pygame
pygame.init()

# 3. Create the Canvas
WIDTH, HEIGHT = 1400, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("assteroid game ;)")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 80)
small_font = pygame.font.Font(None, 30)

# 4. Color Definitions (RGB Format)
BACKGROUND_COLOR = (30, 30, 40)

# --- INITIALIZE GAME VARIABLES OUTSIDE THE LOOP ---
spaceship_height = 80
spaceship_width = 50
asteroid_img = pygame.image.load("assets/asteroid.png")
spaceship = pygame.transform.scale(pygame.image.load("assets/spaceship.png"), (spaceship_width, spaceship_height))
nothrust = pygame.transform.scale(pygame.image.load("assets/jet_nothrust.png"), (spaceship_width, spaceship_height))
medthrust = pygame.transform.scale(pygame.image.load("assets/jet_medthrust.png"), (spaceship_width, spaceship_height))
highthrust = pygame.transform.scale(pygame.image.load("assets/jet_maxthrust.png"), (spaceship_width, spaceship_height))

enemymedthrust = pygame.transform.scale(pygame.image.load("assets/enemy.png"), (spaceship_width, spaceship_height))
enemyhighthrust = rotated_image = pygame.transform.rotate(pygame.transform.scale(pygame.image.load("assets/enemy turbo.png"), (spaceship_width, spaceship_height)), 20)


thrust_state = 0 
enemy_thrust_state = 0

NUM_ASTEROIDS = 6
asteroids_shot = 0
BULLET_SPEED = 10
SHIP_RADIUS = 20
START = pygame.math.Vector2(WIDTH / 2, HEIGHT / 2)
enemystartpos = [(0,random.randint(0, 1400)),(1400,random.randint(0, 1400)),(random.randint(0, 1400),0),(random.randint(0, 1400),1400)]
ENEMY_START = pygame.math.Vector2(random.choice(enemystartpos))
compass_center = (WIDTH / 2, HEIGHT / 2)


def make_asteroids():
    asteroids = []
    while len(asteroids) < NUM_ASTEROIDS:
        r = random.randint(20, 40)
        pos = pygame.math.Vector2(random.randint(r, WIDTH - r), random.randint(r, HEIGHT - r))
        if pos.distance_to(START) < 200:
            continue
        vel = pygame.math.Vector2(
            random.choice([-1, 1]) * random.randint(1, 3),
            random.choice([-1, 1]) * random.randint(1, 3),
        )
        img = pygame.transform.scale(asteroid_img, (r * 2, r * 2))
        asteroids.append({"pos": pos, "vel": vel, "r": r, "img": img})
    return asteroids

def make_enemy_spaceships():
    enemy_spaceships = []
    while len(enemy_spaceships) < NUM_ASTEROIDS:
        r = random.randint(20, 40)
        pos = pygame.math.Vector2(random.randint(r, WIDTH - r), random.randint(r, HEIGHT - r))
        if pos.distance_to(ENEMY_START) < 200:
            continue
        vel = pygame.math.Vector2(
            random.choice([-1, 1]) * random.randint(1, 3),
            random.choice([-1, 1]) * random.randint(1, 3),
        )
        img = pygame.transform.scale(asteroid_img, (r * 2, r * 2))
        enemy_spaceships.append({"pos": pos, "vel": vel, "r": r, "img": img})
    return enemy_spaceships


def move_asteroids(asteroids):
    for a in asteroids:
        a["pos"] += a["vel"]
        if a["pos"].x < a["r"]:
            a["vel"].x = abs(a["vel"].x)
        if a["pos"].x > WIDTH - a["r"]:
            a["vel"].x = -abs(a["vel"].x)
        if a["pos"].y < a["r"]:
            a["vel"].y = abs(a["vel"].y)
        if a["pos"].y > HEIGHT - a["r"]:
            a["vel"].y = -abs(a["vel"].y)

    for i in range(len(asteroids)):
        for j in range(i + 1, len(asteroids)):
            a, b = asteroids[i], asteroids[j]
            distance = a["pos"].distance_to(b["pos"])
            if 0 < distance < a["r"] + b["r"]:
                normal = (a["pos"] - b["pos"]).normalize()
                a["pos"] += normal
                b["pos"] -= normal
                m1, m2 = a["r"] ** 2, b["r"] ** 2
                v1, v2 = a["vel"].dot(normal), b["vel"].dot(normal)
                a["vel"] += normal * ((v1 * (m1 - m2) + 2 * m2 * v2) / (m1 + m2) - v1)
                b["vel"] += normal * ((v2 * (m2 - m1) + 2 * m1 * v1) / (m1 + m2) - v2)


def draw_message(text, color):
    for line, y_offset in [(text, -40), ("Press R to play again", 40)]:
        surface = font.render(line, True, color)
        screen.blit(surface, surface.get_rect(center=(WIDTH / 2, HEIGHT / 2 + y_offset)))


async def main():
    while True:
        global asteroids_shot
        asteroids = make_asteroids()
        bullets = []
        shoot_cooldown = 0
        enemy_bullets = []
        enemy_shoot_cooldown = 0
        position = pygame.math.Vector2(START)
        enemy_position = pygame.math.Vector2(ENEMY_START)
        angle = 0
        enemy_angle = 0
        speed = 0
        enemy_speed = 2
        turbo_timer = 100 
        state = "playing"


        restart = False
        while not restart:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

            keys = pygame.key.get_pressed()

            if state == "playing":
                thrust_state = 0
                if keys[pygame.K_a]:
                    angle += 2
                if keys[pygame.K_d]:
                    angle -= 2
                if keys[pygame.K_w]:
                    speed += .2
                    if keys[pygame.K_LSHIFT]:
                        thrust_state = 2
                        speed += .1
                    else:
                        thrust_state = 1
                if keys[pygame.K_s]:
                    speed -= .2
                    thrust_state = 1

                enemy_thrust_state = 0
                
                forward = pygame.math.Vector2(0, -1).rotate(-angle)
                position += forward * speed
                speed *= 0.98
                position.x %= WIDTH
                position.y %= HEIGHT

                enemy_forward = pygame.math.Vector2(0, -1).rotate(-enemy_angle)
                to_player = position - enemy_position
                distance = to_player.length()
                seen = 0 < distance < 300 and enemy_forward.dot(to_player.normalize()) > 0.7

                if seen:
                    enemy_thrust_state = 1
                    enemy_shoot_cooldown = max(0, enemy_shoot_cooldown - 1)
                    enemy_angle = (enemy_position - position).angle_to(pygame.math.Vector2(0, 1))
                    if distance < 200:
                        enemy_speed = 12
                    if distance < 40:
                        state = "lost"
                    else:
                        enemy_bullets.append([pygame.math.Vector2(enemy_position), enemy_forward * BULLET_SPEED])
                        enemy_shoot_cooldown = 6.7
                        enemy_speed = 7
                else:
                    enemy_speed = 2
                    enemy_thrust_state = 0
                    enemy_angle += random.uniform(-2, 2)

                enemy_position += enemy_forward * enemy_speed
                enemy_position.x %= WIDTH
                enemy_position.y %= HEIGHT
                #enemy_angle = (enemy_position - position).angle_to(pygame.math.Vector2(0, -1))

                shoot_cooldown = max(0, shoot_cooldown - 1)
                turbo_timer = min(100, turbo_timer + 0.2)    
                if keys[pygame.K_SPACE] and shoot_cooldown == 0:
                    if keys[pygame.K_RSHIFT]:
                        bullets.append([pygame.math.Vector2(position), forward * BULLET_SPEED * 2])
                        turbo_timer -= 5
                        shoot_cooldown = 6.7
                        if turbo_timer <= 0:
                            turbo_timer = 0
                            shoot_cooldown = 300 
                    else:
                        bullets.append([pygame.math.Vector2(position), forward * BULLET_SPEED])
                        shoot_cooldown = 6.7

                move_asteroids(asteroids)

                for b in bullets[:]:
                    b[0] += b[1]
                    if not (0 <= b[0].x <= WIDTH and 0 <= b[0].y <= HEIGHT):
                        bullets.remove(b)
                        continue
                    for a in asteroids:
                        if b[0].distance_to(a["pos"]) < a["r"]:
                            # Remove hit asteroid
                            asteroids.remove(a)
                            asteroids_shot += 1
                            asteroids.append({"pos": pygame.math.Vector2(random.randint(a["r"], WIDTH - a["r"]),
                                                                        random.randint(a["r"], HEIGHT - a["r"])),
                                              "vel": pygame.math.Vector2(random.choice([-1, 1]) * random.randint(1, 3),
                                                                         random.choice([-1, 1]) * random.randint(1, 3)),
                                              "r": a["r"],
                                              "img": pygame.transform.scale(asteroid_img, (a["r"] * 2, a["r"] * 2))})
                            bullets.remove(b)
                            break

                if not asteroids:
                    state = "won"
                for a in asteroids:
                    if position.distance_to(a["pos"]) < a["r"] + SHIP_RADIUS:
                        state = "lost"

            elif keys[pygame.K_r]:
                restart = True

            # Clear screen with background color
            screen.fill(BACKGROUND_COLOR)
            speed_text = small_font.render(f"speed: {speed:.2f}", True, (255, 255, 255))
            screen.blit(speed_text, (20, 20))
            angle_text = small_font.render(f"angle: {angle:.2f}", True, (255, 255, 255))
            screen.blit(angle_text, (20, 50))
            counter_text = small_font.render(f"asteroids shot: {asteroids_shot}", True, (255, 255, 255))
            screen.blit(counter_text, (20, 80))
            shot_cooldown_text = small_font.render(f"shot cooldown: {shoot_cooldown:.2f}", True, (255, 255, 255))
            screen.blit(shot_cooldown_text, (20, 110))
            turboshot_cooldown_text = small_font.render(f"turbo shot cooldown: {turbo_timer:.2f}", True, (255, 255, 255))
            screen.blit(turboshot_cooldown_text, (20, 140))

            for a in asteroids:
                screen.blit(a["img"], (a["pos"].x - a["r"], a["pos"].y - a["r"]))
            for b in bullets:
                pygame.draw.circle(screen, (255, 0, 0), (int(b[0].x), int(b[0].y)), 3)

            #spaceshio
            if thrust_state == 0:
                spaceship = nothrust
            elif thrust_state == 1:
                spaceship = medthrust
            elif thrust_state == 2:
                spaceship = highthrust
            rotated_ship = pygame.transform.rotate(spaceship, angle)
            screen.blit(rotated_ship, rotated_ship.get_rect(center=(position.x, position.y)))


            if enemy_thrust_state == 0:
                enemy_spaceship = enemymedthrust
            elif enemy_thrust_state == 1:
                enemy_spaceship = enemyhighthrust
            rotated_ship_enemy = pygame.transform.rotate(enemy_spaceship, enemy_angle)
            screen.blit(rotated_ship_enemy, rotated_ship_enemy.get_rect(center=(enemy_position.x, enemy_position.y)))           


            if asteroids_shot >= 67:
                state = "won"
            
            if state == "won":
                draw_message("You win!", (80, 220, 120))
            elif state == "lost":
                draw_message("you got fried :(", (230, 80, 80))

            compass_center = pygame.math.Vector2(200, 250)
            needle_tip = compass_center + forward * 50
            pygame.draw.circle(screen, (200, 200, 200), compass_center, 40, 2)
            pygame.draw.line(screen, (255, 0, 0), compass_center, needle_tip, 3)

            # Render changes onto the screen
            pygame.display.flip()

            clock.tick(60)  # Controls game speed (60 frames per second)
            await asyncio.sleep(0)  # CRITICAL: Web loop pause


asyncio.run(main())