#!/usr/bin/env python
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
        self.x = 0
        self.y = 0
        self.pointer = SDL_Rect(0, 0, 10, 10)
        self.clicking = False
        self.r_clicking = False

    def Compute(self, event):
        self.clicking = False
        self.r_clicking = False

        if (event.type == SDL_MOUSEBUTTONDOWN):
            if (event.button.button == SDL_BUTTON_LEFT):
                self.clicking = True

            if (event.button.button == SDL_BUTTON_RIGHT):
                self.r_clicking = True
        
        if (event.type == SDL_MOUSEBUTTONUP):
            if (event.button.button == SDL_BUTTON_LEFT):
                self.clicking = False
            
            if (event.button.button == SDL_BUTTON_RIGHT):
                self.r_clicking = False

        if (event.type == SDL_MOUSEMOTION):
            self.pointer.x = event.motion.x
            self.pointer.y = event.motion.y

        self.x = self.pointer.x
        self.y = self.pointer.y

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
    def __init__(self, renderer, text, width, height, font_name, color = (0, 0, 0), location = (0, 0), font_size = 36):
        self.r = renderer
        if len(font_name) > 1:
            TextObject.fonts[font_name[0]] = TTF_OpenFont(font_name[1], font_size)
        self.color = SDL_Color(color[0], color[1], color[2])
        self.surface = TTF_RenderText_Solid(TextObject.fonts[font_name[0]], text.encode('utf-8'), self.color)
        self.message = SDL_CreateTextureFromSurface(self.r, self.surface)
        SDL_FreeSurface(self.surface)
        self.rect = SDL_Rect(location[0], location[1], width, height)
        self.highlight = False

    def Render(self, x=None, y=None):
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


class DynamicTextObject: #This class allows for constantly updating text to be rendered efficiently on screen
    def __init__(self, renderer, font, size, colors = [(0,0,0)]):
        self.r = renderer
        self.font = TTF_OpenFont(font.encode('utf-8'), size)
        self.colors = dict()

        for color in colors:
            self.colors[color] = dict()
            for i in range(32, 126): #Now this converts the ascii values into the characters they represent
                char = chr(i)
                if char not in self.colors[color]:
                    surface = TTF_RenderText_Solid(self.font, char.encode('utf-8'), SDL_Color(color[0], color[1], color[2], 255))
                    self.colors[color][char] = SDL_CreateTextureFromSurface(self.r, surface)
                    SDL_FreeSurface(surface)

    def RenderText(self, text, location, color = (0,0,0), offset = 0):
        d_rect = SDL_Rect(location[0], location[1], location[2], location[3])
        for char in text:
            SDL_RenderCopy(self.r, self.colors[color][char], None, d_rect)
            d_rect.x += location[2] + offset
        del d_rect

    def __del__(self):
        for color in list(self.colors):
            for char in list(self.colors[color]):
                SDL_DestroyTexture(self.colors[color][char])
        TTF_CloseFont(self.font)


class TextureCache:
    def __init__(self, renderer):
        self.renderer = renderer
        self._cache = dict()

    def LoadTexture(self, filepath):
        if filepath not in self._cache:
            surface = SDL_LoadBMP(filepath.encode('utf-8'))
            self._cache[filepath] = SDL_CreateTextureFromSurface(self.renderer, surface)
            SDL_FreeSurface(surface)
            SDL_SetTextureBlendMode(self._cache[filepath], SDL_BLENDMODE_BLEND)
        return self._cache[filepath]

    def __del__(self):
        for file in list(self._cache):
            SDL_DestroyTexture(self._cache[file])


class GameTile:
    def __init__(self, cache, filepath, x, y, w, h):
        self.c = cache
        self.name = filepath.split('.bmp')[0]
        self.texture = self.c.LoadTexture(filepath)
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.rect = SDL_Rect(self.x, self.y, self.w, self.h)

    def Render(self, camera_pos = (0,0), alpha = 255):
        self.rect.x = self.x + camera_pos[0]
        self.rect.y = self.y + camera_pos[1]
        SDL_SetTextureAlphaMod(self.texture, alpha)
        SDL_RenderCopy(self.c.renderer, self.texture, None, self.rect)

    def SetPos(self, x, y):
        self.x = x
        self.y = y

    def GetPos(self):
        return (self.x, self.y)

    def Collide(self): #Either making a function to handle solid and soft tiles or make an entirely different class just for GameObjects
        pass

    def GetInfo(self):
        return (self.x, self.y, self.w, self.h)


class Camera:
    def __init__(self, w, h, speed, cs = 40):
        self.x = 0
        self.y = 0
        self.speed = speed
        self.cs = cs
        self._rect = SDL_Rect(self.cs // 2, self.cs // 2, w - self.cs, h - self.cs)

    def Show(self, renderer):
        SDL_SetRenderDrawColor(renderer, 0, 0, 255, 255)
        SDL_RenderDrawRect(renderer, self._rect)


class Clock:
    def __init__(self):
        self.last_time = 0
        self.current_time = SDL_GetPerformanceCounter()
        self.dt = 0
        self.dt_s = 0
        self.s = 0
        self.count = 0.0

    def Tick(self):
        self.last_time = self.current_time
        self.current_time = SDL_GetPerformanceCounter()
        self.dt = (self.current_time - self.last_time) * 1000 / SDL_GetPerformanceFrequency()
        self.dt_s = self.dt * .001


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


def Get_Resources():
    resources = []
    for path in os.listdir('./resources/'):
        c = path.split(".bmp")
        resources.append(c[0])

    return resources


def Get_Paths():      #Function returns a dictionary of filepaths to easily reference them with the block selection.  Key: (Block Name) Value: (Block Filepath)
    path = 'resources/'
    paths = dict()

    for l in os.listdir(path):
        c = l.split(".bmp")
        paths[c[0]] = path + l
    
    return paths


def SavetoFile(filepath, tile_filepaths, b_cache, tile_per_line = 10):
    #This function saves the locations of the tiles, and where they are placed, to the .mx file
    file = open(filepath, "w+")
    for tile_type in b_cache:
        file.write('*|'+tile_type+":"+tile_filepaths[tile_type]+':'+'\n')
        line = '+|'
        i = 0
        for tile in b_cache[tile_type]:
            if i == tile_per_line:
                line += '\n'
                file.write(line)
                line = '+|'
                i = 0
            info = tile.GetInfo()
            line += str(info[0]) + '-' + str(info[1]) + '-' + \
                    str(info[2]) + '-' + str(info[3]) + ','
            i += 1

        if (len(line) >= 1):
            line += '\n'
            file.write(line)

    file.close()

def LoadFromFile(filepath, b_cache, cache):
    #This function loads the map created from the ".mx" file specified.
    global tile_name
    global tile_filepath

    if len(filepath.split('\\')) > 1:
        if('.mx' not in filepath.split('\\')[-1]):
            return 0
    else:
        if('.mx' not in filepath.split('/')[-1]):
            return 0

    file = open(filepath, 'r')
    tile_name = ''
    tile_filepath = ''
    for line in file:
        section = line.split('|')
        if (section[0] == '*'):
            subsect = section[1].split(':')
            tile_name = subsect[0]
            tile_filepath = subsect[1]

        elif (section[0] == '+'):
            tiles_information_list = section[1].split(',')
            for tile_info in tiles_information_list:
                tile_xywh = tile_info.split('-')
                if (len(tile_xywh) < 4):
                    pass
                else:
                    x = int(tile_xywh[0])
                    y = int(tile_xywh[1])
                    w = int(tile_xywh[2])
                    h = int(tile_xywh[3])
                    if tile_name not in b_cache:
                        b_cache[tile_name] = [GameTile(cache, tile_filepath, x, y, w, h)]
                    else:
                        b_cache[tile_name].append(GameTile(cache, tile_filepath, x, y, w, h))
    file.close()

    if (len(b_cache) ==0):
        return 0
    return 1

# MAIN_______________________________________________________________________________
def main():
    if (TTF_Init() < 0):
        print(TTF_GetError())
        return -1

    if (SDL_Init(SDL_INIT_VIDEO | SDL_INIT_EVENTS) < 0):
        print(SDL_GetError())
        return -1

    window = SDL_CreateWindow(b"Map Editor - By Sardonicals", SDL_WINDOWPOS_UNDEFINED, SDL_WINDOWPOS_UNDEFINED,
                              WIDTH, HEIGHT, SDL_WINDOW_RESIZABLE)
    renderer = SDL_CreateRenderer(window, -1, SDL_RENDERER_ACCELERATED)
    event = SDL_Event()

    # VARIABLES/STATES_________________________________
    running = True
    game_state = "MENU"
    paused = False
    sub_menu = False
    creating_item = False
    map_name = b''
    tiles = Get_Resources()
    tile_fp = Get_Paths()
    current_item = None
    placement = False
    ghost_tile = None
    tile_size = (32, 32)
    show_size = True
    error_message = False
    show_file_saving = False
    timer = 0
    filepath = ''


    # OBJECTS____________________________________________
    mouse = Pointer()
    camera = Camera(WIDTH, HEIGHT, 3)
    menu_items = {
        "Title": TextObject(renderer, "Map Editor", 400, 190, ['arcade', b'font/arcade.ttf'], location=(200, 100)),
        "New Map": TextObject(renderer, "Create  Map", 200, 50, ['arcade'], location=(280, 320)),
        "Load Map": TextObject(renderer, "Load  Map", 160, 50, ['arcade'], location=(290, 380)),
        "Quit": TextObject(renderer, "Quit", 80, 50, ['arcade'], location=(330, 440)),
    }

    editor_items = {
        "Resources": TextObject(renderer, "Items", 80, 50, ['arcade'], location=(650, 530)),
        "Save": TextObject(renderer, "Save  File", 100, 50, ['arcade'], location = (510, 530))
    }

    cache = TextureCache(renderer)
    block_cache = dict()
    text_renderer = DynamicTextObject(renderer, 'font/joystix.ttf', size = 9,
                                      colors = [(0,0,0), (140,140,140), (255,255,255)])

    l = [650, 200]
    for block in tiles:
        editor_items[block] = TextObject(renderer, block, 80, 50, ['arcade'], location=l)
        l[1] += 50

    clock = Clock()

    # APPLICATION LOOP___________________________________
    while (running):
        clock.Tick()
        keystate = SDL_GetKeyboardState(None)
        mouse.clicking = False
        # EVENT LOOP______________________________
        while (SDL_PollEvent(ctypes.byref(event))):
            mouse.Compute(event)
            if (event.type == SDL_QUIT):
                running = False
                break

            if (event.type == SDL_WINDOWEVENT):
                if (event.window.event == SDL_WINDOWEVENT_RESIZED):
                    SDL_RenderSetLogicalSize(renderer, WIDTH, HEIGHT)

            if (game_state == 'NAMING'):

                if (event.type == SDL_TEXTINPUT):
                    map_name += event.text.text

                if (event.type == SDL_KEYDOWN):
                    if (event.key.keysym.scancode == SDL_SCANCODE_BACKSPACE):
                        map_name = str().join(list(map_name.decode('utf-8'))[0:-1])
                        map_name = map_name.encode('utf-8')

            if (game_state == 'LOADING'):
                if (event.type == SDL_DROPFILE):
                    file = event.drop.file
                    filepath = file.decode()


        # LOGIC_____________________________________________
        # menu__________________________________________
        if (game_state == 'MENU'):
            for item in menu_items:
                if item == "Title":
                    pass
                elif mouse.Is_Touching(menu_items[item]):
                    menu_items[item].highlight = True
                else:
                    menu_items[item].highlight = False

            if mouse.Is_Clicking(menu_items['New Map']):
                game_state = 'NAMING'
                map_name = b'untitled'
                SDL_StartTextInput()

            if mouse.Is_Clicking(menu_items['Load Map']):
                game_state = 'LOADING'

            if mouse.Is_Clicking(menu_items['Quit']):
                running = False
                break

        # naming____________________________________
        if (game_state == 'NAMING'):

            if (keystate[SDL_SCANCODE_RETURN]):
                if (len(map_name.decode().split()) == 0):
                    error_message = True
                else:
                    error_message = False
                    game_state = 'EDITING'
                    map_name = map_name.decode() + '.mx'
                    map_name = map_name.encode('utf-8')
                    SDL_SetWindowTitle(window, map_name + b' - Map Editor')
                    mouse.Set_Cursor(SDL_SYSTEM_CURSOR_CROSSHAIR)
                    SDL_StopTextInput()

        #loading____________________________________
        if (game_state == 'LOADING'):
            if filepath:
                error_message = False
            if (keystate[SDL_SCANCODE_RETURN]):
                if not filepath:
                    error_message = True
                else:
                    if len(filepath.split('\\')) > 1:
                        map_name = filepath.split('\\')[-1].encode('utf-8')
                    else:
                        map_name = filepath.split('/')[-1].encode('utf-8')

                    if (LoadFromFile(filepath, block_cache, cache)):
                        SDL_SetWindowTitle(window, map_name + b' - Map Editor')
                        mouse.Set_Cursor(SDL_SYSTEM_CURSOR_CROSSHAIR)
                        game_state = 'EDITING'

        # editing________________________________
        if (game_state == 'EDITING'):
            placement = True

            #camera speed
            if keystate[SDL_SCANCODE_UP]:
                camera.y += camera.speed
            if keystate[SDL_SCANCODE_DOWN]:
                camera.y -= camera.speed
            if keystate[SDL_SCANCODE_LEFT]:
                camera.x += camera.speed
            if keystate[SDL_SCANCODE_RIGHT]:
                camera.x -= camera.speed

            #main editor option highighting
            for item in editor_items:
                if item == 'Resources' or item == 'Save':
                    if mouse.Is_Touching(editor_items[item]):
                        editor_items[item].highlight = True
                    else:
                        editor_items[item].highlight = False

            #editor file saving
            if mouse.Is_Clicking(editor_items['Save']):
                show_file_saving = True
                SavetoFile("./saved/"+map_name.decode(), tile_fp, block_cache)

            # managing sub menu stuff
            if (mouse.Is_Clicking(editor_items['Resources'])):
                if (sub_menu):
                    sub_menu = False
                else:
                    sub_menu = True

            for item in editor_items:
                if (mouse.Is_Touching(editor_items['Resources'])
                or (mouse.Is_Touching(editor_items['Save']))
                or (mouse.Is_Touching(editor_items[item]) and sub_menu)):
                    placement = False

            #sub menu option highlighting
            if (sub_menu):
                editor_items['Resources'].highlight = True
                for item in editor_items:
                    if item == 'Resources' or item == 'Save':
                        pass
                    elif (mouse.Is_Touching(editor_items[item])):
                        editor_items[item].highlight = True
                    else:
                        editor_items[item].highlight = False

            #main editor functionality
            for item in editor_items:
                if (item == 'Resources' or item == 'Save'):
                    pass
                elif (mouse.Is_Clicking(editor_items[item]) and sub_menu):
                    current_item = item    #Sets the block selected in submenu to the current_item
                    ghost_tile = GameTile(cache, tile_fp[current_item], mouse.x, mouse.y, tile_size[0], tile_size[1])
                
            if (current_item) and (mouse.clicking) and (placement): #Properly places game tile onto surface.
                if current_item not in block_cache:
                    block_cache[current_item] = [GameTile(cache, tile_fp[current_item], mouse.x + (-1 * camera.x),
                                                          mouse.y + (-1 * camera.y), tile_size[0], tile_size[1])]
                else:
                    block_cache[current_item].append(GameTile(cache, tile_fp[current_item], mouse.x + (-1 * camera.x),
                                                              mouse.y + (-1 * camera.y), tile_size[0], tile_size[1]))

            if (ghost_tile):
                ghost_tile.SetPos(mouse.x, mouse.y)

            if (keystate[SDL_SCANCODE_X]):
                current_item = None
                ghost_tile = None


        # RENDERING_______________________________________
        SDL_SetRenderDrawColor(renderer, 220, 220, 220, 255)
        SDL_RenderClear(renderer)

        # menu________________________________________
        if (game_state == 'MENU'):
            for item in menu_items:
                menu_items[item].Render()

        # naming_______________________________________
        if (game_state == 'NAMING'):
            text_renderer.RenderText('Enter File Name: ' + map_name.decode() + '(.mx)', (WIDTH//4, HEIGHT//2, 10, 25))

            if (error_message):
                text_renderer.RenderText("You have to have a file name",
                                         location = ((WIDTH // 4),(HEIGHT//2) + 20, 10, 25 ),
                                         color = (140,140,140))

        # loading_____________________________________
        if (game_state == 'LOADING'):
            text_renderer.RenderText('Drag and drop your file and press enter to load.',
                                     (100, (HEIGHT // 2) - 60, 10, 25),
                                     color = (255,255,255))
            text_renderer.RenderText('file has to be a (.mx) file',
                                     (100, (HEIGHT // 2) - 40, 10, 25),
                                     color = (255, 255, 255))

            text_renderer.RenderText('File: ' + filepath,
                                     (100, HEIGHT // 2, 10, 25))
            if (error_message):
                text_renderer.RenderText("You have to load a file",
                                         location=((WIDTH // 4), (HEIGHT // 2) + 20, 10, 25),
                                         color=(140, 140, 140))
        # editing______________________________________
        if (game_state == 'EDITING'):

            for block in block_cache:
                for x in block_cache[block]:
                    x.Render((camera.x, camera.y))

            editor_items['Resources'].Render()
            editor_items['Save'].Render()

            if (sub_menu):
                for item in editor_items:
                    if item == "Resources" or item == "Save":
                        pass
                    else:
                        editor_items[item].Render()

            if (ghost_tile):
                ghost_tile.Render(alpha = 100) #Does ghost tile effect if block is selected from sub menu

            if (current_item):
                text_renderer.RenderText(text = 'Block Location (x, y): '+ #This renderes the absolute x and y position of the block being placed
                                       str(mouse.x + (-1 * camera.x)) + ', '+ str(mouse.y + (-1 * camera.y)),
                                       location = (40, 560, 10, 15))
                if (show_size):
                    text_renderer.RenderText (text = '(' + str(tile_size[0]) + ',' + str(tile_size[1])+ ')',
                                          location = (mouse.x - 20, mouse.y - 20, 7, 10))

            if (show_file_saving):
                timer += clock.dt_s
                text_renderer.RenderText("Saving text file...", location=(40, 20, 10, 25),
                                         color=(140, 140, 140))
                if (timer >= 1):
                    show_file_saving = False
                    timer = 0

            camera.Show(renderer)

        SDL_RenderPresent(renderer)
        SDL_Delay(10)

    del text_renderer
    Deleter([menu_items])
    SDL_DestroyRenderer(renderer)
    SDL_DestroyWindow(window)
    SDL_Quit()
    TTF_Quit()


main()
