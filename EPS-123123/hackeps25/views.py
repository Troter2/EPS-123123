import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt


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


def get_pose(request):
    """
    El Frontend JS consulta esto para mover al personaje.
    """
    global latest_pose_data
    return JsonResponse(latest_pose_data)