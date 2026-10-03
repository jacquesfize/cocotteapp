from rest_framework.pagination import PageNumberPagination

# Choix proposés par le sélecteur "Recettes par page" de la liste (RecipeListView.vue).
RECIPE_PAGE_SIZES = (10, 20, 50)


class RecipePagination(PageNumberPagination):
    """10 recettes par page par défaut, modifiable via ?page_size= (plafonné à 50)."""

    page_size = RECIPE_PAGE_SIZES[0]
    page_size_query_param = "page_size"
    max_page_size = RECIPE_PAGE_SIZES[-1]
