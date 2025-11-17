from django.db import models

class Usuario(models.Model):
    nome = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    senha = models.CharField(max_length=128)

    def __str__(self):
        return self.nome

# nova model para favoritos
class FavoriteRecipe(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="favoritos")
    recipe_id = models.CharField(max_length=64, blank=True)   
    recipe_name = models.CharField(max_length=255)
    recipe_image = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("usuario", "recipe_id", "recipe_name")  

    def __str__(self):
        return f"{self.recipe_name} ({self.usuario.email})"
