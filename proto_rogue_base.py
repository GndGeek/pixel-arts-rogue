import libtcodpy as libtcod
import math

print "check push"

class messenger:
  window=None

#actual size of the window
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 50

#size of the map
MAP_WIDTH = 80
MAP_HEIGHT = 43
 
#parameters for dungeon generator
ROOM_MAX_SIZE = 10
ROOM_MIN_SIZE = 6
MAX_ROOMS = 30
MAX_ROOM_MONSTERS = 3
MAX_ROOM_ITEMS = 2

#sizes and coordinates relevant for the GUI
BAR_WIDTH = 20
PANEL_HEIGHT = 7
PANEL_Y = SCREEN_HEIGHT - PANEL_HEIGHT
MSG_X = BAR_WIDTH + 2
MSG_WIDTH = SCREEN_WIDTH - BAR_WIDTH - 2
MSG_HEIGHT = PANEL_HEIGHT - 1
INVENTORY_WIDTH = 50

#20 frames-per-second maximum
LIMIT_FPS = 20

FOV_ALGO = 0  #default FOV algorithm
FOV_LIGHT_WALLS = True
TORCH_RADIUS = 10
 
color_dark_wall = libtcod.Color(0, 0, 100)
color_light_wall = libtcod.Color(130, 110, 50)
color_dark_ground = libtcod.Color(50, 50, 150)
color_light_ground = libtcod.Color(200, 180, 50)

class Rect (object):
    #a rectangle on the map. used to characterize a room.
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h
    def center(self):
        center_x = (self.x1 + self.x2) / 2
        center_y = (self.y1 + self.y2) / 2
        return (center_x, center_y)
    def intersect(self, other):
        #returns true if this rectangle intersects with another one
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)

class Tile (object):
    #a tile of the map and its properties
    def __init__(self, char, fg, blocked, block_sight = None):
      self.blocked = blocked
      self.char=char
      self.fg=fg
 
      #by default, if a tile is blocked, it also blocks sight
      if block_sight is None:
        block_sight = blocked
      self.block_sight = block_sight

class GameObject (object):
    #this is a generic object: the player, a monster, an item, the stairs...
    #it's always represented by a character on screen.
    def __init__(self, x, y, name, char, color, blocks=False, always_visible=False):
        self.x = x
        self.y = y
        self.name=name
        self.char = char
        self.color = color
        self.blocks=blocks
        self.always_visible = always_visible
        self.destroyed=False
    def draw(self, con):
        #set the color and then draw the character that represents this object at its position
        libtcod.console_set_default_foreground(con, self.color)
        libtcod.console_put_char(con, self.x, self.y, self.char, libtcod.BKGND_NONE)
 
    def clear(self, con):
        #erase the character that represents this object
        libtcod.console_put_char(con, self.x, self.y, ' ', libtcod.BKGND_NONE)
    def __str__(self):
      return self.name

class Item(GameObject):
  def __init__(self, x, y, name, char, color, owner):
    GameObject.__init__(self, x, y, name, char, color)
    self.owner=owner
  def gotten(self, owner):
    if self.owner: self.owner.removeItem(self)
    self.owner=owner
  def use(self):
    messenger.window.message('This item is useless.', libtcod.white)


class Creature(GameObject):
  def __init__(self, x, y, name, char, color, max_hp, inventory=None):
    GameObject.__init__(self, x, y, name, char, color, blocks=True)
    self.max_hp=max_hp
    self.hp=max_hp
    self.attack=3
    self.defense=2
    if not inventory: inventory = []
    self.inventory=inventory
  def damage(self, damage):
    adjustedDamage = max(damage - self.defense, 0)
    self.hp -= adjustedDamage
    if self.hp <= 0:
      self.destroyed=True
    return adjustedDamage
  def heal(self, heal):
    self.hp+=heal
    if self.hp>self.max_hp:
      self.hp=self.max_hp
  def hit(self, creature):
    messenger.window.messageAt(self.x, self.y, self.name+' hits '+creature.name+' for '+str(creature.damage(self.attack))+' damage.')
    return True
  def move(self, gameMap, dx, dy):
    #move by the given amount, if the destination is not blocked
    if not gameMap.is_blocked(self.x + dx, self.y + dy):
      self.x += dx
      self.y += dy
      return True
    else:
      creatures=gameMap.isBlockedByCreature(self.x + dx, self.y + dy)
      if len(creatures)>0:
        for creature in creatures:
          if creature.name != self.name or creature.name == 'thief':
            self.hit(creature)
        return True
    return False
  def getItem(self, item):
    if len(self.inventory)<26:
      self.inventory.append(item)
      item.gotten(self)
  def removeItem(self, item):
    item.x=self.x
    item.y=self.y
    self.inventory.remove(item)
  def move_towards(self, gameMap, target_x, target_y):
    #vector from this object to the target, and distance
    dx = target_x - self.x
    dy = target_y - self.y
    distance = math.sqrt(dx ** 2 + dy ** 2)

    #normalize it to length 1 (preserving direction), then round it and
    #convert to integer so the movement is restricted to the map grid
    dx = int(round(dx / distance))
    dy = int(round(dy / distance))
    return self.move(gameMap, dx, dy)
  def turn(self, gameMap, player, fov):
    if (not fov) or (not self.move_towards(gameMap, player.x, player.y)):
      self.move(gameMap, libtcod.random_get_int(0, -1, 1), libtcod.random_get_int(0, -1, 1))
  def death_effects(self, window, gameMap, player):
    while self.inventory:
      gameMap.getItem(self.inventory[0])

class Player(Creature):
  def __init__(self, x, y):
    Creature.__init__(self, x, y, 'Player', '@', libtcod.white, 30)
  def death_effects(self, window, gameMap, player):
    window.player_death()

class MapBase (object):
  def __init__(self, width, height): #! This should take size values
      self.explored = [[ bool(False)
          for y in range(MAP_HEIGHT) ]
              for x in range(MAP_WIDTH) ]
      self.objects=[]

      self.width=width
      self.height=height

      #where the player enters the map
      self.startx=0
      self.starty=0

      self.generate_map()

      self.fov_map=libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)
      for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
          libtcod.map_set_properties(self.fov_map, x, y, not self.map[x][y].block_sight, not self.map[x][y].blocked)
  def getItem(self, item):
    self.objects.append(item)
    item.gotten(self)
  def removeItem(self, item):
    self.objects.remove(item)
  def getObjectsAt(self, x, y):
    objects = [obj for obj in self.objects
        if obj.x == x and obj.y == y ]
    return objects
  def is_blocked(self, x, y):
    #first test the map tile
    if x < 0 or x >= MAP_WIDTH or y < 0 or y >= MAP_HEIGHT:
      messenger.window.debug_message("Warning: Creature Attempting to Leave Map. Recommend Immediate Termination.")
      return True
    if self.map[x][y].blocked:
        return True
 
    #now check for any blocking objects
    for object in self.objects:
        if object.blocks and object.x == x and object.y == y:
            return True

    return False
  def isBlockedByCreature(self, x, y):
    creatures=[]
    #now check for any blocking objects
    for obj in self.objects:
      if obj.x == x and obj.y == y and isinstance(obj, Creature):
        creatures.append(obj)
    return creatures
