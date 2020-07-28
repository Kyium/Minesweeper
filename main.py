from tkinter import Tk, Label, Widget, Canvas, Scrollbar
from typing import Tuple, Union, Dict
from functools import partial
from random import randint, shuffle
from time import sleep
from PIL import Image, ImageTk
from qolfac import StopWatch, integer_range_validation as irv, dynamic_arg_count_function as dac
from threading import Thread
from string import ascii_letters


def load_image(source: str):
    return Image.open(source)


def tk_image(image: Image):
    return ImageTk.PhotoImage(image)


def add_tuples(a: Tuple[int, int], b: Tuple[int, int]):
    return a[0] + b[0], a[1] + b[1]


def tk_widget_key_bind(widget: Union[Widget, Tk], key: str, function, args: Union[tuple, list, None] = None,
                       kwargs: Union[Dict[str, any], None] = None):
    def buffer_function(_):
        dac(function, args, kwargs)
    if key in ascii_letters:
        widget.bind(key.lower(), buffer_function)
        widget.bind(key.upper(), buffer_function)
    else:
        widget.bind(key, buffer_function)


class MineSweeper:
    graphics = {f"{i}": load_image(f"Graphics/{i}.png") for i in range(1, 9)}
    graphics["flag"] = load_image("Graphics/flag.png")
    graphics["blank"] = load_image("Graphics/blank.png")
    graphics["blank_c"] = load_image("Graphics/blank(clear).png")
    graphics["mine"] = load_image("Graphics/mine.png")
    graphics["mine_e"] = load_image("Graphics/mine(exploded).png")
    surroundings = [(0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1)]

    def __init__(self, grid_size: Tuple[int, int], mines: int, resolution: Tuple[int, int]):
        assert mines < grid_size[0] * grid_size[1] - 1, "Too many mines."
        self.__running = True
        self.__grid_size = grid_size
        self.__grid = {}
        self.__root = Tk()
        self.__tile_grid = Canvas(self.__root)
        # self.x_bar = Scrollbar(self.__root, orient="horizontal")
        # self.y_bar = Scrollbar(self.__root)
        # self.x_bar.configure()
        self.__graphics = {g: tk_image(MineSweeper.graphics[g]) for g in MineSweeper.graphics}
        self.__root.title("Minesweeper")
        self.__root.resizable(False, False)
        self.max_grid_size: Tuple[int, int] = (resolution[0] // 30, resolution[1] //30)
        self.__mine_count = mines
        self.__click_lock = False
        self.__key_lock = False
        self.__reset_call = False
        self.__timer = StopWatch()
        self.__ng_prompt = False
        self.__p_thread = Thread(target=self.__prompt_thread, name="new_game_setup")
        self.__p_thread.setDaemon(True)
        self.__p_thread.start()
        self.__grid_init()

    def start(self):
        self.grid_draw()
        self.__running = True
        self.__tile_grid.grid(column=0, row=0, sticky="nsew")
        # self.x_bar.grid(column=0, row=1, sticky="ew")
        # self.y_bar.grid(column=1, row=0, sticky="ns")
        self.__timer.start()
        print("\nPress \"R\" to restart or \"N\" to change grid size and mine count.\n")
        self.__apply_mines()
        tk_widget_key_bind(self.__root, "r", self.__reset_grid)
        tk_widget_key_bind(self.__root, "n", self.prompt_ng_input)
        while self.__running:
            if self.__reset_call:
                self.__reset_grid()
                self.__reset_call = False
            self.__root.update()

    def __grid_init(self):
        self.__grid = {}
        for x in range(self.__grid_size[0]):
            for y in range(self.__grid_size[1]):
                self.__grid[(x, y)] = {"label": Label(self.__tile_grid, width=32, height=32, borderwidth=0,
                                       highlightthickness=0, image=self.__graphics["blank"]),
                                       "attrs": {"tile": "blank", "mine": False}}
                self.__grid[(x, y)]["label"].bind("<Button-1>", partial(self.__l_click, (x, y)))
                self.__grid[(x, y)]["label"].bind("<Button-2>", partial(self.__r_click, (x, y)))
                self.__grid[(x, y)]["label"].bind("<Button-3>", partial(self.__r_click, (x, y)))

    def __grid_remove(self):
        for key in self.__grid:
            self.__grid[key]["label"].grid_remove()

    def grid_draw(self):
        for x in range(self.__grid_size[0]):
            for y in range(self.__grid_size[1]):
                self.__grid[(x, y)]["label"].grid(column=x+1, row=y+1, padx=0, pady=0)

    def stop(self):
        self.__running = False

    def prompt_ng_input(self):
        self.__ng_prompt = True

    def canvas_resize(self):
        self.__tile_grid.configure(width="")

    def __prompt_thread(self):
        while 1:
            sleep(0.5)
            if self.__ng_prompt:
                print("\n-New game-")
                length = irv("length", (2, self.max_grid_size[0]))
                height = irv("height", (2, self.max_grid_size[1]))
                self.__mine_count = irv("Mines", (1, self.max_grid_size[0] * self.max_grid_size[1] - 1))
                print("")
                self.__grid_size = (length, height)
                self.__reset_call = True
                self.__ng_prompt = False

    def __reset_grid(self):
        self.__timer.stop()
        self.__timer.reset()
        self.__grid_remove()
        self.__grid_init()
        self.grid_draw()
        if not self.__key_lock:
            for g in self.__grid:
                self.__set_tile(g, "blank")
                self.__grid[g]["attrs"]["mine"] = False
                self.__update_tile(g)
            self.__apply_mines()
            self.__set_click_lock(False)
            self.__timer.start()

    def __apply_mines(self):
        mines = 0
        while mines != self.__mine_count:
            co_ord = (randint(0, self.__grid_size[0]-1), randint(0, self.__grid_size[1]-1))
            if not self.__is_mine(co_ord):
                self.__grid[co_ord]["attrs"]["mine"] = True
                mines += 1
        print(f"Started {self.__grid_size[0]}x{self.__grid_size[1]} game with {self.__mine_count} mines")

    def __set_click_lock(self, state: bool):
        self.__click_lock = state

    def __set_key_lock(self, state: bool):
        self.__key_lock = state

    def __update_tile(self, position: Tuple[int, int]):
        self.__grid[position]["label"].configure(image=self.__graphics[self.__grid[position]["attrs"]["tile"]])
        self.__root.update()

    def __tile_search(self, start_position: Tuple[int, int]):
        search = [start_position]
        done = []
        cardinals = MineSweeper.surroundings
        cardinals.append((0, 0))
        while len(search) > 0:
            for s in search:
                for c in cardinals:
                    new_pos = add_tuples(s, c)
                    if self.__position_valid(new_pos):
                        mines = self.__mines_in_proximity(new_pos)
                        if self.__is_tile(new_pos, "blank") and mines == 0:
                            search.append(new_pos) if new_pos not in done else None
                            done.append(new_pos)
                        elif mines != 0:
                            self.__set_tile(new_pos, str(mines))
                            self.__update_tile(new_pos)
                search.remove(s)
        for d in done:
            self.__set_tile(d, "blank_c")
            self.__update_tile(d)

    def __get_game_statistics(self, win: bool):
        if not win:
            flags_correct = 0
            flags_incorrect = 0
            for g in self.__grid:
                if self.__is_mine(g) and self.__is_tile(g, "flag"):
                    flags_correct += 1
                elif not self.__is_mine(g) and self.__is_tile(g, "flag"):
                    flags_incorrect += 1
            print(f"Flagged Mines: {flags_correct}/{self.__mine_count}")
            print(f"Incorrect Flags:", flags_incorrect)
        print(f"Time: {round(self.__timer.get_time('b'), 1)} seconds\n")

    def __mines_in_proximity(self, position: Tuple[int, int]):
        surroundings = MineSweeper.surroundings
        count = 0
        for s in surroundings:
            new_pos = add_tuples(position, s)
            if self.__position_valid(new_pos):
                if self.__is_mine(new_pos):
                    count += 1
        return count

    def __reveal_mines(self):
        self.__set_key_lock(True)
        mine_tiles = []
        for g in self.__grid:
            if self.__is_mine(g) and not self.__is_tile(g, "mine_e"):
                self.__set_tile(g, "mine")
                self.__update_tile(g)
                mine_tiles.append(g)
        shuffle(mine_tiles)
        sleep(1)
        for m in mine_tiles:
            self.__set_tile(m, "mine_e")
            self.__update_tile(m)
            sleep(0.1 if self.__mine_count < 51 else 0.05 if self.__mine_count < 101 else 0.01)
        self.__set_key_lock(False)

    def __reveal_blanks(self):
        for g in self.__grid:
            if not self.__is_mine(g):
                mines = self.__mines_in_proximity(g)
                self.__set_tile(g, "blank_c" if mines == 0 else str(mines))
                self.__update_tile(g)

    def __l_click(self, position: Tuple[int, int], _):
        if not self.__click_lock:
            if self.__is_tile(position, "flag"):
                pass
            elif self.__is_mine(position):
                self.__set_tile(position, "mine_e")
                self.__update_tile(position)
                print("You Lose.")
                self.__get_game_statistics(False)
                self.__set_click_lock(True)
                self.__reveal_mines()
            elif self.__mines_in_proximity(position) != 0:
                self.__set_tile(position, str(self.__mines_in_proximity(position)))
                self.__update_tile(position)
            else:
                self.__tile_search(position)

    def __r_click(self, position: Tuple[int, int], _):
        if not self.__click_lock:
            if self.__get_tile(position) == "blank":
                self.__set_tile(position, "flag")
            elif self.__get_tile(position) == "flag":
                self.__set_tile(position, "blank")
            self.__update_tile(position)
            win = True
            for g in self.__grid:
                if self.__is_mine(g):
                    if not self.__is_tile(g, "flag"):
                        win = False
                elif self.__is_tile(g, "flag"):
                    win = False
            if win:
                print("You Win!")
                self.__get_game_statistics(True)
                self.__reveal_blanks()
                self.__set_click_lock(True)

    def __get_tile(self, position: Tuple[int, int]):
        return self.__grid[position]["attrs"]["tile"]

    def __set_tile(self, position: Tuple[int, int], tile: str):
        self.__grid[position]["attrs"]["tile"] = tile

    def __is_tile(self, position: Tuple[int, int], tile: str):
        return self.__get_tile(position) == tile

    def __is_mine(self, position: Tuple[int, int]):
        return self.__grid[position]["attrs"]["mine"]

    def __position_valid(self, position: Tuple[int, int]):
        return True if 0 <= position[0] < self.__grid_size[0] and 0 <= position[1] < self.__grid_size[1] else False


if __name__ == '__main__':
    resolution = (1024, 1080)
    game = MineSweeper((15, 15), 50, resolution)
    game.start()
