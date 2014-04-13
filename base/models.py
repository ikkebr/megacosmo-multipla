#*-* encoding: utf-8 *-*
from __future__ import division, unicode_literals

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save

from django.contrib.humanize.templatetags.humanize import intcomma
from descriptions import BUILDING_DESCRIPTIONS, RESEARCH_DESCRIPTIONS, RACE_DESCRIPTIONS
from math import trunc
import math
from random import randint

BASE_ROID_PRODUCTION = 250
BASE_MINE_PRODUCTION = 3000
BASE_TRAVEL_TIME = 13
CLUSTER_TRAVEL_TIME = -1
GALAXY_TRAVEL_TIME = -2
BUILDINGS_PER_TERRAFORMING = 10
BUILDING_LIFE = 10000

BASE_BUILDING_TIME = 8
BASE_RESEARCH_TIME = 10
BASE_BUILDING_COST = 1000

BASE_ROID_COST = 1000
BASE_ROID_MULT = 250
ROID_LIFE = 500

GALAXY_SIZE = 10
CLUSTER_SIZE = 4

MAX_ROID_PERCENTAGE_STOLEN_PER_TICK = 0.40
MAX_BUILDS_PERCENTAGE_DESTROYED_PER_TICK = 0.20

BASE_WAVE_COST = 1000
BASE_SABOTAGE_COST = 5000
BASE_SABOTAGE_AWARENESS = 10

SHIP_PRODUCTION_MODIFIER = 2.5
CONVERSION_PER_RESEARCH_LEVEL = 0.05
BASE_CONVERSION_RATE = 0.5

MIN_SCORE_TO_SABOTAGE = 0.4

RESEARCH_LIST = ('',
                 'research_mines',
                 'research_roids',
                 'research_terrain',
                 'research_sabotage',
                 'research_travel',
                 'research_waves',
                 'research_research')

BUILD_LIST = ('',
              'mines_metal',
              'mines_cristal',
              'mines_uranium',
              'mines_gold',
              'factory_fico',
              #'factory_co',
              'factory_frcr',
              #'factory_cr',
              #'factory_bs',
              'factory_bssp',
              'security_center',
              'waveamp',
              'waveblock')

ROID_LIST = ('',
             'roids_metal',
             'roids_cristal',
             'roids_gold',
             'roids_uranium')

RACES = ((0, u'Terrano'),
         (1, u'Ciclôn'),
         (2, u'Xenófago'),
         (3, u'Qrogano'),
         (4, u'Makulo'),
         )

class Tick(models.Model):
    number = models.IntegerField(default=0)
    last_tick = models.DateTimeField(auto_now=True, auto_now_add=True)
    
class OutOfResourcesException(Exception):
    pass

class OutOfSpaceException(Exception):
    pass

class CrapException(Exception):
    pass

#class Race(models.Model):
    #name = models.CharField(max_length=100)
    #description = models.TextField()
    #power = models.CharField(max_length=100)

    #def __unicode__(self):
        #return "%s" % self.name

class Galaxy(models.Model):
    x = models.SmallIntegerField(default=1)
    y = models.SmallIntegerField(default=1)
    name = models.CharField(max_length=100)
    score = models.IntegerField(default=0)
    roids = models.IntegerField(default=0)
    
    def set_score(self):
        score = sum(x.score for x in self.planet_set.all())
        self.score = score
        self.save()
        
        
    def set_roids(self):
        roids = sum(x.roids() for x in self.planet_set.all())
        self.roids = roids
        self.save()
        
    


    def is_full(self):
        #print len(self.planet_set.all())

        if len(self.planet_set.all()) < GALAXY_SIZE:
            return False

        return True

    def add_planet(self, planet):
        if len(self.planet_set.all()) < GALAXY_SIZE:
            free = range(1, GALAXY_SIZE+1)
            for each in self.planet_set.all():
                try:
                    free.remove(each.z)
                except:
                    pass

            from random import shuffle
            shuffle(free)

            planet.galaxy = self
            planet.x = self.x
            planet.y = self.y
            planet.z = free.pop()
            planet.save()

            try:
                old_vote = Vote.objects.get(source= planet)
                old_vote.delete()
            except:
                pass

            try:
                old_votes = Vote.objects.filter(target= planet)
                for each_vote in old_votes:
                    each_vote.delete()
            except:
                pass

            planet.save()

    def get_planet_list(self):
        plist = []
        for index in range(1, GALAXY_SIZE+1):
            try:
                pl = Planet.objects.get(galaxy=self, z=index)
            except:
                pl = ''
            plist.append((index, pl))

        #print plist
        #print str(Planet.objects.get(id=1))*20
        #print self
        return plist

    def get_enemy_ships(self):
        return [y for y in [x.get_enemy_ships() for x in self.planet_set.all()] if y]

    def __unicode__(self):
        return u"%s - (%s:%s)" % (self.name, self.x, self.y)

    class Meta:
        unique_together = ("x","y")

class Vote(models.Model):
    galaxy = models.ForeignKey(Galaxy)
    source = models.ForeignKey("Planet", unique=True)
    target = models.ForeignKey("Planet", related_name="voted")

    def can_vote(self, source, target):
        if source.galaxy == target.galaxy:
            return True
        return False

    def cast_vote(self, source, target):
        self.source = source
        if source.galaxy == target.galaxy:
            self.target = target
        else:
            self.target = source
        self.save()


class Planet(models.Model): 
    user = models.OneToOneField(User)

    ruler = models.CharField(max_length=20, default='Governante', unique=True)
    name = models.CharField(max_length=20, default='Planeta', unique=True)

    race = models.SmallIntegerField(choices=RACES, default=1)

    score = models.IntegerField(default=0)

    z = models.SmallIntegerField(default=1)
    x = models.SmallIntegerField(default=1)
    y = models.SmallIntegerField(default=1)
    galaxy = models.ForeignKey(Galaxy)

    metal = models.PositiveIntegerField(default=10000)
    cristal = models.PositiveIntegerField(default=10000)
    uranium = models.PositiveIntegerField(default=10000)
    gold = models.PositiveIntegerField(default=10000)

    roids_metal = models.PositiveIntegerField(default=3)
    roids_cristal = models.PositiveIntegerField(default=3)
    roids_uranium = models.PositiveIntegerField(default=3)
    roids_gold = models.PositiveIntegerField(default=3)

    mines_metal = models.PositiveIntegerField(default=1)
    mines_cristal = models.PositiveIntegerField(default=1)
    mines_uranium = models.PositiveIntegerField(default=1)
    mines_gold = models.PositiveIntegerField(default=1)    

    factory_fico = models.PositiveIntegerField(default=1)
    factory_frcr = models.PositiveIntegerField(default=0)
    factory_bssp = models.PositiveIntegerField(default=0)

    security_center = models.PositiveIntegerField(default=0)
    waveamp = models.PositiveIntegerField(default=0)
    waveblock = models.PositiveIntegerField(default=0)

    research_mines = models.IntegerField(default=1)
    research_roids = models.IntegerField(default=1)
    research_terrain =models.IntegerField(default=1)
    research_sabotage = models.IntegerField(default=1)
    research_travel = models.IntegerField(default=1)
    research_waves = models.IntegerField(default=1)
    research_research = models.IntegerField(default=1)

    current_research = models.IntegerField(default=0)
    current_research_time = models.IntegerField(default=0)

    current_building = models.IntegerField(default=0)
    current_building_time = models.IntegerField(default=0)
    
    awareness = models.IntegerField(default=50)
    
    def get_awareness(self):
        return self.awareness + 5*self.security_center
    
    def convert_rate(self):
        return (self.research_research * CONVERSION_PER_RESEARCH_LEVEL + BASE_CONVERSION_RATE)
    
    def convert_currency(self, currency, to, value):
        available = {'0': 'metal', '1': 'cristal', '2': 'uranium', '3': 'gold'}
        
        if value > getattr(self, available[currency]):
            value = getattr(self, available[currency])
        
        setattr(self, available[currency], trunc(getattr(self, available[currency]) - value))
        setattr(self, available[to], trunc(getattr(self, available[to]) + value * self.convert_rate() ))
        
        self.save()

    def roid_cost(self, tp):
        return getattr(self, ROID_LIST[tp]) * BASE_ROID_MULT + BASE_ROID_COST

    def init_roid(self, qt, tp):
        qti = 0
        if tp == 1:
            try:
                while qt > 0:
                    self.remove_metal( self.roid_cost(1) )
                    self.roids_metal +=1
                    qti += 1
                    qt -= 1
            except:
                pass
        elif tp == 2:
            try:
                while qt > 0:
                    self.remove_cristal( self.roid_cost(2) )
                    self.roids_cristal +=1
                    qti += 1
                    qt -= 1
            except:
                pass
        elif tp == 3:
            try:
                while qt > 0:
                    self.remove_gold( self.roid_cost(3) )
                    self.roids_gold +=1
                    qti += 1
                    qt -= 1
            except:
                pass
        else:
            tp = 4
            try:
                while qt > 0:
                    self.remove_uranium( self.roid_cost(4) )
                    self.roids_uranium +=1
                    qti += 1
                    qt -= 1
            except:
                pass

        self.save()
        return (tp, qti)

    def can_build_fi(self):
        if self.factory_fico > 0:
            return True
        return False

    def max_build_fi(self):
        return trunc(self.factory_fico*200*SHIP_PRODUCTION_MODIFIER)

    def max_build_co(self):
        return trunc(self.factory_fico*100*SHIP_PRODUCTION_MODIFIER)

    def max_build_fr(self):
        return trunc(self.factory_frcr*50*SHIP_PRODUCTION_MODIFIER)

    def max_build_cr(self):
        return trunc(self.factory_frcr*15*SHIP_PRODUCTION_MODIFIER)

    def max_build_bs(self):
        return trunc(self.factory_bssp*5*SHIP_PRODUCTION_MODIFIER)

    def unread_messages(self):
        from comm.models import Message
        msg = len(Message.objects.filter(p_to=self, read=False))
        return msg

    def unread_news(self):
        from comm.models import News
        news = len(News.objects.filter(planet=self, read=False))
        return news

    def add_news(self, icon, news):
        from comm.models import News
        news = News(content=news, icon=icon, planet=self)
        news.save()

    def can_build_co(self):
        if self.factory_fico > 0: #and self.research_ships > 1:
            return True
        return False

    def can_build_fr(self):
        if self.factory_frcr > 0: #and self.research_ships > 2:
            return True
        return False

    def can_build_cr(self):
        if self.factory_frcr > 0: # and self.research_ships > 3:
            return True
        return False

    def can_build_bs(self):
        if self.factory_bssp > 0: # and self.research_ships > 4:
            return True
        return False

    def can_build_sp(self):
        if self.factory_bssp > 0: # and self.research_ships > 5:
            return True
        return False


    def average_research_level(self):
        return (self.research_mines + self.research_research + self.research_sabotage + self.research_waves + self.research_terrain + self.research_travel + self.research_roids)/7

    def base_metal_roid_production(self):
        return trunc(self.roids_metal * BASE_ROID_PRODUCTION)

    def roids_metal_production(self):
        return trunc(self.base_metal_roid_production() * self.roids_research_bonus())

    def base_cristal_roid_production(self):
        return trunc(self.roids_cristal * BASE_ROID_PRODUCTION)

    def roids_cristal_production(self):
        return trunc(self.base_cristal_roid_production() * self.roids_research_bonus())

    def base_uranium_roid_production(self):
        return trunc(self.roids_uranium * BASE_ROID_PRODUCTION)

    def roids_uranium_production(self):
        return trunc(self.base_uranium_roid_production() * self.roids_research_bonus())

    def base_gold_roid_production(self):
        return trunc(self.roids_gold * BASE_ROID_PRODUCTION)

    def roids_gold_production(self):
        return trunc(self.base_gold_roid_production() * self.roids_research_bonus())

    def roids_research_bonus(self):
        return 0.95 + self.research_roids * 0.05

    def get_research_time(self, research):
        return getattr(self, RESEARCH_LIST[research]) * BASE_RESEARCH_TIME - self.research_research+1


    def mines_metal_production(self):
        return trunc(self.mines_metal * BASE_MINE_PRODUCTION * self.mines_research_bonus())

    def mines_cristal_production(self):
        return trunc(self.mines_cristal * BASE_MINE_PRODUCTION * self.mines_research_bonus())

    def mines_uranium_production(self):
        return trunc(self.mines_uranium * BASE_MINE_PRODUCTION * self.mines_research_bonus())

    def mines_gold_production(self):
        return trunc(self.mines_gold * BASE_MINE_PRODUCTION * self.mines_research_bonus())

    def total_metal_production(self):
        return self.roids_metal_production() + self.mines_metal_production()

    def total_cristal_production(self):
        return self.roids_cristal_production() + self.mines_cristal_production()

    def total_uranium_production(self):
        return self.roids_uranium_production() + self.mines_uranium_production()

    def total_gold_production(self):
        return self.roids_gold_production() + self.mines_gold_production()

    def mines_research_bonus(self):
        return 0.95 + self.research_mines * 0.05

    def mines_bonus_str(self):
        return 5 * self.research_mines - 5

    def roids_bonus_str(self):
        return 5 * self.research_roids - 5

    def travel_time(self, target=None):
        if target == None:
            return BASE_TRAVEL_TIME - self.research_travel
        elif target.x == self.x and target.y == self.y:
            return BASE_TRAVEL_TIME - self.research_travel + CLUSTER_TRAVEL_TIME + GALAXY_TRAVEL_TIME
        elif target.x == self.x:
            return BASE_TRAVEL_TIME - self.research_travel + CLUSTER_TRAVEL_TIME
        
        return BASE_TRAVEL_TIME - self.research_travel

    def roids(self):
        return self.roids_cristal + self.roids_metal + self.roids_gold + self.roids_uranium

    def can_build(self):
        if self.current_building == 0 and self.available_buildings():
            return True
        if not self.available_buildings():
            raise OutOfSpaceException("Aumente o terraforming.")
        return False

    def remove_gold(self, qt):
        if qt > self.gold:
            raise OutOfResourcesException()
        self.gold -= qt

    def remove_metal(self, qt):
        if qt > self.metal:
            raise OutOfResourcesException()
        self.metal -= qt

    def remove_cristal(self, qt):
        if qt > self.cristal:
            raise OutOfResourcesException()
        self.cristal -= qt

    def remove_uranium(self, qt):
        if qt > self.uranium:
            raise OutOfResourcesException()
        self.uranium -= qt
        
    def sabotage(self, target, sabotage_id):
        from random import randint
        
        if self == target:
            from prod.models import SelfException
            raise SelfException
        
        if self.score * MIN_SCORE_TO_SABOTAGE > target.score:
            from prod.models import NoobBashingException
            raise NoobBashingException        
        
        descoberta = randint(0,100)
        if descoberta > 50:
            descoberta = True
        else:
            descoberta = False
            
        self.remove_metal(BASE_SABOTAGE_COST*sabotage_id)
        self.remove_cristal(BASE_SABOTAGE_COST*sabotage_id)
        self.remove_gold(BASE_SABOTAGE_COST*sabotage_id)
        
        if self.get_awareness() > target.get_awareness():
            ok = True
            
            if sabotage_id == 2: # destruir recursos
                from random import randint
                from math import floor
                
                metal = target.metal
                cristal = target.cristal
                gold = target.gold
                uranium = target.uranium
                
                target.metal =  floor(target.metal * (90+randint(0,9)) / 100)
                target.cristal = floor(target.cristal * (90+randint(0,9)) / 100)
                target.gold = floor(target.gold * (90+randint(0,9)) / 100)
                target.uranium = floor(target.uranium * (90+randint(0,9)) / 100)
                
                self.metal += metal - target.metal
                self.cristal += cristal - target.cristal
                self.gold += gold - target.gold
                self.uranium += uranium -target.uranium
                
                if descoberta:
                    target.add_news('sabotage', u'Inimigos conseguiram sabotar nossas reservas e destruiram uma boa parte de nossos recursos. Acreditamos que eles vieram do planeta %s' % self)
                else:
                    target.add_news('sabotage', u'Inimigos conseguiram sabotar nossas reservas e destruiram uma boa parte de nossos recursos.')
                    
                self.add_news('sabotage', u'Nossos sabotadores conseguiram roubar %s unidades de metal, %s unidades de cristal, %s unidades de ouro e %s unidades de urânio do planeta %s' % (intcomma(int(metal - target.metal)), intcomma(int(cristal - target.cristal)), intcomma(int(gold - target.gold)), intcomma(int(uranium -target.uranium)), target))
                
                target.awareness += BASE_SABOTAGE_AWARENESS * 2
                
            elif sabotage_id == 3: # delay research
                if target.current_research_time > 0:
                    target.current_research_time += 2
                    if descoberta:
                        target.add_news('sabotage', u'Inimigos conseguiram matar alguns dos nossos cientistas. Acreditamos que isso irá causar um atraso de 2 ticks na nossa pesquisa atual. Acreditamos que eles vieram do planeta %s' % self)
                    else:
                        target.add_news('sabotage', u'Inimigos conseguiram matar alguns dos nossos cientistas. Acreditamos que isso irá causar um atraso de 2 ticks na nossa pesquisa atual.')
                    target.awareness += BASE_SABOTAGE_AWARENESS * 2
                    
            elif sabotage_id == 4: # destroy baseships
                from prod.models import Fleet, FleetShip
                
                enemy_base = Fleet.objects.get(planet=target, static=1)
                
                if enemy_base.get_ship_count():
                    from random import choice
                    destroyed_fleetship = choice(list(enemy_base.fleetship_set.filter(quantity__gt=0)))
                    destroyed_fleetship.remove_ships( trunc(destroyed_fleetship.quantity * randint(0,20)/100))
                    if descoberta:
                        target.add_news('sabotage', u'Inimigos explodiram um dos nossos hangares e destruiram algumas naves. Acreditamos que eles vieram do planeta %s' % self)
                    else:
                        target.add_news('sabotage', u'Inimigos explodiram um dos nossos hangares e destruiram algumas naves.')
                    target.awareness += BASE_SABOTAGE_AWARENESS * 3
                    
            elif sabotage_id == 5: # destroy buildings
                total = target.destroy_building(1)
                if sum(total) == 0:
                    target.add_news('sabotage', u'Inimigos quase conseguriam explodir uma das nossas construções. Acreditamos que eles vieram do planeta %s' % self)
                    ok = None
                else:
                    if descoberta:
                        target.add_news('sabotage', u'Inimigos explodiram uma das nossas construções. Acreditamos que eles vieram do planeta %s' % self)
                    else:
                        target.add_news('sabotage', u'Inimigos explodiram uma das nossas construções.')
                target.awareness += BASE_SABOTAGE_AWARENESS * 4
                
        else:
            target.add_news('sabotage', u'Inimigos tentaram nos sabotar mas não conseguiram.')
            ok = False
            
        #target.awareness += BASE_SABOTAGE_AWARENESS
        self.awareness -= BASE_SABOTAGE_AWARENESS
        
        self.save()
        target.save()
        
        return ok
        
    def build(self, item):
        if self.can_build() and item > 0 and item <= len(BUILD_LIST):
            self.remove_gold(self.building_cost())
            self.remove_metal(self.building_cost())
            self.remove_cristal(self.building_cost())
            self.remove_uranium(self.building_cost())
            self.current_building_time = BASE_BUILDING_TIME
            self.current_building = item            
            self.save()
            return True
        raise CrapException("Nao pode iniciar. %s - %s - %s" % (self.can_build(), self.current_building_time, item) )
    
    def destroy_building(self, quantity):
        from random import randint, choice
        
        buildings = []
        for each in BUILD_LIST[1:]:
            buildings.extend([each]*getattr(self,each))
        
        building_list = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        
        for x in range(0, trunc(quantity)):
            building_list[BUILD_LIST[1:].index(choice(buildings))] += 1
            #building_list[randint(0,len(building_list)-1)] += 1
            
        if self.mines_metal - building_list[0] >= 0:
            self.mines_metal -= building_list[0]
        else:
            building_list[0] = self.mines_metal
            self.mines_metal = 0
            
        if self.mines_cristal - building_list[1] >= 0:
            self.mines_cristal -= building_list[1]
        else:
            building_list[1] = self.mines_cristal
            self.mines_cristal = 0        
            
        if self.mines_gold - building_list[2] >= 0:
            self.mines_gold -= building_list[2]
        else:
            building_list[2] = self.mines_gold
            self.mines_gold = 0        
                    
        if self.mines_uranium - building_list[3] >= 0:
            self.mines_uranium -= building_list[3]
        else:
            building_list[3] = self.mines_uranium
            self.mines_uranium = 0
            
        if self.factory_fico - building_list[4] >= 0:
            self.factory_fico -= building_list[4]
        else:
            building_list[4] = self.factory_fico
            self.factory_fico = 0        
        
     
        if self.factory_frcr - building_list[5] >= 0:
            self.factory_frcr -= building_list[5]
        else:
            building_list[5] = self.factory_frcr
            self.mines_metal = 0        
            
        if self.factory_bssp - building_list[6] >= 0:
            self.factory_bssp -= building_list[6]
        else:
            building_list[6] = self.factory_bssp
            self.factory_bssp = 0        
            
        if self.security_center - building_list[7] >= 0:
            self.security_center -= building_list[7]
        else:
            building_list[7] = self.security_center
            self.security_center = 0    
            
        if self.waveamp - building_list[8] >= 0:
            self.waveamp -= building_list[8]
        else:
            building_list[8] = self.waveamp
            self.waveamp = 0            
            
        if self.waveblock - building_list[9] >= 0:
            self.waveblock -= building_list[9]
        else:
            building_list[9] = self.waveblock
            self.waveblock = 0     
            
        self.save()

        return building_list

    def cancel_build(self):
        #print self.current_building_time
        if self.current_building_time != 0:
            self.current_building = 0
            remaining_time_percent = BASE_BUILDING_TIME/100. * self.current_building_time

            self.gold += trunc(self.building_cost() * remaining_time_percent)
            self.uranium += trunc(self.building_cost() * remaining_time_percent)
            self.metal += trunc(self.building_cost() * remaining_time_percent)
            self.cristal += trunc(self.building_cost() * remaining_time_percent)

            self.current_building_time = 0

            self.save()
            return self.building_cost() * remaining_time_percent

        raise CrapException


    def research(self, item):
        if self.can_research() and item > 0 and item <= len(RESEARCH_LIST):
            self.current_research_time = self.get_research_time(item)
            self.current_research = item
            self.save()
            return True
        raise CrapException



    def cancel_research(self):
        if self.current_research_time > 0:
            self.current_research = 0
            self.current_research_time = 0
            self.save()
            return True
        raise CrapException

    def can_research(self):
        if self.current_research == 0:
            return True
        return False

    def buildings(self):
        return self.factory_fico + self.factory_frcr + self.factory_bssp \
               + self.mines_cristal + self.mines_gold + self.mines_metal \
               + self.mines_uranium + self.waveamp + self.waveblock + self.security_center

    def coords(self):
        return u"%i:%i:%i" % (self.galaxy.x, self.galaxy.y, self.z)

    def building_cost(self):
        return self.buildings() * BASE_BUILDING_COST

    def available_buildings(self):
        return BUILDINGS_PER_TERRAFORMING*2**(self.research_terrain-1) - self.buildings()

    def current_building_str(self):
        if self.current_building_time:
            return BUILDING_DESCRIPTIONS[self.current_building][0]
        else:
            return u"Nenhuma construção ativa."

    def get_build_percent(self):
        if self.current_building_time:
            return 100 - (self.current_building_time * 100 / BASE_BUILDING_TIME)
        return 0;

    def current_research_str(self):
        if self.current_research_time:
            return RESEARCH_DESCRIPTIONS[self.current_research][0]
        else:
            return u"Nenhuma pesquisa ativa."

    def get_research_percent(self):
        if self.current_research_time:
            return 100 - (self.current_research_time * 100 / self.get_research_time(self.current_research))
        return 0

    def get_race(self):
        return u"%s" % RACE_DESCRIPTIONS[self.race][0]

    def tick_research(self):
        #print 'Res tick iniciado'
        if self.current_research_time > 0:
            self.current_research_time -= 1
            #print 'Res -1'

        if self.current_research_time == 0 and self.current_research != 0:
            cur_res = getattr(self, RESEARCH_LIST[self.current_research])
            cur_res += 1
            setattr(self, RESEARCH_LIST[self.current_research], cur_res)
            self.add_news('research', u'Nossos cientistas finalizaram a pesquisa  %s com sucesso e estão livres para pesquisar outra tecnologia.' % RESEARCH_DESCRIPTIONS[self.current_research][0] )

            self.current_research = 0
            #print 'Res Terminada'

    def tick_building(self):
        #print 'Build tick iniciado'
        if self.current_building_time > 0:
            self.current_building_time -= 1
            #print 'Build -1'

        if self.current_building_time == 0 and self.current_building != 0:

            cur_bui = getattr(self, BUILD_LIST[self.current_building])
            cur_bui += 1
            setattr(self, BUILD_LIST[self.current_building], cur_bui)

            self.add_news('build', u'Nossos construtores finalizaram a construção de 1 %s com sucesso e estão livres para trabalhar novamente.' % BUILDING_DESCRIPTIONS[self.current_building][0] )

            self.current_building = 0
            
            
    def get_ship_count(self):
        from prod.models import Fleet
        from django.db.models import Q
        
        return sum(x.get_ship_count() for x in Fleet.objects.filter(planet=self))
    
    def get_ships(self):
        from prod.models import ShipStock
        return ShipStock.objects.filter(planet=self, quantity__gt=0)
        

    def allied_ships(self):
        from prod.models import Fleet
        from django.db.models import Q

        return sum(x.get_ship_count() for x in Fleet.objects.filter(Q(target=self),  Q(action=4) | Q(action=5) | Q(action=6) | Q(action=7)))

    def get_allied_ships(self):
        from prod.models import Fleet
        from django.db.models import Q

        return Fleet.objects.filter(Q(target=self),  Q(action=4) | Q(action=5) | Q(action=6) | Q(action=7))


    def enemy_ships(self):
        from prod.models import Fleet
        from django.db.models import Q

        return sum(x.get_ship_count() for x in Fleet.objects.filter(Q(target=self), Q(action=1) | Q(action=2) | Q(action=3)))

    def get_enemy_ships(self):
        from prod.models import Fleet
        from django.db.models import Q

        return Fleet.objects.filter(Q(target=self), Q(action=1) | Q(action=2) | Q(action=3))


    def tick_combat(self):
        from prod.models import Fleet
        from django.db.models import Q

        #localfleets
        #lfleets = Fleet.objects.filter(planet=self, action=0)
        #friendlyships
        ffleets = Fleet.objects.filter( Q(Q(planet=self), Q(action=0)) | Q(Q(target=self), Q(eta=0), Q(action=4) | Q(action=5) | Q(action=6) | Q(action=7)))

        rfleets = Fleet.objects.filter( Q(target=self), Q(eta=0), Q(action=4) | Q(action=5) | Q(action=6) | Q(action=7) )

        #print ffleets.query

        #enemyships
        efleets = Fleet.objects.filter(Q(target=self), Q(eta=0), Q(action=1) | Q(action=2) | Q(action=3))

        debug_fleets = Fleet.objects.filter(Q(target=self), Q(eta=0), Q(action=3))

        #print "As frotas com action 3 sao: ",
        #print debug_fleets

        if rfleets or efleets:
            #print "tick longo"
            #friendly_fi = [(x.ship, x.quantity) for fleet in set(ffleets) for x in fleet.fleetship_set.filter(ship__cls=0, quantity__gt=0)]
            #friendly_co = [(x.ship, x.quantity) for fleet in set(ffleets) for x in fleet.fleetship_set.filter(ship__cls=1, quantity__gt=0)]
            #friendly_fr = [(x.ship, x.quantity) for fleet in set(ffleets) for x in fleet.fleetship_set.filter(ship__cls=2, quantity__gt=0)]
            #friendly_cr = [(x.ship, x.quantity) for fleet in set(ffleets) for x in fleet.fleetship_set.filter(ship__cls=3, quantity__gt=0)]
            #friendly_bs = [(x.ship, x.quantity) for fleet in set(ffleets) for x in fleet.fleetship_set.filter(ship__cls=4, quantity__gt=0)]

            #enemy_fi = [(x.ship, x.quantity) for fleet in efleets for x in fleet.fleetship_set.filter(ship__cls=0, quantity__gt=0)]
            #enemy_co = [(x.ship, x.quantity) for fleet in efleets for x in fleet.fleetship_set.filter(ship__cls=1, quantity__gt=0)]
            #enemy_fr = [(x.ship, x.quantity) for fleet in efleets for x in fleet.fleetship_set.filter(ship__cls=2, quantity__gt=0)]
            #enemy_cr = [(x.ship, x.quantity) for fleet in efleets for x in fleet.fleetship_set.filter(ship__cls=3, quantity__gt=0)]
            #enemy_bs = [(x.ship, x.quantity) for fleet in efleets for x in fleet.fleetship_set.filter(ship__cls=4, quantity__gt=0)]
            
            combat_ships = {}
            # combat_ships[a] = [[fighting, frozen, killed, stollend],[fighting, frozen, killed, stolen]]
            
            involved = set([x.planet for x in ffleets] + [x.planet for x in efleets])

            #simulate combat turns
            clog = ""
            stolen_def = []
            stolen_atk = []
            roidlog = {}

            #friendly_ships_string = u"<br/>".join(["%s - %i - %s" % (x.ship.name, x.quantity, fleet) for fleet in set(ffleets) for x in fleet.fleetship_set.all().order_by('ship__init') if x.quantity > 0])
            #enemy_ships_string = u"<br/>".join(["%s - %i - %s" % (x.ship.name, x.quantity, fleet) for fleet in efleets for x in fleet.fleetship_set.all() if x.quantity > 0 ])

            #clog += u'Antes de Iniciar: <br/><span style="color: green;">%s</span> <br/><span style="color: red;">%s</span><br/>' % ( friendly_ships_string, enemy_ships_string )

            friendly_ships = sorted([(x.ship.init, x.ship, x.quantity, x.ship.cls, x.ship.target, x.ship.attack * (x.quantity-x.frozen), x.ship.defense * x.quantity, x) for fleet in set(ffleets) for x in fleet.fleetship_set.all().order_by('ship__init') if x.quantity > 0])
            enemy_ships =    sorted([(x.ship.init, x.ship, x.quantity, x.ship.cls, x.ship.target, x.ship.attack * (x.quantity-x.frozen), x.ship.defense * x.quantity, x) for fleet in set(efleets) for x in fleet.fleetship_set.all().order_by('ship__init') if x.quantity > 0])

            for ship in (friendly_ships + enemy_ships):
                if ship[1].name not in combat_ships:
                    combat_ships[ship[1].name] = [[0,0,0,0],[0,0,0,0], ship[1].id]
            
            
            # combat_ships[a] = [[fighting, frozen, killed, stollend],[fighting, frozen, killed, stolen]]
            for ship in [x for x in friendly_ships]:
                #print ship
                if ship[1].name in combat_ships:
                    combat_ships[ship[1].name][0][0] += ship[2]
                else:
                    combat_ships[ship[1].name] = [[ship[2],0,0,0],[0,0,0,0], ship[1].id]
                
            # combat_ships[a] = [[fighting, frozen, killed, stollend],[fighting, frozen, killed, stolen]]    
            for ship in [x for x in enemy_ships]:
                #print ship
                if ship[1].name in combat_ships:
                    combat_ships[ship[1].name][1][0] += ship[2]
                else:
                    combat_ships[ship[1].name] = [[0,0,0,0],[ship[2],0,0,0], ship[1].id]
                    
            #friendly_ships = sorted([(x.ship.init, x.ship, x.quantity, x.ship.cls, x.ship.target, x.ship.attack * (x.quantity-x.frozen), x.ship.defense * x.quantity, x) for fleet in set(ffleets) for x in fleet.fleetship_set.all().order_by('ship__init') if x.quantity > 0])
            #enemy_ships =    sorted([(x.ship.init, x.ship, x.quantity, x.ship.cls, x.ship.target, x.ship.attack * (x.quantity-x.frozen), x.ship.defense * x.quantity, x) for fleet in set(efleets) for x in fleet.fleetship_set.all().order_by('ship__init') if x.quantity > 0])
            

            for this_turn in range(0, 30):
                #0,     1,      2,        3,    4,       5,         6,          7
                #init, ship, quantity, class, target, total_atk, total_def, fleetship_object
                friendly_ships = sorted([(x.ship.init, x.ship, x.quantity, x.ship.cls, x.ship.target, x.ship.attack * (x.quantity-x.frozen), x.ship.defense * x.quantity, x) for fleet in set(ffleets) for x in fleet.fleetship_set.all().order_by('ship__init') if x.quantity > 0])
                enemy_ships =    sorted([(x.ship.init, x.ship, x.quantity, x.ship.cls, x.ship.target, x.ship.attack * (x.quantity-x.frozen), x.ship.defense * x.quantity, x) for fleet in set(efleets) for x in fleet.fleetship_set.all().order_by('ship__init') if x.quantity > 0])
                
                #for ship in (friendly_ships + enemy_ships):
                    #if ship[1].name not in combat_ships:
                        #combat_ships[ship[1].name] = [[0,0,0,0],[0,0,0,0]]
                
                
                ## combat_ships[a] = [[fighting, frozen, killed, stollend],[fighting, frozen, killed, stolen]]
                #for ship in [x for x in friendly_ships if x[0] == this_turn]:
                    #print ship
                    #if ship[1].name in combat_ships:
                        #combat_ships[ship[1].name][0][0] += ship[2]
                    #else:
                        #combat_ships[ship[1].name] = [[ship[2],0,0,0],[0,0,0,0]]
                    
                ## combat_ships[a] = [[fighting, frozen, killed, stollend],[fighting, frozen, killed, stolen]]    
                #for ship in [x for x in enemy_ships if x[0] == this_turn]:
                    #print ship
                    #if ship[1].name in combat_ships:
                        #combat_ships[ship[1].name][1][0] += ship[2]
                    #else:
                        #combat_ships[ship[1].name] = [[0,0,0,0],[ship[2],0,0,0]]

                #print this_turn

                #print 'defendendo: '
                attacking_defending_ships = [x for x in friendly_ships if x[0] == this_turn]
                #print attacking_defending_ships

                #print 'atacando'
                attacking_attacking_ships = [x for x in enemy_ships if x[0] == this_turn]
                #print attacking_attacking_ships


                if not attacking_defending_ships and not attacking_attacking_ships:
                    continue
                #defending attack totals

                new_fi = [ x[5] for x in attacking_defending_ships if x[4] == 0]

                atk_def_fi = sum([x[5] for x in attacking_defending_ships if x[4] == 0 and (x[1].skill == 0 or x[1].skill == 1)]) or 1
                atk_def_co = sum([x[5] for x in attacking_defending_ships if x[4] == 1 and (x[1].skill == 0 or x[1].skill == 1)]) or 1
                atk_def_fr = sum([x[5] for x in attacking_defending_ships if x[4] == 2 and (x[1].skill == 0 or x[1].skill == 1)]) or 1
                atk_def_cr = sum([x[5] for x in attacking_defending_ships if x[4] == 3 and (x[1].skill == 0 or x[1].skill == 1)]) or 1
                atk_def_bs = sum([x[5] for x in attacking_defending_ships if x[4] == 4 and (x[1].skill == 0 or x[1].skill == 1)]) or 1

                emp_def_fi = sum([x[5] for x in attacking_defending_ships if x[4] == 0 and x[1].skill == 2]) or 1
                emp_def_co = sum([x[5] for x in attacking_defending_ships if x[4] == 1 and x[1].skill == 2]) or 1
                emp_def_fr = sum([x[5] for x in attacking_defending_ships if x[4] == 2 and x[1].skill == 2]) or 1
                emp_def_cr = sum([x[5] for x in attacking_defending_ships if x[4] == 3 and x[1].skill == 2]) or 1
                emp_def_bs = sum([x[5] for x in attacking_defending_ships if x[4] == 4 and x[1].skill == 2]) or 1

                stl_def_fi = sum([x[5] for x in attacking_defending_ships if x[4] == 0 and x[1].skill == 3]) or 1
                stl_def_co = sum([x[5] for x in attacking_defending_ships if x[4] == 1 and x[1].skill == 3]) or 1
                stl_def_fr = sum([x[5] for x in attacking_defending_ships if x[4] == 2 and x[1].skill == 3]) or 1
                stl_def_cr = sum([x[5] for x in attacking_defending_ships if x[4] == 3 and x[1].skill == 3]) or 1
                stl_def_bs = sum([x[5] for x in attacking_defending_ships if x[4] == 4 and x[1].skill == 3]) or 1
                

                stl_def_fi_percentage = ([ (x[5] / stl_def_fi, x[7]) for x in attacking_defending_ships if x[4] == 0 and x[1].skill == 3])
                stl_def_co_percentage = ([ (x[5] / stl_def_co, x[7]) for x in attacking_defending_ships if x[4] == 1 and x[1].skill == 3])
                stl_def_fr_percentage = ([ (x[5] / stl_def_fr, x[7]) for x in attacking_defending_ships if x[4] == 2 and x[1].skill == 3])
                stl_def_cr_percentage = ([ (x[5] / stl_def_cr, x[7]) for x in attacking_defending_ships if x[4] == 3 and x[1].skill == 3])
                stl_def_bs_percentage = ([ (x[5] / stl_def_bs, x[7]) for x in attacking_defending_ships if x[4] == 4 and x[1].skill == 3])                

                stolen_def = []

                #attacking attack totals
                atk_atk_fi = sum([x[5] for x in attacking_attacking_ships if x[4] == 0 and (x[1].skill == 0 or x[1].skill == 1)])
                atk_atk_co = sum([x[5] for x in attacking_attacking_ships if x[4] == 1 and (x[1].skill == 0 or x[1].skill == 1)])
                atk_atk_fr = sum([x[5] for x in attacking_attacking_ships if x[4] == 2 and (x[1].skill == 0 or x[1].skill == 1)])
                atk_atk_cr = sum([x[5] for x in attacking_attacking_ships if x[4] == 3 and (x[1].skill == 0 or x[1].skill == 1)])
                atk_atk_bs = sum([x[5] for x in attacking_attacking_ships if x[4] == 4 and (x[1].skill == 0 or x[1].skill == 1)])
                
                bombing_atk = sum([x[5] for x in attacking_attacking_ships if x[4] == 7])
                
                if bombing_atk:
                    #print "destruindo construcoes: %i" % bombing_atk
                    possible_buildings_destroyed = int(round(bombing_atk/BUILDING_LIFE))
                    
                    max_buildings_destroyed = self.buildings() * MAX_BUILDS_PERCENTAGE_DESTROYED_PER_TICK
                    builds_destroyed = 0
                    
                    if possible_buildings_destroyed > max_buildings_destroyed:
                        builds_destroyed = max_buildings_destroyed
                    else:
                        builds_destroyed = possible_buildings_destroyed
                        
                    #print "destruindo %i" % builds_destroyed
                    
                    builds_destroyed = trunc(builds_destroyed)
                    
                    destroyed = self.destroy_building(builds_destroyed)
                    
                    clog += "<br/>Destruindo: "
                    clog += "%s" % destroyed
                    
                    #self.save()
                    
                    
                roiding_atk = sum([x[5] for x in attacking_attacking_ships if x[4] == 5])

                if roiding_atk:
                    #print "atacando roids: %i" % roiding_atk

                    possible_roids_stolen = int(round(roiding_atk/ROID_LIFE)) 
                    max_roids_stolen = self.roids() * MAX_ROID_PERCENTAGE_STOLEN_PER_TICK
                    roids_stolen = 0

                    if possible_roids_stolen > max_roids_stolen:
                        roids_stolen = int(round(max_roids_stolen))
                    else:
                        roids_stolen = int(round(possible_roids_stolen))


                    #print "roubando %i" % roids_stolen

                    roids_stolen_metal = int(math.floor( roids_stolen/ self.roids()  * self.roids_metal))
                    roids_stolen_cristal = int(math.floor( roids_stolen / self.roids() * self.roids_cristal))
                    roids_stolen_uranium = int(math.floor( roids_stolen / self.roids() * self.roids_uranium))
                    roids_stolen_gold = int(math.floor( roids_stolen/ self.roids() * self.roids_gold))


                    self.roids_metal -= roids_stolen_metal
                    self.roids_cristal -= roids_stolen_cristal
                    self.roids_uranium -= roids_stolen_uranium
                    self.roids_gold -= roids_stolen_gold
                    self.save()

                    roiding_atk_percentage = ([ (x[5] / roiding_atk, x[5], x[7]) for x in attacking_attacking_ships if x[4] == 5])

                    for percentage, atk_roiding_fleet, fleetship in roiding_atk_percentage:
                        rm, rc, ru, rg = (int(math.floor(roids_stolen_metal * percentage)), 
                                          int(math.floor(roids_stolen_cristal * percentage)), 
                                          int(math.floor(roids_stolen_uranium * percentage)),
                                          int(math.floor(roids_stolen_gold * percentage)))

                        lista = [rm, rc, ru, rg]
                        #while sum(lista) < int(math.floor(atk_roiding_fleet/ROID_LIFE)):
                        #    lista[randint(0,3)] += 1


                        #print u"%s roidou, tinha %i " % (x[7].fleet.planet, x[7].fleet.planet.roids())
                        #print lista


                        planeta = Planet.objects.get(id=fleetship.fleet.planet.id)

                        planeta.roids_metal += lista[0]
                        planeta.roids_cristal += lista[1]
                        planeta.roids_uranium += lista[2]
                        planeta.roids_gold += lista[3]
                        planeta.save()

                        if planeta in roidlog:
                            roidlog[planeta].append(lista[:])
                        else:
                            roidlog[planeta] = lista[:]
                            
                        clog += u"<br/> ROIDOU %i de metal, %i de cristal, %i de uranio e %i de ouro. <br/>" % (lista[0], lista[1], lista[2], lista[3])

                        #print u"%s roidou e ficou com %i " % (planeta, planeta.roids())


                #print "atk anti-fi: %i\natk anti-co: %i\natk anti-fr: %i\natk anti-cr: %i\natk anti-bs:%i" % (atk_atk_fi, atk_atk_co, atk_atk_fr, atk_atk_cr, atk_atk_bs)

                emp_atk_fi = sum([x[5] for x in attacking_attacking_ships if x[4] == 0 and x[1].skill == 2]) or 1
                emp_atk_co = sum([x[5] for x in attacking_attacking_ships if x[4] == 1 and x[1].skill == 2]) or 1
                emp_atk_fr = sum([x[5] for x in attacking_attacking_ships if x[4] == 2 and x[1].skill == 2]) or 1
                emp_atk_cr = sum([x[5] for x in attacking_attacking_ships if x[4] == 3 and x[1].skill == 2]) or 1
                emp_atk_bs = sum([x[5] for x in attacking_attacking_ships if x[4] == 4 and x[1].skill == 2]) or 1

                stl_atk_fi = sum([x[5] for x in attacking_attacking_ships if x[4] == 0 and x[1].skill == 3]) or 1
                stl_atk_co = sum([x[5] for x in attacking_attacking_ships if x[4] == 1 and x[1].skill == 3]) or 1
                stl_atk_fr = sum([x[5] for x in attacking_attacking_ships if x[4] == 2 and x[1].skill == 3]) or 1
                stl_atk_cr = sum([x[5] for x in attacking_attacking_ships if x[4] == 3 and x[1].skill == 3]) or 1
                stl_atk_bs = sum([x[5] for x in attacking_attacking_ships if x[4] == 4 and x[1].skill == 3]) or 1
                
                    
                    
                stl_atk_fi_percentage = ([ (x[5] / stl_atk_fi, x[7]) for x in attacking_attacking_ships if x[4] == 0 and x[1].skill == 3])
                stl_atk_co_percentage = ([ (x[5] / stl_atk_co, x[7]) for x in attacking_attacking_ships if x[4] == 1 and x[1].skill == 3])
                stl_atk_fr_percentage = ([ (x[5] / stl_atk_fr, x[7]) for x in attacking_attacking_ships if x[4] == 2 and x[1].skill == 3])
                stl_atk_cr_percentage = ([ (x[5] / stl_atk_cr, x[7]) for x in attacking_attacking_ships if x[4] == 3 and x[1].skill == 3])
                stl_atk_bs_percentage = ([ (x[5] / stl_atk_bs, x[7]) for x in attacking_attacking_ships if x[4] == 4 and x[1].skill == 3])

                stolen_atk = []

                #defending defense totals
                def_def_fi = sum([x[6] for x in friendly_ships if x[3] == 0]) or 1
                def_def_co = sum([x[6] for x in friendly_ships if x[3] == 1]) or 1
                def_def_fr = sum([x[6] for x in friendly_ships if x[3] == 2]) or 1
                def_def_cr = sum([x[6] for x in friendly_ships if x[3] == 3]) or 1
                def_def_bs = sum([x[6] for x in friendly_ships if x[3] == 4]) or 1

                #attacking defense totals
                def_atk_fi = sum([x[6] for x in enemy_ships if x[3] == 0]) or 1
                def_atk_co = sum([x[6] for x in enemy_ships if x[3] == 1]) or 1
                def_atk_fr = sum([x[6] for x in enemy_ships if x[3] == 2]) or 1
                def_atk_cr = sum([x[6] for x in enemy_ships if x[3] == 3]) or 1
                def_atk_bs = sum([x[6] for x in enemy_ships if x[3] == 4]) or 1

                # ship, quantity, percentage, fleetship
                def_def_fi_percentage = [(x[1], x[2], (x[6]) / def_def_fi, x[7]) for x in friendly_ships if x[3] == 0]
                def_def_co_percentage = [(x[1], x[2], (x[6]) / def_def_co, x[7]) for x in friendly_ships if x[3] == 1]
                def_def_fr_percentage = [(x[1], x[2], (x[6]) / def_def_fr, x[7]) for x in friendly_ships if x[3] == 2]
                def_def_cr_percentage = [(x[1], x[2], (x[6]) / def_def_cr, x[7]) for x in friendly_ships if x[3] == 3]
                def_def_bs_percentage = [(x[1], x[2], (x[6]) / def_def_bs, x[7]) for x in friendly_ships if x[3] == 4]

                def_atk_fi_percentage = [(x[1], x[2], (x[6]) / def_atk_fi, x[7]) for x in enemy_ships if x[3] == 0]
                def_atk_co_percentage = [(x[1], x[2], (x[6]) / def_atk_co, x[7]) for x in enemy_ships if x[3] == 1]
                def_atk_fr_percentage = [(x[1], x[2], (x[6]) / def_atk_fr, x[7]) for x in enemy_ships if x[3] == 2]
                def_atk_cr_percentage = [(x[1], x[2], (x[6]) / def_atk_cr, x[7]) for x in enemy_ships if x[3] == 3]
                def_atk_bs_percentage = [(x[1], x[2], (x[6]) / def_atk_bs, x[7]) for x in enemy_ships if x[3] == 4]

                if emp_atk_fi > 0 or emp_atk_co > 0 or emp_atk_fr > 0 or emp_atk_cr > 0 or emp_atk_bs > 0:
                    for each, atkp in [x for x in [(def_def_fi_percentage, emp_atk_fi),
                                                   (def_def_co_percentage, emp_atk_co), 
                                                   (def_def_fr_percentage, emp_atk_fr),
                                                   (def_def_cr_percentage, emp_atk_cr),
                                                   (def_def_bs_percentage, emp_atk_bs)] if x[1] > 0]:
                        for ship, quantity, percentage, fleetship in each:
                            hit = atkp * percentage

                            frozen =  int(round(hit / ship.defense))
                            
                            # combat_ships[a] = [[fighting, frozen, killed, stollend],[fighting, frozen, killed, stolen]]
                            if frozen > 0:
                                qt = fleetship.freeze(frozen)
                                combat_ships[ship.name][0][1] += qt
                                fleetship.save()
                                #clog += u"<br/>I%i - Atk lança %i EMP em DEF paralizando %i %s" % (this_turn, hit, qt, ship.name)




                if emp_def_fi > 0 or emp_def_co > 0 or emp_def_fr > 0 or emp_def_cr > 0 or emp_def_bs > 0:
                    for each, atkp in [x for x in [(def_atk_fi_percentage, emp_def_fi),
                                                   (def_atk_co_percentage, emp_def_co), 
                                                   (def_atk_fr_percentage, emp_def_fr),
                                                   (def_atk_cr_percentage, emp_def_cr),
                                                   (def_atk_bs_percentage, emp_def_bs)] if x[1] > 0]:
                        for ship, quantity, percentage, fleetship in each:
                            hit = atkp * percentage
                            frozen =  int(round(hit / ship.defense))

                            if frozen > 0:
                                qt = fleetship.freeze(frozen)
                                combat_ships[ship.name][1][1] += qt
                                fleetship.save()
                                #clog += u"<br/>I%i - DEF lança %i EMP em ATK paralizando %i %s" % (this_turn, hit, qt, ship.name)


                if atk_atk_fi > 0 or atk_atk_co > 0 or atk_atk_fr > 0 or atk_atk_cr > 0 or atk_atk_bs > 0:
                    #if atk_atk_co:
                    #    print "ataque do ataque na defesa em corvetas: %i" % atk_atk_co

                    for each, atkp in [x for x in [(def_def_fi_percentage, atk_atk_fi),
                                                   (def_def_co_percentage, atk_atk_co), 
                                                   (def_def_fr_percentage, atk_atk_fr),
                                                   (def_def_cr_percentage, atk_atk_cr),
                                                   (def_def_bs_percentage, atk_atk_bs)] if x[1] > 0]:
                        for ship, quantity, percentage, fleetship in each:
                            hit = atkp * percentage
                            #print "DEF levou %f" % hit
                            dead = int(round(hit / ship.defense))


                            if dead > 0:
                                qt = fleetship.remove_ships(trunc(dead))
                                fleetship.save()
                                combat_ships[ship.name][0][2] += qt
                                #clog += u"<br/>I%i - Atk atira %i em DEF matando %i %s" % (this_turn, hit, qt, ship)


                if atk_def_fi > 0 or atk_def_co > 0 or atk_def_fr > 0 or atk_def_cr > 0 or atk_def_bs > 0:
                    for each, atkp in [x for x in [(def_atk_fi_percentage, atk_def_fi),
                                                   (def_atk_co_percentage, atk_def_co),
                                                   (def_atk_fr_percentage, atk_def_fr),
                                                   (def_atk_cr_percentage, atk_def_cr),
                                                   (def_atk_bs_percentage, atk_def_bs)] if x[1] > 0]:
                        for ship, quantity, percentage, fleetship in each:
                            hit = atkp * percentage
                            #print "ATK levou %f" % hit
                            dead = int(round(hit / ship.defense))
                            #clog += u"<br/>ATK - Morreram: %i - %s" % (dead, ship)

                            if dead > 0:
                                qt = fleetship.remove_ships(trunc(dead))   
                                fleetship.save()
                                combat_ships[ship.name][1][2] += qt
                                #clog += u"<br/>I%i - Def atira %i em ATK matando %i %s" % (this_turn, hit, qt, ship)



                if stl_atk_fi > 0 or stl_atk_co > 0 or stl_atk_fr > 0 or stl_atk_cr > 0 or stl_atk_bs > 0:
                    #lol

                    for each, atkp in [x for x in [(def_def_fi_percentage, stl_atk_fi),
                                                   (def_def_co_percentage, stl_atk_co), 
                                                   (def_def_fr_percentage, stl_atk_fr),
                                                   (def_def_cr_percentage, stl_atk_cr),
                                                   (def_def_bs_percentage, stl_atk_bs)] if x[1] > 0]:
                        for ship, quantity, percentage, fleetship in each:
                            hit = atkp * percentage
                            #print "DEF levou %f" % hit
                            dead = int(round(hit / ship.defense))
                            #clog += u"<br/>DEF - Foi roubada: %i - %s" % (dead, ship)

                            if dead > 0:
                                qt = fleetship.remove_ships(trunc(dead))
                                combat_ships[ship.name][0][3] += qt
                                fleetship.save()

                                #ships attacker have stolen
                                stolen_def.append([ship, qt])
                                #clog += u"<br/>I%i - Atk rouba %i de DEF roubando %i %s" % (this_turn, hit, qt, ship)


                if stl_def_fi > 0 or stl_def_co > 0 or stl_def_fr > 0 or stl_def_cr > 0 or stl_def_bs > 0:
                    for each, atkp in [x for x in [(def_atk_fi_percentage, stl_def_fi),
                                                   (def_atk_co_percentage, stl_def_co),
                                                   (def_atk_fr_percentage, stl_def_fr),
                                                   (def_atk_cr_percentage, stl_def_cr),
                                                   (def_atk_bs_percentage, stl_def_bs)] if x[1] > 0]:
                        for ship, quantity, percentage, fleetship in each:
                            hit = atkp * percentage
                            #print "ATK levou %f" % hit
                            dead = int(round(hit / ship.defense))
                            #clog += u"<br/>ATK - Morreram: %i - %s" % (dead, ship)

                            if dead > 0:
                                qt = fleetship.remove_ships(trunc(dead))
                                combat_ships[ship.name][1][3] += qt
                                fleetship.save()            

                                #ships defenders have stolen
                                stolen_atk.append([ship, qt])
                                #clog += u"<br/>I%i - DEF rouba %i de atk roubando %i %s" % (this_turn, hit, qt, ship)


                #print friendly_ships
                #print enemy_ships

                if stolen_def:
                    for ship, quantity in stolen_def:
                        if ship.cls == 0:
                            for percentage, fleetship in stl_atk_fi_percentage:
                                fleetship.fleet.add_ships(ship, trunc(percentage*quantity))
                                #clog += "<br/>Adicionando Caças"

                        if ship.cls == 1:
                            for percentage, fleetship in stl_atk_co_percentage:
                                fleetship.fleet.add_ships(ship, trunc(percentage*quantity))
                                #clog += "<br/>Adicionando 2"


                        if ship.cls == 2:
                            for percentage, fleetship in stl_atk_fr_percentage:
                                fleetship.fleet.add_ships(ship, trunc(percentage*quantity))
                                #clog += "<br/>Adicionando 3"


                        if ship.cls == 3:
                            for percentage, fleetship in stl_atk_cr_percentage:
                                fleetship.fleet.add_ships(ship, trunc(percentage*quantity))
                                #clog += "<br/>Adicionando 4"

                        if ship.cls == 4:
                            for percentage, fleetship in stl_atk_bs_percentage:
                                fleetship.fleet.add_ships(ship, trunc(percentage*quantity))                    
                                #clog += "<br/>Adicionando 5"

                #print 'naves roubadas: ',
                #print stolen_atk

                if stolen_atk:
                    for ship, quantity in stolen_atk:
                        if ship.cls == 0:
                            for percentage, fleetship in stl_def_fi_percentage:
                                fleetship.fleet.add_ships(ship, trunc(percentage*quantity))
                                #clog += "<br/>Adicionando 6"

                        if ship.cls == 1:
                            for percentage, fleetship in stl_def_co_percentage:
                                fleetship.fleet.add_ships(ship, trunc(percentage*quantity))
                                #clog += "<br/>Adicionando 7"


                        if ship.cls == 2:
                            for percentage, fleetship in stl_def_fr_percentage:
                                fleetship.fleet.add_ships(ship, trunc(percentage*quantity))                                        
                                #clog += "<br/>Adicionando 8"


                        if ship.cls == 3:
                            for percentage, fleetship in stl_def_cr_percentage:
                                fleetship.fleet.add_ships(ship, trunc(percentage*quantity))
                                #clog += "<br/>Adicionando 9"

                        if ship.cls == 4:
                            for percentage, fleetship in stl_def_bs_percentage:
                                fleetship.fleet.add_ships(ship, trunc(percentage*quantity))       
                                #clog += "<br/>Adicionando 10"


            for fleetships in friendly_ships+enemy_ships:
                fleetships[7].unfreeze()  
                
            # combat_ships[a] = [[fighting, frozen, killed, stollend],[fighting, frozen, killed, stolen]]
            result_table = u"""Combate ocorrido em órbita de %s
            <table class='table table-striped table-bordered'>
            <thead>
            <tr>
            <th></th>
            <th colspan='4'>DEFESA</th>
            <th colspan='4'>ATAQUE</th>
            </tr>
            <tr>
            <th>Nave</th>
            <th>Qtd</th>
            <th>Paralizadas</th>
            <th>Mortas</th>
            <th>Roubadas</th>
            <th>Qtd</th>
            <th>Paralizadas</th>
            <th>Mortas</th>
            <th>Roubadas</th>            
            </tr>
            </thead>
            <tbody>
            """ % self
            from operator import itemgetter
            
            for ship_name, lists in sorted(combat_ships.iteritems(), key=lambda x: x[1][2]):
                friendly = lists[0]
                enemy = lists[1]
                ship = lists[2]
                result_table += u"""<tr><td>%s</td><td>%i</td><td>%i</td><td>%i</td><td>%i</td><td>%i</td><td>%i</td><td>%i</td><td>%i</td></tr>""" % (ship_name, friendly[0], friendly[1], friendly[2], friendly[3], enemy[0], enemy[1], enemy[2], enemy[3])
            
            result_table += u"</tbody></table>"
            
            clog += result_table

            clog += "%s" % roidlog

            #clog += u"<br/><br/>DEPOIS do COMBATE:<br/>"
            #friendly_ships = u"<br/>".join(["%s - %i - %s" % (x.ship.name, x.quantity, fleet) for fleet in set(ffleets) for x in fleet.fleetship_set.all().order_by('ship__init') if x.quantity > 0])
            #enemy_ships = u"<br/>".join(["%s - %i - %s" % (x.ship.name, x.quantity, fleet) for fleet in efleets for x in fleet.fleetship_set.all() if x.quantity > 0 ])

            #friendly_fleets = u"<br/>".join([unicode(x) for x in set(list(ffleets))])
            #enemy_fleets = u"<br/>".join([unicode(x) for x in efleets])

            for each in involved:
                each.add_news('war_report', clog)
                if each in roidlog:
                    each.add_news('spoil', "%s" % roidlog[each])

            if self not in involved:
                self.add_news('war_report', clog)




    def tick(self):        
        #from prod.models import Fleet
        #fleets = Fleet.objects.filter(planet=self, static=0)

        #for fleet in fleets:
        #    fleet.first_move_tick()

        self.metal += self.roids_metal_production() + self.mines_metal_production()
        self.cristal += self.roids_cristal_production() + self.mines_cristal_production()
        self.uranium += self.roids_uranium_production() + self.mines_uranium_production()
        self.gold += self.roids_gold_production() + self.mines_gold_production()
        
        if self.awareness < 50:
            self.awareness += 5
            if self.awareness > 50:
                self.awareness = 50
        elif self.awareness > 50:
            self.awareness -= 5
            if self.awareness < 50:
                self.awareness = 50

        self.tick_research()
        self.tick_building()


        from prod.models import ShipYard       
        planetshipyards = ShipYard.objects.filter(planet=self)

        if planetshipyards:
            for each in planetshipyards:
                each.tick()


        #combat
        self.tick_combat()



        #fleets = Fleet.objects.filter(planet=self, static=0)
        #for fleet in fleets:
        #    fleet.second_move_tick()

        #print self.mines_gold
        self.score = self.buildings()*5000 + trunc(self.average_research_level()*100000) + self.roids()*1000 + trunc((self.metal + self.cristal + self.uranium + self.gold)/100)

        from prod.models import ShipStock
        for ship in ShipStock.objects.filter(planet=self):
            #print ship.quantity * trunc((ship.ship.cost_metal + ship.ship.cost_cristal + ship.ship.cost_gold) / 10)
            self.score += ship.quantity * trunc((ship.ship.cost_metal + ship.ship.cost_cristal + ship.ship.cost_gold) / 10)
            
        self.score = int(round(self.score, -3))
        #print self.average_research_level()*100000
        self.save()

    def __unicode__(self):
        return u"%i.%i.%i - %s de %s" % (self.x, self.y, self.z, self.ruler, self.name)

    class Meta:
        ordering = ('x','y','z')
        unique_together = ('x','y','z')


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if len(Galaxy.objects.all()) == 0:
            gal = Galaxy()
            gal.save()

        else:
            from random import shuffle

            #print Galaxy.objects.all()

            gals = list(Galaxy.objects.all())
            shuffle(gals)

            #print 'aqui'

            while True:
                #print 'oi'
                gal = gals.pop()

                #print gal

                #print 'foi'

                #print gal.is_full()

                if not gal.is_full():
                    #print gal
                    break

        from random import randint
        a = Planet.objects.create(user=instance, galaxy=gal, name="%i" % randint(0,1000000) , ruler="%i" % randint(0,1000000), x = gal.x, y =gal.y, z=randint(25,100))
        gal.add_planet(a)

        from prod.models import Fleet
        base = Fleet(planet=a, static=1).save()
        f1 = Fleet(planet=a).save()
        f2 = Fleet(planet=a).save()
        f3 = Fleet(planet=a).save()

post_save.connect(create_user_profile, sender=User)
