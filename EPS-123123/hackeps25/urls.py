"""
URL configuration for hackeps25 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from .views import update_pose, get_pose, index, accordion, camera , carousel, collapse, dial, dismiss, modal, drawer, dropdown, popover, tabs, tooltip, input_counter, datepicker, base
from .views import LoginBootstrapView
from django.contrib.auth.views import LogoutView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),
    path('api/update-pose/', update_pose, name='update_pose'),
    path('api/get-pose/', get_pose, name='get_pose'),
    path('accordion', accordion, name='accordion'),
    path('carousel', carousel, name='carousel'),
    path('collapse', collapse, name='collapse'),
    path('dial', dial, name='dial'),
    path('dismiss', dismiss, name='dismiss'),
    path('modal', modal, name='modal'),
    path('drawer', drawer, name='drawer'),
    path('dropdown', dropdown, name='dropdown'),
    path('popover', popover, name='popover'),
    path('camera', camera, name='camera'),
    path('tabs', tabs, name='tabs'),
    path('tooltip', tooltip, name='tooltip'),
    path('input-counter', input_counter, name='input-counter'),
    path('datepicker', datepicker, name='datepicker'),
    path('base', base, name='base'),
    path('login/', LoginBootstrapView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

]
