from django.http import JsonResponse
from django.views import View
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json
import requests

from .models import Usuario, FavoriteRecipe

MAPA_INGREDIENTES = {
    "Frango": "Chicken",
    "Carne Moída": "Minced Beef",
    "Bife": "Beef",
    "Peixe": "Fish",
    "Arroz": "Rice",
    "Feijão": "Beans",
    "Tomate": "Tomato",
    "Leite": "Milk",
    "Ovos": "Egg",
    "Manteiga": "Butter",
    "Cebola": "Onion",
    "Batata": "Potato",
    "Macarrão": "Pasta",
    "Alho": "Garlic",
    "Farinha": "Flour",
    "Açúcar": "Sugar",
    "Sal": "Salt"
}



def ping(request):
    return JsonResponse({"pong": True})


def greeting(request):
    return JsonResponse({"message": "Bem Vindo"})


class GreetingView(View):
    def get(self, request):
        return JsonResponse({"message": "Olá, bem-vindo à API!"})


class RecipesView(View):
    def get(self, request):
        receitas = [
            {"id": 1, "nome": "Arroz com frango"},
            {"id": 2, "nome": "Bolo de chocolate"},
        ]
        return JsonResponse({"receitas": receitas})



@method_decorator(csrf_exempt, name='dispatch')
class CadastroUsuarioView(View):
    def post(self, request):
        try:

            data = json.loads(request.body)

            nome = data.get("nome")
            email = data.get("email")
            senha = data.get("senha")

            if not nome or not email or not senha:
                return JsonResponse(
                    {"erro": "Campos obrigatórios: nome, email, senha"},
                    status=400
                )

            #  Verifica se email já existe
            if Usuario.objects.filter(email=email).exists():
                return JsonResponse(
                    {"erro": "E-mail já cadastrado."},
                    status=400
                )

            #  Salva no banco
            Usuario.objects.create(nome=nome, email=email, senha=senha)

            return JsonResponse({"status": "Usuário cadastrado com sucesso!"})

        except json.JSONDecodeError:
            return JsonResponse({"erro": "JSON inválido."}, status=400)

@method_decorator(csrf_exempt, name='dispatch')
class LoginUsuarioView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)

            email = data.get("email")
            senha = data.get("senha")

            if not email or not senha:
                return JsonResponse({"erro": "Informe email e senha."}, status=400)

            # verifica no banco
            usuario = Usuario.objects.filter(email=email, senha=senha).first()

            if usuario:
                return JsonResponse({
                    "status": "ok",
                    "id": usuario.id,
                    "nome": usuario.nome,
                    "email": usuario.email
                })

            return JsonResponse({"erro": "Credenciais inválidas."}, status=401)

        except json.JSONDecodeError:
            return JsonResponse({"erro": "JSON inválido."}, status=400)

class FrontendAppView(View):
    def get(self, request):
        return render(request, "index.html")
    
class ReceitasIngredientesView(View):
    def get(self, request):
        ingredientes = request.GET.get("ingredientes")

        if not ingredientes:
            return JsonResponse({"erro": "Nenhum ingrediente informado."}, status=400)

        lista_pt = ingredientes.split(",")

        lista_en = [MAPA_INGREDIENTES.get(i.strip(), i.strip()) for i in lista_pt]

        listas_de_receitas = []

        for ing in lista_en:
            url = f"https://www.themealdb.com/api/json/v1/1/filter.php?i={ing}"
            resposta = requests.get(url).json()

            if resposta.get("meals") is None:
                return JsonResponse({"receitas": []})

            receitas_dict = {meal["idMeal"]: meal for meal in resposta["meals"]}
            listas_de_receitas.append(receitas_dict)

        ids_comuns = set(listas_de_receitas[0].keys())
        for lista in listas_de_receitas[1:]:
            ids_comuns &= set(lista.keys())

        if not ids_comuns:
            return JsonResponse({"receitas": []})

        receitas_finais = []
        for id in ids_comuns:
            for lista in listas_de_receitas:
                if id in lista:
                    receitas_finais.append(lista[id])
                    break

        return JsonResponse({"receitas": receitas_finais})

class ReceitasDetalhesView(View):
    def get(self, request):
        id_receita = request.GET.get("id")

        if not id_receita:
            return JsonResponse({"erro": "ID da receita não informado."}, status=400)

        # Busca na ThemealDB
        url = f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={id_receita}"
        resposta = requests.get(url).json()

        meals = resposta.get("meals")
        if not meals:
            return JsonResponse({"erro": "Receita não encontrada."}, status=404)

        meal = meals[0]

        # --------------------------
        # INGREDIENTES FORMATADOS
        # --------------------------
        ingredientes = []
        for i in range(1, 21):
            nome = meal.get(f"strIngredient{i}")
            medida = meal.get(f"strMeasure{i}")

            if nome and nome.strip():
                ingredientes.append(f"{nome} - {medida}")

        # --------------------------
        # MODO DE PREPARO 
        # --------------------------
        modo_preparo_original = meal.get("strInstructions", "") or ""

        passos_en = [
            passo.strip()
            for passo in modo_preparo_original.split("\n")
            if passo.strip()
        ]

        passos_pt = [traduzir_texto(p) for p in passos_en]

        passos_formatados = [f" {p}" for p in passos_pt]

        receita = {
            "id": meal.get("idMeal"),
            "nomePT": meal.get("strMeal"),
            "thumb": meal.get("strMealThumb"),
            "tempo": "Não informado", 
            "ingredientes": ingredientes,
            "modo_preparo": passos_formatados
        }

        return JsonResponse({"receita": receita})
    
def traduzir_texto(texto):
    try:
        if len(texto) > 400:
            texto = texto[:400]  

        url = f"https://api.mymemory.translated.net/get?q={texto}&langpair=en|pt-br"
        resp = requests.get(url).json()

        traduzido = resp.get("responseData", {}).get("translatedText")
        return traduzido if traduzido else texto

    except:
        return texto
    
    

def _get_usuario_from_request(request):

    email = request.headers.get("X-User-Email")
    if not email:
        try:
            body = json.loads(request.body.decode() or "{}")
            email = body.get("email") or body.get("usuario_email")
        except:
            email = None

    if not email:
        return None, JsonResponse({"erro": "E-mail do usuário não fornecido (envie X-User-Email)."}, status=400)

    usuario = Usuario.objects.filter(email=email).first()
    if not usuario:
        return None, JsonResponse({"erro": "Usuário não encontrado."}, status=404)
    return usuario, None

def user_info(request):
    usuario, err = _get_usuario_from_request(request)
    if err:
        return err

    favoritos = FavoriteRecipe.objects.filter(usuario=usuario).order_by("-created_at")
    favs = [
        {"id": f.recipe_id, "name": f.recipe_name, "image": f.recipe_image}
        for f in favoritos
    ]

    return JsonResponse({
        "nome": usuario.nome,
        "email": usuario.email,
        "favoritos": favs
    })


@csrf_exempt
def update_email(request):
    if request.method != "PUT":
        return JsonResponse({"erro": "Use método PUT."}, status=405)

    usuario, err = _get_usuario_from_request(request)
    if err:
        return err

    try:
        payload = json.loads(request.body.decode() or "{}")
        novo_email = payload.get("new_email") or payload.get("email")
    except:
        return JsonResponse({"erro": "JSON inválido."}, status=400)

    if not novo_email:
        return JsonResponse({"erro": "Informe novo email no campo new_email."}, status=400)

    if Usuario.objects.filter(email=novo_email).exclude(pk=usuario.pk).exists():
        return JsonResponse({"erro": "Email já em uso por outro usuário."}, status=400)

    usuario.email = novo_email
    usuario.save()
    return JsonResponse({"message": "Email atualizado com sucesso.", "email": novo_email})


@csrf_exempt
def update_password(request):
    if request.method != "PUT":
        return JsonResponse({"erro": "Use método PUT."}, status=405)

    usuario, err = _get_usuario_from_request(request)
    if err:
        return err

    try:
        payload = json.loads(request.body.decode() or "{}")
        new_password = payload.get("new_password") or payload.get("password")
    except:
        return JsonResponse({"erro": "JSON inválido."}, status=400)

    if not new_password:
        return JsonResponse({"erro": "Informe a nova senha no campo new_password."}, status=400)

    usuario.senha = new_password
    usuario.save()
    return JsonResponse({"message": "Senha atualizada com sucesso."})


@csrf_exempt
def favorite_recipe(request):
    """
    POST /api/usuarios/favorite/
    Headers: X-User-Email
    Body JSON: { recipe_id: "12345", recipe_name: "Pão", recipe_image: "http..." }
    """
    if request.method != "POST":
        return JsonResponse({"erro": "Use método POST."}, status=405)

    usuario, err = _get_usuario_from_request(request)
    if err:
        return err

    try:
        payload = json.loads(request.body.decode() or "{}")
    except:
        return JsonResponse({"erro": "JSON inválido."}, status=400)

    recipe_id = payload.get("recipe_id") or payload.get("id") or ""
    recipe_name = payload.get("recipe_name") or payload.get("name") or payload.get("recipe")
    recipe_image = payload.get("recipe_image") or payload.get("image") or ""

    if not recipe_name:
        return JsonResponse({"erro": "Informe recipe_name."}, status=400)

    # evita duplicar
    existing = FavoriteRecipe.objects.filter(usuario=usuario, recipe_id=recipe_id, recipe_name=recipe_name).first()
    if existing:
        return JsonResponse({"message": "Receita já favoritada."})

    fav = FavoriteRecipe.objects.create(
        usuario=usuario,
        recipe_id=recipe_id,
        recipe_name=recipe_name,
        recipe_image=recipe_image
    )

    return JsonResponse({"message": "Receita favoritada.", "favorite_id": fav.id})


@csrf_exempt
def unfavorite_recipe(request):
    """
    POST /api/usuarios/unfavorite/
    Body: { recipe_id } and X-User-Email header
    """
    if request.method != "POST":
        return JsonResponse({"erro": "Use método POST."}, status=405)

    usuario, err = _get_usuario_from_request(request)
    if err:
        return err

    try:
        payload = json.loads(request.body.decode() or "{}")
    except:
        return JsonResponse({"erro": "JSON inválido."}, status=400)

    recipe_id = payload.get("recipe_id") or payload.get("id") or ""
    if not recipe_id:
        return JsonResponse({"erro": "Informe recipe_id."}, status=400)

    deleted, _ = FavoriteRecipe.objects.filter(usuario=usuario, recipe_id=recipe_id).delete()
    if deleted:
        return JsonResponse({"message": "Removido das favoritas."})
    else:
        return JsonResponse({"message": "Não encontrada nas favoritas."})