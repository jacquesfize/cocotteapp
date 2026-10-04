import factory

from .models import Announcement


class AnnouncementFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Announcement

    title_fr = factory.Sequence(lambda n: f"Annonce {n}")
    message_fr = "Un message."
