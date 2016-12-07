# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'user_per.ch'
        db.delete_column('user_per', 'ch')


    def backwards(self, orm):
        # Adding field 'user_per.ch'
        db.add_column('user_per', 'ch',
                      self.gf('django.db.models.fields.CharField')(max_length=10, null=True),
                      keep_default=False)


    models = {
        u'user.admin': {
            'Meta': {'object_name': 'admin', 'db_table': "'admin'"},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'isadmin': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True'}),
            'lastlogin': ('django.db.models.fields.DateTimeField', [], {}),
            'logincount': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'vaild': ('django.db.models.fields.IntegerField', [], {'default': '1', 'null': 'True'})
        },
        u'user.per_code': {
            'Meta': {'object_name': 'per_code', 'db_table': "'per_code'"},
            'Per_code': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'Per_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'user.user_chpass': {
            'Meta': {'object_name': 'user_chpass', 'db_table': "'user_chpass'"},
            'ctime': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'passuuid': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'user.user_per': {
            'Meta': {'object_name': 'user_per', 'db_table': "'user_per'"},
            'Per_code': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'Per_user': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['user']