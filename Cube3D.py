#!/usr/bin/env python3
"""Cubo 3D rotando en la terminal con iluminación, z-buffer y sombra sobre el piso.
Controles: + / - cambian la velocidad, q sale."""
import math
import os
import shutil
import sys
import time

if os.name == "nt":
    import msvcrt
else:
    import select
    import termios
    import tty

CHARS = ".,-~:;=!*#$@"     # de oscuro a brillante
FLOOR_Y = -2.0             # altura del piso
DIST = 6.0                 # distancia de la cámara
STEP = 0.05                # densidad de puntos del cubo
FPS = 30


def normalize(v):
    m = math.sqrt(sum(c * c for c in v))
    return tuple(c / m for c in v)


LX, LY, LZ = normalize((-1.0, 1.5, -1.0))   # dirección hacia la luz


def build_cube():
    faces = [
        ((1, 0, 0), (0, 1, 0), (0, 0, 1)), ((-1, 0, 0), (0, 1, 0), (0, 0, 1)),
        ((0, 1, 0), (1, 0, 0), (0, 0, 1)), ((0, -1, 0), (1, 0, 0), (0, 0, 1)),
        ((0, 0, 1), (1, 0, 0), (0, 1, 0)), ((0, 0, -1), (1, 0, 0), (0, 1, 0)),
    ]
    n = int(2 / STEP) + 1
    pts = []
    for nrm, u, v in faces:
        for i in range(n):
            a = -1 + 2 * i / (n - 1)
            for j in range(n):
                b = -1 + 2 * j / (n - 1)
                p = tuple(nrm[k] + u[k] * a + v[k] * b for k in range(3))
                pts.append((p, nrm))
    return pts


def rotation(a, b, c):
    ca, sa, cb, sb, cc, sc = math.cos(a), math.sin(a), math.cos(b), math.sin(b), math.cos(c), math.sin(c)
    # R = Rz(c) * Ry(b) * Rx(a)
    return (
        (cc * cb, cc * sb * sa - sc * ca, cc * sb * ca + sc * sa),
        (sc * cb, sc * sb * sa + cc * ca, sc * sb * ca - cc * sa),
        (-sb, cb * sa, cb * ca),
    )


class Keys:
    """Lectura de teclas sin bloquear ni esperar Enter (Windows y Unix)."""

    def start(self):
        if os.name != "nt":
            self.fd = sys.stdin.fileno()
            self.old = termios.tcgetattr(self.fd)
            tty.setcbreak(self.fd)

    def stop(self):
        if os.name != "nt":
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old)

    def read(self):
        keys = []
        if os.name == "nt":
            while msvcrt.kbhit():
                keys.append(msvcrt.getwch())
        else:
            while select.select([sys.stdin], [], [], 0)[0]:
                keys.append(os.read(self.fd, 1).decode(errors="ignore"))
        return keys


def main():
    if os.name == "nt":
        os.system("")  # habilita ANSI en Windows

    cols, rows = shutil.get_terminal_size((80, 24))
    W, H = cols, rows - 1
    N = W * H
    f = min(W / 4.5, H * 0.8)

    def project(x, y, z):
        ooz = 1 / z
        return int(W / 2 + 2 * f * x * ooz), int(H / 2 - f * y * ooz), ooz

    # Piso estático (tablero de ajedrez), se calcula una sola vez
    floor_z = [0.0] * N
    floor_buf = [(" ", 0)] * N
    floor_mask = bytearray(N)
    steps = [i * 0.05 - 3 for i in range(121)]
    for fx in steps:
        for fz in steps:
            sx, sy, ooz = project(fx, FLOOR_Y, fz + DIST)
            if 0 <= sx < W and 0 <= sy < H:
                i = sy * W + sx
                if ooz > floor_z[i]:
                    floor_z[i] = ooz
                    checker = (math.floor(fx) + math.floor(fz)) % 2
                    floor_buf[i] = (":" if checker else ".", 244 if checker else 240)
                    floor_mask[i] = 1

    cube = build_cube()
    A = B = C = 0.0
    speed = 1.0
    keys = Keys()
    keys.start()
    sys.stdout.write("\x1b[?1049h\x1b[2J\x1b[?25l")  # pantalla alternativa, limpiar, ocultar cursor

    try:
        while True:
            t0 = time.time()
            zbuf = floor_z[:]
            buf = floor_buf[:]
            cube_mask = bytearray(N)
            shadow = bytearray(N)
            (m00, m01, m02), (m10, m11, m12), (m20, m21, m22) = rotation(A, B, C)

            for (px, py, pz), (nx, ny, nz) in cube:
                x = m00 * px + m01 * py + m02 * pz
                y = m10 * px + m11 * py + m12 * pz
                z = m20 * px + m21 * py + m22 * pz

                # Sombra: proyectar el punto sobre el piso siguiendo la luz
                t = (y - FLOOR_Y) / LY
                sx, sy, _ = project(x - t * LX, FLOOR_Y, z - t * LZ + DIST)
                if 0 <= sx < W and 0 <= sy < H:
                    shadow[sy * W + sx] = 1

                # Cubo con z-buffer e iluminación difusa
                sx, sy, ooz = project(x, y, z + DIST)
                if 0 <= sx < W and 0 <= sy < H:
                    i = sy * W + sx
                    if ooz > zbuf[i]:
                        zbuf[i] = ooz
                        rnx = m00 * nx + m01 * ny + m02 * nz
                        rny = m10 * nx + m11 * ny + m12 * nz
                        rnz = m20 * nx + m21 * ny + m22 * nz
                        lum = rnx * LX + rny * LY + rnz * LZ
                        val = 0.12 + 0.88 * max(0.0, lum)
                        buf[i] = (CHARS[int(val * (len(CHARS) - 1))], 232 + int(val * 23))
                        cube_mask[i] = 1

            for i in range(N):
                if shadow[i] and floor_mask[i] and not cube_mask[i]:
                    buf[i] = (" ", 0)

            lines = []
            for r in range(H):
                parts, last = [], None
                for ch, col in buf[r * W:(r + 1) * W]:
                    if col != last and ch != " ":
                        parts.append(f"\x1b[38;5;{col}m")
                        last = col
                    parts.append(ch)
                lines.append("".join(parts))
            status = f"\x1b[0m velocidad: {speed:.2f}x   [+/-] velocidad   [q] salir\x1b[K"
            sys.stdout.write("\x1b[H" + "\n".join(lines) + "\n" + status)
            sys.stdout.flush()

            for ch in keys.read():
                if ch in "qQ":
                    return
                if ch in "+=":
                    speed = min(speed * 1.25, 10.0)
                elif ch in "-_":
                    speed = max(speed / 1.25, 0.05)

            A += 0.04 * speed
            B += 0.03 * speed
            C += 0.015 * speed
            time.sleep(max(0.0, 1 / FPS - (time.time() - t0)))
    except KeyboardInterrupt:
        pass
    finally:
        keys.stop()
        sys.stdout.write("\x1b[0m\x1b[?25h\x1b[?1049l")  # restaurar colores, cursor y pantalla original
        sys.stdout.flush()


if __name__ == "__main__":
    main()
