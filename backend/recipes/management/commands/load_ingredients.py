import csv
import os

from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Load ingredients from CSV file'

    def handle(self, *args, **options):
        csv_file = os.path.join('data', 'ingredients.csv')
        
        if not os.path.exists(csv_file):
            self.stdout.write(
                self.style.ERROR(f'File {csv_file} does not exist')
            )
            return

        with open(csv_file, encoding='utf-8') as file:
            reader = csv.reader(file)
            ingredients = []
            for row in reader:
                name, measurement_unit = row
                ingredients.append(
                    Ingredient(
                        name=name.strip(),
                        measurement_unit=measurement_unit.strip()
                    )
                )
            
            Ingredient.objects.bulk_create(ingredients, ignore_conflicts=True)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully loaded {len(ingredients)} ingredients'
                )
            ) 