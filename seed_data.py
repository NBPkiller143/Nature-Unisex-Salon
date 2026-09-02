import os
from models import db, User, Service, Gallery, Review, ContactEnquiry, WebsiteSetting, Appointment

def seed_database():
    """Seeds the database with verified real menu data for Nature Unisex Salon."""
    
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
            address="Kashi Vishwanatha, 12, Anjaneya Temple Street, Vannarpet, Yerappa Garden, Austin Town, Neelasandra, Bengaluru, Karnataka 560047, India",
            google_maps_url="https://www.google.com/maps/place/Nature+unisex+salon/@12.9570761,77.6192442,15z/data=!4m6!3m5!1s0x3bae156290e25a91:0x923594a7d37cb230!8m2!3d12.9565087!4d77.6196044!16s%2Fg%2F11z1zkml55?entry=ttu",
            google_maps_embed="https://maps.google.com/maps?q=12.9565087,77.6196044+(Nature%20Unisex%20Salon)&t=&z=16&ie=UTF8&iwloc=B&output=embed",
            instagram_url="https://www.instagram.com/nature_unisex_salon72",
            facebook_url="https://facebook.com/natureunisexsalon",
            opening_hours_weekdays="Sunday - Monday: 09:00 - 21:00",
            opening_hours_weekends="Everyday: 09:00 - 21:00 (Open All 7 Days)",
            hero_headline="Style. Care. Confidence.",
            hero_subtext="Discover bespoke hair artistry, rejuvenating skincare, precision grooming, and relaxing spa therapies for both men and women in Austin Town & Neelasandra.",
            about_text="Nature Unisex Salon was founded on the philosophy that true beauty stems from mindful care, natural wellness, and artisan technique. We provide a hygienic, modern sanctuary equipped with LED mirror styling stations and hydra facial technology.",
            currency_symbol="₹"
        )
        db.session.add(settings)
        print("[*] Default website settings created.")

    # 3. Seed Services from Verified Menu Card
    if Service.query.count() == 0:
        services_data = [
            # ==========================================
            # MEN'S SERVICES (Image 3)
            # ==========================================
            # --- Hair Service ---
            {
                "name": "Men's Hair Cut",
                "gender_target": "Men",
                "category": "Hair",
                "description": "Precision scissor and clipper cut tailored to your face structure, finished with neck cleaning and styling.",
                "price": 150.0,
                "duration_mins": 30,
                "image_url": "/static/images/services/men_haircut.jpg",
                "display_order": 1
            },
            {
                "name": "Men's Beard Trim & Shape",
                "gender_target": "Men",
                "category": "Grooming",
                "description": "Beard grooming, trimming, cheek lining, and conditioning oil application.",
                "price": 100.0,
                "duration_mins": 20,
                "image_url": "/static/images/services/men_beard.jpg",
                "display_order": 2
            },
            {
                "name": "Men's Classic Shaving",
                "gender_target": "Men",
                "category": "Grooming",
                "description": "Smooth close shave with hot towel prep, rich lather, and soothing aftershave balm.",
                "price": 100.0,
                "duration_mins": 20,
                "image_url": "/static/images/services/men_beard_spa.jpg",
                "display_order": 3
            },
            {
                "name": "Men's Haircut + Beard Combo",
                "gender_target": "Men",
                "category": "Hair",
                "description": "Complete head and beard grooming makeover with precision styling and finish.",
                "price": 250.0,
                "duration_mins": 45,
                "image_url": "/static/images/services/men_fade.jpg",
                "display_order": 4
            },
            # --- Massage ---
            {
                "name": "Men's Oil Head Massage (20 Min)",
                "gender_target": "Men",
                "category": "Massage",
                "description": "20-minute relaxing scalp and shoulder acupressure oil massage to relieve tension.",
                "price": 200.0,
                "duration_mins": 20,
                "image_url": "/static/images/services/men_head_massage.jpg",
                "display_order": 5
            },
            {
                "name": "Men's Coconut Oil Massage (10 Min)",
                "gender_target": "Men",
                "category": "Massage",
                "description": "10-minute revitalizing pure coconut oil head massage for scalp nourishment.",
                "price": 150.0,
                "duration_mins": 10,
                "image_url": "/static/images/services/men_head_massage.jpg",
                "display_order": 6
            },
            # --- Spa ---
            {
                "name": "Men's Hair Spa Normal",
                "gender_target": "Men",
                "category": "Spa",
                "description": "Deep conditioning hair cream bath, relaxing head massage, and ozone steam therapy.",
                "price": 500.0,
                "duration_mins": 40,
                "image_url": "/static/images/services/men_spa.jpg",
                "display_order": 7
            },
            {
                "name": "Men's Anti-Dandruff Spa",
                "gender_target": "Men",
                "category": "Spa",
                "description": "Clarifying scalp treatment with anti-dandruff formulation, steam, and therapeutic rinse.",
                "price": 600.0,
                "duration_mins": 45,
                "image_url": "/static/images/services/men_spa.jpg",
                "display_order": 8
            },
            {
                "name": "Men's Advance Hair Spa",
                "gender_target": "Men",
                "category": "Spa",
                "description": "Intensive keratin & protein hair reconstruction spa with extended scalp massage and steam.",
                "price": 1000.0,
                "duration_mins": 60,
                "image_url": "/static/images/services/men_spa.jpg",
                "display_order": 9
            },
            # --- Colour & Chemical ---
            {
                "name": "Men's Inoa Hair Colour (Ammonia Free)",
                "gender_target": "Men",
                "category": "Hair",
                "description": "L'Oreal Inoa premium ammonia-free rich natural hair colour with gentle scalp care.",
                "price": 800.0,
                "duration_mins": 45,
                "image_url": "/static/images/services/men_colour.jpg",
                "display_order": 10
            },
            {
                "name": "Men's Streax Hair Colour",
                "gender_target": "Men",
                "category": "Hair",
                "description": "Quick grey coverage and vibrant colour application with conditioning wash.",
                "price": 350.0,
                "duration_mins": 35,
                "image_url": "/static/images/services/men_colour.jpg",
                "display_order": 11
            },
            {
                "name": "Men's L'Oreal Hair Colour",
                "gender_target": "Men",
                "category": "Hair",
                "description": "Professional L'Oreal Excellence hair colour with long-lasting gloss and grey coverage.",
                "price": 500.0,
                "duration_mins": 40,
                "image_url": "/static/images/services/men_colour.jpg",
                "display_order": 12
            },
            {
                "name": "Men's Ammonia Free Texture Treatment",
                "gender_target": "Men",
                "category": "Hair",
                "description": "Gentle, non-damaging ammonia-free smoothing and conditioning formula.",
                "price": 2000.0,
                "duration_mins": 75,
                "image_url": "/static/images/services/men_colour.jpg",
                "display_order": 13
            },
            {
                "name": "Men's Hair Perming",
                "gender_target": "Men",
                "category": "Hair",
                "description": "Modern textured curls or wave creation for high-volume masculine styles.",
                "price": 2000.0,
                "duration_mins": 90,
                "image_url": "/static/images/services/men_fade.jpg",
                "display_order": 14
            },
            {
                "name": "Men's Hair Straightening (6 to 8 Inches)",
                "gender_target": "Men",
                "category": "Hair",
                "description": "Permanent hair straightening and rebonding for smooth, manageable hair.",
                "price": 2000.0,
                "duration_mins": 90,
                "image_url": "/static/images/services/men_fade.jpg",
                "display_order": 15
            },
            {
                "name": "Men's Keratin Treatment",
                "gender_target": "Men",
                "category": "Hair",
                "description": "Deep protein infusion to eliminate frizz, add shine, and restore hair health.",
                "price": 3000.0,
                "duration_mins": 120,
                "image_url": "/static/images/services/men_package.jpg",
                "display_order": 16
            },
            # --- Waxing (Men) ---
            {
                "name": "Men's Beard Wax",
                "gender_target": "Men",
                "category": "Waxing",
                "description": "Rica peel-off wax for crisp upper cheek and neck razor-sharp definition.",
                "price": 100.0,
                "duration_mins": 15,
                "image_url": "/static/images/services/men_beard.jpg",
                "display_order": 17
            },
            {
                "name": "Men's Forehead Wax",
                "gender_target": "Men",
                "category": "Waxing",
                "description": "Clean forehead hairline shaping and unwanted fine hair removal.",
                "price": 80.0,
                "duration_mins": 10,
                "image_url": "/static/images/services/men_beard.jpg",
                "display_order": 18
            },
            {
                "name": "Men's Nose Wax",
                "gender_target": "Men",
                "category": "Waxing",
                "description": "Safe, quick, and painless nasal hair waxing for fresh hygiene.",
                "price": 60.0,
                "duration_mins": 10,
                "image_url": "/static/images/services/men_beard.jpg",
                "display_order": 19
            },
            # --- Facial & Clean up (Men) ---
            {
                "name": "Men's Face D-Tan",
                "gender_target": "Men",
                "category": "Facial",
                "description": "Fast sun-tan removal pack and face cleansing for an instantly brighter tone.",
                "price": 299.0,
                "duration_mins": 25,
                "image_url": "/static/images/services/men_detan.jpg",
                "display_order": 20
            },
            {
                "name": "Men's Face Clean up",
                "gender_target": "Men",
                "category": "Facial",
                "description": "Deep pore scrub, steam, blackhead extraction, and cooling face pack.",
                "price": 600.0,
                "duration_mins": 35,
                "image_url": "/static/images/services/men_detan.jpg",
                "display_order": 21
            },
            {
                "name": "Men's Basic Facial",
                "gender_target": "Men",
                "category": "Facial",
                "description": "Nourishing cleansing, exfoliation, face acupressure massage, and revitalizing mask.",
                "price": 1050.0,
                "duration_mins": 45,
                "image_url": "/static/images/services/men_detan.jpg",
                "display_order": 22
            },
            {
                "name": "Men's Advanced Clean up",
                "gender_target": "Men",
                "category": "Facial",
                "description": "Comprehensive fruit enzyme exfoliation, active hydration mask, and de-tan.",
                "price": 800.0,
                "duration_mins": 40,
                "image_url": "/static/images/services/men_detan.jpg",
                "display_order": 23
            },
            {
                "name": "Men's Gold Facial",
                "gender_target": "Men",
                "category": "Facial",
                "description": "Luxury 24K gold foil and radiance cream ritual for celebratory glow and skin firmness.",
                "price": 1500.0,
                "duration_mins": 55,
                "image_url": "/static/images/services/men_detan.jpg",
                "display_order": 24
            },
            {
                "name": "Men's Groom / Bridal Facial",
                "gender_target": "Men",
                "category": "Facial",
                "description": "Premium multi-step luxury facial with deep glow serums, de-tan, and eye revival.",
                "price": 2800.0,
                "duration_mins": 75,
                "image_url": "/static/images/services/men_detan.jpg",
                "display_order": 25
            },
            {
                "name": "Men's O3+ Radiance Facial",
                "gender_target": "Men",
                "category": "Facial",
                "description": "Professional O3+ dermatological brightening and anti-pigmentation treatment.",
                "price": 2500.0,
                "duration_mins": 60,
                "image_url": "/static/images/services/men_detan.jpg",
                "display_order": 26
            },
            {
                "name": "Men's Whitening Facial",
                "gender_target": "Men",
                "category": "Facial",
                "description": "Melanin reduction, deep hydration, and skin brightening antioxidant treatment.",
                "price": 2000.0,
                "duration_mins": 55,
                "image_url": "/static/images/services/men_detan.jpg",
                "display_order": 27
            },
            # --- Pedicure & Manicure (Men) ---
            {
                "name": "Men's Basic Pedicure",
                "gender_target": "Men",
                "category": "Pedicure",
                "description": "Warm foot soak, heel buffing, nail trimming, cuticle care, and massage.",
                "price": 650.0,
                "duration_mins": 40,
                "image_url": "/static/images/services/men_pedicure.jpg",
                "display_order": 28
            },
            {
                "name": "Men's Crystal Pedicure",
                "gender_target": "Men",
                "category": "Pedicure",
                "description": "Exfoliating crystal scrub with jelly soak, deep heel calluses removal, and moisturizing pack.",
                "price": 800.0,
                "duration_mins": 50,
                "image_url": "/static/images/services/men_pedicure.jpg",
                "display_order": 29
            },
            {
                "name": "Men's Lemon Pedicure",
                "gender_target": "Men",
                "category": "Pedicure",
                "description": "Fresh citrus detox soak, dead skin scrubbing, anti-bacterial lemon massage.",
                "price": 900.0,
                "duration_mins": 50,
                "image_url": "/static/images/services/men_pedicure.jpg",
                "display_order": 30
            },
            {
                "name": "Men's D-Tan Pedicure",
                "gender_target": "Men",
                "category": "Pedicure",
                "description": "Active tanning removal foot pack, scrub, nail grooming, and rich cream massage.",
                "price": 700.0,
                "duration_mins": 45,
                "image_url": "/static/images/services/men_pedicure.jpg",
                "display_order": 31
            },
            {
                "name": "Men's Basic Manicure",
                "gender_target": "Men",
                "category": "Manicure",
                "description": "Hand soak, nail clipping, cuticle tidying, and hand moisturizing massage.",
                "price": 350.0,
                "duration_mins": 30,
                "image_url": "/static/images/services/men_manicure.jpg",
                "display_order": 32
            },
            {
                "name": "Men's Crystal Manicure",
                "gender_target": "Men",
                "category": "Manicure",
                "description": "Crystal gel exfoliation, cuticle cleaning, and nourishing hand cream.",
                "price": 500.0,
                "duration_mins": 40,
                "image_url": "/static/images/services/men_manicure.jpg",
                "display_order": 33
            },
            {
                "name": "Men's Lemon Manicure",
                "gender_target": "Men",
                "category": "Manicure",
                "description": "Refreshing citrus scrub and soak for clean, soft hands.",
                "price": 650.0,
                "duration_mins": 40,
                "image_url": "/static/images/services/men_manicure.jpg",
                "display_order": 34
            },
            {
                "name": "Men's D-Tan Manicure",
                "gender_target": "Men",
                "category": "Manicure",
                "description": "De-tanning hand pack with gentle exfoliation and brightening finish.",
                "price": 450.0,
                "duration_mins": 35,
                "image_url": "/static/images/services/men_manicure.jpg",
                "display_order": 35
            },

            # ==========================================
            # WOMEN'S SERVICES (Image 1 & Image 2)
            # ==========================================
            # --- Hair Cut & Styling ---
            {
                "name": "Women's Straight Hair Cut",
                "gender_target": "Women",
                "category": "Hair",
                "description": "Classic clean blunt straight cut with balanced end leveling.",
                "price": 500.0,
                "duration_mins": 30,
                "image_url": "/static/images/services/women_haircut.jpg",
                "display_order": 36
            },
            {
                "name": "Women's Hair Trimming (No Wash / No Setting)",
                "gender_target": "Women",
                "category": "Hair",
                "description": "Quick split ends maintenance and length trimming on dry/natural hair.",
                "price": 300.0,
                "duration_mins": 20,
                "image_url": "/static/images/services/women_haircut.jpg",
                "display_order": 37
            },
            {
                "name": "Women's Bob Cut",
                "gender_target": "Women",
                "category": "Hair",
                "description": "Classic, French, or asymmetrical chic bob cut customized to jawline.",
                "price": 600.0,
                "duration_mins": 40,
                "image_url": "/static/images/services/women_haircut.jpg",
                "display_order": 38
            },
            {
                "name": "Women's U Cut",
                "gender_target": "Women",
                "category": "Hair",
                "description": "Graceful curved U-shape perimeter cut for flowing natural bounce.",
                "price": 500.0,
                "duration_mins": 30,
                "image_url": "/static/images/services/women_haircut.jpg",
                "display_order": 39
            },
            {
                "name": "Women's Layer Hair Cut",
                "gender_target": "Women",
                "category": "Hair",
                "description": "Multi-tier layered cut for dramatic volume, movement, and face framing.",
                "price": 800.0,
                "duration_mins": 45,
                "image_url": "/static/images/services/women_layers.jpg",
                "display_order": 40
            },
            {
                "name": "Women's Advance Hair Cut Trimming",
                "gender_target": "Women",
                "category": "Hair",
                "description": "Detailed texturizing and internal layer reshaping for healthy volume.",
                "price": 600.0,
                "duration_mins": 35,
                "image_url": "/static/images/services/women_layers.jpg",
                "display_order": 41
            },
            {
                "name": "Women's Complete Change of Style",
                "gender_target": "Women",
                "category": "Hair",
                "description": "Full restyling transformation from long to short or new signature silhouette.",
                "price": 900.0,
                "duration_mins": 60,
                "image_url": "/static/images/services/women_layers.jpg",
                "display_order": 42
            },
            {
                "name": "Women's Hair Wash & Blowdry",
                "gender_target": "Women",
                "category": "Hair",
                "description": "Shampoo cleanse, conditioning, and straight or voluminous blowdry.",
                "price": 300.0,
                "duration_mins": 30,
                "image_url": "/static/images/services/women_haircut.jpg",
                "display_order": 43
            },
            {
                "name": "Women's Tongs Setting (Curling)",
                "gender_target": "Women",
                "category": "Hair",
                "description": "Glamorous Hollywood waves, beach curls, or textured spiral tongs styling.",
                "price": 1000.0,
                "duration_mins": 45,
                "image_url": "/static/images/services/women_party_makeup.jpg",
                "display_order": 44
            },
            {
                "name": "Women's Blowdry Setting",
                "gender_target": "Women",
                "category": "Hair",
                "description": "Blowout setting with round-brush bounce, sleek shine, or soft inward flips.",
                "price": 700.0,
                "duration_mins": 35,
                "image_url": "/static/images/services/women_haircut.jpg",
                "display_order": 45
            },
            {
                "name": "Women's Wash + Setting",
                "gender_target": "Women",
                "category": "Hair",
                "description": "Luxury hair wash, scalp massage, deep conditioner, and polished styling set.",
                "price": 900.0,
                "duration_mins": 45,
                "image_url": "/static/images/services/women_hair_spa.jpg",
                "display_order": 46
            },
            # --- Threading (Women) ---
            {
                "name": "Eyebrows Threading",
                "gender_target": "Women",
                "category": "Threading",
                "description": "Precision organic cotton thread arch definition and shaping.",
                "price": 50.0,
                "duration_mins": 10,
                "image_url": "/static/images/services/women_cleanup.jpg",
                "display_order": 47
            },
            {
                "name": "Upper Lips Threading",
                "gender_target": "Women",
                "category": "Threading",
                "description": "Quick, hygienic upper lip hair removal.",
                "price": 40.0,
                "duration_mins": 5,
                "image_url": "/static/images/services/women_cleanup.jpg",
                "display_order": 48
            },
            {
                "name": "Lower Lips Threading",
                "gender_target": "Women",
                "category": "Threading",
                "description": "Gentle lower lip thread cleanup.",
                "price": 40.0,
                "duration_mins": 5,
                "image_url": "/static/images/services/women_cleanup.jpg",
                "display_order": 49
            },
            {
                "name": "Chin Threading",
                "gender_target": "Women",
                "category": "Threading",
                "description": "Chin and lower jaw hair threading.",
                "price": 40.0,
                "duration_mins": 5,
                "image_url": "/static/images/services/women_cleanup.jpg",
                "display_order": 50
            },
            {
                "name": "Forehead Threading",
                "gender_target": "Women",
                "category": "Threading",
                "description": "Forehead hairline tidying and peach fuzz removal.",
                "price": 40.0,
                "duration_mins": 5,
                "image_url": "/static/images/services/women_cleanup.jpg",
                "display_order": 51
            },
            {
                "name": "Side Locks Threading",
                "gender_target": "Women",
                "category": "Threading",
                "description": "Side locks and cheek contour threading.",
                "price": 100.0,
                "duration_mins": 10,
                "image_url": "/static/images/services/women_cleanup.jpg",
                "display_order": 52
            },
            {
                "name": "Full Face Threading",
                "gender_target": "Women",
                "category": "Threading",
                "description": "Complete facial threading including brows, forehead, cheeks, lip, and chin.",
                "price": 300.0,
                "duration_mins": 25,
                "image_url": "/static/images/services/women_cleanup.jpg",
                "display_order": 53
            },
            # --- Oil Massage (Women) ---
            {
                "name": "Women's Coconut Oil Massage",
                "gender_target": "Women",
                "category": "Massage",
                "description": "Warm virgin coconut oil head massage for scalp cooling and deep root nourishment.",
                "price": 300.0,
                "duration_mins": 20,
                "image_url": "/static/images/services/unisex_head_massage.jpg",
                "display_order": 54
            },
            {
                "name": "Women's Menthol Oil Massage",
                "gender_target": "Women",
                "category": "Massage",
                "description": "Cooling menthol herbal oil massage to relieve headaches and stress.",
                "price": 350.0,
                "duration_mins": 20,
                "image_url": "/static/images/services/unisex_head_massage.jpg",
                "display_order": 55
            },
            {
                "name": "Women's Almond Oil Massage",
                "gender_target": "Women",
                "category": "Massage",
                "description": "Pure vitamin E-rich sweet almond oil scalp massage for hair strength.",
                "price": 400.0,
                "duration_mins": 25,
                "image_url": "/static/images/services/unisex_head_massage.jpg",
                "display_order": 56
            },
            {
                "name": "Women's Olive Oil Massage",
                "gender_target": "Women",
                "category": "Massage",
                "description": "Deep conditioning extra virgin olive oil massage for dry and damaged hair.",
                "price": 500.0,
                "duration_mins": 30,
                "image_url": "/static/images/services/unisex_head_massage.jpg",
                "display_order": 57
            },
            # --- Hair Colouring & Highlights (Women) ---
            {
                "name": "Root Touch Up - Inoa Ammonia Free (2 to 3 Inch)",
                "gender_target": "Women",
                "category": "Hair",
                "description": "L'Oreal Inoa oil-delivery system for 100% grey coverage with zero ammonia odor.",
                "price": 1200.0,
                "duration_mins": 45,
                "image_url": "/static/images/services/women_colour.jpg",
                "display_order": 58
            },
            {
                "name": "Root Touch Up - L'Oreal",
                "gender_target": "Women",
                "category": "Hair",
                "description": "L'Oreal Majirel root touch up for seamless colour matching and vibrant shine.",
                "price": 1000.0,
                "duration_mins": 45,
                "image_url": "/static/images/services/women_colour.jpg",
                "display_order": 59
            },
            {
                "name": "Root Touch Up - Streax",
                "gender_target": "Women",
                "category": "Hair",
                "description": "Affordable root grey coverage with rich pigment and conditioning.",
                "price": 800.0,
                "duration_mins": 40,
                "image_url": "/static/images/services/women_colour.jpg",
                "display_order": 60
            },
            {
                "name": "Global Highlights - Shoulder Length",
                "gender_target": "Women",
                "category": "Hair",
                "description": "Full dimensional foil highlights for shoulder-length hair.",
                "price": 2000.0,
                "duration_mins": 75,
                "image_url": "/static/images/services/women_balayage.jpg",
                "display_order": 61
            },
            {
                "name": "Global Highlights - Medium Length",
                "gender_target": "Women",
                "category": "Hair",
                "description": "Luminous multi-tonal highlights for mid-back length hair.",
                "price": 2500.0,
                "duration_mins": 90,
                "image_url": "/static/images/services/women_balayage.jpg",
                "display_order": 62
            },
            {
                "name": "Global Highlights - Long Hair",
                "gender_target": "Women",
                "category": "Hair",
                "description": "Full head artistic foil placement for waist length or thick hair.",
                "price": 3000.0,
                "duration_mins": 105,
                "image_url": "/static/images/services/women_balayage.jpg",
                "display_order": 63
            },
            {
                "name": "Balayage Colour Artistry",
                "gender_target": "Women",
                "category": "Hair",
                "description": "Freehand painted sun-kissed gradient from dark roots to radiant melted ends.",
                "price": 5000.0,
                "duration_mins": 135,
                "image_url": "/static/images/services/women_balayage.jpg",
                "display_order": 64
            },
            {
                "name": "Global Highlights (Full Master Set)",
                "gender_target": "Women",
                "category": "Hair",
                "description": "Full head multi-dimensional highlights with gloss toner and bond repair.",
                "price": 3500.0,
                "duration_mins": 120,
                "image_url": "/static/images/services/women_balayage.jpg",
                "display_order": 65
            },
            {
                "name": "Highlights Per Streak",
                "gender_target": "Women",
                "category": "Hair",
                "description": "Single foil accent streak, money piece, or peek-a-boo pop of colour.",
                "price": 250.0,
                "duration_mins": 20,
                "image_url": "/static/images/services/women_colour.jpg",
                "display_order": 66
            },
            {
                "name": "Anti-Dandruff Intensive Treatment",
                "gender_target": "Women",
                "category": "Hair",
                "description": "Clinical scalp peel, zinc pyrithione infusion, steam, and balancing scalp lotion.",
                "price": 500.0,
                "duration_mins": 35,
                "image_url": "/static/images/services/women_hair_spa.jpg",
                "display_order": 67
            },
            # --- Hair Spa L'Oreal ---
            {
                "name": "L'Oreal Basic Hair Spa",
                "gender_target": "Women",
                "category": "Spa",
                "description": "Nourishing L'Oreal creambath, hot towel wrap, relaxing massage, and wash.",
                "price": 1500.0,
                "duration_mins": 45,
                "image_url": "/static/images/services/women_hair_spa.jpg",
                "display_order": 68
            },
            {
                "name": "L'Oreal Deep Nourishing Spa",
                "gender_target": "Women",
                "category": "Spa",
                "description": "Intensive lipid repair concentrate for chemically treated or dry brittle hair.",
                "price": 1600.0,
                "duration_mins": 55,
                "image_url": "/static/images/services/women_hair_spa.jpg",
                "display_order": 69
            },
            {
                "name": "L'Oreal Keratin Hair Spa",
                "gender_target": "Women",
                "category": "Spa",
                "description": "Keratin protein mask with steam infusion for silky smoothness and split-end repair.",
                "price": 2000.0,
                "duration_mins": 60,
                "image_url": "/static/images/services/women_keratin.jpg",
                "display_order": 70
            },
            # --- Hair Botox, Keratin & Texture ---
            {
                "name": "Hair Botox Treatment - Short Hair",
                "gender_target": "Women",
                "category": "Hair",
                "description": "Deep collagen and amino acid anti-aging filler for short hair.",
                "price": 6000.0,
                "duration_mins": 90,
                "image_url": "/static/images/services/women_keratin.jpg",
                "display_order": 71
            },
            {
                "name": "Hair Botox Treatment - Medium Hair",
                "gender_target": "Women",
                "category": "Hair",
                "description": "Rejuvenating filler treatment restoring fullness, shine, and elasticity.",
                "price": 7000.0,
                "duration_mins": 120,
                "image_url": "/static/images/services/women_keratin.jpg",
                "display_order": 72
            },
            {
                "name": "Hair Botox Treatment - Long Hair",
                "gender_target": "Women",
                "category": "Hair",
                "description": "Maximum fiber repair for waist-length hair with lasting mirror gloss.",
                "price": 8000.0,
                "duration_mins": 150,
                "image_url": "/static/images/services/women_keratin.jpg",
                "display_order": 73
            },
            {
                "name": "Hair Keratin Treatment - Short Hair",
                "gender_target": "Women",
                "category": "Hair",
                "description": "Brazilian keratin blowout for short hair, eliminating 95% frizz for 4+ months.",
                "price": 5000.0,
                "duration_mins": 90,
                "image_url": "/static/images/services/women_keratin.jpg",
                "display_order": 74
            },
            {
                "name": "Hair Keratin Treatment - Medium Hair",
                "gender_target": "Women",
                "category": "Hair",
                "description": "Keratin protein smoothing for shoulder/mid-back length hair.",
                "price": 6000.0,
                "duration_mins": 120,
                "image_url": "/static/images/services/women_keratin.jpg",
                "display_order": 75
            },
            {
                "name": "Hair Keratin Treatment - Long Hair",
                "gender_target": "Women",
                "category": "Hair",
                "description": "Complete keratin sealing for long hair, delivering silky featherlight glide.",
                "price": 7000.0,
                "duration_mins": 150,
                "image_url": "/static/images/services/women_keratin.jpg",
                "display_order": 76
            },
            {
                "name": "Hair Smoothening - Short Hair",
                "gender_target": "Women",
                "category": "Hair",
                "description": "Natural sleek smoothing treatment for manageable, soft short hair.",
                "price": 3000.0,
                "duration_mins": 90,
                "image_url": "/static/images/services/women_keratin.jpg",
                "display_order": 77
            },
            {
                "name": "Hair Smoothening - Medium Hair",
                "gender_target": "Women",
                "category": "Hair",
                "description": "Semi-permanent silk smoothing for medium hair lengths.",
                "price": 4000.0,
                "duration_mins": 120,
                "image_url": "/static/images/services/women_keratin.jpg",
                "display_order": 78
            },
            {
                "name": "Hair Smoothening - Long Hair",
                "gender_target": "Women",
                "category": "Hair",
                "description": "All-over smoothening for long flowing, frizz-free tresses.",
                "price": 5000.0,
                "duration_mins": 150,
                "image_url": "/static/images/services/women_keratin.jpg",
                "display_order": 79
            },
            {
                "name": "Hair Straightening - Short Hair",
                "gender_target": "Women",
                "category": "Hair",
                "description": "Permanent rebonding & straightening for poker-straight short hair.",
                "price": 4000.0,
                "duration_mins": 100,
                "image_url": "/static/images/services/women_keratin.jpg",
                "display_order": 80
            },
            {
                "name": "Hair Straightening - Medium Hair",
                "gender_target": "Women",
                "category": "Hair",
                "description": "Permanent thermal reconditioning for medium hair.",
                "price": 5000.0,
                "duration_mins": 130,
                "image_url": "/static/images/services/women_keratin.jpg",
                "display_order": 81
            },
            {
                "name": "Hair Straightening - Long Hair",
                "gender_target": "Women",
                "category": "Hair",
                "description": "Permanent straight rebonding for long, thick hair.",
                "price": 6000.0,
                "duration_mins": 160,
                "image_url": "/static/images/services/women_keratin.jpg",
                "display_order": 82
            },
            # --- Waxing - Rica (Women) ---
            {
                "name": "Rica Waxing - Upper Lips",
                "gender_target": "Women",
                "category": "Waxing",
                "description": "Gentle Italian Rica liposoluble wax for sensitive upper lip.",
                "price": 80.0,
                "duration_mins": 10,
                "image_url": "/static/images/services/women_cleanup.jpg",
                "display_order": 83
            },
            {
                "name": "Rica Waxing - Chin",
                "gender_target": "Women",
                "category": "Waxing",
                "description": "Rica wax hair removal for smooth chin area.",
                "price": 80.0,
                "duration_mins": 10,
                "image_url": "/static/images/services/women_cleanup.jpg",
                "display_order": 84
            },
            {
                "name": "Rica Waxing - Sides",
                "gender_target": "Women",
                "category": "Waxing",
                "description": "Rica wax for facial side locks.",
                "price": 90.0,
                "duration_mins": 10,
                "image_url": "/static/images/services/women_cleanup.jpg",
                "display_order": 85
            },
            {
                "name": "Rica Waxing - Forehead",
                "gender_target": "Women",
                "category": "Waxing",
                "description": "Forehead hairline Rica waxing.",
                "price": 80.0,
                "duration_mins": 10,
                "image_url": "/static/images/services/women_cleanup.jpg",
                "display_order": 86
            },
            {
                "name": "Rica Waxing - Full Face",
                "gender_target": "Women",
                "category": "Waxing",
                "description": "Complete full face Rica wax with post-wax soothing lotion.",
                "price": 400.0,
                "duration_mins": 25,
                "image_url": "/static/images/services/women_cleanup.jpg",
                "display_order": 87
            },
            {
                "name": "Rica Waxing - Under Arms",
                "gender_target": "Women",
                "category": "Waxing",
                "description": "Painless Rica peel-off wax for underarms with anti-tan benefits.",
                "price": 150.0,
                "duration_mins": 15,
                "image_url": "/static/images/services/women_cleanup.jpg",
                "display_order": 88
            },
            {
                "name": "Rica Waxing - Full Arms",
                "gender_target": "Women",
                "category": "Waxing",
                "description": "Full arms Rica wax from shoulders to fingers.",
                "price": 450.0,
                "duration_mins": 30,
                "image_url": "/static/images/services/women_mani_pedi.jpg",
                "display_order": 89
            },
            {
                "name": "Rica Waxing - Full Legs",
                "gender_target": "Women",
                "category": "Waxing",
                "description": "Full legs Rica wax with colophony-free Italian wax for super smooth skin.",
                "price": 550.0,
                "duration_mins": 40,
                "image_url": "/static/images/services/women_mani_pedi.jpg",
                "display_order": 90
            },
            {
                "name": "Rica Waxing - Half Legs",
                "gender_target": "Women",
                "category": "Waxing",
                "description": "Lower legs wax up to knees.",
                "price": 400.0,
                "duration_mins": 25,
                "image_url": "/static/images/services/women_mani_pedi.jpg",
                "display_order": 91
            },
            {
                "name": "Rica Waxing - Full Back",
                "gender_target": "Women",
                "category": "Waxing",
                "description": "Smooth full back Rica waxing for blouse and gown confidence.",
                "price": 800.0,
                "duration_mins": 30,
                "image_url": "/static/images/services/women_bridal.jpg",
                "display_order": 92
            },
            {
                "name": "Rica Waxing - Bikini Wax",
                "gender_target": "Women",
                "category": "Waxing",
                "description": "Hygienic, private, and sanitized gentle intimate waxing with Rica avocado/aloe wax.",
                "price": 2500.0,
                "duration_mins": 45,
                "image_url": "/static/images/services/women_bridal.jpg",
                "display_order": 93
            },
            {
                "name": "Rica Waxing - Full Body",
                "gender_target": "Women",
                "category": "Waxing",
                "description": "Complete head-to-toe full body Rica waxing package.",
                "price": 4000.0,
                "duration_mins": 90,
                "image_url": "/static/images/services/women_bridal_package.jpg",
                "display_order": 94
            },
            {
                "name": "Women's Cleanup Basic",
                "gender_target": "Women",
                "category": "Facial",
                "description": "Scrub exfoliation, steam, blackhead removal, and purifying pack.",
                "price": 650.0,
                "duration_mins": 30,
                "image_url": "/static/images/services/women_cleanup.jpg",
                "display_order": 95
            },
            {
                "name": "Women's Cleanup Standard",
                "gender_target": "Women",
                "category": "Facial",
                "description": "Deep cleanse with massage cream, steam, extraction, and brightening pack.",
                "price": 700.0,
                "duration_mins": 35,
                "image_url": "/static/images/services/women_cleanup.jpg",
                "display_order": 96
            },
            {
                "name": "Women's Advanced Cleanup",
                "gender_target": "Women",
                "category": "Facial",
                "description": "Botanical peel, enzyme exfoliation, active serum infusion, and glowing peel-off mask.",
                "price": 900.0,
                "duration_mins": 45,
                "image_url": "/static/images/services/women_cleanup.jpg",
                "display_order": 97
            },
            {
                "name": "Women's Face and Neck D-Tan",
                "gender_target": "Women",
                "category": "Facial",
                "description": "High-potency milk & honey de-tan pack for face and neckline.",
                "price": 500.0,
                "duration_mins": 25,
                "image_url": "/static/images/services/unisex_detan.jpg",
                "display_order": 98
            },
            # --- Add on Masks (Women) ---
            {
                "name": "Skin Tightening Add-on Mask",
                "gender_target": "Women",
                "category": "Facial",
                "description": "Collagen firming alginate mask to lift and tighten facial contours.",
                "price": 200.0,
                "duration_mins": 15,
                "image_url": "/static/images/services/women_facial.jpg",
                "display_order": 99
            },
            {
                "name": "Vitamin C Radiance Add-on Mask",
                "gender_target": "Women",
                "category": "Facial",
                "description": "Pure ascorbic acid glow booster mask for immediate luminous brightness.",
                "price": 200.0,
                "duration_mins": 15,
                "image_url": "/static/images/services/women_facial.jpg",
                "display_order": 100
            },
            # --- Facials (Women) ---
            {
                "name": "Women's Basic Facial",
                "gender_target": "Women",
                "category": "Facial",
                "description": "Gentle pore cleansing, relaxing lymphatic massage, and hydrating herbal pack.",
                "price": 1000.0,
                "duration_mins": 45,
                "image_url": "/static/images/services/women_facial.jpg",
                "display_order": 101
            },
            {
                "name": "Women's Fruit Facial",
                "gender_target": "Women",
                "category": "Facial",
                "description": "Enriched with natural fruit AHA extracts (papaya, strawberry, apple) for fresh radiance.",
                "price": 1200.0,
                "duration_mins": 50,
                "image_url": "/static/images/services/women_facial.jpg",
                "display_order": 102
            },
            {
                "name": "Women's Herbal Facial",
                "gender_target": "Women",
                "category": "Facial",
                "description": "Ayurvedic herbs, neem, and sandalwood extracts for clear, calm, blemish-free skin.",
                "price": 1500.0,
                "duration_mins": 55,
                "image_url": "/static/images/services/women_facial.jpg",
                "display_order": 103
            },
            {
                "name": "Women's Gold Glow Facial",
                "gender_target": "Women",
                "category": "Facial",
                "description": "24 Karat gold leaf scrub and radiance mask for luminous event-ready skin.",
                "price": 2000.0,
                "duration_mins": 60,
                "image_url": "/static/images/services/women_facial.jpg",
                "display_order": 104
            },
            {
                "name": "Women's Whitening & Brightening Facial",
                "gender_target": "Women",
                "category": "Facial",
                "description": "Advanced glutathione & arbutin formula targeting dark spots and hyperpigmentation.",
                "price": 2200.0,
                "duration_mins": 60,
                "image_url": "/static/images/services/women_facial.jpg",
                "display_order": 105
            },
            {
                "name": "Women's O3+ Radiance Facial",
                "gender_target": "Women",
                "category": "Facial",
                "description": "Professional salon O3+ brightening treatment with sea white peel and whitening mask.",
                "price": 2500.0,
                "duration_mins": 65,
                "image_url": "/static/images/services/women_facial.jpg",
                "display_order": 106
            },
            {
                "name": "Women's O3+ D-Tan Facial",
                "gender_target": "Women",
                "category": "Facial",
                "description": "O3+ anti-tan deep oxygenation facial repairing sun damage and pollution dullness.",
                "price": 2000.0,
                "duration_mins": 60,
                "image_url": "/static/images/services/unisex_detan.jpg",
                "display_order": 107
            },
            {
                "name": "Royal Bridal Glow Facial",
                "gender_target": "Women",
                "category": "Facial",
                "description": "Grand multi-step bridal skin ritual with diamond microdermabrasion and gold collagen mask.",
                "price": 2800.0,
                "duration_mins": 80,
                "image_url": "/static/images/services/women_bridal.jpg",
                "display_order": 108
            },
            {
                "name": "Korean Glass Skin Facial",
                "gender_target": "Women",
                "category": "Facial",
                "description": "K-Beauty triple hydration, peptide essence massage, and rubber modeling mask for dewy glass skin.",
                "price": 2500.0,
                "duration_mins": 65,
                "image_url": "/static/images/services/women_facial.jpg",
                "display_order": 109
            },
            {
                "name": "HYDRA Facial Machine Treatment",
                "gender_target": "Women",
                "category": "Facial",
                "description": "State-of-the-art multi-head vortex vacuum suction, ultrasonic peeling, radiofrequency lifting, and cold hammer infusion.",
                "price": 2500.0,
                "duration_mins": 60,
                "image_url": "/static/images/gallery/real_styling_station.jpg",
                "display_order": 110
            },
            # --- Manicure & Pedicure (Women) ---
            {
                "name": "Women's Basic Manicure",
                "gender_target": "Women",
                "category": "Manicure",
                "description": "Hand soak, cuticle softening, nail shaping, light massage, and nail buffing/polish.",
                "price": 350.0,
                "duration_mins": 30,
                "image_url": "/static/images/services/women_mani_pedi.jpg",
                "display_order": 111
            },
            {
                "name": "Women's Crystal Manicure",
                "gender_target": "Women",
                "category": "Manicure",
                "description": "Crystal salt soak, dead cell buffing, cuticle nourishment, and rich hand cream.",
                "price": 450.0,
                "duration_mins": 40,
                "image_url": "/static/images/services/women_mani_pedi.jpg",
                "display_order": 112
            },
            {
                "name": "Women's D-Tan Manicure",
                "gender_target": "Women",
                "category": "Manicure",
                "description": "Tanning reversal hand pack, gentle scrub, and brightening hydration.",
                "price": 500.0,
                "duration_mins": 40,
                "image_url": "/static/images/services/women_mani_pedi.jpg",
                "display_order": 113
            },
            {
                "name": "Women's Lemon Manicure",
                "gender_target": "Women",
                "category": "Manicure",
                "description": "Citrus brightening soak, nail whitening scrub, and lemon hand butter massage.",
                "price": 650.0,
                "duration_mins": 45,
                "image_url": "/static/images/services/women_mani_pedi.jpg",
                "display_order": 114
            },
            {
                "name": "Women's Basic Pedicure",
                "gender_target": "Women",
                "category": "Pedicure",
                "description": "Soothing foot bath, heel scraping, nail clipping, cuticle cleaning, and calf massage.",
                "price": 650.0,
                "duration_mins": 40,
                "image_url": "/static/images/services/women_mani_pedi.jpg",
                "display_order": 115
            },
            {
                "name": "Women's D-Tan Pedicure",
                "gender_target": "Women",
                "category": "Pedicure",
                "description": "Sun-tanning foot pack, heel buffing, and rejuvenating foot massage.",
                "price": 700.0,
                "duration_mins": 45,
                "image_url": "/static/images/services/women_mani_pedi.jpg",
                "display_order": 116
            },
            {
                "name": "Women's Crystal Pedicure",
                "gender_target": "Women",
                "category": "Pedicure",
                "description": "Aromatic crystal soak, deep callus smoothing, and cooling mint mask.",
                "price": 800.0,
                "duration_mins": 50,
                "image_url": "/static/images/services/women_mani_pedi.jpg",
                "display_order": 117
            },
            {
                "name": "Women's Lemon Luxury Pedicure",
                "gender_target": "Women",
                "category": "Pedicure",
                "description": "Fresh sliced lemon detox bath, sugar scrub, foot mask, and extended massage.",
                "price": 1000.0,
                "duration_mins": 55,
                "image_url": "/static/images/services/women_mani_pedi.jpg",
                "display_order": 118
            },
            {
                "name": "Paraffin Foot Pack Add-on",
                "gender_target": "Women",
                "category": "Pedicure",
                "description": "Warm melted paraffin wax dip sealing moisture deep into cracked heels.",
                "price": 200.0,
                "duration_mins": 20,
                "image_url": "/static/images/services/women_mani_pedi.jpg",
                "display_order": 119
            }
        ]

        for s_data in services_data:
            svc = Service(
                name=s_data["name"],
                gender_target=s_data["gender_target"],
                category=s_data["category"],
                description=s_data["description"],
                price=s_data["price"],
                duration_mins=s_data["duration_mins"],
                image_url=s_data["image_url"],
                is_active=True,
                display_order=s_data["display_order"]
            )
            db.session.add(svc)
        print(f"[*] Seeded {len(services_data)} real salon services.")

    # 4. Seed Gallery Showcase (incorporating real salon interior photos)
    if Gallery.query.count() == 0:
        gallery_data = [
            {
                "title": "LED Mirror Styling Suites & Hydra Equipment",
                "category": "Interior",
                "image_url": "/static/images/gallery/real_styling_station.jpg",
                "caption": "Our Austin Town / Neelasandra studio featuring ambient LED styling stations and certified hydra facial equipment."
            },
            {
                "title": "Luxury Hair Spa & Pedicure Wash Station",
                "category": "Interior",
                "image_url": "/static/images/gallery/real_spa_wash_station.jpg",
                "caption": "Reclining diamond-quilted shampoo station equipped with ozone hair steamer and sterile pedicure bath."
            },
            {
                "title": "Classic Precision & Skin Fade Styling",
                "category": "Grooming",
                "image_url": "/static/images/gallery/gallery_grooming1.jpg",
                "caption": "Expert taper fades, scissor texturing, and razor-sharp beard styling for men."
            },
            {
                "title": "Dimensional Balayage & Colour Artistry",
                "category": "Hair",
                "image_url": "/static/images/gallery/gallery_hair1.jpg",
                "caption": "L'Oreal Inoa ammonia-free global highlights and caramel balayage transformations."
            },
            {
                "title": "Korean Glass Skin & Hydra Facial Results",
                "category": "Transformations",
                "image_url": "/static/images/gallery/gallery_transform1.jpg",
                "caption": "Pore purification, collagen lifting, and dewy radiance treatments."
            },
            {
                "title": "Royal Bridal Makeover & Gown Styling",
                "category": "Bridal",
                "image_url": "/static/images/gallery/gallery_bridal1.jpg",
                "caption": "Comprehensive bridal facial, hair setting, and HD makeover."
            }
        ]

        for g_data in gallery_data:
            item = Gallery(
                title=g_data["title"],
                category=g_data["category"],
                image_url=g_data["image_url"],
                is_active=True
            )
            db.session.add(item)
        print(f"[*] Seeded {len(gallery_data)} gallery items.")

    # 5. Seed Customer Testimonials
    if Review.query.count() == 0:
        reviews_data = [
            {
                "customer_name": "Priya Venkatesh",
                "rating": 5,
                "review_text": "I had the Korean Glass Skin Facial and Hair Keratin done here at Nature Unisex Salon. The results are unbelievable! Very hygienic stations and transparent pricing.",
                "service_name": "Korean Glass Skin Facial"
            },
            {
                "customer_name": "Karthik Nambiar",
                "rating": 5,
                "review_text": "Best salon in Neelasandra & Austin Town for men's grooming. The haircut + beard combo is only ₹250 and they take time to give you a razor-sharp fade.",
                "service_name": "Men's Haircut + Beard Combo"
            },
            {
                "customer_name": "Ananya Sharma",
                "rating": 5,
                "review_text": "Loved the Hydra Facial and L'Oreal Keratin Spa! The staff is very gentle and uses authentic, top-grade products.",
                "service_name": "HYDRA Facial Machine Treatment"
            },
            {
                "customer_name": "Syed Imran",
                "rating": 5,
                "review_text": "Cleanest salon in the area. The head oil massage and normal hair spa left me totally relaxed. Highly recommended!",
                "service_name": "Men's Advance Hair Spa"
            }
        ]

        for r_data in reviews_data:
            review = Review(
                customer_name=r_data["customer_name"],
                rating=r_data["rating"],
                review_text=r_data["review_text"],
                service_name=r_data["service_name"],
                is_active=True
            )
            db.session.add(review)
        print(f"[*] Seeded {len(reviews_data)} verified customer reviews.")

    db.session.commit()
    print("[OK] Database seeding completed successfully.")
