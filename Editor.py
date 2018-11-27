# -*- coding: utf-8 -*
import os
os.environ["PYSDL2_DLL_PATH"] = os.path.dirname(os.path.abspath(__file__))
from sdl2 import *
from sdl2.sdlttf import *
import ctypes
# Editor by Sardonicals

# GLOBALS___________________________________________________________________________
WIDTH = 800
HEIGHT = 600


# CLASSES___________________________________________________________________________
class Pointer:
    cursors = dict()

    def __init__(self):
        self.pointer = SDL_Rect(0, 0, 10, 10)
        self.clicking = False
        self.r_clicking = False

    def Compute(self, event):
        self.clicking = False
        self.r_clicking = False

        if(event.type == SDL_MOUSEBUTTONDOWN):
            if(event.button.button == SDL_BUTTON_LEFT):
                self.clicking = True

            if(event.button.button == SDL_BUTTON_RIGHT):
                self.r_clicking = True

        if(event.type == SDL_MOUSEMOTION):
            self.pointer.x = event.motion.x
            self.pointer.y = event.motion.y

    def Is_Touching(self, item):
        return SDL_HasIntersection(self.pointer, item.rect)

    def Is_Clicking(self, item):
        return self.Is_Touching(item) and self.clicking

    def Is_R_Clicking(self, item):
        return self.Is_Touching(item) and self.r_clicking

    def Set_Cursor(self, id):
        if id not in Pointer.cursors:
            Pointer.cursors[id] = SDL_CreateSystemCursor(id)
        SDL_SetCursor(Pointer.cursors[id])

    def __del__(self):
        for cursor in Pointer.cursors:
            SDL_FreeCursor(Pointer.cursors[cursor])


class TextObject:
    fonts = dict()

    def __init__(self, renderer, text, width, height,
                font_name, color = (0, 0, 0), location = (0, 0), font_size = 36):
        self.r = renderer
        if len(font_name) > 1:
            TextObject.fonts[font_name[0]] = TTF_OpenFont(font_name[1], font_size)
        self.color = SDL_Color(color[0], color[1], color[2])
        self.surface = TTF_RenderText_Solid(TextObject.fonts[font_name[0]], text.encode('utf-8'), self.color)
        self.message = SDL_CreateTextureFromSurface(self.r, self.surface)
        SDL_FreeSurface(self.surface)
        self.rect = SDL_Rect(location[0], location[1], width, height)
        self.highlight = False

    def Render(self, x = None, y = None):
        if self.highlight:
            SDL_SetRenderDrawColor(self.r, self.color.r, self.color.g, self.color.b, self.color.a)
            SDL_RenderDrawRect(self.r, self.rect)
        if x is None and y:
            self.rect.y = y
        elif x and y is None:
            self.rect.x = x
        elif x and y:
            self.rect.x = x
            self.rect.y = y
        SDL_RenderCopy(self.r, self.message, None, self.rect)

    def __del__(self):
        for keys in list(TextObject.fonts):
            font = TextObject.fonts.pop(keys, None)
            if font: TTF_CloseFont(font)
        SDL_DestroyTexture(self.message)


class Camera:
    def __init__(self, w, h, speed):
        self.x = 0
        self.y = 0
        self.speed = speed
        cs = 40
        self._rect = SDL_Rect(cs // 2, cs // 2, w-cs, h-cs)

    def Show(self, renderer):
        SDL_SetRenderDrawColor(renderer, 0, 0, 255, 255)
        SDL_RenderDrawRect(renderer, self._rect)


# FUNCTIONS_________________________________________________________________________
def WindowState(window, renderer, fs):
    if not fs:
        SDL_SetWindowFullscreen(window, 0)

    elif fs:
        SDL_SetWindowFullscreen(window, SDL_WINDOW_FULLSCREEN_DESKTOP)
        SDL_RenderSetLogicalSize(renderer, WIDTH, HEIGHT)


def Deleter(dictionary_list):
    for dictionary in dictionary_list:
        for item in list(dictionary):
            del dictionary[item]


# MAIN_______________________________________________________________________________
def main():
    if (TTF_Init() < 0):
        print(TTF_GetError())

    if (SDL_Init(SDL_INIT_VIDEO | SDL_INIT_EVENTS) < 0):
        print(SDL_GetError())

    window = SDL_CreateWindow(b"Map Editor - By Sardonicals", SDL_WINDOWPOS_UNDEFINED, SDL_WINDOWPOS_UNDEFINED,
                              WIDTH, HEIGHT, SDL_WINDOW_SHOWN)
    renderer = SDL_CreateRenderer(window, -1, SDL_RENDERER_ACCELERATED)
    event = SDL_Event()

    # Boolean States/Variables____________________________
    running = True
    menu = True
    editing = False
    paused = False
    map_name = b'untitled.mx'

    # Objects____________________________________________
    mouse = Pointer()
    camera = Camera(WIDTH, HEIGHT, 6)
    menu_items = {
    "Title":     TextObject(renderer, "Map Editor", 400, 190, ['arcade', 'font/arcade.ttf'], location = (200, 100)),
    "New Map":   TextObject(renderer, "Create  Map", 200, 50, ['arcade'], location = (280, 320)),
    "Load Map":  TextObject(renderer, "Load  Map", 160, 50, ['arcade'], location = (290, 380)),
    "Quit":      TextObject(renderer, "Quit", 80, 50, ['arcade'], location = (330, 440)),
        }

    # Application Loop___________________________________
    while(running):
        keystate = SDL_GetKeyboardState(None)

        # Event Loop______________________________
        while(SDL_PollEvent(ctypes.byref(event))):
            mouse.Compute(event)
            if (event.type == SDL_QUIT):
                running = False
                break

        # Application Logic______________________________

        # menu__________________________________________
        if (menu):
            for item in menu_items:
                if item == "Title":
                    pass
                elif mouse.Is_Touching(menu_items[item]):
                    menu_items[item].highlight = True
                else:
                    menu_items[item].highlight = False

            if mouse.Is_Clicking(menu_items['New Map']):
                menu = False
                editing = True
                mouse.Set_Cursor(SDL_SYSTEM_CURSOR_CROSSHAIR)

            if mouse.Is_Clicking(menu_items['Quit']):
                running = False
                break

        # editing________________________________
        if (editing):
            SDL_SetWindowTitle(window, map_name + b' ― Map Editor')
            if keystate[SDL_SCANCODE_UP]:
                camera.y += camera.speed
            if keystate[SDL_SCANCODE_DOWN]:
                camera.y -= camera.speed
            if keystate[SDL_SCANCODE_LEFT]:
                camera.x += camera.speed
            if keystate[SDL_SCANCODE_RIGHT]:
                camera.x -= camera.speed

        # Rendering_______________________________________
        SDL_SetRenderDrawColor(renderer, 220, 220, 220, 255)
        SDL_RenderClear(renderer)

        # menu________________________________________
        if (menu):
            for item in menu_items:
                menu_items[item].Render()

        # editing______________________________________
        if (editing):
            camera.Show(renderer)

        SDL_RenderPresent(renderer)
        SDL_Delay(10)

    Deleter([menu_items])
    SDL_DestroyRenderer(renderer)
    SDL_DestroyWindow(window)
    SDL_Quit()
    TTF_Quit()


main()
