import shutil
from pathlib import Path

def setup_images():
    base_dir = Path(__file__).resolve().parent
    static_images = base_dir / 'static' / 'images'
    services_dir = static_images / 'services'
    gallery_dir = static_images / 'gallery'
    uploads_dir = base_dir / 'static' / 'uploads'
    
    services_dir.mkdir(parents=True, exist_ok=True)
    gallery_dir.mkdir(parents=True, exist_ok=True)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    
    # Brain artifacts directory with generated images
    brain_dir = Path(r"C:\Users\namee\.gemini\antigravity-ide\brain\0d6917c3-6b14-4e21-837b-c6687b012c24")
    
    hero_gen = list(brain_dir.glob("hero_salon_*.jpg"))
    about_gen = list(brain_dir.glob("about_salon_*.jpg"))
    groom_gen = list(brain_dir.glob("mens_grooming_*.jpg"))
    
    hero_src = hero_gen[0] if hero_gen else None
    about_src = about_gen[0] if about_gen else None
    groom_src = groom_gen[0] if groom_gen else None
    
    if hero_src and hero_src.exists():
        shutil.copy(hero_src, static_images / 'hero_salon.jpg')
        shutil.copy(hero_src, gallery_dir / 'gallery_interior1.jpg')
        shutil.copy(hero_src, gallery_dir / 'gallery_interior2.jpg')
        print("Copied hero image.")
        
    if about_src and about_src.exists():
        shutil.copy(about_src, static_images / 'about_salon.jpg')
        shutil.copy(about_src, gallery_dir / 'gallery_hair1.jpg')
        shutil.copy(about_src, gallery_dir / 'gallery_makeup1.jpg')
        shutil.copy(about_src, gallery_dir / 'gallery_transform1.jpg')
        shutil.copy(about_src, services_dir / 'women_haircut.jpg')
        shutil.copy(about_src, services_dir / 'women_layers.jpg')
        shutil.copy(about_src, services_dir / 'women_colour.jpg')
        shutil.copy(about_src, services_dir / 'women_balayage.jpg')
        shutil.copy(about_src, services_dir / 'women_hair_spa.jpg')
        shutil.copy(about_src, services_dir / 'women_keratin.jpg')
        shutil.copy(about_src, services_dir / 'women_facial.jpg')
        shutil.copy(about_src, services_dir / 'women_cleanup.jpg')
        shutil.copy(about_src, services_dir / 'women_mani_pedi.jpg')
        shutil.copy(about_src, services_dir / 'women_party_makeup.jpg')
        shutil.copy(about_src, services_dir / 'women_bridal.jpg')
        shutil.copy(about_src, services_dir / 'women_bridal_package.jpg')
        shutil.copy(about_src, services_dir / 'unisex_head_massage.jpg')
        shutil.copy(about_src, services_dir / 'unisex_detan.jpg')
        print("Copied women and unisex service images.")
        
    if groom_src and groom_src.exists():
        shutil.copy(groom_src, gallery_dir / 'gallery_grooming1.jpg')
        shutil.copy(groom_src, gallery_dir / 'gallery_hair2.jpg')
        shutil.copy(groom_src, gallery_dir / 'gallery_bridal1.jpg')
        shutil.copy(groom_src, services_dir / 'men_haircut.jpg')
        shutil.copy(groom_src, services_dir / 'men_fade.jpg')
        shutil.copy(groom_src, services_dir / 'men_beard.jpg')
        shutil.copy(groom_src, services_dir / 'men_beard_spa.jpg')
        shutil.copy(groom_src, services_dir / 'men_colour.jpg')
        shutil.copy(groom_src, services_dir / 'men_spa.jpg')
        shutil.copy(groom_src, services_dir / 'men_facial.jpg')
        shutil.copy(groom_src, services_dir / 'men_package.jpg')
        print("Copied men service and grooming images.")

if __name__ == '__main__':
    setup_images()
