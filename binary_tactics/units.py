from UserList import UserList
from stone import Stone
from const import ELEMENTS, E, F, I, W
class Unit(Stone):
    def __init__(self, element, comp, name=None, location=None):
        if not element in ELEMENTS:
            raise Exception("Invalid element: %s, valid elements are %s" \
            % (element, ELEMENTS))
        Stone.__init__(self, comp)
        self.element = element
        if name == None:
            self.name = self.__hash__()
        self.name = name
        self.location = location
        self.val = self.value()
    
class Scient(Unit):
    """A Scient (playable character) unit.
    
    Initializer takes element and comp:
      * element - this unit's element (E, F, I, or W) aka 'suit'
      * comp - dictionary of this unit's composition on (0..255) {E: earth, 
      F: fire, I: ice, W: wind}
    """
    
    def __init__(self, element, comp, name=None, weapon=None,
                 weapon_bonus=dict(Stone()), location=None):
        Unit.__init__(self, element, comp, name, location)
        self.move = 4
        self.weapon = weapon
        self.weapon_bonus = weapon_bonus
        self.equip_limit = {E:1, F:1 ,I:1 ,W:1}
        for i in self.equip_limit:
            self.equip_limit[i] = self.equip_limit[i] + self.comp[i] \
            + self.weapon_bonus[i]
        self.calcstats()
        #self.equip(self.weapon)

    def calcstats(self):
        self.p    = (2*(self.comp[F] + self.comp[E]) +
                        self.comp[I] + self.comp[W]) 
        self.m    = (2*(self.comp[I] + self.comp[W]) +
                        self.comp[F] + self.comp[E])
        self.atk  = (2*(self.comp[F] + self.comp[I]) + 
                        self.comp[E] + self.comp[W]) + (2 * self.value())
        self.defe = (2*(self.comp[E] + self.comp[W]) + 
                        self.comp[F] + self.comp[I]) 
        
        self.pdef = self.p + self.defe + (2 * self.comp[E])
        self.patk = self.p + self.atk  + (2 * self.comp[F])
        self.matk = self.m + self.atk  + (2 * self.comp[I])
        self.mdef = self.m + self.defe + (2 * self.comp[W])
        self.hp   = 4 * (self.pdef + self.mdef) + self.value()

    def equip(self, weapon): #TODO move to battlefield
        """
        A function that automagically equips items based on element.
        should be moved someplace else.
        """
        if weapon == None:
            if self.element == 'Earth':
                self.weapon = Sword(self.element, Stone())
            elif self.element == 'Fire':
                self.weapon = Bow(self.element, Stone())
            elif self.element == 'Ice':
                self.weapon = Wand(self.element, Stone())
            else:
                self.weapon = Glove(self.element, Stone())
            
        else:
            '''
            if weapon.value() > self.equip_limit[weapon.type]:
                raise Exception("This unit cannot equip this weapon")
            else:
                self.weapon = weapon
            '''
            self.weapon = weapon
            
class Nescient(Unit):
        def bite(self, target):
            pass
        def breath(self, target):
            pass

class Squad(UserList):
    """contains a number of Units. Takes a list of Units"""
    def unit_size(self, object):
        if isinstance(object, Unit) == False:
            raise TypeError("Squads can contain only Units")
        else:
            if isinstance(object, Scient):
                return 1
            else:
                return 2
    
    def hp(self):
        """Returns the total HP of the Squad."""
        return sum([unit.hp for unit in self])

    def __init__(self, data=None, name=None):
        self.value = 0
        self.free_spaces = 8
        self.name = name
        UserList.__init__(self)
        if data == None:
            return
            
        if isinstance(data, list):
            for x in data: 
                self.append(x)
        else:
            self.append(data)
            
    def __setitem__(self, key, val):
        #need to change how value of a squad is calculated.
        #does the value of a squad go down when a unit dies?
        #how do survival bonuses change squad values?
        size = self.unit_size(key)
        if self.free_spaces < size:
            raise Exception( \
            "There is not enough space in the squad for this unit")
        list.__setitem__(self, key, val)
        self.value += val.value()
        self.free_spaces -= size
        key.squad = self
        
    def __delitem__(self, key):
        del self.data[key].squad
        temp = self[key].value()
        self.free_spaces += self.unit_size(self[key])
        self.data.__delitem__(self, key)
        self.value -= temp
        
    def append(self, item):
        size = self.unit_size(item)
        if self.free_spaces < size:
            raise Exception( \
            "There is not enough space in the squad for this unit")
        self.data.append(item)
        self.value += item.value()
        self.free_spaces -= size
        item.squad = self
            
    def __repr__(self, more=None):
        """This could be done better..."""
        if more != None:
            if self.value > 0:
                s = ''
                for i in range(len(self)):
                    s += str(i) + ': ' + str(self[i].name) + '\n'
                return "Name: %s, Value: %s, Free spaces: %s \n%s" \
                %(self.name, self.value, self.free_spaces, s)
        else:
            return "Name: %s, Value: %s, Free spaces: %s \n" %(self.name, \
            self.value, self.free_spaces)
    
    def __call__(self, more=None):
        return self.__repr__(more)