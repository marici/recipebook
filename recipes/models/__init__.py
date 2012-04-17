# -*- coding: utf-8 -*-
from recipes.models.master import *
from recipes.models.service import *
from recipes.models.user import *

register_task(UserProfile)
register_task(Recipe)
register_task(Direction)
register_task(Comment)

register_index(Contest)
register_index(Recipe)
