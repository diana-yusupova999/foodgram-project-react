import csv

from django.core.management import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = "Загрузка ингредиентов в базу данных."

    def handle(self, *args, **kwargs):
        csv_file = "data/ingredients.csv"

        with open(csv_file, encoding="utf-8") as file:
            csv_reader = csv.reader(file, delimiter=",")
            for name, measurement_unit in csv_reader:
                _, created = Ingredient.objects.get_or_create(
                    name=name,
                    measurement_unit=measurement_unit
                )
                if created:
                    self.stdout.write(f"Создан ингредиент: {name}")
                else:
                    self.stdout.write(f"Ингредиент {name} уже существует")
            self.stdout.write(
                self.style.SUCCESS("Ингредиенты успешно загружены.")
            )
