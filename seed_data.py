import os
from models import db, User, Service, Gallery, Review, ContactEnquiry, WebsiteSetting, Appointment

def seed_database():
    """Seeds the database with realistic demo data for Nature Unisex Salon if empty."""
    
    # 1. Seed Admin User
    admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
    admin_email = os.environ.get('ADMIN_EMAIL', 'admin@natureunisexsalon.com')
    admin_password = os.environ.get('ADMIN_PASSWORD', 'Admin@Nature2026')
    
    existing_admin = User.query.filter_by(username=admin_username).first()
    if not existing_admin:
        admin = User(
            username=admin_username,
            email=admin_email,
            is_admin=True
        )
        admin.set_password(admin_password)
        db.session.add(admin)
        print(f"[*] Admin user created: {admin_username}")

    # 2. Seed Website Settings
    if not WebsiteSetting.query.first():
        settings = WebsiteSetting(
            salon_name="Nature Unisex Salon",
            tagline="Style. Care. Confidence.",
            phone="+91 74837 37517",
            whatsapp_number="917483737517",
            email="info@natureunisexsalon.com",
            address="Nature Unisex Salon, Austin Town / Neelasandra, Bengaluru, Karnataka 560047, India",
            google_maps_url="https://www.google.com/maps/place/Nature+unisex+salon/@12.9570761,77.6192442,15z/data=!4m6!3m5!1s0x3bae156290e25a91:0x923594a7d37cb230!8m2!3d12.9565087!4d77.6196044!16s%2Fg%2F11z1zkml55?entry=ttu",
            google_maps_embed="https://maps.google.com/maps?q=12.9565087,77.6196044+(Nature%20Unisex%20Salon)&t=&z=16&ie=UTF8&iwloc=B&output=embed",
            instagram_url="https://instagram.com/natureunisexsalon",
            facebook_url="https://facebook.com/natureunisexsalon",
            opening_hours_weekdays="Mon - Sat: 9:00 AM - 9:00 PM",
            opening_hours_weekends="Sun: 10:00 AM - 8:00 PM",
            hero_headline="Style. Care. Confidence.",
            hero_subtext="Discover bespoke hair artistry, rejuvenating skincare, and precision grooming crafted for both men and women in an atmosphere of organic calm and modern elegance.",
            about_text="Nature Unisex Salon was founded on the philosophy that true beauty stems from mindful care, natural wellness, and artisan technique. We provide a hygienic, welcoming sanctuary where top-tier stylists tailor every cut, colour, and skin ritual to your unique identity.",
            currency_symbol="₹"
        )
        db.session.add(settings)
        print("[*] Default website settings created.")

    # 3. Seed Services
    if Service.query.count() == 0:
        services_data = [
            # MEN SERVICES
            {
                "name": "Classic Precision Haircut",
                "gender_target": "Men",
                "category": "Hair",
                "description": "Custom consultation, precision scissor and clipper styling, soothing hair wash, and blowdry finish.",
                "price": 350.0,
                "duration_mins": 30,
                "image_url": "/static/images/services/men_haircut.jpg",
                "display_order": 1
            },
            {
                "name": "Executive Fade & Texture Styling",
                "gender_target": "Men",
                "category": "Hair",
                "description": "Skin fade or taper with scissor texturizing, scalp massage, and premium matte styling clay finish.",
                "price": 500.0,
                "duration_mins": 45,
                "image_url": "/static/images/services/men_fade.jpg",
                "display_order": 2
            },
            {
                "name": "Beard Trim & Razor Line Sculpting",
                "gender_target": "Men",
                "category": "Grooming",
                "description": "Hot towel prep, organic beard oil conditioning, crisp razor lining, and shaping.",
                "price": 250.0,
                "duration_mins": 25,
                "image_url": "/static/images/services/men_beard.jpg",
                "display_order": 3
            },
            {
                "name": "Royal Charcoal Beard Spa",
                "gender_target": "Men",
                "category": "Grooming",
                "description": "Deep exfoliating scrub, steam infusion, nourishing beard butter mask, and razor edge detailing.",
                "price": 450.0,
                "duration_mins": 35,
                "image_url": "/static/images/services/men_beard_spa.jpg",
                "display_order": 4
            },
            {
                "name": "Men's Organic Grey Blending & Hair Colour",
                "gender_target": "Men",
                "category": "Hair",
                "description": "Ammonia-free subtle grey coverage or fashion shade application with conditioning gloss.",
                "price": 900.0,
                "duration_mins": 50,
                "image_url": "/static/images/services/men_colour.jpg",
                "display_order": 5
            },
            {
                "name": "Scalp Detox & Anti-Dandruff Spa",
                "gender_target": "Men",
                "category": "Hair",
                "description": "Tea-tree clarifying scrub, steam therapy, botanical scalp serum, and relaxing 20-min acupressure massage.",
                "price": 1200.0,
                "duration_mins": 60,
                "image_url": "/static/images/services/men_spa.jpg",
                "display_order": 6
            },
            {
                "name": "Deep Cleanse Hydra-Oxygen Facial",
                "gender_target": "Men",
                "category": "Skin",
                "description": "Ultrasonic pore purification, botanical vitamin C infusion, face lymphatic drainage massage, and cooling clay mask.",
                "price": 1500.0,
                "duration_mins": 50,
                "image_url": "/static/images/services/men_facial.jpg",
                "display_order": 7
            },
            {
                "name": "Gentleman's Signature Grooming Package",
                "gender_target": "Men",
                "category": "Packages",
                "description": "Complete transformation: Haircut, Royal Beard Spa, De-tan Cleanse, and invigorating Head & Shoulder massage.",
                "price": 2200.0,
                "duration_mins": 90,
                "image_url": "/static/images/services/men_package.jpg",
                "display_order": 8
            },

            # WOMEN SERVICES
            {
                "name": "Signature Precision Haircut & Styling",
                "gender_target": "Women",
                "category": "Hair",
                "description": "Personalized face-contouring haircut, luxury wash, moisture mask, and professional salon blowout.",
                "price": 750.0,
                "duration_mins": 45,
                "image_url": "/static/images/services/women_haircut.jpg",
                "display_order": 9
            },
            {
                "name": "Advance Feather & Butterfly Layers",
                "gender_target": "Women",
                "category": "Hair",
                "description": "Volumizing layered cut with curtain bangs or face framing, finished with bouncy salon curls.",
                "price": 950.0,
                "duration_mins": 60,
                "image_url": "/static/images/services/women_layers.jpg",
                "display_order": 10
            },
            {
                "name": "Global Organic Ammonia-Free Hair Colour",
                "gender_target": "Women",
                "category": "Hair",
                "description": "Rich, high-shine dimensional color infused with plant oils to protect hair integrity and shine.",
                "price": 2500.0,
                "duration_mins": 90,
                "image_url": "/static/images/services/women_colour.jpg",
                "display_order": 11
            },
            {
                "name": "Artisan Balayage / Babylights",
                "gender_target": "Women",
                "category": "Hair",
                "description": "Freehand blended highlights with custom toner, bond-builder therapy, and glam gloss finish.",
                "price": 4500.0,
                "duration_mins": 150,
                "image_url": "/static/images/services/women_balayage.jpg",
                "display_order": 12
            },
            {
                "name": "Moroccan Argan Intensive Hair Spa",
                "gender_target": "Women",
                "category": "Hair",
                "description": "Deep nourishment with pure argan elixir, steam micro-mist, scalp acupressure, and serum seal.",
                "price": 1800.0,
                "duration_mins": 60,
                "image_url": "/static/images/services/women_hair_spa.jpg",
                "display_order": 13
            },
            {
                "name": "Brazilian Keratin Smoothening Treatment",
                "gender_target": "Women",
                "category": "Hair",
                "description": "Eliminates frizz, restores protein keratin structure, delivers mirror-like shine lasting up to 4 months.",
                "price": 4999.0,
                "duration_mins": 180,
                "image_url": "/static/images/services/women_keratin.jpg",
                "display_order": 14
            },
            {
                "name": "Botanical Radiance Gold Facial",
                "gender_target": "Women",
                "category": "Skin",
                "description": "24K gold active peptides, deep skin micro-exfoliation, collagen sheet mask, and jade roller therapy.",
                "price": 1800.0,
                "duration_mins": 60,
                "image_url": "/static/images/services/women_facial.jpg",
                "display_order": 15
            },
            {
                "name": "O3+ Deep Whitening & Glow Cleanup",
                "gender_target": "Women",
                "category": "Skin",
                "description": "Rapid skin rejuvenation, blackhead extraction, de-pigmentation serum, and instant brightness pack.",
                "price": 1200.0,
                "duration_mins": 45,
                "image_url": "/static/images/services/women_cleanup.jpg",
                "display_order": 16
            },
            {
                "name": "Luxury Rose & Vanilla Pedicure & Manicure",
                "gender_target": "Women",
                "category": "Spa",
                "description": "Essential oil soak, dead skin peel, exfoliating scrub, hydration mask, nail shaping, and gel lacquer.",
                "price": 1400.0,
                "duration_mins": 75,
                "image_url": "/static/images/services/women_mani_pedi.jpg",
                "display_order": 17
            },
            {
                "name": "Celebrity HD Party Makeup & Styling",
                "gender_target": "Women",
                "category": "Makeup",
                "description": "Flawless HD skin finish, international cosmetic brands, false lashes, contouring, and event hairstyling.",
                "price": 3500.0,
                "duration_mins": 90,
                "image_url": "/static/images/services/women_party_makeup.jpg",
                "display_order": 18
            },
            {
                "name": "Royal Bridal HD Makeup & Saree Draping",
                "gender_target": "Women",
                "category": "Bridal",
                "description": "Complete luxury bridal makeover: Airbrush/HD finish, jewelry setting, designer hair do, and custom draping.",
                "price": 12500.0,
                "duration_mins": 210,
                "image_url": "/static/images/services/women_bridal.jpg",
                "display_order": 19
            },
            {
                "name": "Bridal Glow Head-to-Toe Pre-Wedding Package",
                "gender_target": "Women",
                "category": "Packages",
                "description": "Full Body Polishing, Radiance Facial, Moroccan Hair Spa, Luxury Mani-Pedi, Threading & Full Waxing.",
                "price": 8500.0,
                "duration_mins": 240,
                "image_url": "/static/images/services/women_bridal_package.jpg",
                "display_order": 20
            },

            # UNISEX SERVICES
            {
                "name": "Herbal Express Scalp & Neck Therapy",
                "gender_target": "Unisex",
                "category": "Spa",
                "description": "Ayurvedic herbal warm oil head massage targeting stress points, followed by steam and herbal rinse.",
                "price": 650.0,
                "duration_mins": 30,
                "image_url": "/static/images/services/unisex_head_massage.jpg",
                "display_order": 21
            },
            {
                "name": "De-Tan Brightening Pack & Face Scrub",
                "gender_target": "Unisex",
                "category": "Skin",
                "description": "Natural fruit acid gentle exfoliation to reverse sun damage, tanning, and dullness.",
                "price": 800.0,
                "duration_mins": 30,
                "image_url": "/static/images/services/unisex_detan.jpg",
                "display_order": 22
            }
        ]
        for item in services_data:
            svc = Service(**item)
            db.session.add(svc)
        print(f"[*] Seeded {len(services_data)} salon services.")

    # 4. Seed Gallery Items
    if Gallery.query.count() == 0:
        gallery_data = [
            {"title": "Balayage & Soft Waves", "category": "Hair", "image_url": "/static/images/gallery/gallery_hair1.jpg"},
            {"title": "Gentleman's Fade & Beard Sculpting", "category": "Grooming", "image_url": "/static/images/gallery/gallery_grooming1.jpg"},
            {"title": "Royal Bridal Makeover", "category": "Bridal", "image_url": "/static/images/gallery/gallery_bridal1.jpg"},
            {"title": "Glam Evening Makeup & Updo", "category": "Makeup", "image_url": "/static/images/gallery/gallery_makeup1.jpg"},
            {"title": "Modern Salon Interior & Styling Stations", "category": "Interior", "image_url": "/static/images/gallery/gallery_interior1.jpg"},
            {"title": "Complete Color Transformation", "category": "Transformations", "image_url": "/static/images/gallery/gallery_transform1.jpg"},
            {"title": "Textured Crop & Clean Edges", "category": "Hair", "image_url": "/static/images/gallery/gallery_hair2.jpg"},
            {"title": "Botanical Skin Treatment Session", "category": "Interior", "image_url": "/static/images/gallery/gallery_interior2.jpg"},
        ]
        for item in gallery_data:
            gal = Gallery(**item)
            db.session.add(gal)
        print(f"[*] Seeded {len(gallery_data)} gallery portfolio items.")

    # 5. Seed Customer Reviews
    if Review.query.count() == 0:
        reviews_data = [
            {
                "customer_name": "Aarav Sharma",
                "rating": 5,
                "review_text": "Easily one of the best salon experiences in town. The stylist understood exactly the fade and beard contour I wanted. Extremely hygienic and polite staff.",
                "service_name": "Gentleman's Signature Grooming Package",
                "display_order": 1
            },
            {
                "customer_name": "Priya Sen",
                "rating": 5,
                "review_text": "Got my Balayage and Argan hair spa done here. The results exceeded my expectations! My hair feels so soft and the colour dimension is gorgeous. Highly recommend Nature Unisex Salon.",
                "service_name": "Artisan Balayage & Hair Spa",
                "display_order": 2
            },
            {
                "customer_name": "Rohan Mehra",
                "rating": 5,
                "review_text": "Very clean, soothing ambiance and premium products. The Hydra facial left my skin feeling completely refreshed. Will definitely be a regular customer here.",
                "service_name": "Deep Cleanse Hydra-Oxygen Facial",
                "display_order": 3
            },
            {
                "customer_name": "Ananya Kapoor",
                "rating": 5,
                "review_text": "Nature Unisex Salon did my engagement makeup and hairstyling. The team was punctual, attentive to my preferences, and the makeup stayed flawless throughout the evening!",
                "service_name": "Celebrity HD Party Makeup",
                "display_order": 4
            },
            {
                "customer_name": "Vikram Malhotra",
                "rating": 5,
                "review_text": "Top notch hair styling for men. No rushed cuts, proper attention to detail, and a very relaxing hair wash.",
                "service_name": "Executive Fade & Texture Styling",
                "display_order": 5
            }
        ]
        for item in reviews_data:
            rev = Review(**item)
            db.session.add(rev)
        print(f"[*] Seeded {len(reviews_data)} customer reviews.")

    # 6. Seed Sample Appointments for Admin Preview
    if Appointment.query.count() == 0:
        sample_appointments = [
            {
                "customer_name": "Sameer Verma",
                "phone": "+91 98112 34567",
                "email": "sameer.v@example.com",
                "gender": "Men",
                "service_name": "Executive Fade & Texture Styling",
                "appointment_date": "2026-08-26",
                "appointment_time": "11:30 AM",
                "message": "Prefer stylist with experience in textured fades.",
                "status": "Pending"
            },
            {
                "customer_name": "Ritika Joshi",
                "phone": "+91 98223 45678",
                "email": "ritika.j@example.com",
                "gender": "Women",
                "service_name": "Artisan Balayage / Babylights",
                "appointment_date": "2026-08-26",
                "appointment_time": "02:00 PM",
                "message": "Want subtle honey blonde highlights.",
                "status": "Confirmed",
                "admin_notes": "Confirmed via phone call. Assigned senior colorist."
            },
            {
                "customer_name": "Karan Singhal",
                "phone": "+91 98334 56789",
                "email": "karan.s@example.com",
                "gender": "Men",
                "service_name": "Gentleman's Signature Grooming Package",
                "appointment_date": "2026-08-25",
                "appointment_time": "04:30 PM",
                "message": "Pre-wedding grooming session.",
                "status": "Completed",
                "admin_notes": "Completed smoothly. Client was very satisfied."
            }
        ]
        for item in sample_appointments:
            app = Appointment(**item)
            db.session.add(app)
        print(f"[*] Seeded {len(sample_appointments)} sample appointments.")

    # 7. Seed Sample Contact Enquiry
    if ContactEnquiry.query.count() == 0:
        sample_enquiry = ContactEnquiry(
            name="Neha Deshmukh",
            phone="+91 98445 67890",
            email="neha.d@example.com",
            subject="Bridal Party Booking Query",
            message="Hi, we have 4 family members looking for hair styling and makeup on September 12th morning. Do you have slots available for group bookings?",
            is_read=False
        )
        db.session.add(sample_enquiry)
        print("[*] Seeded sample contact enquiry.")

    db.session.commit()
    print("[OK] Database seeding completed successfully.")
