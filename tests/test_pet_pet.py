from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from odoo import fields
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta


class TestPetPet(TransactionCase):
    def setUp(self):
        super().setUp()
        self.PetPet = self.env['pet.pet']
        self.PetSpecies = self.env['pet.species']
        self.PetBreed = self.env['pet.breed']
        self.ResPartner = self.env['res.partner']

        # Create a species
        self.species = self.PetSpecies.create({'name': 'Dog'})

        # Create a breed
        self.breed = self.PetBreed.create({'name': 'Labrador', 'species_id': self.species.id})

        # Create an owner
        self.owner = self.ResPartner.create({'name': 'John Doe'})

    def test_create_pet(self):
        pet = self.PetPet.create({
            'name': 'Buddy',
            'species_id': self.species.id,
            'breed_id': self.breed.id,
            'gender': 'male',
            'birth_date': '2020-01-01',
            'owner_id': self.owner.id,
            'weight': 25.0
        })
        self.assertEqual(pet.name, 'Buddy')
        self.assertEqual(pet.species_id, self.species)
        self.assertEqual(pet.breed_id, self.breed)
        self.assertEqual(pet.gender, 'male')
        self.assertEqual(pet.birth_date, '2020-01-01')
        self.assertEqual(pet.owner_id, self.owner)
        self.assertEqual(pet.weight, 25.0)
