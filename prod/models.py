#-*- encoding: utf-8 *-*
from __future__ import division
from django.db import models
from base.models import RACES, Planet, OutOfResourcesException
from math import trunc
#from django.shortcuts import get_object_or_crea

PROD_TIME = 8
FLEETS = 3
MIN_SCORE_TO_ATTACK = 0.4

SKILLS = ((0, u'Normal'),
          (1, u'Invisível'),
          (2, u'EMP'),
          (3, u'Roubo'),
          (4, u'Bombardeamento'),
          (5, u'Asteróides'),
          )

CLASSES = ((0, u'Caça'),
           (1, u'Corveta'),
           (2, u'Fragata'),
           (3, u'Cruzador'),
           (4, u'Nave-Mãe'),
           (5, u'Asteróides'),
           (6, u'Especial'),
           (7, u'Construções')
           )
           
class CantBuildException(Exception):
    pass

class FactoryFullException(Exception):
    pass

class FleetAwayException(Exception):
    pass

class SelfException(Exception):
    pass

class LackUraniunException(Exception):
    pass

class EmptyFleetException(Exception):
    pass

class NoobBashingException(Exception):
    pass

class Ship(models.Model):
    name = models.CharField(max_length=30)
    cls = models.PositiveSmallIntegerField(choices=CLASSES)
    skill = models.PositiveSmallIntegerField(choices=SKILLS)
    
    init = models.PositiveIntegerField(default=0)
    attack = models.PositiveIntegerField(default=0)
    defense = models.PositiveIntegerField(default=0)
    
    target = models.PositiveSmallIntegerField(choices=CLASSES)
    
    cost_metal = models.IntegerField(default=0)
    cost_cristal = models.IntegerField(default=0)
    #cost_uranium = models.IntegerField(default=0)
    cost_gold = models.IntegerField(default=0)
    
    race = models.PositiveIntegerField(choices=RACES)
    
    def get_class_as_str(self):
        return u"%s" % CLASSES[self.cls][1]
    
    def get_target_as_str(self):
        return u"%s" % CLASSES[self.target][1]
    
    def get_race_as_str(self):
        return u"%s" % RACES[self.race][1]
    
    def get_skill_as_str(self):
        return u"%s" % SKILLS[self.skill][1]
    
    def __unicode__(self):
        return u"%s - %s - %s" % (self.name, self.get_class_as_str(), SKILLS[self.skill][1])
    
    
class ShipYard(models.Model):
    planet = models.ForeignKey(Planet)
    ship = models.ForeignKey(Ship)
    quantity = models.PositiveIntegerField(default=0)
    time = models.IntegerField(default=PROD_TIME)
    
    def cancel_prod(self):
        total_metal = self.ship.cost_metal * self.quantity
        total_cristal = self.ship.cost_cristal * self.quantity
        total_gold = self.ship.cost_gold * self.quantity
        
        relative_gold = int(round(total_gold * self.time / PROD_TIME))
        relative_metal = int(round(total_metal * self.time / PROD_TIME))
        relative_cristal = int(round(total_cristal * self.time / PROD_TIME))
        
        self.planet.metal += relative_metal
        self.planet.cristal += relative_cristal
        self.planet.gold += relative_gold
        
        self.planet.save()
        
        return (relative_metal, relative_cristal, relative_gold)
    
    def start_prod(self, qt):
        
        if self.ship.cls == 0:
            if self.planet.can_build_fi():
                mqt = self.planet.max_build_fi() - sum([x.quantity for x in ShipYard.objects.filter(planet=self.planet, ship__cls=0)])
            else:
                raise CantBuildException
        elif self.ship.cls == 1:
            if self.planet.can_build_co():
                mqt = self.planet.max_build_co() - sum([x.quantity for x in ShipYard.objects.filter(planet=self.planet, ship__cls=1)])
  
        elif self.ship.cls == 2:
            if self.planet.can_build_fr():
                mqt = self.planet.max_build_fr() - sum([x.quantity for x in ShipYard.objects.filter(planet=self.planet, ship__cls=2)])
            else:
                raise CantBuildException
        elif self.ship.cls == 3:
            if self.planet.can_build_cr():
                mqt = self.planet.max_build_cr() - sum([x.quantity for x in ShipYard.objects.filter(planet=self.planet, ship__cls=3)])
            else:
                raise CantBuildException
        elif self.ship.cls == 4:
            if self.planet.can_build_bs():
                mqt = self.planet.max_build_bs() - sum([x.quantity for x in ShipYard.objects.filter(planet=self.planet, ship__cls=4)])
            else:
                raise CantBuildException
  
        #elif self.ship.cls == 5:
        #    pass
        
        max_prod = min([ self.planet.gold / self.ship.cost_gold, self.planet.cristal / self.ship.cost_cristal, self.planet.metal / self.ship.cost_metal ])
        
        from math import trunc
        qt = trunc(min([max_prod, qt, mqt]))
        #if qt > max_prod:
        #    qt = max_prod
        
        if max_prod < 1:
            raise OutOfResourcesException
        
        if qt < 1:
            raise FactoryFullException
        
        self.planet.remove_gold( qt * self.ship.cost_gold )
        self.planet.remove_cristal( qt * self.ship.cost_cristal )
        self.planet.remove_metal ( qt * self.ship.cost_metal )
        
        self.planet.save()
        
        self.quantity = qt
        self.time = PROD_TIME
        self.save()
        
        return qt
    
    def tick(self):
        self.time -= 1
        
        if self.time == 0:
            stock = ShipStock.objects.get_or_create(planet=self.planet, ship=self.ship)[0]
            stock.quantity += self.quantity
            stock.save()
            
            base = Fleet.objects.get(planet=self.planet, static=1)
            fleetship = FleetShip.objects.get_or_create(fleet=base, ship=self.ship)[0]
            fleetship.quantity += self.quantity
            fleetship.save()
            
            self.delete()
            return 1
        
        self.save()
        
    def __unicode__(self):
        return u"%s - %s - %i (%i)"  % (self.planet, self.ship, self.quantity, self.time)
    
    
class ShipStock(models.Model):
    planet = models.ForeignKey(Planet)
    ship = models.ForeignKey(Ship)
    quantity = models.IntegerField(default=0)
    
    def __unicode__(self):
        return u"%s - %s - %i" % (self.planet, self.ship, self.quantity)
    
    def get_in_base(self):
        base = Fleet.objects.get(planet=self.planet, static=1)
        return FleetShip.objects.get_or_create(fleet=base, ship=self.ship)[0].quantity
    
    def get_in_fleet1(self):
        base = Fleet.objects.filter(planet=self.planet, static=0)[0]
        return FleetShip.objects.get_or_create(fleet=base, ship=self.ship)[0].quantity
    
    def get_in_fleet2(self):
        base = Fleet.objects.filter(planet=self.planet, static=0)[1]
        return FleetShip.objects.get_or_create(fleet=base, ship=self.ship)[0].quantity    
    
    def get_in_fleet3(self):
        base = Fleet.objects.filter(planet=self.planet, static=0)[2]
        return FleetShip.objects.get_or_create(fleet=base, ship=self.ship)[0].quantity        
    
    class Meta:
        unique_together = ('planet', 'ship')
        ordering = ('ship',)
    
    
class Fleet(models.Model):
    planet = models.ForeignKey(Planet)
    action = models.SmallIntegerField(default=0)
    target = models.ForeignKey(Planet, related_name="target", blank=True, null=True)
    eta = models.SmallIntegerField(default=0)
    static = models.SmallIntegerField(default=0)
    
    def get_ship_true_count(self):
        count = 0
        for each in self.fleetship_set.all():
                count += each.quantity
                
        return count
    
    def get_ship_count(self):
        count = 0
        for each in self.fleetship_set.all():
            if each.ship.skill != 1:
                count += each.quantity
                
        return count
    
    def __unicode__(self):
        return u"Frota %i de %s (%s)" % (self.id, self.planet, self.get_action())
    
    def get_action(self):
        if self.action == 1:
            return u'Atacar 1 tick [%s]' % self.target
        elif self.action == 2:
            return u'Atacar 2 ticks [%s]' % self.target
        elif self.action == 3:
            return u'Atacar 3 ticks [%s]' % self.target
        elif self.action == 4:
            return u'Defender 1 tick [%s]' % self.target
        elif self.action == 5:
            return u'Defender 2 ticks [%s]' % self.target
        elif self.action == 6:
            return u'Defender 3 ticks [%s]' % self.target
        elif self.action == 7:
            return u'Defender 4 ticks [%s]' % self.target
        elif self.action == 10:
            return u'RETORNANDO'
        elif self.action == 0:
            return u"Aguardando Ordens"
    
    def set_action(self, target, eta, action):
        if not self.get_ship_true_count():
            raise EmptyFleetException
        
        if self.planet == target and int(action) != 10:
            raise SelfException
        
        if int(action) == 10 and self.action != 10 and self.action != 0: #recuar frota
            self.action = 10
            
            relative_uranium = trunc( self.eta / self.planet.travel_time(self.target) * self.cost() )           
            self.eta = self.planet.travel_time(self.target) - self.eta
            self.target = self.planet
            self.save()
            self.planet.uranium += relative_uranium
            self.planet.save()            
            
            if self.eta == 0:
                self.action = 0
                self.save()
            
            return relative_uranium
            
        elif action in ['1','2','3','4','5','6','7']: #atacar ou defender
            
            if action in ['1','2','3']: #cap pra atacar
                if self.planet.score * MIN_SCORE_TO_ATTACK > target.score:
                    raise NoobBashingException
                
            self.target = target
            self.eta = self.planet.travel_time(self.target)
            self.action = int(action)
            self.planet.remove_uranium(self.cost())
            self.save()
            self.planet.save()
           
        self.save() 
        return 0
            
    def first_move_tick(self):
        if self.action == 10 and self.eta == 1:
            self.action = 0
            self.eta = 0
            self.save()
            
        if self.eta > 0 and self.action != 0:
            self.eta -= 1
            self.save()
            
        if self.eta == 0 and self.action == 10:
            self.action = 0
            self.eta = 0
            self.save()
            
        #if self.action == 3 and self.eta == 0 :
        #    print 'terminou o move tick e a action eh 3 e o eta eh 0 e a frota eh %s' % self
            
        
        
    def second_move_tick(self):
        #if self.action == 3 and self.eta == 0:
        #    print "terminou o combate e a action eh 3 e o eta eh 0 e a frota eh %s" % self
        #    #return 1
            
        if self.action in [7, 6, 5, 3, 2] and self.eta == 0:
            self.action -= 1
            self.save()
            
        elif (self.action == 1 or  self.action == 4) and self.eta == 0:
            self.action = 10
            self.eta = self.planet.travel_time(self.target)
            self.target = self.planet
            self.save()
            
            
        if self.get_ship_true_count() == 0:
            self.action = 0
            self.target = self.planet
            self.eta = 0
            self.save()
        
        #self.save()
    
    def cost(self):
        cost = 0
        for ship in FleetShip.objects.filter(fleet=self):
            cost += ship.quantity * trunc((ship.ship.cost_metal + ship.ship.cost_cristal + ship.ship.cost_gold) / 100)
        return cost
    
    def moving(self):
        if self.action == 0:
            return False
        return True
    
    def move(self, ship, to, qt):
        
        if self.moving() or to.moving():
            raise FleetAwayException
        
        myfs = FleetShip.objects.get_or_create(fleet=self, ship=ship)[0]
        tofs = FleetShip.objects.get_or_create(fleet=to, ship=ship)[0]
        
        print qt,
        print myfs.quantity
        print qt > myfs.quantity
        
        if qt > myfs.quantity or qt < 0:
            qt = myfs.quantity
        
        print qt
        
        if myfs == tofs:
            raise SelfException
        
        myfs.quantity -= qt
        
        
        tofs.quantity += qt
        
        tofs.save()
        myfs.save()
        
    def add_ships(self, ship, qt):
        myfs = FleetShip.objects.get_or_create(fleet=self, ship=ship)[0]
        myfs.quantity += qt
        
        
        myshipstock = ShipStock.objects.get_or_create(planet=self.planet, ship=ship)[0]
        myshipstock.quantity += qt
        
        myfs.save()
        myshipstock.save()
        
    class Meta:
        ordering = ('id',)
    
class FleetShip(models.Model):
    fleet = models.ForeignKey(Fleet)
    ship = models.ForeignKey(Ship)
    quantity = models.IntegerField(default=0)
    frozen = models.IntegerField(default=0)
    
    def remove_ships(self, qt):
        
        if qt > self.quantity:
            qt = self.quantity
            
        self.quantity -= qt
        shipstock = self.fleet.planet.shipstock_set.get(ship=self.ship)
        shipstock.quantity -= qt
        
        self.save()
        shipstock.save()
        
        return qt
        
    def unfreeze(self):
        self.frozen = 0
        self.save()
        
    def freeze(self, qt):
        if (qt + self.frozen) > self.quantity:
            qt = self.quantity - self.frozen
            
        self.frozen = qt
        
        return qt
    
    class Meta:
        unique_together = ('fleet', 'ship')
