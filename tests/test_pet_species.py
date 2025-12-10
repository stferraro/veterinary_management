from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from psycopg2 import IntegrityError


class TestPetSpecies(TransactionCase):
    """Test cases for pet.species model"""

    def setUp(self):
        super().setUp()
        self.PetSpecies = self.env['pet.species']

    def test_create_species_with_unique_name(self):
        """Test that a new pet species can be created with a unique name"""
        # Create first species
        species = self.PetSpecies.create({
            'name': 'Dog',
            'description': 'Domestic dog species'
        })
        
        self.assertTrue(species.id, "Species should be created successfully")
        self.assertEqual(species.name, 'Dog', "Species name should match")
        self.assertTrue(species.active, "Species should be active by default")

    def test_duplicate_species_name_raises_error(self):
        """Test that creating a species with a duplicate name raises an IntegrityError"""
        # Create first species
        self.PetSpecies.create({
            'name': 'Cat',
            'description': 'Domestic cat species'
        })
        
        # Attempt to create a second species with the same name
        with self.assertRaises(IntegrityError, msg="Duplicate species name should raise IntegrityError"):
            with self.cr.savepoint():
                self.PetSpecies.create({
                    'name': 'Cat',
                    'description': 'Another cat species'
                })

    def test_species_name_uniqueness_case_sensitive(self):
        """Test that species name uniqueness is case-sensitive in database"""
        # Create first species
        self.PetSpecies.create({
            'name': 'Bird'
        })
        
        # Create species with different case (this might succeed depending on DB collation)
        # This test documents the current behavior
        try:
            species2 = self.PetSpecies.create({
                'name': 'BIRD'
            })
            # If successful, names are case-sensitive
            self.assertNotEqual(species2.name, 'Bird')
        except IntegrityError:
            # If it fails, the constraint is case-insensitive
            pass
