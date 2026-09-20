from rest_framework.routers import DefaultRouter

from .views import AllergenViewSet, IngredientViewSet

router = DefaultRouter()
router.register("allergens", AllergenViewSet, basename="allergen")
router.register("ingredients", IngredientViewSet, basename="ingredient")

urlpatterns = router.urls
