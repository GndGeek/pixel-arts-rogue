from proto_rogue_base import *

class Wall(Tile):
  def __init__(self):
    Tile.__init__(self, '#', libtcod.light_gray, True)

class Floor(Tile):
  def __init__(self):
    Tile.__init__(self, ' ', libtcod.yellow, False)

class Water(Tile):
  def __init__(self):
    Tile.__init__(self, '~', libtcod.light_blue, True, block_sight=False)

class Stair(Tile):
  def __init__(self):
    Tile.__init__(self, '>', libtcod.white, False)

class Rat(Creature):
  def __init__(self, x, y):
    Creature.__init__(self,x, y, 'rat', 'r', libtcod.sepia, 3)

class Orc(Creature):
  def __init__(self, x, y):
    Creature.__init__(self,x, y, 'orc', 'o', libtcod.green, 10)

class Troll(Creature):
  def __init__(self, x, y):
    Creature.__init__(self,x, y, 'troll', 'T', libtcod.darker_green, 20)
    self.attack=4

class Thief(Creature):
  def __init__(self, x, y):
    Creature.__init__(self,x, y, 'thief', 't', libtcod.gray, 4)
    self.attack = 0
  def turn(self, map, player, bool):
    objects_at = map.getObjectsAt(self.x, self.y)
    took_objects = False
    for obj in objects_at:
      if isinstance(obj, Item):
        self.getItem(obj)
        took_objects = True
    if not took_objects:
      super(Thief, self).turn(map, player, bool)
  def hit(self, creature):
    if not super(Thief, self).hit(creature): return False
    if creature.inventory:
      r = libtcod.random_get_int(0, 0, len(creature.inventory)-1)
      loot = creature.inventory[r]
      self.getItem(loot)
      messenger.window.messageAt(self.x, self.y, self.name+' steals '+loot.name+' from '+creature.name+'.')
    return True

class HealingPotion(Item):
  def __init__(self, x, y, owner):
    Item.__init__(self, x, y, 'healing potion', '!', libtcod.purple, owner)
  def use(self):
    self.owner.heal(10)
    self.owner.removeItem(self)
    messenger.window.message('You feel better.', libtcod.light_purple)

class AttackPotion(Item):
  def __init__(self, x, y, owner):
    Item.__init__(self, x, y, 'attack potion', '!', libtcod.red, owner)
  def use(self):
    self.owner.attack+=1
    self.owner.removeItem(self)
    messenger.window.message('You feel more powerful. Attack +1!', libtcod.red)

class DefensePotion(Item):
  def __init__(self, x, y, owner):
    Item.__init__(self, x, y, 'defense potion', '!', libtcod.dark_green, owner)
  def use(self):
    self.owner.defense+=1
    self.owner.removeItem(self)
    messenger.window.message('You feel safer. Defense +1!', libtcod.dark_green)

class Map(MapBase):
  def __init__(self, width, height, difficulty):
    MapBase.__init__(self, width, height)
    self.difficulty=difficulty
  def create_room(self, room):
    if libtcod.random_get_int(0, 0, 4)==4:
      if libtcod.random_get_int(0, 0, 1)==1:
        # Maybe make the edges flooded
        for x in range(room.x1, room.x2+1):
          for y in range(room.y1, room.y2+1):
            self.map[x][y] = Water()
      else:
        # Maybe make the walls crumbled
        for x in range(room.x1, room.x2+1):
          for y in range(room.y1, room.y2+1):
            if libtcod.random_get_int(0, 0, 2)==2:
              self.map[x][y] = Floor()

    #go through the tiles in the rectangle and make them passable
    for x in range(room.x1 + 1, room.x2):
      for y in range(room.y1 + 1, room.y2):
        self.map[x][y] = Floor()
  def place_items(self, room):
    #choose random number of items
    num_items = libtcod.random_get_int(0, 0, MAX_ROOM_ITEMS)
 
    for i in range(num_items):
        #choose random spot for this item
        x = libtcod.random_get_int(0, room.x1+1, room.x2-1)
        y = libtcod.random_get_int(0, room.y1+1, room.y2-1)
 
        #only place it if the tile is not blocked
        if not self.is_blocked(x, y):
            item_type=libtcod.random_get_int(0, 0, 3)
            if item_type==0 or item_type==1:
              #create a healing potion
              self.getItem(HealingPotion(x, y, None))
            elif item_type==2:
              self.getItem(AttackPotion(x, y, None))
            elif item_type==3:
              self.getItem(DefensePotion(x, y, None))
  def place_monsters(self, room):
    #choose random number of monsters
    num_monsters = libtcod.random_get_int(0, 0, MAX_ROOM_MONSTERS)
 
    for i in range(num_monsters):
        #choose random spot for this monster
        x = libtcod.random_get_int(0, room.x1+1, room.x2-1)
        y = libtcod.random_get_int(0, room.y1+1, room.y2-1)
 
        #only place it if the tile is not blocked
        if not self.is_blocked(x, y):
          if libtcod.random_get_int(0, 0, 5)==4:
            self.objects.append(Troll(x, y))
          else:
            if libtcod.random_get_int(0, 0, 4)==0:
              self.objects.append(Orc(x, y))
            else:
              if libtcod.random_get_int(0, 0, 2)==0:
                self.objects.append(Thief(x, y))
              else:
                self.objects.append(Rat(x, y))
  def create_h_tunnel(self, x1, x2, y):
    #horizontal tunnel. min() and max() are used in case x1>x2
    for x in range(min(x1, x2), max(x1, x2) + 1):
        self.map[x][y]=Floor()
  def create_v_tunnel(self, y1, y2, x):
    #vertical tunnel
    for y in range(min(y1, y2), max(y1, y2) + 1):
        self.map[x][y]=Floor()
  def generate_map(self):
    #fill map with "blocked" tiles
    self.map = [[ Wall()
        for y in range(MAP_HEIGHT) ]
            for x in range(MAP_WIDTH) ]
 
    new_x=0
    new_y=0

    rooms = []
    num_rooms = 0
 
    for r in range(MAX_ROOMS):
        #random width and height
        w = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        h = libtcod.random_get_int(0, ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        #random position without going out of the boundaries of the map
        x = libtcod.random_get_int(0, 0, MAP_WIDTH - w - 1)
        y = libtcod.random_get_int(0, 0, MAP_HEIGHT - h - 1)
 
        #"Rect" class makes rectangles easier to work with
        new_room = Rect(x, y, w, h)
 
        #run through the other rooms and see if they intersect with this one
        failed = False
        for other_room in rooms:
            if new_room.intersect(other_room):
                failed = True
                break
 
        if not failed:
            #this means there are no intersections, so this room is valid
 
            #"paint" it to the map's tiles
            self.create_room(new_room)
            self.place_items(new_room)
            self.place_monsters(new_room)
 
            #center coordinates of new room, will be useful later
            (new_x, new_y) = new_room.center()
 
            if num_rooms == 0:
                #this is the first room, where the player starts at
                self.startx = new_x
                self.starty = new_y
            else:
                #all rooms after the first:
                #connect it to the previous room with a tunnel
 
                #center coordinates of previous room
                (prev_x, prev_y) = rooms[num_rooms-1].center()
 
                #draw a coin (random number that is either 0 or 1)
                if libtcod.random_get_int(0, 0, 1) == 1:
                    #first move horizontally, then vertically
                    self.create_h_tunnel(prev_x, new_x, prev_y)
                    self.create_v_tunnel(prev_y, new_y, new_x)
                else:
                    #first move vertically, then horizontally
                    self.create_v_tunnel(prev_y, new_y, prev_x)
                    self.create_h_tunnel(prev_x, new_x, new_y)
 
            #finally, append the new room to the list
            rooms.append(new_room)
            num_rooms += 1

    #create stairs at the center of the last room
    self.map[new_x][new_y] = Stair()
