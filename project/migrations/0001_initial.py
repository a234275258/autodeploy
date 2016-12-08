# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'project'
        db.create_table('project', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('Pro_name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=20)),
            ('Pro_desc', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('svn_ip', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('certificateid', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('mavenpara', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('buildtype', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('username', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
        ))
        db.send_create_signal(u'project', ['project'])

        # Adding model 'project_build'
        db.create_table('project_build', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('Pro_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('builddate', self.gf('django.db.models.fields.DateTimeField')()),
            ('success', self.gf('django.db.models.fields.BooleanField')()),
            ('file', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('svnversion', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
            ('username', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('buildlog', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'project', ['project_build'])


    def backwards(self, orm):
        # Deleting model 'project'
        db.delete_table('project')

        # Deleting model 'project_build'
        db.delete_table('project_build')


    models = {
        u'project.project': {
            'Meta': {'object_name': 'project', 'db_table': "'project'"},
            'Pro_desc': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'Pro_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'}),
            'buildtype': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'certificateid': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mavenpara': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'svn_ip': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'})
        },
        u'project.project_build': {
            'Meta': {'object_name': 'project_build', 'db_table': "'project_build'"},
            'Pro_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'builddate': ('django.db.models.fields.DateTimeField', [], {}),
            'buildlog': ('django.db.models.fields.TextField', [], {}),
            'file': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'success': ('django.db.models.fields.BooleanField', [], {}),
            'svnversion': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        }
    }

    complete_apps = ['project']