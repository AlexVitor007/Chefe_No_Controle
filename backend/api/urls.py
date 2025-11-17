from django.urls import path
from .views import (
    RecipesView, CadastroUsuarioView, GreetingView, ping, greeting,
    LoginUsuarioView, ReceitasIngredientesView, ReceitasDetalhesView,
    user_info, update_email, update_password, favorite_recipe, unfavorite_recipe
)

urlpatterns = [
    path("recipes/", RecipesView.as_view()),
    path("usuarios/cadastro/", CadastroUsuarioView.as_view()),
    path("usuarios/login/", LoginUsuarioView.as_view()),
    path("usuarios/me/", user_info),
    path("usuarios/update-email/", update_email),
    path("usuarios/update-password/", update_password),
    path("usuarios/favorite/", favorite_recipe),
    path("usuarios/unfavorite/", unfavorite_recipe),
    path("greeting/", greeting),
    path("ping/", ping),
    path("receitas/", ReceitasIngredientesView.as_view()),
    path("receita_detalhe/", ReceitasDetalhesView.as_view()),
]