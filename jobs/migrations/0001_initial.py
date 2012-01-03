# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Job'
        db.create_table('jobs_job', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('url', self.gf('django.db.models.fields.CharField')(max_length=1024)),
            ('post_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('close_date', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('contact_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('contact_email', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('telecommute', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('salary_start', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('salary_end', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('email_message_id', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True)),
            ('job_type', self.gf('django.db.models.fields.CharField')(default='ft', max_length=2)),
            ('employer', self.gf('django.db.models.fields.related.ForeignKey')(related_name='jobs', null=True, to=orm['jobs.Employer'])),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name='jobs', null=True, to=orm['auth.User'])),
        ))
        db.send_create_signal('jobs', ['Job'])

        # Adding model 'Employer'
        db.create_table('jobs_employer', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('address', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('city', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('state', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('country', self.gf('django.db.models.fields.CharField')(max_length=2)),
            ('domain', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal('jobs', ['Employer'])

        # Adding model 'Keyword'
        db.create_table('jobs_keyword', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('ignore', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('subject', self.gf('django.db.models.fields.related.ForeignKey')(related_name='keywords', null=True, to=orm['jobs.Subject'])),
        ))
        db.send_create_signal('jobs', ['Keyword'])

        # Adding model 'Subject'
        db.create_table('jobs_subject', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('slug', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('freebase_id', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('freebase_type_id', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('jobs', ['Subject'])

        # Adding M2M table for field jobs on 'Subject'
        db.create_table('jobs_subject_jobs', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('subject', models.ForeignKey(orm['jobs.subject'], null=False)),
            ('job', models.ForeignKey(orm['jobs.job'], null=False))
        ))
        db.create_unique('jobs_subject_jobs', ['subject_id', 'job_id'])


    def backwards(self, orm):
        
        # Deleting model 'Job'
        db.delete_table('jobs_job')

        # Deleting model 'Employer'
        db.delete_table('jobs_employer')

        # Deleting model 'Keyword'
        db.delete_table('jobs_keyword')

        # Deleting model 'Subject'
        db.delete_table('jobs_subject')

        # Removing M2M table for field jobs on 'Subject'
        db.delete_table('jobs_subject_jobs')


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
        'jobs.employer': {
            'Meta': {'object_name': 'Employer'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'state': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'jobs.job': {
            'Meta': {'object_name': 'Job'},
            'close_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'contact_email': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'contact_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobs'", 'null': 'True', 'to': "orm['auth.User']"}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'email_message_id': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            'employer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'jobs'", 'null': 'True', 'to': "orm['jobs.Employer']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'job_type': ('django.db.models.fields.CharField', [], {'default': "'ft'", 'max_length': '2'}),
            'post_date': ('django.db.models.fields.DateTimeField', [], {}),
            'salary_end': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'salary_start': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'telecommute': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '1024'})
        },
        'jobs.keyword': {
            'Meta': {'object_name': 'Keyword'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignore': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'subject': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'keywords'", 'null': 'True', 'to': "orm['jobs.Subject']"})
        },
        'jobs.subject': {
            'Meta': {'object_name': 'Subject'},
            'freebase_id': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'freebase_type_id': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'jobs': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'subjects'", 'null': 'True', 'to': "orm['jobs.Job']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['jobs']
