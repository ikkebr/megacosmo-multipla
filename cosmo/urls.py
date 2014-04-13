from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'cosmo.views.home', name='home'),
    # url(r'^cosmo/', include('cosmo.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    url(r'^overview/?$', 'base.views.overview', name='overview'),
    url(r'^traffic/?$', 'base.views.galaxy_traffic', name='traffic'),

    url(r'^messages/?$', 'comm.views.list_messages', name='messages'),
    url(r'^messages/remove/(?P<msgid>\d+)/?$', 'comm.views.remove_message', name='remove_message'),
    
    
    url(r'^news/?$', 'comm.views.list_news', name='news'),
    url(r'^news/remove/(?P<newsid>\d+)/?$', 'comm.views.remove_news', name='remove_news'),
    url(r'^news/removeall/?$', 'comm.views.remove_all_news', name='remove_all_news'),
    url(r'^news/publish/(?P<newsid>\d+)/?$', 'comm.views.publish_news', name='publish_news'),
    url(r'^news/public/(?P<newsid>\d+)/?$', 'comm.views.show_public_news', name='show_public_news'),
    
    url(r'^galaxy/(?P<x>\d+)/(?P<y>\d+)/?$', 'base.views.show_galaxy', name='galaxy'),
    url(r'^resources/?$', 'base.views.resources', name='resources'),
    url(r'^research/?$', 'base.views.research', name='research'),
    
    
    url(r'^build/?$', 'base.views.build', name='build'),
    url(r'^build/(?P<branch>\d+)/?$', 'base.views.init_build', name='init_build'),
    url(r'^build/cancel/?$', 'base.views.cancel_build', name='cancel_build'),
    
    url(r'^production/?$', 'prod.views.production', name='production'),
    url(r'^production/cancel/(?P<prod_id>\d+)/?$', 'prod.views.cancel_production', name='cancel_production'),
    
    url(r'^research/(?P<branch>\d+)/?$', 'base.views.init_research', name='init_research'),
    url(r'^research/cancel/?$', 'base.views.cancel_research', name='cancel_research'),
    
    url(r'^military/?$', 'prod.views.military', name='military'),
    url(r'^missions/?$', 'prod.views.missions', name='missions'),
    
    
    url(r'^ranking/?$', 'base.views.ranking', name='ranking'),
    url(r'^ranking/gal/?$', 'base.views.gal_ranking', name='gal_ranking'),
    
    url(r'^sabotage/?$', 'base.views.sabotage', name='sabotage'),
    url(r'^spy/?$', 'base.views.spy', name='spy'),

    #url(r'^tick/$', 'base.views.tick', name='tick'),
    #url(r'^lemaster_tick/$', 'base.views.master_tick', name='master_tick'),

    url(r'^login/?$', 'django.contrib.auth.views.login', name='login'),
    url(r'^logout/?$', 'base.views.logout_view', name='logout'),
    url(r'^signup/?$', 'base.views.signup', name='signup'),

    url(r'^popular/?$', 'prod.views.popular', name='popular'),
    url(r'^table/?$', 'prod.views.table', name='table'),
    url(r'', 'base.views.overview', name='overview'),
)
