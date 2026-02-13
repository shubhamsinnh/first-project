"""
Seed script for Temples and Temple Pujas

Usage:
    python seed_temples.py          # Add temples (skips existing)
    python seed_temples.py --reset  # Delete all and re-seed
"""

import sys
from app import app
from database import db
from models import Temple, TemplePuja

TEMPLES_DATA = [
    {
        'name': 'Kashi Vishwanath',
        'location': 'Varanasi',
        'state': 'Uttar Pradesh',
        'image_url': 'temples/kashi.jfif',
        'deity': 'Lord Shiva',
        'description': 'One of the most famous Hindu temples dedicated to Lord Shiva. Located on the western bank of the holy river Ganga.',
        'significance': 'One of the twelve Jyotirlingas. Believed to liberate souls from the cycle of birth and death.',
        'starting_price': 1100,
        'is_featured': True,
        'pujas': [
            {'name': 'Rudrabhishek', 'price': 1100, 'duration': '2-3 hours', 'description': 'Sacred abhishek of Lord Shiva with holy ingredients', 'benefits': 'Removes obstacles, brings peace and prosperity', 'includes': 'Video proof, Prasad, Aashirwad box', 'is_popular': True},
            {'name': 'Mahashivratri Puja', 'price': 2100, 'duration': '4-5 hours', 'description': 'Special puja performed on Mahashivratri', 'benefits': 'Spiritual upliftment, blessings of Lord Shiva', 'includes': 'Video proof, Prasad, Rudraksha, Aashirwad box', 'is_popular': True},
            {'name': 'Kaal Sarp Dosh Puja', 'price': 5100, 'duration': '3-4 hours', 'description': 'Removes Kaal Sarp Dosh from kundali', 'benefits': 'Relief from Kaal Sarp Dosh effects', 'includes': 'Video proof, Prasad, Puja certificate'},
        ]
    },
    {
        'name': 'Vaishno Devi',
        'location': 'Katra',
        'state': 'Jammu & Kashmir',
        'image_url': 'temples/vaishno devi.jpg',
        'deity': 'Maa Vaishno Devi',
        'description': 'One of the most revered Hindu shrines dedicated to Goddess Vaishno Devi, located in the Trikuta Mountains.',
        'significance': 'One of the Shakti Peethas. Millions of devotees visit annually to seek blessings of the Divine Mother.',
        'starting_price': 1500,
        'is_featured': True,
        'pujas': [
            {'name': 'Mata Ki Aarti', 'price': 1500, 'duration': '1-2 hours', 'description': 'Participate in the sacred aarti of Maa Vaishno Devi', 'benefits': 'Divine blessings, fulfillment of wishes', 'includes': 'Video proof, Prasad', 'is_popular': True},
            {'name': 'Navratri Puja', 'price': 2500, 'duration': '2-3 hours', 'description': 'Special puja during Navratri festival', 'benefits': 'Blessings of all nine forms of Goddess', 'includes': 'Video proof, Prasad, Chunri, Aashirwad box', 'is_popular': True},
            {'name': 'Akhand Jyoti', 'price': 1100, 'duration': '24 hours', 'description': 'Continuous lamp lighting in your name', 'benefits': 'Continuous divine blessings', 'includes': 'Photo proof, Certificate'},
        ]
    },
    {
        'name': 'Ram Mandir',
        'location': 'Ayodhya',
        'state': 'Uttar Pradesh',
        'image_url': 'temples/ayodhya.webp',
        'deity': 'Lord Ram',
        'description': 'The newly constructed grand temple at the birthplace of Lord Ram in Ayodhya.',
        'significance': 'Ram Janmabhoomi - the sacred birthplace of Lord Ram. A symbol of faith and devotion.',
        'starting_price': 2100,
        'is_featured': True,
        'pujas': [
            {'name': 'Ram Darshan', 'price': 2100, 'duration': '1-2 hours', 'description': 'Special darshan and puja at Ram Janmabhoomi', 'benefits': 'Blessings of Lord Ram, peace and prosperity', 'includes': 'Video proof, Prasad, Aashirwad box', 'is_popular': True},
            {'name': 'Ram Navami Puja', 'price': 3100, 'duration': '3-4 hours', 'description': 'Special puja on Ram Navami', 'benefits': 'Divine blessings on auspicious day', 'includes': 'Video proof, Prasad, Ram idol, Aashirwad box', 'is_popular': True},
            {'name': 'Saryu Aarti', 'price': 1500, 'duration': '1 hour', 'description': 'Evening aarti at the holy Saryu river', 'benefits': 'Purification and spiritual peace', 'includes': 'Video proof, Prasad'},
        ]
    },
    {
        'name': 'Tirupati Balaji',
        'location': 'Tirumala',
        'state': 'Andhra Pradesh',
        'image_url': 'temples/Tirupati.jfif',
        'deity': 'Lord Venkateswara',
        'description': 'The richest and most visited temple in the world, dedicated to Lord Venkateswara.',
        'significance': 'Known as the abode of Lord Vishnu in Kali Yuga. Grants all wishes of devotees.',
        'starting_price': 1800,
        'is_featured': True,
        'pujas': [
            {'name': 'Suprabhatam', 'price': 1800, 'duration': '1-2 hours', 'description': 'Early morning wake-up seva for the Lord', 'benefits': 'Divine start to your endeavors', 'includes': 'Video proof, Prasad, Laddu', 'is_popular': True},
            {'name': 'Archana', 'price': 1100, 'duration': '30 minutes', 'description': 'Chanting of divine names with offerings', 'benefits': 'Fulfillment of specific wishes', 'includes': 'Video proof, Prasad', 'is_popular': True},
            {'name': 'Kalyanotsavam', 'price': 5100, 'duration': '2-3 hours', 'description': 'Celestial wedding ceremony of the Lord', 'benefits': 'Blessings for marriage and relationships', 'includes': 'Video proof, Prasad, Aashirwad box'},
        ]
    },
    {
        'name': 'Somnath',
        'location': 'Prabhas Patan',
        'state': 'Gujarat',
        'image_url': 'temples/somnath.jpg',
        'deity': 'Lord Shiva',
        'description': 'The first among the twelve Jyotirlingas, located at the shore of the Arabian Sea.',
        'significance': 'Mentioned in ancient scriptures. Rebuilt multiple times, symbolizing eternal faith.',
        'starting_price': 1300,
        'is_featured': True,
        'pujas': [
            {'name': 'Jyotirlinga Puja', 'price': 1300, 'duration': '2 hours', 'description': 'Special puja at the sacred Jyotirlinga', 'benefits': 'Liberation from sins, spiritual progress', 'includes': 'Video proof, Prasad, Aashirwad box', 'is_popular': True},
            {'name': 'Aarti', 'price': 800, 'duration': '30 minutes', 'description': 'Participate in the temple aarti', 'benefits': 'Divine blessings and peace', 'includes': 'Video proof, Prasad', 'is_popular': True},
            {'name': 'Laghu Rudrabhishek', 'price': 2100, 'duration': '2 hours', 'description': 'Abbreviated Rudrabhishek ceremony', 'benefits': 'Removal of obstacles, health benefits', 'includes': 'Video proof, Prasad, Bhasma'},
        ]
    },
    {
        'name': 'Shirdi Sai Baba',
        'location': 'Shirdi',
        'state': 'Maharashtra',
        'image_url': 'temples/shirdi.jfif',
        'deity': 'Sai Baba',
        'description': 'The holy shrine of Sai Baba, who preached love, forgiveness, and helping others.',
        'significance': 'Sai Baba is revered by devotees of all religions. "Sabka Malik Ek" - One God for all.',
        'starting_price': 999,
        'is_featured': True,
        'pujas': [
            {'name': 'Kakad Aarti', 'price': 999, 'duration': '1 hour', 'description': 'Early morning aarti at 4:30 AM', 'benefits': 'Auspicious start, divine blessings', 'includes': 'Video proof, Prasad, Udi', 'is_popular': True},
            {'name': 'Sai Puja', 'price': 1500, 'duration': '1-2 hours', 'description': 'Special puja with abhishek', 'benefits': 'Fulfillment of wishes, peace of mind', 'includes': 'Video proof, Prasad, Udi, Photo', 'is_popular': True},
            {'name': 'Dhoop Aarti', 'price': 800, 'duration': '30 minutes', 'description': 'Evening aarti at sunset', 'benefits': 'Peaceful end to the day', 'includes': 'Video proof, Prasad'},
        ]
    },
    {
        'name': 'Rameswaram',
        'location': 'Rameswaram',
        'state': 'Tamil Nadu',
        'image_url': 'temples/ramesharwaram.jpg',
        'deity': 'Lord Shiva',
        'description': 'One of the Char Dham pilgrimage sites and one of the twelve Jyotirlingas.',
        'significance': 'Established by Lord Ram himself. Known for its magnificent corridor with 1212 pillars.',
        'starting_price': 1400,
        'is_featured': False,
        'pujas': [
            {'name': 'Jyotirlinga Puja', 'price': 1400, 'duration': '2 hours', 'description': 'Puja at the sacred Jyotirlinga', 'benefits': 'Absolution of sins, spiritual merit', 'includes': 'Video proof, Prasad, Aashirwad box', 'is_popular': True},
            {'name': 'Setu Darshan', 'price': 1100, 'duration': '2-3 hours', 'description': 'Visit to Ram Setu and special puja', 'benefits': 'Connection with Ram Katha', 'includes': 'Video proof, Prasad', 'is_popular': True},
            {'name': '22 Theertham Bath', 'price': 2100, 'duration': '3-4 hours', 'description': 'Sacred bath in 22 holy wells', 'benefits': 'Purification of body and soul', 'includes': 'Video proof, Certificate'},
        ]
    },
    {
        'name': 'Kamakhya Devi',
        'location': 'Guwahati',
        'state': 'Assam',
        'image_url': 'temples/Kamakhya.jpg',
        'deity': 'Goddess Kamakhya',
        'description': 'One of the oldest and most revered Shakti Peethas, dedicated to Goddess Kamakhya.',
        'significance': 'Believed to be where the womb of Goddess Sati fell. Powerful tantric temple.',
        'starting_price': 1600,
        'is_featured': False,
        'pujas': [
            {'name': 'Shakti Puja', 'price': 1600, 'duration': '2 hours', 'description': 'Powerful puja to invoke Goddess Shakti', 'benefits': 'Strength, protection, removal of negativity', 'includes': 'Video proof, Prasad, Sindoor', 'is_popular': True},
            {'name': 'Ambubachi Puja', 'price': 3100, 'duration': '3 hours', 'description': 'Special puja during Ambubachi festival', 'benefits': 'Fertility blessings, wish fulfillment', 'includes': 'Video proof, Prasad, Angavastra', 'is_popular': True},
            {'name': 'Tantric Puja', 'price': 5100, 'duration': '4-5 hours', 'description': 'Traditional tantric ritual', 'benefits': 'Powerful spiritual protection', 'includes': 'Video proof, Prasad, Yantra'},
        ]
    },
    {
        'name': 'ISKCON Vrindavan',
        'location': 'Vrindavan',
        'state': 'Uttar Pradesh',
        'image_url': 'temples/vrindavan.jpg',
        'deity': 'Lord Krishna',
        'description': 'Beautiful ISKCON temple in the holy land of Vrindavan, the playground of Lord Krishna.',
        'significance': 'Vrindavan is where Krishna spent his childhood. ISKCON spreads Krishna consciousness worldwide.',
        'starting_price': 1200,
        'is_featured': False,
        'pujas': [
            {'name': 'Krishna Puja', 'price': 1200, 'duration': '1-2 hours', 'description': 'Special puja to Lord Krishna', 'benefits': 'Divine love, joy, and spiritual growth', 'includes': 'Video proof, Prasad, Tulsi mala', 'is_popular': True},
            {'name': 'Janmashtami Puja', 'price': 2500, 'duration': '3-4 hours', 'description': 'Midnight puja on Krishna Janmashtami', 'benefits': 'Special blessings on birthday of Lord', 'includes': 'Video proof, Prasad, Makhan, Aashirwad box', 'is_popular': True},
            {'name': 'Govardhan Puja', 'price': 1800, 'duration': '2 hours', 'description': 'Puja commemorating Krishna lifting Govardhan', 'benefits': 'Protection and abundance', 'includes': 'Video proof, Prasad, Govardhan shila'},
        ]
    },
]


def seed_temples(reset=False):
    """Seed temples and pujas into the database."""
    with app.app_context():
        if reset:
            print('Deleting existing temple data...')
            TemplePuja.query.delete()
            Temple.query.delete()
            db.session.commit()
            print('Done.\n')

        existing_count = Temple.query.count()
        if existing_count > 0 and not reset:
            print(f'Found {existing_count} existing temples. Use --reset to clear and re-seed.')
            print('Skipping seed to avoid duplicates.\n')
            return

        print('Seeding temples...\n')

        for temple_data in TEMPLES_DATA:
            pujas_data = temple_data.pop('pujas', [])

            temple = Temple(**temple_data)
            db.session.add(temple)
            db.session.flush()  # Get the temple ID

            for puja_data in pujas_data:
                puja = TemplePuja(temple_id=temple.id, **puja_data)
                db.session.add(puja)

            print(f'  Added: {temple.name} ({len(pujas_data)} pujas)')

        db.session.commit()
        print(f'\nSeeded {len(TEMPLES_DATA)} temples successfully!')


if __name__ == '__main__':
    reset = '--reset' in sys.argv
    seed_temples(reset=reset)
