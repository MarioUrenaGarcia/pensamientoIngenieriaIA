#!/usr/bin/env python3
"""
Matrix Rain - efecto visual de lluvia de código estilo Matrix en terminal.
Solo usa la librería estándar (curses), no requiere instalar nada.

Uso:
    python3 matrix_rain.py

Controles:
    q  -> salir
    +  -> más rápido
    -  -> más lento
"""

import curses
import random
import time

CHARS = "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


class Column:
    def __init__(self, x, height):
        self.x = x
        self.height = height
        self.reset()

    def reset(self):
        self.y = random.randint(-self.height, 0)
        self.length = random.randint(5, self.height)
        self.speed = random.uniform(0.5, 1.5)
        self._progress = 0.0

    def step(self, dt):
        self._progress += dt * self.speed * 15
        while self._progress >= 1:
            self.y += 1
            self._progress -= 1
        if self.y - self.length > self.height:
            self.reset()

    def glyphs(self):
        """Devuelve lista de (fila, char, es_cabeza)"""
        out = []
        for i in range(self.length):
            row = self.y - i
            if 0 <= row < self.height:
                ch = random.choice(CHARS)
                out.append((row, ch, i == 0))
        return out


def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_GREEN, -1)
    curses.init_pair(2, curses.COLOR_WHITE, -1)
    curses.init_pair(3, curses.COLOR_GREEN, -1)

    height, width = stdscr.getmaxyx()
    columns = [Column(x, height) for x in range(width)]

    delay = 0.03
    last = time.time()

    while True:
        now = time.time()
        dt = now - last
        last = now

        key = stdscr.getch()
        if key == ord('q'):
            break
        elif key == ord('+'):
            delay = max(0.005, delay - 0.005)
        elif key == ord('-'):
            delay = min(0.15, delay + 0.005)

        new_height, new_width = stdscr.getmaxyx()
        if new_height != height or new_width != width:
            height, width = new_height, new_width
            columns = [Column(x, height) for x in range(width)]

        stdscr.erase()
        for col in columns:
            col.step(dt)
            for row, ch, is_head in col.glyphs():
                try:
                    if is_head:
                        stdscr.addstr(row, col.x, ch, curses.color_pair(2) | curses.A_BOLD)
                    else:
                        stdscr.addstr(row, col.x, ch, curses.color_pair(1))
                except curses.error:
                    pass  # esquina inferior derecha, se ignora

        stdscr.refresh()
        time.sleep(delay)


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
