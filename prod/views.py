#*-* encoding: utf-8 *-*
from django.shortcuts import get_object_or_404, redirect, render_to_response, RequestContext
from django.contrib.auth.decorators import login_required

from django.contrib.humanize.templatetags.humanize import intcomma

from models import Ship, ShipStock, ShipYard, CantBuildException, FactoryFullException, Fleet, FleetShip, SelfException, EmptyFleetException, NoobBashingException
from base.models import Planet, OutOfResourcesException
from django.contrib import messages

@login_required
def production(request):
    planet = request.user.get_profile()
    ships = Ship.objects.filter(race=planet.race)
    if request.method == 'POST':
        #print request.POST
        print request.POST.keys()
        
        bships = []
        
        for x in request.POST.keys():
            try:
                if x.startswith("ship-") and len(x) > 5:
                    bships.append( int(x[5:]) )
            except:
                pass
        
        
        for each in bships:
            try:
                qt = int(request.POST["ship-%i" % each])
                ship = Ship.objects.get(id=each, race=planet.race)
                yard = ShipYard(planet=planet, ship=ship)
                qtb = yard.start_prod(qt)
                messages.add_message(request, messages.INFO, u"Foi iniciada a produção de %s %s" % (intcomma(qtb), ship.name))
                yard.save()
            except OutOfResourcesException:
                messages.add_message(request, messages.ERROR, u'Você não tem recursos suficientes pra iniciar esse pedido.')
            except CantBuildException:
                messages.add_message(request, messages.ERROR, u"Você não tem fábricas para produzir %s. Construa pelo menos uma fábrica." % ship.get_class_as_str() )
            except FactoryFullException:
                messages.add_message(request, messages.ERROR, u"Todas as fábricas para a produção de %s estão lotadas. Tente construir mais fábricas, \
                ou aguarde até que a fila atual termine." % ship.get_class_as_str())
            except:
                pass
        return redirect("production")
            
    return render_to_response('in/production.html', {'planet': planet, 'ships': ships, 'production': 1}, context_instance=RequestContext(request))


@login_required
def cancel_production(request, prod_id):
    planet = request.user.get_profile()
    shipyard = get_object_or_404(ShipYard, planet=planet, id=prod_id)
    
    metal, cristal, gold = shipyard.cancel_prod()
    
    shipyard.delete()
    
    messages.add_message(request, messages.INFO, u"Foram devolvidas %s unidades de metal \
    %s unidades de cristal e %s unidades de ouro." % (intcomma(metal), intcomma(cristal), intcomma(gold)))
    
    return redirect("production")

@login_required
def military(request):
    planet = request.user.get_profile()    
    
    if request.method == 'POST':
        for x in range(6):
            try:
                shipid = request.POST['ship-%i' % x]
                #ship = Ship.objects.get(id=shipid, race=planet.race)
                
                if shipid in ['99', '98', '97', '96', '95', '94']:
                    pass
                else:
                    ship = Ship.objects.get(id=shipid)
                
                fromfleetid = request.POST['from-%i' % x]
                fromfleet = Fleet.objects.get(id=fromfleetid, planet=planet, action=0)
                
                tofleetid = request.POST['to-%i' % x]
                tofleet = Fleet.objects.get(id=tofleetid, planet=planet, action=0)
                
                #todas as naves
                if shipid == '99':
                    for fleetship in fromfleet.fleetship_set.filter(quantity__gt=0):
                        fromfleet.move(fleetship.ship, tofleet, fleetship.quantity)
                        
                #todos os caças
                elif shipid == '98':
                    for fleetship in fromfleet.fleetship_set.filter(quantity__gt=0, ship__cls=0):
                        fromfleet.move(fleetship.ship, tofleet, fleetship.quantity)
                        
                #todos os corvetas
                elif shipid == '97':
                    for fleetship in fromfleet.fleetship_set.filter(quantity__gt=0, ship__cls=1):
                        fromfleet.move(fleetship.ship, tofleet, fleetship.quantity)
                        
                #todos os fragatas
                elif shipid == '96':
                    for fleetship in fromfleet.fleetship_set.filter(quantity__gt=0, ship__cls=2):
                        fromfleet.move(fleetship.ship, tofleet, fleetship.quantity)                        
                
                #todos os cruzadores
                elif shipid == '95':
                    for fleetship in fromfleet.fleetship_set.filter(quantity__gt=0, ship__cls=3):
                        fromfleet.move(fleetship.ship, tofleet, fleetship.quantity)             
                
                #todos os battleships
                elif shipid == '94':
                    for fleetship in fromfleet.fleetship_set.filter(quantity__gt=0, ship__cls=4):
                        fromfleet.move(fleetship.ship, tofleet, fleetship.quantity)            
                        
                else:
                    fromfleet.move(ship, tofleet, int(request.POST['qt-%i' % x]))
                
            except:
                pass
     
        
    base, fleet1, fleet2, fleet3 = Fleet.objects.filter(planet=planet)
    stock = ShipStock.objects.filter(planet=planet, quantity__gt=0)
    
    return render_to_response('in/military.html', {'planet': planet, 'stock': stock, 'base': base, 'fleet1': fleet1, 'fleet2': fleet2, 'fleet3': fleet3, 'military': 1}, context_instance=RequestContext(request))
    
@login_required
def missions(request):
    planet = request.user.get_profile() 
    base, fleet1, fleet2, fleet3 = Fleet.objects.filter(planet=planet)
    stock = ShipStock.objects.filter(planet=planet, quantity__gt=0)
    
    if request.method == 'POST':
        for i in [1,2,3]:
            try:
                option = request.POST['fleet-%i' % i]
                
                if option == '10':
                    target = planet
                    
                else:
                    x = request.POST['x-%i' % i];
                    y = request.POST['y-%i' % i];
                    z = request.POST['z-%i' % i];
                
                    target = Planet.objects.get(x=x, y=y, z=z)            
                
                #lt = request.POST['when-%i' % i];
                
                thisfleet = Fleet.objects.filter(planet=planet)[i]
                
                if thisfleet.action != 0 and option != '10':
                    messages.add_message(request, messages.ERROR, u"Impossível dar uma ordem para a Frota %i. Ela já está se deslocando: %s" % (i, thisfleet.get_action()))
                    continue
                elif thisfleet.action != 10:
                    old = thisfleet.target
                
                ura = thisfleet.set_action(target, planet.travel_time(), option)
                thisfleet.save()
                
                
                if int(option) in [1,2,3]:
                    Planet.objects.get(x=x, y=y, z=z).add_news("war_hostile", u"%s enviou naves para atacar o seu planeta. Espere a chegada de %s naves hostis em %i ticks." % (planet.coords(), intcomma(thisfleet.get_ship_count()), planet.travel_time()))
                elif int(option) in [4,5,6,7]:
                    Planet.objects.get(x=x, y=y, z=z).add_news("war_friendly", u"%s enviou naves para defender o seu planeta. Espere a chegada de %s naves amigs em %i ticks." % (planet.coords(), intcomma(thisfleet.get_ship_count()), planet.travel_time()))
                    
                if int(option) == 10:
                    old.add_news("war_recall", u"%s recuou uma frota que vinha em direção ao seu planeta." % (planet.coords()))
                    planet.add_news("war_recall", u"Nós recuamos uma frota que ia em direção ao planeta %s e recebemos %s unidades de urânio de volta" % (old.coords(), intcomma(ura)))
                    messages.add_message(request, messages.INFO, u"Frota %i recuada. Foram recuperadas %s unidades de urânio." % (i, intcomma(ura)))
                else:
                    messages.add_message(request, messages.INFO, u"Frota %i voando. Foram utilizadas %s unidades de urânio." % (i, intcomma(thisfleet.cost())))
                    
            except EmptyFleetException:
                messages.add_message(request, messages.ERROR, u"É necessário possuir pelo menos uma nave na frota para poder realizar operações militares.")
                
            except SelfException:
                messages.add_message(request, messages.ERROR, u"Embora pareça uma idéia interessante, não é possível realizar missões no seu próprio planeta.")
                
            except OutOfResourcesException:
                messages.add_message(request, messages.ERROR, u"Você não tem Urânio suficiente para movimentar essa frota. Remova naves ou consiga mais Urânio.")
                
            except NoobBashingException:
                messages.add_message(request, messages.ERROR, u"O planeta %s é pequeno demais para ser atacado por você." % target.coords())
                
            except: #CantBuildException:
                pass
            
        return redirect("missions")
    
    base, fleet1, fleet2, fleet3 = Fleet.objects.filter(planet=planet)
    
    return render_to_response('in/missions.html', {'planet': planet, 'stock': stock, 'base': base, 'fleet1': fleet1, 'fleet2': fleet2, 'fleet3': fleet3, 'missions': 1}, context_instance=RequestContext(request))
    
def popular(request):
    sh = Ship(name="FiTe01", cls=0, skill=1, init=6, attack=6, defense=9, target=3, cost_metal=1000, cost_cristal=1000, cost_gold=1000, race=0).save()
    sh = Ship(name="FiTe02", cls=0, skill=2, init=1, attack=20, defense=8, target=2, cost_metal=1000, cost_cristal=1000, cost_gold=1000, race=0).save()
    sh = Ship(name="CoTe01", cls=1, skill=0, init=12, attack=12, defense=20, target=1, cost_metal=2000, cost_cristal=2000, cost_gold=2000, race=0).save()
    sh = Ship(name="CoTe02", cls=1, skill=1, init=7, attack=11, defense=25, target=2, cost_metal=2000, cost_cristal=2000, cost_gold=2000, race=0).save()
    sh = Ship(name="CoTe03", cls=1, skill=2, init=2, attack=30, defense=30, target=3, cost_metal=2000, cost_cristal=2000, cost_gold=2000, race=0).save()
    sh = Ship(name="CoTe04", cls=1, skill=5, init=20, attack=20, defense=20, target=5, cost_metal=2000, cost_cristal=2000, cost_gold=2000, race=0).save()
    sh = Ship(name="FrTe01", cls=2, skill=3, init=18, attack=17, defense=31, target=1, cost_metal=4000, cost_cristal=4000, cost_gold=4000, race=0).save()
    sh = Ship(name="FrTe02", cls=2, skill=4, init=20, attack=35, defense=35, target=7, cost_metal=4000, cost_cristal=4000, cost_gold=4000, race=0).save()
    sh = Ship(name="FrTe03", cls=2, skill=5, init=20, attack=30, defense=30, target=5, cost_metal=4000, cost_cristal=4000, cost_gold=4000, race=0).save()
    sh = Ship(name="FrTe04", cls=2, skill=0, init=13, attack=20, defense=33, target=2, cost_metal=4000, cost_cristal=4000, cost_gold=4000, race=0).save()
    sh = Ship(name="CrTe01", cls=3, skill=0, init=14, attack=110, defense=110, target=4, cost_metal=15000, cost_cristal=15000, cost_gold=15000, race=0).save()
    sh = Ship(name="BsTe01", cls=4, skill=0, init=15, attack=400, defense=390, target=0, cost_metal=40000, cost_cristal=40000, cost_gold=40000, race=0).save()
    
    
    sh = Ship(name="FiCi01", cls=0, skill=0, init=11, attack=7, defense=9, target=1, cost_metal=1000, cost_cristal=1000, cost_gold=1000, race=1).save()
    sh = Ship(name="FiCi02", cls=0, skill=3, init=16, attack=12, defense=4, target=3, cost_metal=2000, cost_cristal=500, cost_gold=500, race=1).save()
    sh = Ship(name="CoCi01", cls=1, skill=0, init=12, attack=17, defense=20, target=2, cost_metal=2000, cost_cristal=2000, cost_gold=2000, race=1).save()
    sh = Ship(name="CoCi02", cls=1, skill=3, init=17, attack=65, defense=12, target=0, cost_metal=4000, cost_cristal=1000, cost_gold=1000, race=1).save()
    sh = Ship(name="CoCi04", cls=1, skill=3, init=17, attack=65, defense=20, target=4, cost_metal=4000, cost_cristal=1000, cost_gold=1000, race=1).save()
    sh = Ship(name="CoCi05", cls=1, skill=5, init=20, attack=30, defense=30, target=5, cost_metal=2000, cost_cristal=2000, cost_gold=2000, race=1).save()
    sh = Ship(name="FrCi01", cls=2, skill=0, init=13, attack=22, defense=29, target=0, cost_metal=4000, cost_cristal=4000, cost_gold=4000, race=1).save()
    sh = Ship(name="CrCi01", cls=3, skill=0, init=14, attack=50, defense=90, target=1, cost_metal=15000, cost_cristal=15000, cost_gold=15000, race=1).save()
    sh = Ship(name="BsCi01", cls=4, skill=3, init=19, attack=450, defense=200, target=4, cost_metal=80000, cost_cristal=20000, cost_gold=20000, race=1).save()
    sh = Ship(name="BsCi02", cls=4, skill=4, init=20, attack=550, defense=500, target=7, cost_metal=40000, cost_cristal=40000, cost_gold=40000, race=1).save()
    sh = Ship(name="BsCi03", cls=4, skill=5, init=20, attack=500, defense=500, target=5, cost_metal=40000, cost_cristal=40000, cost_gold=40000, race=1).save()
    sh = Ship(name="BsCi04", cls=4, skill=3, init=17, attack=455, defense=350, target=1, cost_metal=80000, cost_cristal=20000, cost_gold=20000, race=1).save()    
    
    sh = Ship(name="FiXe01", cls=0, skill=1, init=6, attack=4, defense=8, target=0, cost_metal=500, cost_cristal=2000, cost_gold=500, race=2).save()
    sh = Ship(name="FiXe02", cls=0, skill=4, init=20, attack=10, defense=9, target=7, cost_metal=1000, cost_cristal=1000, cost_gold=1000, race=2).save()
    sh = Ship(name="FiXe03", cls=0, skill=1, init=6, attack=15, defense=10, target=4, cost_metal=500, cost_cristal=2000, cost_gold=5000, race=2).save()
    sh = Ship(name="FiXe04", cls=0, skill=5, init=20, attack=7, defense=7, target=5, cost_metal=1000, cost_cristal=1000, cost_gold=1000, race=2).save()
    sh = Ship(name="CoXe01", cls=1, skill=1, init=7, attack=27, defense=20, target=4, cost_metal=1000, cost_cristal=4000, cost_gold=1000, race=2).save()
    sh = Ship(name="FrXe01", cls=2, skill=1, init=8, attack=30, defense=30, target=3, cost_metal=2000, cost_cristal=8000, cost_gold=2000, race=2).save()
    sh = Ship(name="CrXe01", cls=3, skill=1, init=9, attack=45, defense=40, target=2, cost_metal=10000, cost_cristal=25000, cost_gold=10000, race=2).save()
    sh = Ship(name="CrXe02", cls=3, skill=1, init=9, attack=50, defense=80, target=1, cost_metal=10000, cost_cristal=25000, cost_gold=10000, race=2).save()
    sh = Ship(name="BsXe01", cls=4, skill=1, init=15, attack=180, defense=300, target=4, cost_metal=20000, cost_cristal=80000, cost_gold=20000, race=2).save()
    sh = Ship(name="BsXe02", cls=4, skill=1, init=15, attack=130, defense=350, target=0, cost_metal=20000, cost_cristal=80000, cost_gold=20000, race=2).save()
    sh = Ship(name="BsXe03", cls=4, skill=1, init=15, attack=150, defense=300, target=1, cost_metal=20000, cost_cristal=80000, cost_gold=20000, race=2).save()
    sh = Ship(name="BsXe04", cls=4, skill=5, init=20, attack=330, defense=330, target=5, cost_metal=40000, cost_cristal=40000, cost_gold=40000, race=2).save()
    
    sh = Ship(name="FiQr01", cls=0, skill=0, init=11, attack=5, defense=12, target=0, cost_metal=1000, cost_cristal=1000, cost_gold=1000, race=3).save()
    sh = Ship(name="CoQr01", cls=1, skill=0, init=12, attack=12, defense=24, target=2, cost_metal=2000, cost_cristal=2000, cost_gold=2000, race=3).save()
    sh = Ship(name="CoQr02", cls=1, skill=4, init=20, attack=15, defense=30, target=7, cost_metal=2000, cost_cristal=2000, cost_gold=2000, race=3).save()
    sh = Ship(name="FrQr01", cls=2, skill=0, init=13, attack=30, defense=50, target=2, cost_metal=4000, cost_cristal=4000, cost_gold=4000, race=3).save()
    sh = Ship(name="FrQr02", cls=2, skill=0, init=13, attack=30, defense=50, target=3, cost_metal=4000, cost_cristal=4000, cost_gold=4000, race=3).save()
    sh = Ship(name="FrQr03", cls=2, skill=0, init=13, attack=50, defense=30, target=4, cost_metal=4000, cost_cristal=4000, cost_gold=4000, race=3).save()
    sh = Ship(name="FrQr04", cls=2, skill=5, init=20, attack=40, defense=40, target=5, cost_metal=4000, cost_cristal=4000, cost_gold=4000, race=3).save()
    sh = Ship(name="CrQr01", cls=3, skill=0, init=14, attack=50, defense=150, target=2, cost_metal=15000, cost_cristal=15000, cost_gold=15000, race=3).save()
    sh = Ship(name="CrQr02", cls=3, skill=0, init=14, attack=80, defense=150, target=3, cost_metal=15000, cost_cristal=15000, cost_gold=15000, race=3).save()
    sh = Ship(name="CrQr03", cls=3, skill=0, init=14, attack=150, defense=100, target=4, cost_metal=15000, cost_cristal=15000, cost_gold=15000, race=3).save()
    sh = Ship(name="CrQr04", cls=3, skill=5, init=20, attack=100, defense=100, target=5, cost_metal=15000, cost_cristal=15000, cost_gold=15000, race=3).save()
    sh = Ship(name="BsQr01", cls=4, skill=0, init=15, attack=500, defense=550, target=1, cost_metal=40000, cost_cristal=40000, cost_gold=40000, race=3).save()
    
    sh = Ship(name="FiMa01", cls=0, skill=2, init=1, attack=5, defense=10, target=0, cost_metal=500, cost_cristal=500, cost_gold=2000, race=4).save()
    sh = Ship(name="FiMa02", cls=0, skill=2, init=1, attack=15, defense=7, target=2, cost_metal=500, cost_cristal=500, cost_gold=2000, race=4).save()
    sh = Ship(name="FiMa03", cls=0, skill=0, init=1, attack=30, defense=5, target=3, cost_metal=1000, cost_cristal=1000, cost_gold=1000, race=4).save()
    sh = Ship(name="FiMa04", cls=0, skill=5, init=20, attack=15, defense=15, target=5, cost_metal=1000, cost_cristal=1000, cost_gold=1000, race=4).save()
    sh = Ship(name="CoMa01", cls=1, skill=2, init=2, attack=40, defense=20, target=4, cost_metal=1000, cost_cristal=1000, cost_gold=4000, race=4).save()
    sh = Ship(name="CoMa02", cls=1, skill=2, init=2, attack=20, defense=15, target=0, cost_metal=1000, cost_cristal=1000, cost_gold=4000, race=4).save()
    sh = Ship(name="FrMa01", cls=2, skill=2, init=3, attack=50, defense=40, target=2, cost_metal=2000, cost_cristal=8000, cost_gold=2000, race=4).save()
    sh = Ship(name="CrMa01", cls=3, skill=2, init=4, attack=100, defense=150, target=4, cost_metal=10000, cost_cristal=25000, cost_gold=10000, race=4).save()
    sh = Ship(name="CrMa02", cls=3, skill=0, init=14, attack=50, defense=100, target=1, cost_metal=15000, cost_cristal=15000, cost_gold=15000, race=4).save()
    sh = Ship(name="CrMa03", cls=3, skill=4, init=20, attack=200, defense=80, target=7, cost_metal=15000, cost_cristal=15000, cost_gold=15000, race=4).save()
    sh = Ship(name="CrMa04", cls=3, skill=5, init=20, attack=120, defense=120, target=5, cost_metal=15000, cost_cristal=15000, cost_gold=15000, race=4).save()
    sh = Ship(name="BsMa01", cls=4, skill=2, init=5, attack=500, defense=400, target=3, cost_metal=20000, cost_cristal=80000, cost_gold=20000, race=4).save()
    
    from base.models import Galaxy
    #a = Galaxy(x=1, y=1, name='UmUm').save()
    a = Galaxy(x=1, y=2, name='UmDois').save()
    a = Galaxy(x=1, y=3, name='UmTres').save()
    a = Galaxy(x=1, y=4, name='UmQuatro').save()
    a = Galaxy(x=2, y=1, name='DoisUm').save()
    a = Galaxy(x=2, y=2, name='DoisDois').save()
    a = Galaxy(x=2, y=3, name='DoisTres').save()
    a = Galaxy(x=2, y=4, name='DoisQuatro').save()
    
    return redirect("overview")


def table(request):
    ships = Ship.objects.all()
    return render_to_response("table.html", {'ships': ships})
