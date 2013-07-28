#!/usr/bin/python
#!/usr/bin/python
#
# libtcod prototype roguelike
#

import textwrap
import shelve
from proto_rogue_mod import *

class GameWindow (object):
  def __init__(self):
    messenger.window=self
    libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'Rogue Prototype', False)
    libtcod.sys_set_fps(LIMIT_FPS)#create object representing the player
    self.con = libtcod.console_new(SCREEN_WIDTH, SCREEN_HEIGHT)
    self.panel = libtcod.console_new(SCREEN_WIDTH, PANEL_HEIGHT)

    self.game_msgs=[]

    self.mouse = libtcod.Mouse()
    self.key = libtcod.Key()
  def new_game(self):
    libtcod.console_clear(self.con)
    self.game_msgs = []
    self.dungeon_level = 0

    #self.map=Map(self.dungeon_level)

    self.game_state='playing'

    self.player = Player(0, 0)

    self.newMap()

    #the list of objects with those two
    #self.map.objects.append(self.player)

    self.fov_recompute=True
 
    #a warm welcoming message!
    self.message('Welcome stranger! Prepare to perish in the Tombs of the Ancient Kings.', libtcod.red)
  def main_loop(self):
    while not libtcod.console_is_window_closed():
      #check for any events
      libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS|libtcod.EVENT_MOUSE, self.key, self.mouse)

      #render the screen
      self.render()

      #handle keys and exit game if needed
      player_action = self.handle_keys()
      if player_action=='exit':
          break

      #let monsters take their turn
      if self.game_state == 'playing' and player_action != 'didnt-take-turn':
        for obj in self.map.objects:
          if obj != self.player and isinstance(obj, Creature):
            obj.turn(self.map, self.player, libtcod.map_is_in_fov(self.map.fov_map, obj.x, obj.y))
        for obj in self.map.objects:
          if obj.destroyed:
            obj.death_effects(self, self.map, self.player)
            self.map.objects.remove(obj)
  def player_death(self):
    #the game ended!
    messenger.window.message('You died!', libtcod.red)
    self.game_state = 'dead'
 
    #for added effect, transform the player into a corpse!
    self.player.char = '%'
    self.player.color = libtcod.dark_red
  def newMap(self):
    self.dungeon_level+=1

    self.map=Map(MAP_WIDTH, MAP_HEIGHT, self.dungeon_level)

    self.player.x=self.map.startx
    self.player.y=self.map.starty

    self.map.objects.append(self.player)

    if self.dungeon_level!=1:
      #advance to the next level
      self.message('You take a moment to rest, and recover your strength.', libtcod.light_violet)
      self.player.heal(self.player.max_hp / 2)  #heal the player by 50%

    libtcod.console_print_ex(self.panel, 1, 3, libtcod.BKGND_NONE, libtcod.LEFT, 'Dungeon level ' + str(self.dungeon_level))
 
    libtcod.console_clear(self.con)  #unexplored areas start black (which is the default background color)

    self.fov_recompute=True
  def handle_keys(self):
    if self.key.vk == libtcod.KEY_ENTER and self.key.lalt:
        #Alt+Enter: toggle fullscreen
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
 
    elif self.key.vk == libtcod.KEY_ESCAPE:
        return 'exit'  #exit game

    if self.game_state=='playing':
      #movement keys
      if self.key.vk == libtcod.KEY_UP or self.key.vk == libtcod.KEY_KP8:
        self.player.move(self.map, 0, -1)
        self.fov_recompute = True
      elif self.key.vk == libtcod.KEY_DOWN or self.key.vk == libtcod.KEY_KP2:
        self.player.move(self.map, 0, 1)
        self.fov_recompute = True
      elif self.key.vk == libtcod.KEY_LEFT or self.key.vk == libtcod.KEY_KP4:
        self.player.move(self.map, -1, 0)
        self.fov_recompute = True
      elif self.key.vk == libtcod.KEY_RIGHT or self.key.vk == libtcod.KEY_KP6:
        self.player.move(self.map, 1, 0)
        self.fov_recompute = True
      elif self.key.vk == libtcod.KEY_HOME or self.key.vk == libtcod.KEY_KP7:
        self.player.move(self.map, -1, -1)
        self.fov_recompute = True
      elif self.key.vk == libtcod.KEY_PAGEUP or self.key.vk == libtcod.KEY_KP9:
        self.player.move(self.map, 1, -1)
        self.fov_recompute = True
      elif self.key.vk == libtcod.KEY_END or self.key.vk == libtcod.KEY_KP1:
        self.player.move(self.map, -1, 1)
        self.fov_recompute = True
      elif self.key.vk == libtcod.KEY_PAGEDOWN or self.key.vk == libtcod.KEY_KP3:
        self.player.move(self.map, 1, 1)
        self.fov_recompute = True
      elif self.key.vk == libtcod.KEY_KP5:
        pass  #do nothing ie wait for the monster to come to you
      else:
        #test for other keys
        key_char = chr(self.key.c)
        if key_char == '>' or key_char == '<' or key_char == 'c':
          if isinstance(self.map.map[self.player.x][self.player.y], Stair):
              self.newMap()
          else:
              return 'didnt-take-turn'
        elif key_char == 'x' or key_char == 'g':
          objects_at=self.map.getObjectsAt(self.player.x, self.player.y)
          if len(objects_at)<2: # Remember, player is always here
            return 'didnt-take-turn'
          else:
            for obj in objects_at:
              if obj!=self.player:
                self.message('You take the '+obj.name+'.', libtcod.light_violet)
                self.player.getItem(obj)
        elif key_char == 'z' or key_char == 'u':
          chosen_item = self.inventory_menu('Press the key next to an item to use it, or any other to cancel.\n')
          if chosen_item is not None:
            chosen_item.use()
          else:
            return 'didnt-take-turn'
        elif key_char == 'a' or key_char == 'd':
          chosen_item = self.inventory_menu('Press the key next to an item to drop it, or any other to cancel.\n')
          if chosen_item is not None:
            self.message('You drop the '+chosen_item.name+'.', libtcod.light_violet)
            self.map.getItem(chosenItem)
          else:
            return 'didnt-take-turn'
        else:
          return 'didnt-take-turn'
  def get_names_under_mouse(self):
    #return a string with the names of all objects under the mouse
    (x, y) = (self.mouse.cx, self.mouse.cy)
 
    #create a list with the names of all objects at the mouse's coordinates and in FOV
    names = [obj.name for obj in self.map.objects
        if obj.x == x and obj.y == y and libtcod.map_is_in_fov(self.map.fov_map, obj.x, obj.y)]
 
    names = ', '.join(names)  #join the names, separated by commas
    return names.capitalize()
  def render(self):
    self.render_map()
    self.render_panel()

    libtcod.console_flush()

    #erase all objects at their old locations, before they move
    for object in self.map.objects:
      object.clear(self.con)
  def render_bar(self, x, y, total_width, name, value, maximum, bar_color, back_color):
    #render a bar (HP, experience, etc). first calculate the width of the bar
    bar_width = int(float(value) / maximum * total_width)
 
    #render the background first
    libtcod.console_set_default_background(self.panel, back_color)
    libtcod.console_rect(self.panel, x, y, total_width, 1, False, libtcod.BKGND_SCREEN)
 
    #now render the bar on top
    libtcod.console_set_default_background(self.panel, bar_color)
    if bar_width > 0:
        libtcod.console_rect(self.panel, x, y, bar_width, 1, False, libtcod.BKGND_SCREEN)
 
    #finally, some centered text with the values
    libtcod.console_set_default_foreground(self.panel, libtcod.white)
    libtcod.console_print_ex(self.panel, x + total_width / 2, y, libtcod.BKGND_NONE, libtcod.CENTER,
        name + ': ' + str(value) + '/' + str(maximum))
  def render_panel(self):
    #prepare to render the GUI panel
    libtcod.console_set_default_background(self.panel, libtcod.black)
    libtcod.console_clear(self.panel)
 
    #print the game messages, one line at a time
    y = 1
    for (line, color) in self.game_msgs:
        libtcod.console_set_default_foreground(self.panel, color)
        libtcod.console_print_ex(self.panel, MSG_X, y, libtcod.BKGND_NONE, libtcod.LEFT, line)
        y += 1
 
    #show the player's stats
    self.render_bar(1, 1, BAR_WIDTH, 'HP', self.player.hp, self.player.max_hp,
        libtcod.light_red, libtcod.darker_red)
 
    #display names of objects under the mouse
    libtcod.console_set_default_foreground(self.panel, libtcod.light_gray)
    libtcod.console_print_ex(self.panel, 1, 0, libtcod.BKGND_NONE, libtcod.LEFT, self.get_names_under_mouse())
 
    #blit the contents of "panel" to the root console
    libtcod.console_blit(self.panel, 0, 0, SCREEN_WIDTH, PANEL_HEIGHT, 0, 0, PANEL_Y)
  def render_map(self):
    if self.fov_recompute:
        #recompute FOV if needed (the player moved or something)
        self.fov_recompute = False
        libtcod.map_compute_fov(self.map.fov_map, self.player.x, self.player.y, TORCH_RADIUS, FOV_LIGHT_WALLS, FOV_ALGO)
 
        #go through all tiles, and set their background color according to the FOV
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                visible = libtcod.map_is_in_fov(self.map.fov_map, x, y)
                wall = self.map.map[x][y].block_sight
                if not visible:
                    #if it's not visible right now, the player can only see it if it's explored
                    if self.map.explored[x][y]:
                       libtcod.console_put_char_ex(self.con, x, y, self.map.map[x][y].char, self.map.map[x][y].fg, color_dark_ground)
                else:
                    #it's visible
                    libtcod.console_put_char_ex(self.con, x, y, self.map.map[x][y].char, self.map.map[x][y].fg, color_light_ground)
                    #since it's visible, explore it
                    self.map.explored[x][y] = True
 
    #draw all objects in the list
    for obj in self.map.objects:
      #only show if it's visible to the player; or it's set to "always visible" and on an explored tile
      if (libtcod.map_is_in_fov(self.map.fov_map, obj.x, obj.y) or (obj.always_visible and self.map.explored[obj.x][obj.y])):
        obj.draw(self.con)
 
    #blit the contents of "con" to the root console
    libtcod.console_blit(self.con, 0, 0, MAP_WIDTH, MAP_HEIGHT, 0, 0, 0)
  def menu(self, header, options, width):
    if len(options) > 26: raise ValueError('Cannot have a menu with more than 26 options.')
 
    #calculate total height for the header (after auto-wrap) and one line per option
    header_height = libtcod.console_get_height_rect(self.con, 0, 0, width, SCREEN_HEIGHT, header)
    if header == '':
        header_height = 0
    height = len(options) + header_height
 
    #create an off-screen console that represents the menu's window
    window = libtcod.console_new(width, height)
 
    #print the header, with auto-wrap
    libtcod.console_set_default_foreground(window, libtcod.white)
    libtcod.console_print_rect_ex(window, 0, 0, width, height, libtcod.BKGND_NONE, libtcod.LEFT, header)
 
    #print all the options
    y = header_height
    letter_index = ord('a')
    for option_text in options:
        text = '(' + chr(letter_index) + ') ' + option_text
        libtcod.console_print_ex(window, 0, y, libtcod.BKGND_NONE, libtcod.LEFT, text)
        y += 1
        letter_index += 1
 
    #blit the contents of "window" to the root console
    x = SCREEN_WIDTH/2 - width/2
    y = SCREEN_HEIGHT/2 - height/2
    libtcod.console_blit(window, 0, 0, width, height, 0, x, y, 1.0, 0.7)
 
    #present the root console to the player and wait for a key-press
    libtcod.console_flush()
    key = libtcod.console_wait_for_keypress(True)
 
    if key.vk == libtcod.KEY_ENTER and key.lalt:  #(special case) Alt+Enter: toggle fullscreen
        libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
 
    #convert the ASCII code to an index; if it corresponds to an option, return it
    index = key.c - ord('a')
    if index >= 0 and index < len(options): return index
    return None
  def debug_message(self, new_msg):
    print "Debug: " + new_msg
  def message(self, new_msg, color = libtcod.white):
    #split the message if necessary, among multiple lines
    new_msg_lines = textwrap.wrap(new_msg, MSG_WIDTH)
 
    for line in new_msg_lines:
        #if the buffer is full, remove the first line to make room for the new one
        if len(self.game_msgs) == MSG_HEIGHT:
            del self.game_msgs[0]
 
        #add the new line as a tuple, with the text and the color
        self.game_msgs.append( (line, color) )
  def messageAt(self, x, y, new_msg, color = libtcod.white):
    if libtcod.map_is_in_fov(self.map.fov_map, x, y):
      self.message(new_msg, color = libtcod.white)
    else:
      self.debug_message("Hidden Message: " + new_msg + " at location: (" + str(x) + ", " + str(y) + ")")
  def inventory_menu(self, header):
    #show a menu with each item of the inventory as an option
    if len(self.player.inventory) == 0:
        options = ['Inventory is empty.']
    else:
        options = [item.name for item in self.player.inventory]
 
    index = self.menu(header, options, INVENTORY_WIDTH)
 
    #if an item was chosen, return it
    if index is None or len(self.player.inventory) == 0: return None
    return self.player.inventory[index]
  def main_menu(self):
    while not libtcod.console_is_window_closed():
        #show the game's title, and some credits!
        libtcod.console_set_default_foreground(0, libtcod.light_yellow)
        libtcod.console_print_ex(0, SCREEN_WIDTH/2, SCREEN_HEIGHT/2-5, libtcod.BKGND_NONE, libtcod.CENTER,
            'This Is Your Rogue-like')
        libtcod.console_print_ex(0, SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 4, libtcod.BKGND_NONE, libtcod.CENTER,
            'By You!')
        libtcod.console_print_ex(0, SCREEN_WIDTH/2, SCREEN_HEIGHT-8, libtcod.BKGND_NONE, libtcod.CENTER,
            'CONTROLS')
        libtcod.console_print_ex(0, SCREEN_WIDTH/2, SCREEN_HEIGHT-7, libtcod.BKGND_NONE, libtcod.CENTER,
            '-' * (SCREEN_WIDTH/2))
        libtcod.console_print_ex(0, SCREEN_WIDTH/2, SCREEN_HEIGHT-6, libtcod.BKGND_NONE, libtcod.CENTER,
            'Arrow Keys or Numpad - Movement')
        libtcod.console_print_ex(0, SCREEN_WIDTH/2, SCREEN_HEIGHT-5, libtcod.BKGND_NONE, libtcod.CENTER,
            'c, < or > - Use Stairs        g or x - Get Item')
        libtcod.console_print_ex(0, SCREEN_WIDTH/2, SCREEN_HEIGHT-4, libtcod.BKGND_NONE, libtcod.CENTER,
            'd - Drop Item               u - Use Item')
 
        #show options and wait for the player's choice
        choice = self.menu('', ['Play a new game', 'Quit'], 24)
 
        if choice == 0:  #new game
            self.new_game()
            self.main_loop()
        elif choice == 1:  #quit
            break

game=GameWindow()
game.main_menu()
