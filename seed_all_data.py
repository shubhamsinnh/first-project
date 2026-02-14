"""
Seed/Sync script for all data (Pandits, Materials, Testimonials, Bundles)

Usage:
    python seed_all_data.py          # Update existing + add missing
    python seed_all_data.py --reset  # Delete all and re-seed
"""

import sys
from app import app
from database import db
from models import Pandit, PujaMaterial, Testimonial, Bundle

PANDITS_DATA = [
    {
        'id': 1,
        'name': 'Pandit Govind Jha',
        'location': 'Delhi, NCR',
        'experience': '15+ Years',
        'image_url': 'govind 1.jpg',
        'availability': True,
        'is_approved': True,
    },
    {
        'id': 2,
        'name': 'Pandit Medhansh Acharya',
        'location': 'Mumbai, Maharashtra',
        'experience': '10+ Years',
        'image_url': 'Medhansh 1.jpg',
        'availability': True,
        'is_approved': True,
    },
    {
        'id': 3,
        'name': 'Pandit Pankaj Jha',
        'location': 'Bangalore, Karnataka',
        'experience': '20+ Years',
        'image_url': 'pankaj-jha1.jpg',
        'availability': False,
        'is_approved': True,
    },
    {
        'id': 4,
        'name': 'Pandit Shankar Pandit',
        'location': 'Pune, Maharashtra',
        'experience': '12+ Years',
        'image_url': 'shankar pandit 1.jpg',
        'availability': True,
        'is_approved': True,
    },
]

MATERIALS_DATA = [
    {
        'id': 1,
        'name': 'Premium Incense Sticks Set',
        'price': 299.00,
        'image_url': 'pujamaterial/Premium Incense Sticks Set.webp',
        'description': 'High-quality incense sticks for daily puja',
    },
    {
        'id': 2,
        'name': 'Brass Diya Collection',
        'price': 599.00,
        'image_url': 'pujamaterial/brass collection.jpg',
        'description': 'Traditional brass diyas for auspicious occasions',
    },
    {
        'id': 3,
        'name': 'Sacred Puja Thali Set',
        'price': 1299.00,
        'image_url': 'pujamaterial/Puja thali set.webp',
        'description': 'Complete puja thali with all essentials',
    },
    {
        'id': 4,
        'name': 'Organic Camphor Tablets',
        'price': 149.00,
        'image_url': 'pujamaterial/camphor tablet.webp',
        'description': 'Pure organic camphor for aarti',
    },
]

TESTIMONIALS_DATA = [
    {
        'id': 1,
        'author': 'Priya Sharma',
        'location': 'Mumbai, Maharashtra',
        'rating': 5,
        'author_image': 'testimonial/priya.jpg',
        'content': 'Excellent service! The pandit was very knowledgeable and performed the puja with great devotion.',
    },
    {
        'id': 2,
        'author': 'Rajesh Kumar',
        'location': 'Delhi, NCR',
        'rating': 5,
        'author_image': 'testimonial/rajesh.jpg',
        'content': 'Very professional and punctual. The puja materials were authentic and of high quality.',
    },
    {
        'id': 3,
        'author': 'Anjali Verma',
        'location': 'Bangalore, Karnataka',
        'rating': 5,
        'author_image': 'testimonial/anjali.jpg',
        'content': 'Amazing experience! Everything was perfectly organized and the pandit explained every ritual.',
    },
    {
        'id': 4,
        'author': 'Vikram Singh',
        'location': 'Jaipur, Rajasthan',
        'rating': 4,
        'author_image': 'testimonial/vikram.jpg',
        'content': 'Good service overall. The booking process was smooth and hassle-free.',
    },
]

BUNDLES_DATA = [
    {
        'id': 1,
        'name': 'Griha Pravesh Complete Package',
        'original_price': 5999.00,
        'discounted_price': 4499.00,
        'image_url': 'bundle/griha parvesh.jpg',
        'description': 'Complete package for house warming ceremony',
    },
    {
        'id': 2,
        'name': 'Satyanarayan Puja Bundle',
        'original_price': 3499.00,
        'discounted_price': 2799.00,
        'image_url': 'bundle/Satyanarayan Puja Bundle.jpg',
        'description': 'Everything needed for Satyanarayan Katha',
    },
    {
        'id': 3,
        'name': 'Monthly Puja Essentials Box',
        'original_price': 999.00,
        'discounted_price': 799.00,
        'image_url': 'bundle/Monthly Puja Essentials Box.webp',
        'description': 'Monthly subscription box for daily puja needs',
    },
    {
        'id': 4,
        'name': 'Wedding Ritual Complete Set',
        'original_price': 15999.00,
        'discounted_price': 12999.00,
        'image_url': 'bundle/Wedding Ritual Complete.webp',
        'description': 'Complete set for wedding ceremonies',
    },
]


def seed_all_data(reset=False):
    """Seed/update all data in the database."""
    with app.app_context():
        if reset:
            print('Deleting existing data...')
            Pandit.query.delete()
            PujaMaterial.query.delete()
            Testimonial.query.delete()
            Bundle.query.delete()
            db.session.commit()
            print('Done.\n')

        # Sync Pandits
        print('Syncing Pandits...')
        for data in PANDITS_DATA:
            pandit = Pandit.query.get(data['id'])
            if pandit:
                for key, value in data.items():
                    if key != 'id':
                        setattr(pandit, key, value)
                print(f"  Updated: {data['name']}")
            else:
                pandit = Pandit(**data)
                db.session.add(pandit)
                print(f"  Added: {data['name']}")

        # Sync Materials
        print('\nSyncing Materials...')
        for data in MATERIALS_DATA:
            material = PujaMaterial.query.get(data['id'])
            if material:
                for key, value in data.items():
                    if key != 'id':
                        setattr(material, key, value)
                print(f"  Updated: {data['name']}")
            else:
                material = PujaMaterial(**data)
                db.session.add(material)
                print(f"  Added: {data['name']}")

        # Sync Testimonials
        print('\nSyncing Testimonials...')
        for data in TESTIMONIALS_DATA:
            testimonial = Testimonial.query.get(data['id'])
            if testimonial:
                for key, value in data.items():
                    if key != 'id':
                        setattr(testimonial, key, value)
                print(f"  Updated: {data['author']}")
            else:
                testimonial = Testimonial(**data)
                db.session.add(testimonial)
                print(f"  Added: {data['author']}")

        # Sync Bundles
        print('\nSyncing Bundles...')
        for data in BUNDLES_DATA:
            bundle = Bundle.query.get(data['id'])
            if bundle:
                for key, value in data.items():
                    if key != 'id':
                        setattr(bundle, key, value)
                print(f"  Updated: {data['name']}")
            else:
                bundle = Bundle(**data)
                db.session.add(bundle)
                print(f"  Added: {data['name']}")

        db.session.commit()
        print('\nAll data synced successfully!')


if __name__ == '__main__':
    reset = '--reset' in sys.argv
    seed_all_data(reset=reset)
