# encoding: utf-8
from __future__ import absolute_import, division, print_function, unicode_literals

import re
import logging
import multiprocessing
from progressbar import ProgressBar, RotatingMarker, Bar, Percentage, ETA, Counter
import time
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import close_old_connections, reset_queries
from django.utils.encoding import force_text, smart_bytes
from django.utils.timezone import now

from haystack import connections as haystack_connections
from haystack.exceptions import NotHandled
from haystack.query import SearchQuerySet
from haystack.utils.app_loading import haystack_get_models, haystack_load_apps

DEFAULT_BATCH_SIZE = None
DEFAULT_AGE = None
DEFAULT_MAX_RETRIES = 5

LOG = multiprocessing.log_to_stderr(level=logging.WARNING)

# ----------------------------------------------------------------------------------------------------------------------

def plural(string):
    patterns = [('[sxz]$', '$', 'es'),
                ('[^aeioudgkprt]h$', '$', 'es'),
                ('[^aeiou]y$', 'y$', 'ies'),
                ('$', '$', 's')]

    rules = map(lambda (pattern, search, replace): lambda word: re.search(pattern, word) and
                                                                re.sub(search, replace, word), patterns)
    for rule in rules:
        result = rule(string)
        if result:
            return result

# ----------------------------------------------------------------------------------------------------------------------

def do_update(backend, index, qs, commit=True, max_retries=DEFAULT_MAX_RETRIES):

    retries = 0
    while retries < max_retries:
        try:
            backend.update(index, qs, commit=commit)
            break
        except Exception:
            retries += 1
            time.sleep(2 ** retries)

# ----------------------------------------------------------------------------------------------------------------------


class Command(BaseCommand):
    help = "Freshens the index for the given app(s)."

# ----------------------------------------------------------------------------------------------------------------------

    def add_arguments(self, parser):
        parser.add_argument(
            'app_label', nargs='*',
            help='App label of an application to update the search index.'
        )
        parser.add_argument(
            '-a', '--age', type=int, default=DEFAULT_AGE,
            help='Number of hours back to consider objects new.'
        )
        parser.add_argument(
            '-s', '--start', dest='start_date',
            help='The start date for indexing within. Can be any dateutil-parsable string, recommended to be YYYY-MM-DDTHH:MM:SS.'
        )
        parser.add_argument(
            '-e', '--end', dest='end_date',
            help='The end date for indexing within. Can be any dateutil-parsable string, recommended to be YYYY-MM-DDTHH:MM:SS.'
        )
        parser.add_argument(
            '-b', '--batch-size', dest='batchsize', type=int,
            help='Number of items to index at once.'
        )
        parser.add_argument(
            '-r', '--remove', action='store_true', default=False,
            help='Remove objects from the index that are no longer present in the database.'
        )
        parser.add_argument(
            '-u', '--using', action='append', default=[],
            help='Update only the named backend (can be used multiple times). '
                 'By default all backends will be updated.'
        )
        parser.add_argument(
            '-k', '--workers', type=int, default=0,
            help='Allows for the use multiple workers to parallelize indexing.'
        )
        parser.add_argument(
            '--nocommit', action='store_false', dest='commit',
            default=True, help='Will pass commit=False to the backend.'
        )
        parser.add_argument(
            '-t', '--max-retries', action='store', dest='max_retries',
            type=int, default=DEFAULT_MAX_RETRIES,
            help='Maximum number of attempts to write to the backend when an error occurs.'
        )

# ----------------------------------------------------------------------------------------------------------------------

    def handle(self, **options):
        self.verbosity = int(options.get('verbosity', 1))
        self.batchsize = options.get('batchsize', DEFAULT_BATCH_SIZE)
        self.start_date = None
        self.end_date = None
        self.remove = options.get('remove', False)
        self.workers = options.get('workers', 0)
        self.commit = options.get('commit', True)
        self.max_retries = options.get('max_retries', DEFAULT_MAX_RETRIES)

        self.backends = options.get('using')
        if not self.backends:
            self.backends = haystack_connections.connections_info.keys()

        age = options.get('age', DEFAULT_AGE)
        start_date = options.get('start_date')
        end_date = options.get('end_date')

        if self.verbosity > 2:
            LOG.setLevel(logging.DEBUG)
        elif self.verbosity > 1:
            LOG.setLevel(logging.INFO)

        if age is not None:
            self.start_date = now() - timedelta(hours=int(age))

        if start_date is not None:
            from dateutil.parser import parse as dateutil_parse

            try:
                self.start_date = dateutil_parse(start_date)
            except ValueError:
                pass

        if end_date is not None:
            from dateutil.parser import parse as dateutil_parse

            try:
                self.end_date = dateutil_parse(end_date)
            except ValueError:
                pass

        labels = options.get('app_label') or haystack_load_apps()
        for label in labels:
            for using in self.backends:
                try:
                    self.update_backend(label, using)
                except:
                    LOG.exception("Error updating %s using %s ", label, using)
                    raise

# ----------------------------------------------------------------------------------------------------------------------

    def update_backend(self, label, using):
        backend = haystack_connections[using].get_backend()
        unified_index = haystack_connections[using].get_unified_index()

        for model in haystack_get_models(label):
            try:
                index = unified_index.get_index(model)
            except NotHandled:
                continue

            qs = index.build_queryset(using=using, start_date=self.start_date,
                                      end_date=self.end_date)

            total = qs.count()

            if self.verbosity >= 1:
                self.stdout.write(u"Indexing %d %s" % (
                    total, plural(force_text(model._meta.verbose_name)))
                )

            batch_size = self.batchsize or backend.batch_size

            pbar = ProgressBar(widgets=['{0}: '.format(model._meta.verbose_name),
                                        Percentage(), ' (', Counter(), ') ',
                                        Bar(marker=RotatingMarker()), ' ', ETA()],
                               maxval=total).start()

            last_pk = None
            for start in range(0, total, batch_size):
                pbar.update(start)
                if not last_pk:
                    last_pk = qs.only('pk').values_list('pk')[start][0]
                original_data = model.objects.using(using).filter(pk__gt=last_pk).prefetch_related(
                    *index.get_prefetch()).order_by('pk')[:batch_size]
                actual_size = len(original_data)
                last_pk = original_data[actual_size - 1].pk
                do_update(backend, index, original_data, commit=self.commit, max_retries=self.max_retries)

            pbar.update(total)
            pbar.finish()

# ----------------------------------------------------------------------------------------------------------------------
