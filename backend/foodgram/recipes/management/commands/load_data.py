from itertools import count
from django.core.management.base import BaseCommand
import json
from recipes.models import Ingredient


class Command(BaseCommand):
    def handle(self, *args, **options):
        with open('ingredients.json', 'rb') as f:
            data = json.load(f)
            for i in data:
                if Ingredient.objects.filter(
                        name=i['name'],
                        measurement_unit=i['measurement_unit']
                ).exists():
                    continue
                ingredient = Ingredient()
                ingredient.name = i['name']
                ingredient.measurement_unit = i['measurement_unit']
                ingredient.save()
                print(i['name'], i['measurement_unit'])