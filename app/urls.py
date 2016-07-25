from django.conf.urls import url

from . import views

urlpatterns = [
    # ex: /app/
    url(r'^$', views.index, name='index'),
    # ex: /app/v1
    url(r'^v1$', views.index_v1, name='index-v1'),  
    # ex: /app/login_fb
    url(r'^login_fb$', views.login_fb, name='login_fb'),
    # ex: /app/fb_real_time_updates/
    url(r'^fb_real_time_updates/$', views.fb_real_time_updates, name='fb_real_time_updates'),
    # ex: /app/check_user
    url(r'^check_user$', views.check_user, name='check_user'),
    # ex: /app/write_permissions_fb
    url(r'^write_permissions_fb', views.write_permissions_fb, name='write_permissions_fb'),

    url(r'^process_login$', views.process_login, name='process_login'),
    url(r'^register$', views.register, name='register'),
    url(r'^login_IS$', views.login_IS, name='login_IS'),

    url(r'^register_v1$', views.register_v1, name='register-v1'),


]
