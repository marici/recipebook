# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'Contest.finished_at'
        db.alter_column('recipes_contest', 'finished_at', self.gf('django.db.models.fields.DateTimeField')(null=True))

        # Changing field 'Contest.closed_at'
        db.alter_column('recipes_contest', 'closed_at', self.gf('django.db.models.fields.DateTimeField')(null=True))
    def backwards(self, orm):

        # Changing field 'Contest.finished_at'
        db.alter_column('recipes_contest', 'finished_at', self.gf('django.db.models.fields.DateTimeField')(default=None))

        # Changing field 'Contest.closed_at'
        db.alter_column('recipes_contest', 'closed_at', self.gf('django.db.models.fields.DateTimeField')(default=None))
    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'recipes.comment': {
            'Meta': {'object_name': 'Comment'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_moderated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'owner_comment'", 'null': 'True', 'to': "orm['auth.User']"}),
            'photo': ('maricilib.django.db.models.fields.S3SyncResizedImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'photo_s3': ('maricilib.django.db.models.fields.S3SyncResizedImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'photo_s3_sync': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'recipe': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['recipes.Recipe']"}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'my_comment'", 'to': "orm['auth.User']"})
        },
        'recipes.contest': {
            'Meta': {'object_name': 'Contest'},
            'closed_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'comment': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'dish': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['recipes.Dish']", 'null': 'True', 'blank': 'True'}),
            'feeling': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['recipes.Feeling']", 'null': 'True', 'blank': 'True'}),
            'finished_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('maricilib.django.db.models.fields.ResizedImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'ingredients': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['recipes.Ingredient']", 'null': 'True', 'blank': 'True'}),
            'is_finished': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_reviewing': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'producer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['recipes.FarmProducer']", 'null': 'True', 'blank': 'True'}),
            'published_at': ('django.db.models.fields.DateTimeField', [], {}),
            'reviewing_photo1': ('maricilib.django.db.models.fields.ResizedImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'reviewing_photo2': ('maricilib.django.db.models.fields.ResizedImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'reviewing_photo3': ('maricilib.django.db.models.fields.ResizedImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'reviewing_photo4': ('maricilib.django.db.models.fields.ResizedImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'reviewing_photo5': ('maricilib.django.db.models.fields.ResizedImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'royalty': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '3'})
        },
        'recipes.direction': {
            'Meta': {'object_name': 'Direction'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'photo': ('maricilib.django.db.models.fields.S3SyncResizedImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'photo_s3': ('maricilib.django.db.models.fields.S3SyncResizedImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'photo_s3_sync': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'recipe': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['recipes.Recipe']"}),
            'text': ('django.db.models.fields.TextField', [], {})
        },
        'recipes.dish': {
            'Meta': {'object_name': 'Dish'},
            'categories': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['recipes.DishCategory']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'photo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'recipes.dishcategory': {
            'Meta': {'object_name': 'DishCategory'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'photo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'recipes.farmproducer': {
            'Meta': {'object_name': 'FarmProducer'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'introduction': ('django.db.models.fields.TextField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'photo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        'recipes.favoriterecipe': {
            'Meta': {'object_name': 'FavoriteRecipe'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'recipe': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['recipes.Recipe']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'recipes.favoriteuser': {
            'Meta': {'object_name': 'FavoriteUser'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'target': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'target'", 'to': "orm['auth.User']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'owner'", 'to': "orm['auth.User']"})
        },
        'recipes.feeling': {
            'Meta': {'object_name': 'Feeling'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'photo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'recipes.ingredient': {
            'Meta': {'object_name': 'Ingredient'},
            'categories': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['recipes.IngredientCategory']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'photo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'recipes.ingredientcategory': {
            'Meta': {'object_name': 'IngredientCategory'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'photo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        'recipes.recipe': {
            'Meta': {'object_name': 'Recipe'},
            'ancestor': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'descendants'", 'null': 'True', 'to': "orm['recipes.Recipe']"}),
            'contest': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['recipes.Contest']", 'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'feeling': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['recipes.Feeling']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ingredients': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'introduction': ('django.db.models.fields.TextField', [], {}),
            'is_awarded': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_draft': ('django.db.models.fields.NullBooleanField', [], {'default': 'True', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'num_moderated_comments': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'num_people': ('django.db.models.fields.IntegerField', [], {'default': '2'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'related_name': "'children'", 'null': 'True', 'to': "orm['recipes.Recipe']"}),
            'photo': ('maricilib.django.db.models.fields.S3SyncResizedImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'photo_s3': ('maricilib.django.db.models.fields.S3SyncResizedImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'photo_s3_sync': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'published_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'reviewed_contest': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['recipes.ReviewedContest']", 'null': 'True', 'blank': 'True'}),
            'score': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'tips': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'recipes.reviewedcontest': {
            'Meta': {'object_name': 'ReviewedContest'},
            'contest': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['recipes.Contest']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'recipes.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'alter_email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'birth_year': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'blog_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'deny_comment': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'deny_mail_magazine': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'icon': ('maricilib.django.db.models.fields.S3SyncResizedImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'icon_s3': ('maricilib.django.db.models.fields.S3SyncResizedImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'icon_s3_sync': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_female': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'karma': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'key_issued_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'level': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'pending_email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'prefecture': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'profile_text': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'recipe_token': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'token_issued_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'}),
            'validation_key': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'vote_point': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'})
        },
        'recipes.vote': {
            'Meta': {'object_name': 'Vote'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'recipe': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['recipes.Recipe']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        }
    }

    complete_apps = ['recipes']