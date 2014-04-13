#*-* encoding: utf-8 *-*
from django.shortcuts import render_to_response, RequestContext, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from base.models import Planet
from models import Message, News
from django import forms
from django.contrib import messages

class MessageForm(forms.Form):
    x = forms.IntegerField()
    y = forms.IntegerField()
    z = forms.IntegerField()

    subject = forms.CharField(max_length=255)
    content = forms.CharField()

    def clean(self):
        if 'x' in self.cleaned_data and 'y' in self.cleaned_data and 'z' in self.cleaned_data:
            try:
                Planet.objects.get(x=self.cleaned_data['x'], y=self.cleaned_data['y'], z=self.cleaned_data['z'])
            except:
                raise forms.ValidationError("Invalid Coords")
        else:
            raise forms.ValidationError("Invalid Coords")

        return self.cleaned_data

@login_required
def list_messages(request):
    message_list = Message.objects.filter(p_to = request.user.get_profile())
    message_list.update(read=True)
    
    form = MessageForm(request.POST or None)

    if form.is_valid():
        new_msg = Message(p_from = request.user.get_profile(), 
                          p_to = Planet.objects.get(x = form.cleaned_data['x'], y = form.cleaned_data['y'], z = form.cleaned_data['z']),
                          subject = form.cleaned_data['subject'],
                          content = form.cleaned_data['content'])
        new_msg.save()
        messages.add_message(request, messages.INFO, 'Sua mensagem foi enviada com sucesso.')
    elif form.errors:
        messages.add_message(request, messages.ERROR, u'Sua mensagem não pode ser enviada. Verifique as coordenadas e tente novamente.')


    return render_to_response("in/messages.html", {'message_list': message_list, 'planet': request.user.get_profile(), 'messagesp': 1}, context_instance=RequestContext(request))


@login_required
def list_news(request):
    planet = request.user.get_profile()
    news_list = News.objects.filter(planet = planet)
    news_list.update(read=True)

    return render_to_response("in/news.html", {'news_list': news_list, 'planet': planet, 'news': 1}, context_instance = RequestContext(request))

@login_required
def publish_news(request, newsid):
    news = get_object_or_404(News, id=newsid, planet = request.user.get_profile())
    if news.public:
        news.public = False
        messages.add_message(request, messages.ERROR, u'A notícia não é mais pública.')
    else:
        news.public = True
        messages.add_message(request, messages.ERROR, u'A notícia é pública. Você pode passar o link dela para seus amigos.')
        
    news.save()
    return redirect("news")


def show_public_news(request, newsid):
    news = get_object_or_404(News, id=newsid, public=True)
    return render_to_response('in/public_news.html', {'news': news}, context_instance=RequestContext(request))
        

@login_required
def remove_news(request, newsid):
    news = get_object_or_404(News, id=newsid, planet = request.user.get_profile())
    news.delete()

    messages.add_message(request, messages.INFO, u'Notícia removida com sucesso.')

    return redirect("news")


@login_required
def remove_all_news(request):
    if request.method == 'POST':
        planet = request.user.get_profile()
        news_list = News.objects.filter(planet=planet).delete()

        messages.add_message(request, messages.INFO, u'Todas as notícias foram removidas com sucesso.')

    return redirect("news")

@login_required
def remove_message(request, msgid):
    msg = get_object_or_404(Message, id=msgid, p_to=request.user.get_profile())

    msg.delete()
    messages.add_message(request, messages.INFO, u'Mensagem removida com sucesso.')

    return redirect("messages")


@login_required
def remove_all_messages(request):
    if request.method == 'POST':
        planet = request.user.get_profile()
        message_list = Message.objects.filter(p_to=planet).delete()
        
        messages.add_message(request, messages.INFO, u'Todas as mensagens foram removidas com sucesso.')
