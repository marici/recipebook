# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from recipes import models

urlpatterns = patterns('recipes.views',
    url(r'^recipe/register/$', 'register_recipe',
        name='recipes-register'),
    url(r'^recipe/register/(?P<contest_id>\d+)/$', 'register_recipe',
        name='recipes-register-to-contest'),
    url(r'^recipe/(?P<recipe_id>\d+)/$', 'show_recipe',
        name='recipes-show'),
    url(r'^recipe/(?P<recipe_id>\d+)/print/$', 'show_recipe_for_print',
        name='recipes-show-print'),
    url(r'^recipe/(?P<recipe_id>\d+)/edit/$', 'edit_recipe',
        name='recipes-edit'),
    url(r'^recipe/(?P<recipe_id>\d+)/delete/$', 'delete_recipe',
        name='recipes-delete'),
    url(r'^recipe/(?P<recipe_id>\d+)/mail/$', 'mail_recipe',
        name='recipes-mail'),
    url(r'^recipe/(?P<recipe_id>\d+)/submit/$', 'submit_recipe_to_contest',
        name='recipes-submit'),
    url(r'^recipe/(?P<recipe_id>\d+)/status/change/$',
        'toggle_recipe_open_state',
        name='recipes-change-status'),
    url(r'^recipe/(?P<recipe_id>\d+)/direction/register/',
        'register_direction',
        name='recipes-direction-register'),
    url(r'^recipe/(?P<recipe_id>\d+)/direction/(?P<direction_id>\d+)/edit/',
        'edit_direction',
        name='recipes-direction-edit'),
    url(r'^recipe/(?P<recipe_id>\d+)/direction/direction_id/edit/',
        'edit_direction',
        name='recipes-direction-edit-dummy'),
    url(r'^recipe/(?P<recipe_id>\d+)/direction/(?P<direction_id>\d+)/delete/',
        'delete_direction',
        name='recipes-direction-delete'),
    url(r'^recipe/(?P<recipe_id>\d+)/direction/direction_id/delete/',
        'delete_direction',
        name='recipes-direction-delete-dummy'),
    url(r'^recipe/(?P<recipe_id>\d+)/direction/sort/$',
        'sort_directions',
        name='recipes-direction-sort'),
    url(r'^recipe/(?P<recipe_id>\d+)/favorite/add/$',
        'add_favorite_recipe',
        name='recipes-favorite-add'),
    url(r'^recipe/(?P<recipe_id>\d+)/favorite/remove/$',
        'remove_favorite_recipe',
        name='recipes-favorite-remove'),
    url(r'^recipe/(?P<recipe_id>\d+)/vote/$',
        'vote_to_recipe',
        name='recipes-vote'),
    url(r'^recipe/(?P<recipe_id>\d+)/vote/users$',
        'show_voting_users',
        name='recipes-vote-users'),
    url(r'^recipe/(?P<recipe_id>\d+)/comment/$',
        'comment_to_recipe',
        name='recipes-comment-add'),
    url(r'^recipe/comment/(?P<comment_id>\d+)/delete/$',
        'delete_comment',
        name='recipes-comment-delete'),
    url(r'^recipe/comment/(?P<comment_id>\d+)/approve/$',
        'approve_comment',
        name='recipes-comment-approve'),
    url(r'^recipe/(?P<recipe_id>\d+)/copy/$',
        'copy_recipe',
        name='recipes-copy'),
    url(r'^recipe/search/(?P<query>.*)/$',
        'search_recipes',
        name='recipes-search'),
    url(r'^recipe/search/(?P<query>.*)/(?P<page>\d+)$',
        'search_recipes',
        name='recipes-search-with-page'),
)

urlpatterns += patterns('recipes.views.contests',
    url(r'^contest/current/$', 'show_current_contest_list',
        name='recipes-contests-current'),
    url(r'^contest/current/(?P<page>\d+)$', 'show_current_contest_list',
        name='recipes-contests-current-with-page'),
    url(r'^contest/closed/$', 'show_closed_contest_list',
        name='recipes-contests-closed'),
    url(r'^contest/closed/(?P<page>\d+)$', 'show_closed_contest_list',
        name='recipes-contests-closed-with-page'),
    url(r'^contest/(?P<contest_id>\d+)/$', 'show_contest',
        name='recipes-contests-show'),
    url(r'^contest/(?P<contest_id>\d+)/recipes/$', 'show_recipes',
        name='recipes-contests-recipes'),
    url(r'^contest/(?P<contest_id>\d+)/recipes/(?P<page>\d+)$', 'show_recipes',
        name='recipes-contests-recipes-with-page'),
    url(r'^contest/(?P<contest_id>\d+)/submit/(?P<recipe_id>\d+)/$',
        'submit_recipe', name='recipes-contests-submit-recipe'),
    url(r'^contest/(?P<contest_id>\d+)/mail_template', 'mail_recipe_template',
        name='recipes-contests-mail-template'),
    url(r'^recipe/mail_template', 'mail_recipe_template',
        {'contest_id': None}, 'recipes-mail-template'),
    url(r'^contest/search/(?P<query>.*)/$',
        'search_contests',
        name='recipes-contests-search'),
    url(r'^contest/search/(?P<query>.*)/(?P<page>\d+)$',
        'search_contests',
        name='recipes-contests-search-with-page'),
)

urlpatterns += patterns('django.views.generic',
    url(r'^feelings/', 'list_detail.object_list',
        {'queryset': models.Feeling.objects.all()},
        name='recipes-feelings'),
    url(r'^dishcategory/$', 'list_detail.object_list',
        {'queryset': models.DishCategory.objects.all()},
        name='recipes-dishcategories'),
    url(r'^dishcategory/(?P<object_id>\d+)', 'list_detail.object_detail',
        {'queryset': models.DishCategory.objects.all()},
        name='recipes-dishcategory-show'),
    url(r'^ingcategory/$', 'list_detail.object_list',
        {'queryset': models.IngredientCategory.objects.all()},
        name='recipes-ingcategories'),
    url(r'^ingcategory/(?P<object_id>\d+)', 'list_detail.object_detail',
        {'queryset': models.IngredientCategory.objects.all()},
        name='recipes-ingcategory-show'),
)

urlpatterns += patterns('',
    url(r'^accounts/password_reset/$',
        'django.contrib.auth.views.password_reset'),
    url(r'^accounts/password_reset/iphone/$',
        'django.contrib.auth.views.password_reset',
        {'template_name': 'registration/password_reset_form-iphone.html',
         'post_reset_redirect': '/accounts/password_reset_done/iphone/'}
    ),
    url(r'^accounts/password_reset_done/iphone/$',
        'django.contrib.auth.views.password_reset_done',
        {'template_name': 'registration/password_reset_done-iphone.html'}
    )
)

urlpatterns += patterns('recipes.views.users',
    url(r'^accounts/login/', 'login',
        name='recipes-users-login'),
    url(r'^accounts/new/', 'new',
        name='recipes-users-new'),
    url(r'^accounts/validate/(?P<key>.*)$', 'validate',
        name='recipes-users-validate'),
    url(r'^accounts/settings/$', 'edit_profile',
        name='recipes-users-edit-profile'),
    url(r'^accounts/change_email/$', 'change_email',
        name='recipes-users-email-change'),
    url(r'^accounts/change_email/(?P<user_id>\d*)/(?P<key>.*)/$',
        'validate_change_email',
        name='recipes-users-validate-email'),
    url(r'^accounts/withdraw/$', 'inactivate',
        name='recipes-users-inactivate'),
    url(r'^home/$', 'show_home',
        name='recipes-users-home'),
    url(r'^home/comments/(?P<page>\d+)?$', 'show_owner_comments',
        name='recipes-users-home-comments'),
    url(r'^home/comments/noapproval/(?P<page>\d+)?$', 'show_owner_comments',
        {'only_not_moderated': True},
        'recipes-users-home-comments-noapproval'),
    url(r'^user/(?P<user_id>[^/]*)/$', 'show',
        name='recipes-users-show'),
    url(r'^user/(?P<user_id>[^/]*)/recipes/$', 'show_recipe_list',
        name='recipes-users-recipes'),
    url(r'^user/(?P<user_id>[^/]*)/recipes/(?P<page>\d+)$', 'show_recipe_list',
        name='recipes-users-recipes-with-page'),
    url(r'^user/(?P<user_id>[^/]*)/favorite/add$', 'add_favorite_user',
        name='recipes-users-favorite-add'),
    url(r'^user/(?P<user_id>[^/]*)/favorite/remove$', 'remove_favorite_user',
        name='recipes-users-favorite-remove'),
    url(r'^user/(?P<user_id>[^/]*)/favorites/recipes/$',
        'show_favorite_recipes', name='recipes-users-favorite-recipes-show'),
    url(r'^user/(?P<user_id>[^/]*)/favorites/recipes/(?P<page>\d+)$',
        'show_favorite_recipes',
        name='recipes-users-favorite-recipes-show-with-page'),
    url(r'^user/(?P<user_id>[^/]*)/favorites/members/$', 'show_favorite_users',
        name='recipes-users-favorite-users-show'),
    url(r'^user/(?P<user_id>[^/]*)/favorites/members/(?P<page>\d+)$',
        'show_favorite_users',
        name='recipes-users-favorite-users-show-with-page'),
)

urlpatterns += patterns('recipes.views.api',
    url(r'^api/contest/list/(?P<output_format>\w+)$', 'contest_api',
        name='recipes-api-contest'),
    url(r'^api/contest/detail/(?P<contest_id>\d+)/(?P<output_format>\w+)$',
       'contest_detail_api', name='recipes-api-contest-detail'),
    url(r'^api/recipe/list/(?P<user_id>\w+)/(?P<output_format>\w+)$',
        'recipe_list_api', name='recipes-api-recipe-list'),
    url(r'^api/recipe/make$', 'make_new_recipe',
        name='recipes-api-recipe-make'),
    url(r'^api/recipe/make/(?P<contest_id>\d+)$',
        'make_new_recipe', name='recipes-api-recipe-make-to-contest'),
    url(r'^api/recipe/edit/(?P<recipe_id>\d+)$',
        'edit_recipe', name='recipes-api-recipe-edit'),
    url(r'^api/login/(?P<output_format>\w+)$',
        'login_api', name='api-login')
)
