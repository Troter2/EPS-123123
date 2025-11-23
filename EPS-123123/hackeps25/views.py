import json
from django.contrib.auth.decorators import login_required
import form
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect


@login_required  # This decorator checks if user is logged in
def index(request):
    # Si el usuario ha enviado el formulario (ha pulsado el botón "Lock In Selection")
    if request.method == 'POST':
        # 1. Capturamos los datos del formulario usando los 'name' de los inputs ocultos
        selected_character = request.POST.get('captain')  # Recibirá: 'the_boss', 'monster', etc.
        selected_stage = request.POST.get('sidekick')  # Recibirá: 'church', 'disco', etc.

        # 2. (Opcional) Imprimimos en la terminal para comprobar que funciona
        print(f"--- SELECCIÓN RECIBIDA ---")
        print(f"Personaje: {selected_character}")
        print(f"Escenario: {selected_stage}")

        # 3. Guardamos la selección para usarla después (por ejemplo, en la vista del juego)
        # Usar 'request.session' es la forma correcta de pasar datos entre páginas en Django
        request.session['player_character'] = selected_character
        request.session['player_stage'] = selected_stage

        # 4. ¿Qué quieres hacer ahora?
        # Opción A: Quedarse en la misma página
        # return render(request, 'index.html')

        # Opción B (Recomendada): Redirigir a la página donde empieza la acción
        # Asegúrate de que 'capture_motion_view' es el nombre de la URL en tu urls.py
        # return redirect('capture_motion_view')

    # Si es una visita normal (GET), solo mostramos la página
    return render(request, 'index.html')


def accordion(request):
    return render(request, 'accordion.html')


def carousel(request):
    return render(request, 'carousel.html')

@login_required  # This decorator checks if user is logged in
def camera(request):
    # Inicializamos el contexto vacío o con valores por defecto
    context = {}

    # Si recibimos el formulario desde index.html
    if request.method == 'POST':
        selected_character = request.POST.get('captain')
        selected_stage = request.POST.get('sidekick')

        print(f"--- DATOS RECIBIDOS EN CAMERA ---")
        print(f"Personaje: {selected_character}")
        print(f"Escenario: {selected_stage}")

        # Guardamos en sesión (opcional, pero útil si recargas la página)
        request.session['player_character'] = selected_character
        request.session['player_stage'] = selected_stage

        # Preparamos los datos para enviarlos al HTML 'camera.html'
        context = {
            'selected_character': selected_character,
            'selected_stage': selected_stage
        }

    # Si entran directo por GET, intentamos recuperar de la sesión (opcional)
    else:
        context = {
            'selected_character': request.session.get('player_character'),
            'selected_stage': request.session.get('player_stage')
        }

    # Renderizamos pasando el contexto
    return render(request, 'camera.html', context)


def collapse(request):
    return render(request, 'collapse.html')


def dial(request):
    return render(request, 'dial.html')


def dismiss(request):
    return render(request, 'dismiss.html')


def modal(request):
    return render(request, 'modal.html')


def drawer(request):
    return render(request, 'drawer.html')


def dropdown(request):
    return render(request, 'dropdown.html')


def popover(request):
    return render(request, 'popover.html')


def tooltip(request):
    return render(request, 'tooltip.html')


def tabs(request):
    return render(request, 'tabs.html')


def input_counter(request):
    return render(request, 'input-counter.html')


def datepicker(request):
    return render(request, 'datepicker.html')


def base(request):
    return render(request, 'base.html')




latest_pose_data = {
    "extremities": {
        "nose": {"x": 0.5, "y": 0.5},
        "left_wrist": {"x": 0.5, "y": 0.5},
        "right_wrist": {"x": 0.5, "y": 0.5}
    }
}


@csrf_exempt
def update_pose(request):
    """
    Recibe el JSON completo del script de Python.
    Espera estructura: { "extremities": { ... }, "timestamp": ... }
    """
    global latest_pose_data
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Validamos si viene la data de extremidades
            if "extremities" in data:
                latest_pose_data = data
            # Soporte retroactivo para scripts viejos que solo mandan x, y
            elif "x" in data and "y" in data:
                latest_pose_data = {
                    "extremities": {
                        "nose": {"x": data["x"], "y": data["y"]}
                    }
                }

            return JsonResponse({"status": "ok", "received": len(str(data))})
        except Exception as e:
            print(f"Error en update_pose: {e}")
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    return JsonResponse({"error": "POST only"}, status=405)


def capture_motion_view(request):
    # Asegúrate de que mocap.html esté en tu carpeta templates
    return render(request, 'mocap.html')


def get_pose(request):
    """
    El Frontend JS consulta esto para mover al personaje.
    """
    global latest_pose_data
    return JsonResponse(latest_pose_data)


class LoginBootstrapView(LoginView):
    template_name = 'login.html'

    def form_invalid(self, form):
        messages.error(self.request, "Usuario o contraseña incorrectos")
        return super().form_invalid(form)


GLOBAL_POSE_DATA = {
    "position": {"x": 0, "y": 0},
    "state": "normal"  # Por defecto
}


@csrf_exempt
def update_coords(request):
    """
    Recibe datos desde el script de Python (tracking_api.py)
    """
    global GLOBAL_POSE_DATA
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            # 1. Guardar Posición
            GLOBAL_POSE_DATA["position"] = {
                "x": data.get("x", 0),
                "y": data.get("y", 0)
            }

            # 2. Guardar Estado (Waving / Normal)
            # El .get("state", "normal") significa: si no envías nada, pon "normal"
            GLOBAL_POSE_DATA["state"] = data.get("state", "normal")

            return JsonResponse({"status": "ok"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})

    return JsonResponse({"status": "bad request"})


def get_pose(request):
    """
    Envía datos al navegador (Three.js)
    """
    global GLOBAL_POSE_DATA
    return JsonResponse(GLOBAL_POSE_DATA)




def register(request):
    from .forms import RegisterForm
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully!")
            return redirect("login")  # change to your login URL
    else:
        form = RegisterForm()

    return render(request, "registre.html", {"form": form})
# 1. Update this import line at the top to include 'logout'
from django.contrib.auth import login, authenticate, logout
# ... keep your other imports ...

# 2. Add this function at the bottom of your file
def sign_out(request):
    logout(request) # This clears the session and logs the user out
    messages.success(request, "You have been logged out.")
    return redirect('login') # Redirects back to login page