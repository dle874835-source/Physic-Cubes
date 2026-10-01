import pygame
import math

pygame.init()

# =========================================================
# WINDOW
# =========================================================
WIDTH = 900
HEIGHT = 650

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Physics Cubes")

clock = pygame.time.Clock()


# =========================================================
# COLORS
# =========================================================
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

RED = (230, 80, 80)
GREEN = (80, 200, 120)


# =========================================================
# PHYSICS
# =========================================================
GRAVITY = 0.5
BOUNCE = 0.25

AIR_FRICTION = 0.995
GROUND_FRICTION = 0.80

RESTITUTION = 0.18
CUBE_FRICTION = 0.80

FLING_POWER = 0.35
MIN_FLING_SPEED = 2.0

CUBE_SIZE = 70
MAX_CUBES = 5

TOP_LIMIT = 50
GROUND_Y = HEIGHT


# =========================================================
# ROTATION
# =========================================================

# Gia tốc góc khi đang lật
TIP_GRAVITY = 0.10

# Ma sát quay
ANGULAR_DAMPING = 0.992

# Tốc độ tối đa
MAX_ANGULAR_SPEED = 12.0

# 360° khi fling
FLING_ROTATION_SPEED = 12.0

# Tốc độ tự dựng lại khi đã nằm ổn định
RESTORE_SPEED = 5.0


# =========================================================
# BUTTONS
# =========================================================
reset_button = pygame.Rect(
    10, 10, 100, 40
)

add_button = pygame.Rect(
    120, 10, 120, 40
)


# =========================================================
# CUBE
# =========================================================
class Cube:

    def __init__(self, x, y):

        self.x = float(x)
        self.y = float(y)

        self.size = CUBE_SIZE

        self.vx = 0.0
        self.vy = 0.0

        # Góc hiển thị
        self.angle = 0.0

        # Tốc độ góc
        self.angular_velocity = 0.0

        # =================================================
        # FLING
        # =================================================
        self.target_angle = None
        self.pending_rotation = False

        # =================================================
        # DRAG
        # =================================================
        self.dragging = False

        # =================================================
        # SUPPORT
        # =================================================
        self.support = None

        # =================================================
        # GROUND
        # =================================================
        self.on_ground = False

        # =================================================
        # TIPPING
        # =================================================
        self.tipping = False

        # Điểm pivot khi lật
        self.pivot_x = 0.0
        self.pivot_y = 0.0

        # Vector từ pivot tới tâm cube
        self.pivot_dx = 0.0
        self.pivot_dy = 0.0

        # Góc của vector pivot -> tâm
        self.pivot_angle = 0.0

        # Bán kính từ pivot tới tâm
        self.pivot_radius = 0.0

        # Hướng quay:
        # +1 = tăng góc
        # -1 = giảm góc
        self.pivot_direction = 0

        # =================================================
        # LANDING
        # =================================================
        self.landing = False

        # =================================================
        # VISUAL
        # =================================================
        self.surface = pygame.Surface(
            (self.size, self.size),
            pygame.SRCALPHA
        )

        pygame.draw.rect(
            self.surface,
            WHITE,
            (
                0,
                0,
                self.size,
                self.size
            ),
            border_radius=5
        )

        # AABB cho collision
        self.rect = pygame.Rect(
            int(self.x - self.size / 2),
            int(self.y - self.size / 2),
            self.size,
            self.size
        )

    # =====================================================
    # UPDATE RECT
    # =====================================================
    def update_rect(self):

        self.rect.center = (
            round(self.x),
            round(self.y)
        )

    # =====================================================
    # ROTATED CORNERS
    # =====================================================
    def get_corners(self):

        half = self.size / 2

        rad = math.radians(
            self.angle
        )

        cos_a = math.cos(rad)
        sin_a = math.sin(rad)

        corners = []

        for px, py in [
            (-half, -half),
            (half, -half),
            (half, half),
            (-half, half)
        ]:

            rx = (
                px * cos_a
                - py * sin_a
            )

            ry = (
                px * sin_a
                + py * cos_a
            )

            corners.append(
                (
                    self.x + rx,
                    self.y + ry
                )
            )

        return corners

    # =====================================================
    # LOWEST POINT
    # =====================================================
    def lowest_y(self):

        return max(
            y
            for x, y in self.get_corners()
        )

    # =====================================================
    # DRAW
    # =====================================================
    def draw(self):

        rotated = pygame.transform.rotate(
            self.surface,
            self.angle
        )

        draw_rect = rotated.get_rect(
            center=(
                round(self.x),
                round(self.y)
            )
        )

        screen.blit(
            rotated,
            draw_rect
        )


# =========================================================
# CREATE CUBES
# =========================================================
def create_cubes():

    return [
        Cube(450, 300)
    ]


cubes = create_cubes()


# =========================================================
# DRAG VARIABLES
# =========================================================
dragged_cube = None

previous_mouse_pos = None

mouse_velocity_x = 0.0
mouse_velocity_y = 0.0

drag_offset_x = 0.0
drag_offset_y = 0.0


# =========================================================
# RESET
# =========================================================
def reset_game():

    global cubes
    global dragged_cube
    global previous_mouse_pos
    global mouse_velocity_x
    global mouse_velocity_y

    cubes = create_cubes()

    dragged_cube = None

    previous_mouse_pos = None

    mouse_velocity_x = 0.0
    mouse_velocity_y = 0.0


# =========================================================
# ADD CUBE
# =========================================================
def add_cube():

    if len(cubes) >= MAX_CUBES:
        return

    positions = [
        (450, 300),
        (350, 250),
        (550, 250),
        (350, 150),
        (550, 150)
    ]

    x, y = positions[len(cubes)]

    cubes.append(
        Cube(x, y)
    )


# =========================================================
# ANGLE
# =========================================================
def normalize_angle(angle):

    while angle > 180:
        angle -= 360

    while angle < -180:
        angle += 360

    return angle


def nearest_right_angle(angle):

    return (
        round(angle / 90)
        * 90
    )


# =========================================================
# POINT INSIDE
# =========================================================
def cube_contains_point(cube, pos):

    return cube.rect.collidepoint(pos)


# =========================================================
# FIND SUPPORT
# =========================================================
def find_support(cube):

    # Khi đang lật thì TUYỆT ĐỐI không nhận support
    if cube.tipping:
        return None

    best = None
    best_gap = float("inf")

    for other in cubes:

        if other is cube:
            continue

        if other.tipping:
            continue

        # Phải nằm bên dưới
        if other.y <= cube.y:
            continue

        gap = (
            other.rect.top
            - cube.rect.bottom
        )

        if gap < -5:
            continue

        if gap > 8:
            continue

        # Có giao nhau X không?
        left = max(
            cube.rect.left,
            other.rect.left
        )

        right = min(
            cube.rect.right,
            other.rect.right
        )

        if right <= left:
            continue

        if gap < best_gap:

            best_gap = gap
            best = other

    return best


# =========================================================
# START TIPPING FROM EDGE
# =========================================================
def start_tipping(cube, support):

    if cube.tipping:
        return

    cube.tipping = True
    cube.landing = False

    cube.support = None

    cube.target_angle = None
    cube.pending_rotation = False

    half = cube.size / 2

    # =====================================================
    # XÁC ĐỊNH MÉP PIVOT
    # =====================================================

    # -----------------------------------------------------
    # Cube nhô sang PHẢI
    #
    # Pivot = mép phải của support
    # -----------------------------------------------------
    if cube.x > support.rect.right:

        cube.pivot_x = support.rect.right
        cube.pivot_y = support.rect.top

        # Tâm cube nằm phía trên + bên trái pivot
        dx = cube.x - cube.pivot_x
        dy = cube.y - cube.pivot_y

        cube.pivot_direction = -1

    # -----------------------------------------------------
    # Cube nhô sang TRÁI
    # -----------------------------------------------------
    else:

        cube.pivot_x = support.rect.left
        cube.pivot_y = support.rect.top

        dx = cube.x - cube.pivot_x
        dy = cube.y - cube.pivot_y

        cube.pivot_direction = 1

    cube.pivot_dx = dx
    cube.pivot_dy = dy

    cube.pivot_radius = math.sqrt(
        dx * dx
        + dy * dy
    )

    cube.pivot_angle = math.atan2(
        dy,
        dx
    )

    # =====================================================
    # TẠO MỘT TỐC ĐỘ QUAY NHỎ
    # =====================================================

    # Nếu đang nhô sang phải
    if cube.x > support.rect.right:

        cube.angular_velocity = -0.35

    else:

        cube.angular_velocity = 0.35


# =========================================================
# UPDATE TIPPING
# =========================================================
def update_tipping(cube, dt):

    # =====================================================
    # GRAVITY TẠO TORQUE
    # =====================================================

    # Góc hiện tại của vector tâm -> pivot
    angle = cube.pivot_angle

    # Thành phần làm cube tiếp tục đổ
    torque = (
        math.sin(angle)
        * TIP_GRAVITY
    )

    cube.angular_velocity += (
        torque
        * cube.pivot_direction
        * dt
    )

    # Ma sát
    cube.angular_velocity *= (
        ANGULAR_DAMPING
    )

    cube.angular_velocity = max(
        -MAX_ANGULAR_SPEED,
        min(
            MAX_ANGULAR_SPEED,
            cube.angular_velocity
        )
    )

    # =====================================================
    # XOAY QUANH PIVOT
    # =====================================================
    cube.pivot_angle += (
        math.radians(
            cube.angular_velocity
        )
        * dt
    )

    # =====================================================
    # TÍNH LẠI TÂM CUBE
    # =====================================================
    cube.x = (
        cube.pivot_x
        + math.cos(
            cube.pivot_angle
        )
        * cube.pivot_radius
    )

    cube.y = (
        cube.pivot_y
        + math.sin(
            cube.pivot_angle
        )
        * cube.pivot_radius
    )

    # =====================================================
    # GÓC HÌNH VUÔNG
    # =====================================================
    cube.angle += (
        cube.angular_velocity
        * dt
    )

    cube.update_rect()

    # =====================================================
    # ĐÃ LẬT ĐỦ XA
    #
    # Khi cube đã rời khỏi pivot,
    # cho nó trở thành vật thể tự do.
    # =====================================================
    if abs(
        cube.angle
    ) >= 85:

        cube.tipping = False
        cube.landing = False

        # Tiếp tục rơi bằng vận tốc hiện tại
        cube.vx = (
            cube.angular_velocity
            * 0.35
        )

        cube.vy += 0.5

        cube.support = None

        cube.angular_velocity *= 0.7


# =========================================================
# LANDING STABILIZATION
# =========================================================
def stabilize_landing(cube, dt):

    target = nearest_right_angle(
        cube.angle
    )

    difference = normalize_angle(
        target - cube.angle
    )

    # Tự xoay từ từ về góc chuẩn
    if difference > 0:

        step = min(
            RESTORE_SPEED * dt,
            difference
        )

    else:

        step = max(
            -RESTORE_SPEED * dt,
            difference
        )

    cube.angle += step

    # Khi đủ gần thì dừng
    if abs(
        difference
    ) < 0.8:

        cube.angle = target

        cube.angular_velocity = 0

        cube.landing = False
        cube.tipping = False


# =========================================================
# MOVE DRAGGED CUBE
# =========================================================
def move_dragged_cube(
    cube,
    new_x,
    new_y
):

    old_x = cube.x
    old_y = cube.y

    # =====================================================
    # X
    # =====================================================
    cube.x = new_x
    cube.update_rect()

    for other in cubes:

        if other is cube:
            continue

        if not cube.rect.colliderect(
            other.rect
        ):
            continue

        # -------------------------------------------------
        # Kéo sang phải
        # -------------------------------------------------
        if new_x > old_x:

            overlap = (
                cube.rect.right
                - other.rect.left
            )

            cube.x -= overlap
            cube.update_rect()

            # Đẩy cube kia
            other.x += overlap
            other.vx += (
                overlap * 0.15
            )
            other.update_rect()

        # -------------------------------------------------
        # Kéo sang trái
        # -------------------------------------------------
        elif new_x < old_x:

            overlap = (
                other.rect.right
                - cube.rect.left
            )

            cube.x += overlap
            cube.update_rect()

            other.x -= overlap
            other.vx -= (
                overlap * 0.15
            )
            other.update_rect()

    # =====================================================
    # Y
    # =====================================================
    cube.y = new_y
    cube.update_rect()

    for other in cubes:

        if other is cube:
            continue

        if not cube.rect.colliderect(
            other.rect
        ):
            continue

        # -------------------------------------------------
        # Kéo xuống
        # -------------------------------------------------
        if new_y > old_y:

            overlap = (
                cube.rect.bottom
                - other.rect.top
            )

            cube.y -= overlap
            cube.update_rect()

            other.y += overlap
            other.vy += (
                overlap * 0.15
            )
            other.update_rect()

        # -------------------------------------------------
        # Kéo lên
        # -------------------------------------------------
        elif new_y < old_y:

            overlap = (
                other.rect.bottom
                - cube.rect.top
            )

            cube.y += overlap
            cube.update_rect()

            other.y -= overlap
            other.vy -= (
                overlap * 0.15
            )
            other.update_rect()

    # =====================================================
    # WALLS
    # =====================================================
    if cube.rect.left < 0:

        cube.x = (
            cube.size / 2
        )

        cube.update_rect()

    if cube.rect.right > WIDTH:

        cube.x = (
            WIDTH
            - cube.size / 2
        )

        cube.update_rect()

    if cube.rect.top < TOP_LIMIT:

        cube.y = (
            TOP_LIMIT
            + cube.size / 2
        )

        cube.update_rect()


# =========================================================
# CUBE COLLISION
# =========================================================
def resolve_cube_collision(a, b):

    if not a.rect.colliderect(
        b.rect
    ):
        return

    overlap_x = min(
        a.rect.right
        - b.rect.left,

        b.rect.right
        - a.rect.left
    )

    overlap_y = min(
        a.rect.bottom
        - b.rect.top,

        b.rect.bottom
        - a.rect.top
    )

    if overlap_x <= 0 or overlap_y <= 0:
        return

    # =====================================================
    # X COLLISION
    # =====================================================
    if overlap_x < overlap_y:

        if a.x < b.x:

            nx = -1

            a.x -= (
                overlap_x / 2
            )

            b.x += (
                overlap_x / 2
            )

        else:

            nx = 1

            a.x += (
                overlap_x / 2
            )

            b.x -= (
                overlap_x / 2
            )

        ny = 0

    # =====================================================
    # Y COLLISION
    # =====================================================
    else:

        nx = 0

        if a.y < b.y:

            ny = -1

            a.y -= (
                overlap_y / 2
            )

            b.y += (
                overlap_y / 2
            )

        else:

            ny = 1

            a.y += (
                overlap_y / 2
            )

            b.y -= (
                overlap_y / 2
            )

    a.update_rect()
    b.update_rect()

    # =====================================================
    # RELATIVE VELOCITY
    # =====================================================
    relative_vx = (
        a.vx - b.vx
    )

    relative_vy = (
        a.vy - b.vy
    )

    normal_velocity = (
        relative_vx * nx
        + relative_vy * ny
    )

    if normal_velocity >= 0:
        return

    # =====================================================
    # IMPULSE
    # =====================================================
    impulse = (
        -(1 + RESTITUTION)
        * normal_velocity
        / 2
    )

    impulse_x = (
        impulse * nx
    )

    impulse_y = (
        impulse * ny
    )

    if not a.dragging:

        a.vx += impulse_x
        a.vy += impulse_y

    if not b.dragging:

        b.vx -= impulse_x
        b.vy -= impulse_y

    # =====================================================
    # FRICTION
    # =====================================================
    tangent_velocity = (
        relative_vx * (-ny)
        + relative_vy * nx
    )

    friction = (
        tangent_velocity
        * CUBE_FRICTION
        / 2
    )

    fx = (
        friction * (-ny)
    )

    fy = (
        friction * nx
    )

    if not a.dragging:

        a.vx -= fx
        a.vy -= fy

    if not b.dragging:

        b.vx += fx
        b.vy += fy


# =========================================================
# GROUND
# =========================================================
def handle_ground(cube):

    lowest = cube.lowest_y()

    if lowest < GROUND_Y:
        cube.on_ground = False
        return

    cube.on_ground = True

    # Đẩy cube lên để không xuyên đất
    cube.y -= (
        lowest
        - GROUND_Y
    )

    cube.update_rect()

    # -----------------------------------------------------
    # Nảy
    # -----------------------------------------------------
    if cube.vy > 1:

        cube.vy *= -BOUNCE

    else:

        cube.vy = 0

    cube.vx *= GROUND_FRICTION

    # -----------------------------------------------------
    # Nếu đang lật mà chạm đất
    # -----------------------------------------------------
    if cube.tipping:

        cube.tipping = False
        cube.landing = True

        cube.angular_velocity *= 0.4

        cube.support = None

    # -----------------------------------------------------
    # Nếu nằm nghiêng
    # -----------------------------------------------------
    elif abs(
        normalize_angle(
            cube.angle
        )
    ) > 1:

        cube.landing = True


# =========================================================
# MAIN LOOP
# =========================================================
running = True

while running:

    dt = (
        clock.tick(60)
        / 16.666
    )

    mouse_pos = pygame.mouse.get_pos()

    # =====================================================
    # EVENTS
    # =====================================================
    for event in pygame.event.get():

        if event.type == pygame.QUIT:

            running = False

        # =================================================
        # MOUSE DOWN
        # =================================================
        elif event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1:

                # Reset
                if reset_button.collidepoint(
                    event.pos
                ):

                    reset_game()
                    continue

                # Add Cube
                if add_button.collidepoint(
                    event.pos
                ):

                    add_cube()
                    continue

                # Tìm cube
                for cube in reversed(cubes):

                    if cube_contains_point(
                        cube,
                        event.pos
                    ):

                        dragged_cube = cube

                        cube.dragging = True

                        cube.vx = 0
                        cube.vy = 0

                        cube.angular_velocity = 0

                        cube.target_angle = None
                        cube.pending_rotation = False

                        cube.tipping = False
                        cube.landing = False

                        cube.support = None

                        previous_mouse_pos = (
                            event.pos
                        )

                        mouse_velocity_x = 0
                        mouse_velocity_y = 0

                        drag_offset_x = (
                            cube.x
                            - event.pos[0]
                        )

                        drag_offset_y = (
                            cube.y
                            - event.pos[1]
                        )

                        break

        # =================================================
        # MOUSE UP
        # =================================================
        elif event.type == pygame.MOUSEBUTTONUP:

            if event.button == 1:

                if dragged_cube is not None:

                    cube = dragged_cube

                    cube.dragging = False

                    speed = math.sqrt(
                        mouse_velocity_x ** 2
                        + mouse_velocity_y ** 2
                    )

                    # =====================================
                    # FLING
                    # =====================================
                    if speed >= MIN_FLING_SPEED:

                        cube.vx = (
                            mouse_velocity_x
                            * FLING_POWER
                        )

                        cube.vy = (
                            mouse_velocity_y
                            * FLING_POWER
                        )

                        cube.angular_velocity = 0

                        cube.tipping = False
                        cube.landing = False

                        if cube.on_ground:

                            cube.pending_rotation = True
                            cube.target_angle = None

                        else:

                            cube.pending_rotation = False

                            cube.target_angle = (
                                cube.angle
                                + 360
                            )

                    # =====================================
                    # KHÔNG FLING
                    # =====================================
                    else:

                        cube.vx = 0
                        cube.vy = 0

                        cube.angular_velocity = 0

                        cube.target_angle = None
                        cube.pending_rotation = False

                    dragged_cube = None

                    previous_mouse_pos = None

                    mouse_velocity_x = 0
                    mouse_velocity_y = 0

    # =====================================================
    # DRAGGING
    # =====================================================
    if dragged_cube is not None:

        cube = dragged_cube

        if previous_mouse_pos is not None:

            mouse_velocity_x = (
                mouse_pos[0]
                - previous_mouse_pos[0]
            )

            mouse_velocity_y = (
                mouse_pos[1]
                - previous_mouse_pos[1]
            )

        previous_mouse_pos = mouse_pos

        desired_x = (
            mouse_pos[0]
            + drag_offset_x
        )

        desired_y = (
            mouse_pos[1]
            + drag_offset_y
        )

        move_dragged_cube(
            cube,
            desired_x,
            desired_y
        )

        cube.vx = 0
        cube.vy = 0

        cube.angular_velocity = 0

        cube.target_angle = None
        cube.pending_rotation = False

    # =====================================================
    # BASIC MOVEMENT
    # =====================================================
    for cube in cubes:

        if cube.dragging:
            continue

        # Nếu đang pivot thì KHÔNG dùng
        # chuyển động tâm bình thường
        if cube.tipping:
            continue

        cube.vy += (
            GRAVITY * dt
        )

        cube.x += (
            cube.vx * dt
        )

        cube.y += (
            cube.vy * dt
        )

        cube.update_rect()

        # -------------------------------------------------
        # LEFT WALL
        # -------------------------------------------------
        if cube.rect.left < 0:

            cube.x = (
                cube.size / 2
            )

            cube.vx *= -BOUNCE

            cube.update_rect()

        # -------------------------------------------------
        # RIGHT WALL
        # -------------------------------------------------
        if cube.rect.right > WIDTH:

            cube.x = (
                WIDTH
                - cube.size / 2
            )

            cube.vx *= -BOUNCE

            cube.update_rect()

        # -------------------------------------------------
        # TOP
        # -------------------------------------------------
        if cube.rect.top < TOP_LIMIT:

            cube.y = (
                TOP_LIMIT
                + cube.size / 2
            )

            cube.vy *= -BOUNCE

            cube.update_rect()

        cube.on_ground = False

        cube.vx *= AIR_FRICTION

    # =====================================================
    # CUBE COLLISIONS
    # =====================================================
    for _ in range(3):

        for i in range(
            len(cubes)
        ):

            for j in range(
                i + 1,
                len(cubes)
            ):

                resolve_cube_collision(
                    cubes[i],
                    cubes[j]
                )

    # =====================================================
    # SUPPORT CHECK
    # =====================================================
    for cube in cubes:

        if cube.dragging:
            continue

        if cube.tipping:
            continue

        support = find_support(cube)

        cube.support = support

        if support is None:
            continue

        # =================================================
        # KIỂM TRA CUBE CÓ BỊ LỆCH KHỎI MÉP KHÔNG
        # =================================================

        left_edge = support.rect.left
        right_edge = support.rect.right

        # -------------------------------------------------
        # HƠN NỬA RA NGOÀI BÊN PHẢI
        # -------------------------------------------------
        if cube.x > right_edge:

            start_tipping(
                cube,
                support
            )

            continue

        # -------------------------------------------------
        # HƠN NỬA RA NGOÀI BÊN TRÁI
        # -------------------------------------------------
        if cube.x < left_edge:

            start_tipping(
                cube,
                support
            )

            continue

        # =================================================
        # VẪN Ở TRÊN SUPPORT
        # =================================================
        cube.y = (
            support.rect.top
            - cube.size / 2
        )

        cube.vy = min(
            cube.vy,
            0
        )

        cube.update_rect()

    # =====================================================
    # UPDATE TIPPING
    # =====================================================
    for cube in cubes:

        if cube.dragging:
            continue

        if cube.tipping:

            update_tipping(
                cube,
                dt
            )

    # =====================================================
    # GROUND
    # =====================================================
    for cube in cubes:

        if cube.dragging:
            continue

        if cube.tipping:
            continue

        handle_ground(cube)

    # =====================================================
    # LANDING
    # =====================================================
    for cube in cubes:

        if cube.dragging:
            continue

        if not cube.landing:
            continue

        if not cube.on_ground:
            continue

        stabilize_landing(
            cube,
            dt
        )

    # =====================================================
    # FLING ROTATION START
    # =====================================================
    for cube in cubes:

        if cube.dragging:
            continue

        if cube.pending_rotation:

            if not cube.on_ground:

                cube.pending_rotation = False

                cube.target_angle = (
                    cube.angle
                    + 360
                )

    # =====================================================
    # FLING 360
    # =====================================================
    for cube in cubes:

        if cube.dragging:
            continue

        if cube.target_angle is None:
            continue

        # Chạm đất
        if cube.on_ground:

            cube.target_angle = None
            cube.angular_velocity = 0

            cube.landing = True

            continue

        # Bắt đầu tipping
        if cube.tipping:

            cube.target_angle = None

            continue

        difference = (
            cube.target_angle
            - cube.angle
        )

        if abs(
            difference
        ) <= FLING_ROTATION_SPEED:

            cube.angle = (
                cube.target_angle
            )

            cube.target_angle = None

        else:

            if difference > 0:

                cube.angle += (
                    FLING_ROTATION_SPEED
                )

            else:

                cube.angle -= (
                    FLING_ROTATION_SPEED
                )

    # =====================================================
    # DRAW
    # =====================================================
    screen.fill(BLACK)

    # Buttons
    pygame.draw.rect(
        screen,
        RED,
        reset_button,
        border_radius=6
    )

    pygame.draw.rect(
        screen,
        GREEN,
        add_button,
        border_radius=6
    )

    # Text
    font = pygame.font.SysFont(
        None,
        24
    )

    reset_text = font.render(
        "Reset",
        True,
        WHITE
    )

    add_text = font.render(
        "Add Cube",
        True,
        WHITE
    )

    screen.blit(
        reset_text,
        reset_text.get_rect(
            center=reset_button.center
        )
    )

    screen.blit(
        add_text,
        add_text.get_rect(
            center=add_button.center
        )
    )

    # Cubes
    for cube in cubes:

        cube.draw()

    pygame.display.flip()


pygame.quit()
