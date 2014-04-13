#*-* encoding: utf-8 *-*
from django.shortcuts import render_to_response, RequestContext, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from models import Planet, Galaxy, RESEARCH_LIST, OutOfResourcesException, BUILD_LIST, OutOfSpaceException, CLUSTER_SIZE, RACES, BASE_WAVE_COST, BASE_SABOTAGE_COST, BASE_SABOTAGE_AWARENESS

from django.contrib import messages
from descriptions import RESEARCH_DESCRIPTIONS, BUILDING_DESCRIPTIONS, SABOTAGE_DESCRIPTIONS, WAVE_DESCRIPTIONS


from pprint import pprint
from django.contrib.auth import logout

from prod.models import SelfException, NoobBashingException

from django.contrib.humanize.templatetags.humanize import intcomma

from django import forms

@login_required
def overview(request):
    planet = request.user.get_profile()

    from prod.models import Fleet
    base, fleet1, fleet2, fleet3 = Fleet.objects.filter(planet=planet)

    return render_to_response('in/overview.html', {'planet': request.user.get_profile(), 'overview': 1, 'base': base, 'fleet1': fleet1, 'fleet2': fleet2, 'fleet3': fleet3}, context_instance=RequestContext(request))

@login_required
def galaxy_traffic(request):
    planet = request.user.get_profile()
    galaxy = planet.galaxy

    return render_to_response('in/trafic.html', {'planet': planet, 'galaxy': galaxy, 'traffic': 1}, context_instance=RequestContext(request))

@login_required
def ranking(request):
    planet = request.user.get_profile()

    planets = Planet.objects.all().order_by('-score')

    return render_to_response('in/ranking.html', {'planet': planet, 'planets': planets, 'ranking': 1}, context_instance=RequestContext(request))


@login_required
def gal_ranking(request):
    planet = request.user.get_profile()
    galaxys = Galaxy.objects.all().order_by('-score')
    
    return render_to_response('in/gal_ranking.html', {'planet': planet, 'galaxys': galaxys, 'gal_ranking': 1}, context_instance=RequestContext(request))

@login_required
def tick(request):
    planet = request.user.get_profile()
    planet.tick()
    return redirect("overview")

@login_required
def research(request):
    planet = request.user.get_profile()

    current_researches = [''] + [getattr(planet, RESEARCH_LIST[x]) for x in range(1, len(RESEARCH_LIST))]
    current_researches = zip(RESEARCH_DESCRIPTIONS, current_researches)

    #pprint(current_researches)

    return render_to_response('in/research.html', {'planet': planet, 'current_researches': current_researches, 'research': 1 }, context_instance = RequestContext(request))

@login_required
def build(request):
    planet = request.user.get_profile()

    current_builds = [''] + [getattr(planet, BUILD_LIST[x]) for x in range(1, len(BUILD_LIST))]
    current_builds = zip(BUILDING_DESCRIPTIONS, current_builds)

    return render_to_response('in/build.html', {'planet': planet, 'current_builds': current_builds , 'build': 1}, context_instance = RequestContext(request))

@login_required
def spy(request):
    planet = request.user.get_profile()
    wave = 0
    target = planet
    current_waves = zip( WAVE_DESCRIPTIONS, [x*BASE_WAVE_COST for x in range(0,6)] )
    
    base = fleet1 = fleet2 = stock = fleet3 = None
    #stock = None
    if request.method == 'POST':
        try:
            wave = int(request.POST['wave'])
            
            if wave <= planet.research_waves: # se a onda eh uma onda possivel
                target = Planet.objects.get(x=int(request.POST['x']), y=int(request.POST['y']), z=int(request.POST['z']))
                planet.remove_metal(BASE_WAVE_COST*wave)
                planet.remove_cristal(BASE_WAVE_COST*wave)
                planet.remove_gold(BASE_WAVE_COST*wave)
                planet.save()
                
                from prod.models import ShipStock, Fleet
                stock = ShipStock.objects.filter(planet=target, quantity__gt=0)
                base, fleet1, fleet2, fleet3 = Fleet.objects.filter(planet=target)
                
                if planet.waveamp >= target.waveblock:
                    pass
                else:
                    messages.add_message(request, messages.ERROR, u"Não foi possível espioanr o planeta adversário. Temos que construir mais amplificadores.")
                    wave = 0
            else:
                wave = 0
        except OutOfResourcesException:
            messages.add_message(request, messages.ERROR, u'Você não possui recursos suficientes para espionar este planeta.')
            wave = 0
        except:
            wave = 0
        
    return render_to_response('in/spy.html', {'planet': planet, 'spy': 1, 'wave': wave, 'current_waves': current_waves, 'target': target, 'stock': stock, 'fleet1': fleet1, 'fleet2': fleet2, 'fleet3': fleet3}, context_instance=RequestContext(request))


@login_required
def sabotage(request):
    planet = request.user.get_profile()
    sabotage = 0
    target = planet
    
    current_sabotages = zip( SABOTAGE_DESCRIPTIONS, [x*BASE_SABOTAGE_COST for x in range(0,6)])
    
    if request.method == 'POST':
        try:
            sabotage = int(request.POST['sabotage'])
            
            if sabotage <= planet.research_sabotage:
                target = Planet.objects.get(x=int(request.POST['x']), y=int(request.POST['y']), z=int(request.POST['z']))
                ok = planet.sabotage(target, sabotage)
                
                if ok:
                    messages.add_message(request, messages.SUCCESS, u'Nossos sabotadores conseguiram sabotar o planeta inimigo.')
                elif ok==None:
                    messages.add_message(request, messages.ERROR, u'Não conseguimos sabotar o planeta inimigo. Ele é muito pequeno.')
                else:
                    messages.add_message(request, messages.ERROR, u'Não conseguimos sabotar o planeta inimigo. A segurança deles é muito forte.')
            else:
                sabotage = 0
        except OutOfResourcesException:
            messages.add_message(request, messages.ERROR, u'Você não possui recursos suficientes para sabotar este planeta.')
            sabotage = 0
        except NoobBashingException:
            messages.add_message(request, messages.ERROR, u'O planeta é pequeno demais para ser sabotado por nós.')
            sabotage = 0
        except SelfException:
            messages.add_message(request, messages.ERROR, u'Você não pode sabotar o seu próprio planeta.')
        except:
            sabotage = 0
            
        return redirect("sabotage")
    
    return render_to_response('in/sabotage.html', {'planet': planet, 'sabotage': 1, 'current_sabotages': current_sabotages}, context_instance=RequestContext(request))
    
@login_required
def init_build(request, branch):
    planet = request.user.get_profile()

    try:

        branch = int(branch)
        planet.build(branch)
        messages.add_message(request, messages.INFO, u'Construção iniciada com sucesso. Foram descontados dos nossos cofres %s unidades de cada recurso. Dentro de %i horas teremos o resultado.' % ( intcomma(planet.building_cost()), planet.current_building_time))


    except OutOfResourcesException:
        messages.add_message(request, messages.ERROR, u'Você não possui recursos suficientes para iniciar uma construção.')
    except OutOfSpaceException:
        messages.add_message(request, messages.ERROR, u'Não existem mais espaços disponíveis para construção no nosso Planeta. Tente pesquisar mais.')
    #except:
    #    messages.add_message(request, messages.ERROR, u'Não foi possível iniciar a construção.')

    return redirect("build")

@login_required
def cancel_build(request):
    planet = request.user.get_profile()

    try:
        cost = planet.cancel_build()
        messages.add_message(request, messages.INFO, u'Construção cancelada. Você recebeu de volta %s unidades de cada recurso.' % intcomma(cost))
    except:
        messages.add_message(request, messages.ERROR, u'Não foi possível cancelar a construção.')

    return redirect("build")

@login_required
def init_research(request, branch):
    planet = request.user.get_profile()

    try:
        branch = int(branch)
        planet.research(branch)
        messages.add_message(request, messages.INFO, u'Pesquisa iniciada com sucesso. Dentro de %i horas teremos o resultado.' % planet.current_research_time)
    except:
        messages.add_message(request, messages.ERROR, u'Não foi possível iniciar a pesquisa.')

    return redirect("research")

@login_required
def cancel_research(request):
    planet = request.user.get_profile()

    try:
        planet.cancel_research()
        messages.add_message(request, messages.INFO, u'Pesquisa cancelada com sucesso.')
    except:
        messages.add_message(request, messages.ERROR, u'Não foi possível cancelar a pesquisa.')

    return redirect("research")

@login_required
def show_galaxy(request, x = None, y = None):
    planet = request.user.get_profile()

    if x is None or y is None:
        x = planet.x
        y = planet.y

    x = int(x)
    y = int(y)        
    #print x,
    #print y    

    if request.method == "POST":
        print request.POST

        if 'x' in request.POST and 'y' in request.POST:
            x = int(request.POST['x'])
            y = int(request.POST['y'])

        if 'prev' in request.POST and y > 1:
            y -= 1
        elif 'prev' in request.POST:
            y = CLUSTER_SIZE
            x -= 1

        if 'next' in request.POST and y < CLUSTER_SIZE+1:
            y += 1
        elif 'next' in request.POST:
            x += 1
            y = 1

        if 'go' in request.POST and 'x' in request.POST and 'y' in request.POST:
            #print 'AQUI'*10
            y = request.POST['y']
            x = request.POST['x']

        #if y < 1 or y > CLUSTER_SIZE:
        #    y = 1

        #print x,
        #print y         

        return redirect("galaxy", x, y)

    try:
        galaxy = Galaxy.objects.get(x=x, y=y)
    except:
        return redirect("galaxy", 1, 1)

    return render_to_response('in/galaxy.html', {'planet': planet, 'galaxy': galaxy, 'gal': 1}, context_instance=RequestContext(request))


CONVERSION_LIST = (['0', 'Metal'], ['1', 'Cristal'], ['2', 'Urânio'], ['3', 'Ouro'])

class ConvertionForm(forms.Form):
    value = forms.IntegerField(label='Quantidade')
    from_list = forms.ChoiceField(choices=CONVERSION_LIST, label=u'De')
    to_list = forms.ChoiceField(choices=CONVERSION_LIST, label=u'Para')
    
@login_required
def resources(request):
    planet = request.user.get_profile()
    resource_convertion = ConvertionForm(request.POST or None)
    
    if resource_convertion.is_valid():
        if resource_convertion.cleaned_data['from_list'] != resource_convertion.cleaned_data['to_list']:
            planet.convert_currency(resource_convertion.cleaned_data['from_list'], resource_convertion.cleaned_data['to_list'], resource_convertion.cleaned_data['value'])
            messages.add_message(request, messages.SUCCESS, u'Convertido com sucesso!')    
        else:
            messages.add_message(request, messages.ERROR, u'Impossível converter para o mesmo tipo de material!') 
        
        resource_convertion = ConvertionForm()
        #redirect("resources")

    if request.method == "POST":
            
        try:
            metal = int(request.POST['metal'])

            if metal > 0:
                old_planet_metal = planet.metal
                tp, qti = planet.init_roid(metal, 1)
                if qti:
                    messages.add_message(request, messages.INFO, u'Foram iniciados %i asteróides de Metal. Ao custo de %s unidades de Metal.' % (qti, intcomma(old_planet_metal - planet.metal)))
        except:
            pass

        try:
            metal = int(request.POST['cristal'])
            if metal > 0:
                old_planet_metal = planet.cristal
                tp, qti = planet.init_roid(metal, 2)            
                if qti:
                    messages.add_message(request, messages.INFO, u'Foram iniciados %i asteróides de Cristal. Ao custo de %s unidades de Cristal.' % (qti, intcomma(old_planet_metal - planet.cristal)))
        except:
            pass

        try:
            metal = int(request.POST['uranium'])
            if metal > 0:
                old_planet_metal = planet.uranium

                print planet.uranium

                tp, qti = planet.init_roid(metal, 4)

                print 'aqui'*10
                print tp,
                print qti
                print old_planet_metal


                if qti:
                    messages.add_message(request, messages.INFO, u'Foram iniciados %i asteróides de Urânio. Ao custo de %s unidades de Urânio.' % (qti, intcomma(old_planet_metal - planet.uranium)))
        except:
            pass

        try:
            metal = int(request.POST['gold'])
            if metal > 0:
                old_planet_metal = planet.gold
                tp, qti = planet.init_roid(metal, 3)
                if qti:
                    messages.add_message(request, messages.INFO, u'Foram iniciados %i asteróides de Ouro. Ao custo de %s unidades de Ouro.' % (qti, intcomma(old_planet_metal - planet.gold)))
        except:
            pass        

    return render_to_response('in/resources.html', {'planet': request.user.get_profile(), 'resources': 1, 'convertion': resource_convertion }, context_instance=RequestContext(request))

@login_required
def logout_view(request):
    logout(request)
    return redirect("login")



from django import forms
class SignupForm(forms.Form):
    username = forms.CharField(max_length=40)
    email = forms.EmailField(max_length=40)
    password = forms.CharField(max_length=40)

    ruler_name = forms.CharField(max_length=40)
    planet_name = forms.CharField(max_length=40)
    race = forms.TypedChoiceField(choices=RACES)

def signup(request):
    form = SignupForm(request.POST or None)

    if form.is_valid():
        from django.contrib.auth.models import User
        user = User.objects.create_user(form.cleaned_data['username'], form.cleaned_data['email'], form.cleaned_data['password'])
        user.save()

        user.planet.name = form.cleaned_data['planet_name']
        user.planet.ruler = form.cleaned_data['ruler_name']
        user.planet.race = form.cleaned_data['race']
        user.planet.save()
        

        return redirect("overview")

    return render_to_response("registration/signup.html", {'form': form}, context_instance=RequestContext(request))

#@login_required
def master_tick():#request):
    planetas = Planet.objects.all()
    

    from prod.models import Fleet
    Fleet.objects.update()
    #fleets = Fleet.objects.filter(static=0)

    for fleet in Fleet.objects.filter(static=0):
        print "era ",
        print fleet
        fleet = Fleet.objects.get(id=fleet.id)
        
        print "depois ",
        print fleet
        fleet.first_move_tick()
        
        print "no fim ",
        print fleet


    #combate e calculos    
    #lista = [ planeta.tick() for planeta in planetas ]
    
    for planeta in planetas:
        planeta = Planet.objects.get(id=planeta.id)
        planeta.tick()
        
    Fleet.objects.update()
    for fleet in Fleet.objects.filter(static=0).exclude(action=0):
        print "era ",
        print fleet        
        
        fleet = Fleet.objects.get(id=fleet.id)
        print "depois ",
        print fleet        
        
        
        fleet.second_move_tick()
        print "no fim ",
        print fleet        

    #messages.add_message(request, messages.INFO, "Tickou.")
    
    for galaxy in Galaxy.objects.all():
        galaxy.set_score()
        galaxy.set_roids()

    return 1#redirect("research")
