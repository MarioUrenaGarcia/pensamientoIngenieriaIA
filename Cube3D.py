#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cubo 3D rotando en terminal, renderizado en ASCII con z-buffer.
Solo usa la librería estándar (curses + math), no requiere instalar nada.

Uso:
    python3 cube3d.py

Controles:
    q       -> salir
    +/-     -> más rápido / más lento
"""

import curses
import math
import time

WIDTH = 50
HEIGHT = 25
DISTANCE = 60
K1 = 30  # factor de escala de proyección

SURFACE_CHARS = ".,-~:;=!*#$@"


def rotate(x, y, z, a, b, c):
    """Rota el punto (x,y,z) por los ángulos a (X), b (Y), c (Z)."""
    # Rotación en X
    y, z = y * math.cos(a) - z * math.sin(a), y * math.sin(a) + z * math.cos(a)
    # Rotación en Y
    x, z = x * math.cos(b) + z * math.sin(b), -x * math.sin(b) + z * math.cos(b)
    # Rotación en Z
    x, y = x * math.cos(c) - y * math.sin(c), x * math.sin(c) + y * math.cos(c)
    return x, y, z


def project(x, y, z):
    z_eff = z + DISTANCE
    ooz = 1.0 / z_eff if z_eff != 0 else 0
    xp = int(WIDTH / 2 + K1 * ooz * x * 2)  # *2 compensa aspecto de caracteres
    yp = int(HEIGHT / 2 + K1 * ooz * y)
    return xp, yp, ooz


def draw_surface(buffer, zbuffer, cube_x, cube_y, cube_z, ch, a, b, c):
    """Rellena una cara del cubo muestreando puntos en su superficie."""
    step = 0.4
    u = -8.0
    while u < 8.0:
        v = -8.0
        while v < 8.0:
            if cube_x is not None:
                x, y, z = cube_x, u, v
            elif cube_y is not None:
                x, y, z = u, cube_y, v
            else:
                x, y, z = u, v, cube_z

            rx, ry, rz = rotate(x, y, z, a, b, c)
            xp, yp, ooz = project(rx, ry, rz)

            if 0 <= xp < WIDTH and 0 <= yp < HEIGHT:
                if ooz > zbuffer[yp][xp]:
                    zbuffer[yp][xp] = ooz
                    luminance_index = min(int(ooz * K1 * 3), len(SURFACE_CHARS) - 1)
                    buffer[yp][xp] = SURFACE_CHARS[max(luminance_index, 0)]
            v += step
        u += step


def render_frame(a, b, c):
    buffer = [[' ' for _ in range(WIDTH)] for _ in range(HEIGHT)]
    zbuffer = [[0.0 for _ in range(WIDTH)] for _ in range(HEIGHT)]

    size = 8
    draw_surface(buffer, zbuffer, size, None, None, '@', a, b, c)   # +X
    draw_surface(buffer, zbuffer, -size, None, None, '$', a, b, c)  # -X
    draw_surface(buffer, zbuffer, None, size, None, '~', a, b, c)   # +Y
    draw_surface(buffer, zbuffer, None, -size, None, '#', a, b, c)  # -Y
    draw_surface(buffer, zbuffer, None, None, size, ';', a, b, c)   # +Z
    draw_surface(buffer, zbuffer, None, None, -size, '.', a, b, c)  # -Z

    return buffer


def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_CYAN, -1)

    a = b = c = 0.0
    delay = 0.03
    speed = 0.05

    while True:
        key = stdscr.getch()
        if key == ord('q'):
            break
        elif key == ord('+'):
            speed += 0.01
        elif key == ord('-'):
            speed = max(0.0, speed - 0.01)

        buffer = render_frame(a, b, c)

        stdscr.erase()
        max_y, max_x = stdscr.getmaxyx()
        offset_y = max(0, (max_y - HEIGHT) // 2)
        offset_x = max(0, (max_x - WIDTH) // 2)

        for row in range(HEIGHT):
            line = "".join(buffer[row])
            try:
                stdscr.addstr(offset_y + row, offset_x, line, curses.color_pair(1))
            except curses.error:
                pass

        try:
            stdscr.addstr(offset_y + HEIGHT + 1, offset_x, "q: salir   +/-: velocidad")
        except curses.error:
            pass

        stdscr.refresh()

        a += speed
        b += speed * 0.7
        c += speed * 0.5

        time.sleep(delay)


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
