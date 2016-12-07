# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'admin'
        db.create_table('admin', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('username', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
            ('vaild', self.gf('django.db.models.fields.IntegerField')(default=1, null=True)),
            ('isadmin', self.gf('django.db.models.fields.IntegerField')(default=0, null=True)),
            ('logincount', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('lastlogin', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal(u'user', ['admin'])

        # Adding model 'user_per'
        db.create_table('user_per', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('Per_user', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('Per_code', self.gf('django.db.models.fields.CharField')(max_length=5)),
            ('comment', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True)),
        ))
        db.send_create_signal(u'user', ['user_per'])

        # Adding model 'per_code'
        db.create_table('per_code', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('Per_code', self.gf('django.db.models.fields.CharField')(max_length=5)),
            ('Per_name', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal(u'user', ['per_code'])

        # Adding model 'user_chpass'
        db.create_table('user_chpass', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('username', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('passuuid', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('ctime', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal(u'user', ['user_chpass'])


    def backwards(self, orm):
        # Deleting model 'admin'
        db.delete_table('admin')

        # Deleting model 'user_per'
        db.delete_table('user_per')

        # Deleting model 'per_code'
        db.delete_table('per_code')

        # Deleting model 'user_chpass'
        db.delete_table('user_chpass')


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