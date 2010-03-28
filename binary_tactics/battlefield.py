"""contains battlefield objects"""
from warnings import warn
from operator import contains
import random

from const import COMP, ELEMENTS, E, F, I, W, ORTH
from defs import Scient, Loc, noloc, Stone

class Tile(Stone):
    def __init__(self, comp=Stone(), contents=None):
        Stone.__init__(self, comp)
        self.contents = contents

class Grid(Stone):
    """Tiles are stones, Grids most likely should be too."""
    def __init__(self, comp=None, x=16, y=16, tiles=None):
        Stone.__init__(self)
        self.x, self.y = self.size = (x, y)
        if tiles == None:
            self.tiles = {}
            for i in range(x):
                bar = {}
                for j in range(y):
                    bar.update({j: Tile()})
                self.tiles.update({i: bar})
        else:
            self.tiles = tiles

    def __iter__(self):
        return iter(self.tiles)
    def __contains__(self, value):
        return value in self.tiles
    def __getitem__(self,key):
        return self.tiles[key]
    def __setitem__(self,key,value):
        self.tiles[key] = value
    def __len__(self):
        return len(self.tiles)
    def __repr__(self):
        return dict.__repr__(self.tiles)
        
class Battlefield(object):
    """contains grid, units and the logic for damage and movement."""
    def __init__(self, grid=None, squad1=None, squad2=None):
        #grid is a tuple of tuples containing tiles
        self.game_id = 0 #?
        self.grid = grid
        self.graveyard = []
        self.squad1 = squad1
        self.squad2 = squad2
        self.dmg_queue = {}
        self.squads = (self.squad1, self.squad2)
        self.units = self.get_units()
    
    def get_units(self):
        """looks in squads, returns all units in squads."""
        #Squads should be made immutable somewhere in Battlefield.
        units =[]
        for s in self.squads:
            if s != None:
                for u in s:
                    units.append(u)
        return tuple(units)
        
    def move_unit(self, src, dest):
        """move unit from src tile to dest tile"""
        if 0 <= src[0] < self.grid.x:
            if 0 <= src[1] < self.grid.y:
                xsrc, ysrc = src
            else:
                raise Exception("source y (src[1]: %s) is out of range" %src[1])
        else:
            raise Exception("source x (src[0]: %s) is out of range" %src[0])
        
        if 0 <= dest[0] < self.grid.x:
            if 0 <= dest[1] < self.grid.y:
                xdest, ydest = dest
            else:
                raise Exception("Destination y (dest[1]: %s) is out of range" %dest[1])
        else:
            raise Exception("Destination x (dest[0]: %s) is out of range" %dest[0])
            
        if self.grid[xsrc][ysrc].contents:
            if not self.grid[xdest][ydest].contents:
                move = self.grid[xsrc][ysrc].contents.move
                if abs(xsrc-xdest) + abs(ysrc-ydest) <= move:
                    self.grid[xdest][ydest].contents = \
                    self.grid[xsrc][ysrc].contents
                    self.grid[xdest][ydest].contents.location = Loc(xdest, ydest)
                    self.grid[xsrc][ysrc].contents = None
                    return True 
                else:
                    raise Exception("tried moving more than %s tiles" %move)
            else:
                raise Exception("There is already something at %s" %str(dest))
        else:
            raise Exception("There is nothing at %s" %str(src))
    
    def place_unit(self, unit, tile):
        """Places unit at tile, if already on grid, move_unit is called"""
        if 0 <= tile[0] < self.grid.x:
            if 0 <= tile[1] < self.grid.y:
                xpos,ypos = tile
            else:
                raise Exception("Tile y (tile[1]: %s) is out of range" %tile[1])
        else:
            raise Exception("Tile x (tile[0]: %s) is out of range" %tile[0])
        
        if unit.location == noloc:
            if self.grid[xpos][ypos].contents == None:
                self.grid[xpos][ypos].contents = unit
                unit.location = Loc(xpos, ypos)
                self.dmg_queue[unit] = [] #append unit to dmg_queue
                return True
                
            elif unit.location == Loc(xpos, ypos):
                raise Exception("This unit is already on (%s,%s)" %(xpos, ypos))
        
            elif self.grid[xpos][ypos].contents != None:
                raise Exception("(%s, %s) is not empty" %(xpos, ypos))
        else:
            return self.move_unit(unit.location, tile)
        
    def find_units(self):
        list = []
        for x in range(len(self.grid)): #maybe using .x and .y would be faster?
            for y in range(len(self.grid[x])):
                if self.grid[x][y].contents:
                    list.append((x,y)) #maybe this should be a loc?
        return list    
    
    def rand_place_unit(self, unit):
        #readable?
        inset = 0 #place units in a smaller area, for testing.
        def RandPos(): return (random.randint(0, ((self.grid.x - 1) - inset)),
            random.randint(0, ((self.grid.y - 1) - inset)))
        if len(self.find_units()) == (self.grid.x * self.grid.y):
            raise Exception("Grid is full")
        else:
            while unit.location == noloc:
                try:
                    self.place_unit(unit, RandPos())
                    break
                except Exception:
                    pass
    
    def rand_place_squad(self, squad):
        """place the units in a squad randomly on the battlefield"""
        for unit in range(len(squad)):
            self.rand_place_unit(squad[unit])

    def flush_units(self):
        """
        remove all units from grid, returns number of units flushed,
        does not put them in the graveyard. (for testing)
        """
        #maybe find_unit should be used here...
        count = 0
        for x in range(len(self.grid)):
            for y in range(len(self.grid[x])):
                if self.grid[x][y].contents:
                    self.grid[x][y].contents.location = noloc
                    self.grid[x][y].contents = None
                    count += 1
        return count

    #Attack/Damage stuff
    def dmg(self, atkr, defdr, type):
        """Calculates the damage of an attack"""
        dloc = defdr.location
        damage_dealt = {E: 0, F: 0, I: 0, W: 0}
        if 0 <= dloc.x < self.grid.x:
            if 0 <= dloc.y < self.grid.y:
                if contains(('Sword', 'Bow'),type) == True:
                    for element in damage_dealt:
                        dmg = (atkr.p + atkr.patk + (2 * atkr.comp[element]) + 
                        atkr.weapon.comp[element]) - (defdr.p + defdr.pdef +
                        (2 * defdr.comp[element]) + self.grid[dloc.x][dloc.y].comp[element])
                        dmg = max(dmg, 0)
                        damage_dealt[element] = dmg
                    damage = sum(damage_dealt.values())
                    return damage
                else:
                    for element in damage_dealt:
                        dmg = (atkr.m + atkr.matk + (2 * atkr.comp[element]) +
                        atkr.weapon.comp[element]) - (defdr.m + defdr.mdef + 
                        (2 * defdr.comp[element]) + self.grid[dloc.x][dloc.y].comp[element])
                        dmg = max(dmg, 0)
                        damage_dealt[element] = dmg
             
                    damage = sum(damage_dealt.values())
                    if atkr.element == defdr.element:
                        return 0 - damage
                    else:
                        return damage
            else:
                raise Exception("Defender's y coord  %s is off grid" %dy)
        else:
            raise Exception("Defender's x coord %s is off grid" %dx)
    
    def calc_wand_area(self, atkr, target):
        ax,ay = aloc = atkr.location
        dx,dy = dloc = Loc._make(target)
        direction = {0:'West', 1:'North', 2:'East', 3:'South'}
        maxes = (ax, ay, (self.grid.x - 1 - ax), (self.grid.y - 1 - ay),)
        for i in direction:
            pat = atkr.weapon.make_pattern(aloc, maxes[i], direction[i])
            if contains(pat, dloc):
                ranges  = (abs(dx - ax), abs(dy - ay), abs(dx - ax), abs(dy - ay))
                pat_ = atkr.weapon.make_pattern(aloc, ranges[i], direction[i])                
                new_pat = []
                for i in pat_:
                    if 0 <= i[0] < self.grid.x:
                        if 0 <= i[1] < self.grid.y:
                            new_pat.append(i)
                return new_pat
    
    def calc_damage(self, atkr, defdr):
        """Calcuate damage delt to defdr from atkr. Also calculates the damage of 
        all units within a blast range. if weapon has a AOE list of
        (area, [target, dmg]) is returned. otherwise just dmg is returned"""
        #Broken: dmg_queue is applied at the wrong time in battle.py
        weapon = atkr.weapon
        aloc = atkr.location
        dloc = defdr.location
        in_range = weapon.map_to_grid(aloc, self.grid.size)
        if not contains(in_range, dloc):
            raise Exception( \
            "Defender's location: %s is outside of attacker's range" %str(dloc))
        else:
            #this weapon logic is janky.
            if weapon.type != 'Wand':
                dmg = self.dmg(atkr, defdr, weapon.type)
                if weapon.type == 'Sword':
                    return dmg
                if dmg != 0:
                    if weapon.type == 'Bow': 
                        return dmg / 4            
                    else:
                        return dmg / weapon.time #assumes weapon.type == 'Glove'
                else:
                    return None #No damage.
            else:
                direction = {0:'West', 1:'North', 2:'East', 3:'South'}
                maxes = (aloc.x, aloc.y, (self.grid.x - 1 - aloc.x), (self.grid.y - 1 - aloc.y),)
                for i in direction:
                    pat = atkr.weapon.make_pattern(aloc, maxes[i], direction[i])
                    if contains(pat, dloc):
                        #need to check ranges
                        ranges  = (abs(dloc.x - aloc.x), abs(dloc.y - aloc.y), abs(dloc.x - aloc.x), abs(dloc.y - aloc.y))
                        new_pat = atkr.weapon.make_pattern(aloc, ranges[i], direction[i])
                        targets = list(set(self.find_units()) & set(new_pat))
                        dmg_list = []
                        area = len(new_pat)
                        for i in targets:
                            defdr = self.grid[i[0]][i[1]].contents
                            temp_dmg = self.dmg(atkr, defdr, weapon.type)
                            if temp_dmg != 0:
                                temp_dmg /= area
                                dmg_list.append((defdr, temp_dmg))
                            else:
                                pass # no damage was dealt, don't append anything.
                        if len(dmg_list) == 0:
                            return None #No damage.
                        else:
                            return dmg_list

    def apply_dmg(self, target, damage):
        """applies damage to target, called by attack() and 
        apply_queued() returns damage applied"""
        if damage >= target.hp:
            try:
                self.bury(target)
                return "Dead."
                #return target.hp
            except:
                raise Exception("STOP BEING GREEDY.")
        else:
            target.hp -= damage
            return damage
                
    def bury(self, unit):
        """moves unit to graveyard"""
        squad = unit.squad
        name = unit.name
        x,y = unit.location
        unit.hp = 0
        self.grid[x][y].contents = None
        unit.location = Loc(-1,-1)
        del self.dmg_queue[unit] 
        self.graveyard.append(unit)
        return True
                
    def attack(self, atkr, target):
        """calls calc_damage, applies result, Handles death."""
        defdr = self.grid[target[0]][target[1]].contents
        dmg = self.calc_damage(atkr, defdr)
        if dmg != None:
            if isinstance(dmg, int) == True:
                if dmg != 0:
                    recieved_dmg = self.apply_dmg(defdr, dmg)
                else:
                    return [[defdr, 0]]
                if defdr.hp > 0:
                    if atkr.weapon.type == 'Glove':
                        self.dmg_queue[defdr].append([dmg, atkr.weapon.time - 1])
                return [[defdr, recieved_dmg]]

            else:
                defdr_HPs = []
                for i in dmg:
                    if i[0].hp > 0:
                        defdr_HPs.append([i[0], self.apply_dmg(i[0], i[1]) ])
                return defdr_HPs
                    
        else:
            #no damage
            return []
    def get_dmg_queue(self):
        """returns a copy of the dmg_queue."""
        new_dict = {}
        for (key, value) in self.dmg_queue.items():
            new_lst = []
            for lst in value:
                new_lst.append(tuple(lst))
                new_dict[key] = new_lst
        return new_dict
        
    def apply_queued(self):
        """applies damage to targets stored in dmg_queue"""
        defdr_HPs = []
        for i in self.dmg_queue.keys():
            udmg = []
            for dmg_lst in reversed(xrange(len(self.dmg_queue[i]))):
                udmg.append(self.dmg_queue[i][dmg_lst][0])
                self.dmg_queue[i][dmg_lst][1] -= 1
                if self.dmg_queue[i][dmg_lst][1] == 0:
                    del self.dmg_queue[i][dmg_lst]
            
            udmg = sum(udmg)
            if udmg != 0:
                defdr_HPs.append([i, self.apply_dmg(i, udmg)])
        return defdr_HPs
        

