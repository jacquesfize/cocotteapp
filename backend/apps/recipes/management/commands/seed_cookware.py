import hashlib
import io
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from PIL import Image, ImageOps

from apps.recipes.models import Cookware, ImageLicense

# Matériel de cuisine courant d'une cuisine domestique : appareils, cuisson, préparation.
# Nom français (convention de la bibliothèque, comme les ingrédients), nom anglais (utilisé par
# la recherche et pour rapprocher le `#matériel` d'une recette Cooklang écrite en anglais) et
# emoji, seulement quand Unicode en propose un qui représente l'objet lui-même.
COOKWARE = [
    # Appareils
    ("Four", "oven", ""),
    ("Four à micro-ondes", "microwave", ""),
    ("Friteuse à air", "air fryer", ""),
    ("Friteuse", "deep fryer", ""),
    ("Cuiseur vapeur", "steamer", ""),
    ("Autocuiseur", "pressure cooker", ""),
    ("Mijoteuse", "slow cooker", ""),
    ("Cuiseur à riz", "rice cooker", ""),
    ("Robot culinaire", "food processor", ""),
    ("Robot pâtissier", "stand mixer", ""),
    ("Batteur électrique", "hand mixer", ""),
    ("Blender", "blender", ""),
    ("Mixeur plongeant", "immersion blender", ""),
    ("Barbecue", "barbecue", ""),
    ("Plancha", "griddle", ""),
    ("Gaufrier", "waffle iron", ""),
    ("Appareil à raclette", "raclette grill", ""),
    ("Sorbetière", "ice cream maker", ""),
    ("Machine à pain", "bread machine", ""),
    # Cuisson
    ("Poêle", "frying pan", "🍳"),
    ("Sauteuse", "sauté pan", "🥘"),
    ("Wok", "wok", "🥘"),
    ("Casserole", "saucepan", "🍲"),
    ("Faitout", "stockpot", "🍲"),
    ("Cocotte", "dutch oven", "🍲"),
    ("Poêle à crêpes", "crepe pan", ""),
    ("Poêle-gril", "grill pan", ""),
    ("Plat à gratin", "baking dish", ""),
    ("Plaque de cuisson", "baking sheet", ""),
    ("Moule à gâteau", "cake pan", ""),
    ("Moule à tarte", "tart pan", ""),
    ("Moule à cake", "loaf pan", ""),
    ("Moule à muffins", "muffin tin", ""),
    ("Ramequin", "ramekin", ""),
    ("Papier cuisson", "parchment paper", ""),
    ("Papillote", "foil packet", ""),
    # Préparation
    ("Saladier", "mixing bowl", "🥣"),
    ("Fouet", "whisk", ""),
    ("Spatule", "spatula", ""),
    ("Cuillère en bois", "wooden spoon", "🥄"),
    ("Louche", "ladle", ""),
    ("Écumoire", "skimmer", ""),
    ("Pinceau de cuisine", "pastry brush", ""),
    ("Rouleau à pâtisserie", "rolling pin", ""),
    ("Planche à découper", "cutting board", ""),
    ("Couteau de chef", "chef's knife", "🔪"),
    ("Économe", "peeler", ""),
    ("Râpe", "grater", ""),
    ("Mandoline", "mandoline", ""),
    ("Presse-ail", "garlic press", ""),
    ("Mortier et pilon", "mortar and pestle", ""),
    ("Passoire", "colander", ""),
    ("Chinois", "fine-mesh sieve", ""),
    ("Tamis", "sifter", ""),
    ("Essoreuse à salade", "salad spinner", ""),
    ("Presse-agrumes", "citrus juicer", ""),
    ("Moulin à légumes", "food mill", ""),
    ("Balance de cuisine", "kitchen scale", "⚖️"),
    ("Verre doseur", "measuring jug", ""),
    ("Thermomètre de cuisine", "kitchen thermometer", "🌡️"),
    ("Poche à douille", "piping bag", ""),
    ("Film alimentaire", "plastic wrap", ""),
]


@dataclass(frozen=True)
class Photo:
    """Photo d'un matériel sur Wikimedia Commons, téléchargée par le seed (rien n'est livré avec le
    code). Les photos sous CC BY / CC BY-SA nomment leur auteur, affiché avec la photo."""

    file: str  # nom du fichier sur Commons, sans le préfixe "File:"
    license: str = ImageLicense.PUBLIC_DOMAIN
    author: str = ""
    license_url: str = ""
    # "crop" : recadrée au centre ; "pad" : complétée de blanc (objets longs sur fond blanc).
    fit: str = "crop"
    # Zone à garder avant le cadrage carré, en fractions de l'image (gauche, haut, droite, bas),
    # quand l'objet n'occupe qu'une partie de la photo.
    crop_box: tuple[float, float, float, float] | None = None

    @property
    def source_url(self):
        return "https://commons.wikimedia.org/wiki/File:" + urllib.parse.quote(self.file.replace(" ", "_"))


# Choisies une à une : domaine public de préférence, sinon CC BY / CC BY-SA. Les matériels absents
# de cette table restent sans photo (rien de satisfaisant trouvé) ; un admin peut en ajouter une.
PHOTOS = {
    "Four": Photo("Panasonic ELECTRIC OVEN NB-H3800.jpg", license=ImageLicense.CC_BY_SA, author="Dinkun Chen", license_url="https://creativecommons.org/licenses/by-sa/4.0/", fit="pad", crop_box=(0.08, 0.14, 0.98, 0.97)),
    "Four à micro-ondes": Photo("Electrodomésticos de línea blanca 18.JPG", license=ImageLicense.CC_BY_SA, author="19Tarrestnom65", license_url="https://creativecommons.org/licenses/by-sa/4.0/"),
    "Friteuse à air": Photo("Airfryer.jpg", license=ImageLicense.CC_BY_SA, author="Djsgmnd", license_url="https://creativecommons.org/licenses/by-sa/4.0/"),
    "Friteuse": Photo("Freidora.jpg"),
    "Autocuiseur": Photo("Pressure cooker.jpg", license=ImageLicense.CC_BY_SA, author="Wikinaut", license_url="https://creativecommons.org/licenses/by-sa/3.0/"),
    "Mijoteuse": Photo("Crock pot parts.jpg", license=ImageLicense.CC_BY_SA, author="Kowloonese at en.wikipedia", license_url="https://creativecommons.org/licenses/by-sa/3.0/"),
    "Cuiseur à riz": Photo("Rice-cooker.jpg"),
    "Robot culinaire": Photo("American food processor.jpg"),
    "Robot pâtissier": Photo("Sunbeam Heritage Mixmaster Stand Mixer.jpg"),
    "Batteur électrique": Photo("Миксер ДОМОТЕК.jpg", license=ImageLicense.CC_BY_SA, author="Schekinov Alexey Victorovich", license_url="https://creativecommons.org/licenses/by-sa/4.0/", fit="pad"),
    "Blender": Photo("A table-top mixer-grinder or mixie.jpg", license=ImageLicense.CC_BY_SA, author="Vimkay", license_url="https://creativecommons.org/licenses/by-sa/4.0/"),
    "Mixeur plongeant": Photo("Immersion blender used to puree applesauce.jpg"),
    "Barbecue": Photo("Charcoal BBQ.jpg", license=ImageLicense.CC_BY_SA, author="AlphaLemur", license_url="https://creativecommons.org/licenses/by-sa/4.0/"),
    "Plancha": Photo("Bratpan.jpg"),
    "Gaufrier": Photo("Waffle iron.JPG", license=ImageLicense.CC_BY_SA, author="Saopaulo1", license_url="https://creativecommons.org/licenses/by-sa/3.0/"),
    "Appareil à raclette": Photo("Raclette with all the trimmings.jpg"),
    "Sorbetière": Photo("Eismaschine.jpg"),
    "Machine à pain": Photo("Хлебопечка Замес теста - Bread machine Making dough.JPG"),
    "Poêle": Photo("Pfanne (Edelstahl).jpg"),
    "Sauteuse": Photo("Circulon-anodized-aluminum.jpg"),
    "Wok": Photo("Cooking with a wok on an outdoor stove 5.jpg"),
    "Casserole": Photo("Hahn 16cm Saucepan.jpg", license=ImageLicense.CC_BY, author="Cooks & Kitchens from Darlington, UK", license_url="https://creativecommons.org/licenses/by/2.0/", fit="pad"),
    "Faitout": Photo("Druware Dutch Oven.jpg", license=ImageLicense.CC_BY_SA, author="Kerri9494", license_url="https://creativecommons.org/licenses/by-sa/4.0/"),
    "Cocotte": Photo("Cocotte en fonte émaillée Le Creuset, d'un diamètre de vingt centimètres.JPG", license=ImageLicense.CC_BY_SA, author="Jérémy-Günther-Heinz Jähnick", license_url="https://creativecommons.org/licenses/by-sa/3.0/"),
    "Poêle à crêpes": Photo("Crêpière.JPG", license=ImageLicense.CC_BY_SA, author="BrightRaven", license_url="https://creativecommons.org/licenses/by-sa/3.0/", fit="pad"),
    "Plat à gratin": Photo("Veggie casserole.jpg"),
    "Plaque de cuisson": Photo("Runebergin torttuja muffinivuoissa.jpg"),
    "Moule à gâteau": Photo("Moule.jpg"),
    "Moule à tarte": Photo("Chloe Benko-Prieur 2016 (Unsplash).jpg"),
    "Moule à cake": Photo("Loaf pans.JPG"),
    "Moule à muffins": Photo("Cupcake-tin.jpg"),
    "Ramequin": Photo("Brown-ramekin.jpg"),
    "Papier cuisson": Photo("Leivinarkki.jpg"),
    "Saladier": Photo("Mixing bowl (51008449507).jpg"),
    "Fouet": Photo("Balloon spiral ball whisks.jpg", license=ImageLicense.CC_BY, author="Marie-Lan Nguyen", license_url="https://creativecommons.org/licenses/by/2.5/", fit="pad"),
    "Spatule": Photo("Degskrapor.png"),
    "Cuillère en bois": Photo("Wooden spoon(Leswana la setso).jpg"),
    "Louche": Photo("Ladle.jpg", fit="pad"),
    "Écumoire": Photo("Hålslev.JPG"),
    "Pinceau de cuisine": Photo("Kitchen-Silicone-Brush.jpg", fit="pad"),
    "Rouleau à pâtisserie": Photo("Rolling pin 2017.jpg"),
    "Planche à découper": Photo("Chopping Welsh onion (Allium fistulosum) on a wooden cutting board.jpg", license=ImageLicense.CC_BY_SA, author="Sarah5252", license_url="https://creativecommons.org/licenses/by-sa/4.0/"),
    "Couteau de chef": Photo("Eight inch Zwilling J.A. Henckels chef knife.JPG"),
    "Économe": Photo("Peeler 01 Pengo.jpg", license=ImageLicense.CC_BY_SA, author="Pengo", license_url="https://creativecommons.org/licenses/by-sa/3.0/"),
    "Râpe": Photo("6379Photos taken in Poblacion, Baliuag, Bulacan 01.jpg"),
    "Mandoline": Photo("Cooking Mandolin with Carrot.jpg", license=ImageLicense.CC_BY_SA, author="Alex Sims", license_url="https://creativecommons.org/licenses/by-sa/2.5/"),
    "Presse-ail": Photo("Klieste na cesnak.jpg", fit="pad"),
    "Mortier et pilon": Photo("White-Mortar-and-Pestle.jpg"),
    "Passoire": Photo("White Colander (53504734684).jpg"),
    "Chinois": Photo("Sil rostfri perforerad.JPG"),
    "Tamis": Photo("Сито механическое (кружка-сито) Sieve, Flour Sifter.JPG"),
    "Essoreuse à salade": Photo("Essoreuse à salade.jpg"),
    "Presse-agrumes": Photo("Lemon reamer.jpg"),
    "Moulin à légumes": Photo("Moulin Légume.jpg"),
    "Balance de cuisine": Photo("Kitchen scale 20101110.jpg"),
    "Verre doseur": Photo("Simple Measuring Cup.jpg"),
    "Thermomètre de cuisine": Photo("Pork thermometer.jpg"),
    "Poche à douille": Photo("Making Ravioli-002.jpg"),
    "Film alimentaire": Photo("Clingfilm.jpg"),
}

PHOTO_SIZE = 480
# Politique de Wikimedia : un User-Agent identifiable, et pas de rafale de requêtes.
USER_AGENT = "CocotteSeed/1.0 (seed_cookware; https://github.com/jacquesfize/cocotteapp)"
DOWNLOAD_DELAY_SECONDS = 1.0


def fetch_image(file_name: str) -> bytes:
    """Télécharge une version de 800 px de large du fichier Commons (réessaie si limité en débit)."""
    url = "https://commons.wikimedia.org/wiki/Special:FilePath/" + urllib.parse.quote(file_name) + "?width=800"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or attempt == 2:
                raise
            time.sleep(5 * (attempt + 1))
    raise RuntimeError("unreachable")


def square_jpeg(data: bytes, fit: str, crop_box=None) -> bytes:
    image = Image.open(io.BytesIO(data))
    image = ImageOps.exif_transpose(image).convert("RGB")
    if crop_box:
        left, top, right, bottom = crop_box
        image = image.crop((int(left * image.width), int(top * image.height), int(right * image.width), int(bottom * image.height)))
    size = (PHOTO_SIZE, PHOTO_SIZE)
    if fit == "pad":
        image = ImageOps.pad(image, size, Image.LANCZOS, color="white")
    else:
        image = ImageOps.fit(image, size, Image.LANCZOS)
    buffer = io.BytesIO()
    image.save(buffer, "JPEG", quality=82, optimize=True, progressive=True)
    return buffer.getvalue()


def attach_photo(cookware, photo: Photo):
    cookware.image_license = photo.license
    cookware.image_credit_author = photo.author
    cookware.image_credit_source_url = photo.source_url
    cookware.image_credit_license_url = photo.license_url
    content = square_jpeg(fetch_image(photo.file), photo.fit, photo.crop_box)
    # Empreinte du contenu dans le nom : une photo remplacée change d'URL, le navigateur ne
    # ressert donc pas l'ancienne depuis son cache.
    digest = hashlib.sha1(content).hexdigest()[:8]
    cookware.image.save(f"{slugify(cookware.name)}-{digest}.jpg", ContentFile(content), save=True)


def seed_cookware(with_images=True):
    """Crée le matériel manquant (rapproché par nom, sans tenir compte de la casse), complète la
    traduction anglaise, et ne renseigne emoji et photo que s'ils sont vides : ce qu'un admin a
    choisi n'est jamais écrasé, et le matériel ajouté par les utilisateurs n'est pas touché.

    Les photos sont téléchargées depuis Wikimedia Commons ; un échec (hors ligne, fichier
    supprimé...) laisse simplement le matériel sans photo. Renvoie (créés, photos, échecs)."""
    created, downloaded, failed = 0, 0, []
    for name, name_en, emoji in COOKWARE:
        cookware = Cookware.objects.filter(name__iexact=name).first()
        if cookware is None:
            cookware = Cookware.objects.create(name=name, translations={"en": name_en}, emoji=emoji)
            created += 1
        else:
            changed = []
            if cookware.translations.get("en") != name_en:
                cookware.translations = {**cookware.translations, "en": name_en}
                changed.append("translations")
            if emoji and not cookware.emoji:
                cookware.emoji = emoji
                changed.append("emoji")
            if changed:
                cookware.save(update_fields=changed)
        photo = PHOTOS.get(name)
        if with_images and photo and not cookware.image:
            try:
                attach_photo(cookware, photo)
                downloaded += 1
            except Exception as exc:  # noqa: BLE001 - réseau, image illisible : le seed continue
                failed.append(f"{name} ({exc})")
            time.sleep(DOWNLOAD_DELAY_SECONDS)
    return created, downloaded, failed


class Command(BaseCommand):
    help = (
        "Crée la liste de référence du matériel de cuisine (idempotent), avec leurs photos "
        "téléchargées depuis Wikimedia Commons."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-images", action="store_true", help="Ne télécharge aucune photo (installation hors ligne)."
        )

    def handle(self, *args, **options):
        created, downloaded, failed = seed_cookware(with_images=not options["skip_images"])
        self.stdout.write(
            self.style.SUCCESS(
                f"Matériel : {created} créé(s), {len(COOKWARE)} dans la liste de référence, "
                f"{downloaded} photo(s) téléchargée(s)."
            )
        )
        for failure in failed:
            self.stdout.write(self.style.WARNING(f"Photo non téléchargée : {failure}"))
