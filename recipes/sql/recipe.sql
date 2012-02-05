create index recipes_recipe_user_id_created_at on recipes_recipe(user_id, created_at);
create index recipes_recipe_user_id_is_draft_published_at on recipes_recipe(user_id, is_draft, published_at);
create index recipes_recipe_reviewed_contest_id_score on recipes_recipe(reviewed_contest_id, score);
create index recipes_recipe_contest_id_is_awarded on recipes_recipe(contest_id, is_awarded);
