from pathlib import Path
import asyncio
import time
import curses
import random
from itertools import cycle
import logging

from curses_tools import get_frame_size, draw_frame, read_controls

logger = logging.getLogger(__name__)

TIC_TIMEOUT = 0.1


def load_spaceship_frames(folder='animations'):
    """Get list of spaceship animation frames.

    Args:
        folder(str):  folder name where the spaceship frame files are located.

    Return:
        list[str]: A list containing the content of each spaceship frame file.
    """
    spaceship_frames = []
    for frame_filename in Path(folder).glob('rocket_frame_*.txt'):
        with open(frame_filename, 'r') as frame_file:
            spaceship_frames.append(frame_file.read())
    return spaceship_frames


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


async def blink(canvas, row, column, symbol='*', offset_ticks: int = 0):
    """Animate a blinking symbol on the canvas."""
    while True:
        for _ in range(0, offset_ticks):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_DIM)
        for _ in range(0, 20):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(0, 3):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        for _ in range(0, 5):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(0, 3):
            await asyncio.sleep(0)


async def animate_spaceship(canvas, row, column, spaceship_frames):
    border_size = 1
    height, width = canvas.getmaxyx()
    height, width = height - border_size, width - border_size

    frame_rows, frame_columns = get_frame_size(spaceship_frames[0])
    height -= frame_rows
    width -= frame_columns

    for frame in cycle(spaceship_frames):
        for _ in range(2):
            draw_frame(canvas, row, column, frame)
            await asyncio.sleep(0)

            draw_frame(canvas, row, column, frame, negative=True)

            rows_direction, columns_direction, _ = read_controls(canvas)

            if rows_direction or columns_direction:
                row += rows_direction
                column += columns_direction

                row = max(1, row)
                column = max(1, column)

                row = min(row, height)
                column = min(column, width)


def draw(canvas):
    spaceship_frames = load_spaceship_frames()

    canvas.border()
    canvas.nodelay(True)
    curses.curs_set(False)

    coroutines = [
        blink(canvas,
              random.randint(1, int(curses.LINES - 1)),
              random.randint(1, int(curses.COLS - 1)),
              random.choice('+*.:'),
              random.randint(1, 20))
        for i in range(1, 100)
    ]
    coroutines += [fire(canvas,
                        int(curses.LINES / 2),
                        int(curses.COLS / 2),
                        rows_speed=-0.85)]
    coroutines += [animate_spaceship(canvas,
                                     int(curses.LINES / 2),
                                     int(curses.COLS / 2),
                                     spaceship_frames)]
    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        if len(coroutines) == 0:
            break
        canvas.refresh()
        time.sleep(0.1)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
