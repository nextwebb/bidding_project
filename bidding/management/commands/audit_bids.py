"""
Management command to run the daily budget audit
"""
from django.core.management.base import BaseCommand
from bidding.tasks import daily_budget_audit, daily_budget_audit_async


class Command(BaseCommand):
    help = 'Run daily budget audit for ProductBid records'

    def add_arguments(self, parser):
        parser.add_argument(
            '--async',
            action='store_true',
            help='Run audit as async task (requires Huey worker)',
        )

    def handle(self, *args, **options):
        if options['async']:
            self.stdout.write("Scheduling async budget audit task...")
            task = daily_budget_audit_async()
            self.stdout.write(
                self.style.SUCCESS(f"Task scheduled: {task.id}")
            )
        else:
            self.stdout.write("Running budget audit synchronously...")
            result = daily_budget_audit()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Audit completed: {result['total_bids']} bids reviewed, "
                    f"{result['flagged_bids']} flagged"
                )
            )
