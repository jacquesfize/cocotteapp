from rest_framework import serializers

from .models import ImageLicense

REQUIRED_CREDIT_FIELDS = {
    ImageLicense.CC_BY: ("image_credit_author", "image_credit_source_url"),
    ImageLicense.CC_BY_SA: ("image_credit_author", "image_credit_source_url"),
    ImageLicense.PUBLIC_DOMAIN: (),
    ImageLicense.PERSONAL: ("image_credit_author",),
    ImageLicense.PERMISSION: ("image_credit_author", "image_credit_note"),
    ImageLicense.UNKNOWN: (),
}

DEFAULT_LICENSE_URLS = {
    ImageLicense.CC_BY: "https://creativecommons.org/licenses/by/4.0/",
    ImageLicense.CC_BY_SA: "https://creativecommons.org/licenses/by-sa/4.0/",
}


def validate_image_credit(attrs):
    """Validates that attrs has a license and every field that license requires.
    Mutates attrs to auto-fill image_credit_license_url for CC licenses if not already set.
    Call this only when the image is actually new or changing — callers are responsible for
    grandfathering (not calling this at all when an existing image/credit is untouched)."""
    license_value = attrs.get("image_license")
    if not license_value:
        raise serializers.ValidationError({"image_license": "Merci d'indiquer une licence pour cette image."})
    missing = [f for f in REQUIRED_CREDIT_FIELDS.get(license_value, ()) if not attrs.get(f)]
    if missing:
        raise serializers.ValidationError({f: "Ce champ est requis pour cette licence." for f in missing})
    if license_value in DEFAULT_LICENSE_URLS and not attrs.get("image_credit_license_url"):
        attrs["image_credit_license_url"] = DEFAULT_LICENSE_URLS[license_value]
    return attrs
