import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from django.contrib import messages

from hackeps25.forms import ContactoForm


def index(request):
    return render(request, 'index.html')


def accordion(request):
    return render(request, 'accordion.html')


def carousel(request):
    return render(request, 'carousel.html')


def camera(request):
    return render(request, 'camera.html')


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


def registre(request):
    return render(request, 'registre.html')


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


def contacto_view(request):
    if request.method == 'POST':
        form = ContactoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('index')  # Cambia a la URL que quieras
    else:
        form = ContactoForm()

    return render(request, 'contacto.html', {'form': form})
