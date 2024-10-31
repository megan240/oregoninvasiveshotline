from django.db import models
from django.http import QueryDict

from oregoninvasiveshotline.species.models import Category
from oregoninvasiveshotline.counties.models import County
from oregoninvasiveshotline.cities.models import City


class UserNotificationQuery(models.Model):
    """
    TBD
    """
    class Meta:
        db_table = 'user_notification_query'

    user_notification_query_id = models.AutoField(primary_key=True)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    name = models.CharField(
        max_length=255,
        verbose_name=(
            'To make it easier to review your subscriptions, give the search you just performed '
            'a name. For example: "Aquatic plants in Multnomah county".'
        )
    )
    query = models.TextField(
        help_text=(
            'This is a string for a QueryDict of the GET parameters to pass to the '
            'ReportSearchForm that match reports the user should be notified about.'
        )
    )
    created_on = models.DateTimeField(auto_now_add=True)

    @property
    def pretty_query(self):
        """
        Returns a dictionary of human-readable names for select query parameters
        """
        query = QueryDict(self.query)
        query_items = {}
        if query.get('categories'):
            categories = Category.objects.filter(pk__in=query.getlist('categories'))
            categories = categories.values_list('name', flat=True).order_by('name')
            query_items['Categories'] = ", ".join(categories)
        if query.get('counties'):
            counties = County.objects.filter(pk__in=query.getlist('counties'))
            counties = counties.values_list('name', flat=True).order_by('name')
            query_items['Counties'] = ", ".join(counties)
        if query.get('cities'):
            cities = City.objects.filter(pk__in=query.getlist('cities'))
            cities = cities.values_list('name', flat=True).order_by('name')
            query_items['Cities'] = ", ".join(cities)
        if query.get('q'):
            query_items['Keyword'] = query['q']
        return query_items

    def __str__(self):
        return self.name


class Notification(models.Model):
    """
    Keeps track of notifications to users.

    This keeps track of which users have been notified about which
    reports, so they don't get emailed twice about the same report.
    """
    class Meta:
        db_table = 'notification'

    notification_id = models.AutoField(primary_key=True)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    report = models.ForeignKey('reports.Report', on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return 'Notification for: report "{0.report.title}"'.format(self)
