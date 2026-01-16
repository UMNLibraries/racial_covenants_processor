import platform          
from multiprocessing import set_start_method

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        
        if platform.system() == "Darwin":  
            set_start_method("fork", force=True)

        call_command("rebuild_index", "--workers", "4")