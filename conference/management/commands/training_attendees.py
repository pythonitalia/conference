# -*- coding: UTF-8 -*-
import csv
import sys
from django.core.management.base import BaseCommand, CommandError
from conference import models

class Command(BaseCommand):
    """
    """
    def handle(self, *args, **options):
        try:
            conference = args[0]
        except IndexError:
            raise CommandError('conference code is missing')

        booking = models.EventBooking.objects\
            .filter(event__schedule__conference=conference)\
            .filter(event__talk__type='t')\
            .order_by('event__talk__title', 'user__first_name', 'user__last_name')\
            .values('event__talk__title', 'event__schedule__date', 'user__first_name', 'user__last_name')

        w = csv.writer(sys.stdout)
        for row in booking:
            w.writerow((
                row['event__talk__title'].encode('utf-8'),
                row['event__schedule__date'],
                (row['user__first_name'] + u' ' + row['user__last_name']).encode('utf-8'),
            ))
