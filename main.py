import cv2
import numpy as np
import time
import json
import math
import requests
from threading import Thread
from urllib.parse import urlparse, urlunparse

# Intentar importar MediaPipe
try:
    import mediapipe as mp  # type: ignore
except Exception:
    mp = None  # Si falla, se deshabilita la detección de pose


class StereoTracker:
    def __init__(self, left_source=0, right_source=1, json_out="coords.json",
                 api_url="http://localhost:5000/api/movement"):
        # --- CONFIGURACIÓN DE CÁMARAS ---
        self.left_source = left_source
        self.right_source = right_source
        self.json_out = json_out

        # --- CONFIGURACIÓN API Y MOVIMIENTO (NUEVO) ---
        self.api_url = api_url
        self.movement_sensitivity = 3.0  # Mínimo de píxeles para considerar que hubo movimiento
        self.api_send_interval = 0.1  # Enviar datos máx cada 0.1s (10 FPS)
        self.last_api_send_time = 0

        # Extremidades a rastrear (Índices de MediaPipe)
        # Extremidades a rastrear (Índices de MediaPipe)
        # Referencia: https://developers.google.com/mediapipe/solutions/vision/pose
        self.EXTREMITIES_IDX = {
            "nose": 0,
            # Torso (Fundamental para la rotación del cuerpo)
            "left_shoulder": 11,
            "right_shoulder": 12,
            "left_hip": 23,
            "right_hip": 24,
            # Brazos
            "left_elbow": 13,
            "right_elbow": 14,
            "left_wrist": 15,
            "right_wrist": 16,
            # Piernas (Lo que pediste)
            "left_knee": 25,
            "right_knee": 26,
            "left_ankle": 27,
            "right_ankle": 28,
            # Pies (Punta del pie, útil para saber orientación)
            "left_foot_index": 31,
            "right_foot_index": 32
        }
        # Almacena posición anterior { "left_wrist": (x, y), ... }
        self.prev_extremities = {}

        # --- INICIALIZACIÓN DE FUENTES DE VIDEO ---
        self.left_is_ip = isinstance(left_source, str)
        self.right_is_ip = isinstance(right_source, str)
        self.left_is_pc = not self.left_is_ip
        self.right_is_pc = not self.right_is_ip

        print(f"Iniciando cámaras... Izq: {left_source}, Der: {right_source}")
        self.cap_left = cv2.VideoCapture(left_source)
        self.cap_right = cv2.VideoCapture(right_source)
        self.use_single_camera = False

        # Validación de cámaras
        def _validate(cap, attempts=20):
            if cap is None or not cap.isOpened(): return False
            for _ in range(attempts):
                ret, _ = cap.read()
                if ret: return True
                time.sleep(0.05)
            return False

        left_ok = _validate(self.cap_left)
        right_ok = _validate(self.cap_right)

        if left_ok and right_ok:
            print("Modo Estéreo Activo.")
        elif left_ok and not right_ok:
            self.use_single_camera = True
            if right_ok: self.cap_right.release()
            print("Solo cámara Izquierda detectada. Modo SINGLE.")
        else:
            self.no_cameras = True
            print("ERROR: No se encontraron cámaras.")
            return

        # --- CONFIGURACIÓN MEDIAPIPE ---
        self.pose = None
        self.pose_backend = None
        if mp is not None:
            try:
                self.mp_pose = mp.solutions.pose
                self.mp_drawing = mp.solutions.drawing_utils
                self.mp_styles = mp.solutions.drawing_styles
                self.pose = self.mp_pose.Pose(
                    model_complexity=1,
                    enable_segmentation=False,
                    smooth_landmarks=True,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5,
                )
                self.pose_backend = "mediapipe"
            except Exception as e:
                print(f"Error iniciando MediaPipe: {e}")
        else:
            print("MediaPipe no instalado. No se detectarán extremidades.")

        # Variables auxiliares originales
        self.calibration = None
        self.cal_distance_m = 2.0
        self._calib_msg_until = 0.0
        self.anchor_landmark_id = 0

    # --- UTILIDADES ---
    def _nan_to_none(self, v):
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)): return None
        return v

    def _sanitize(self, obj):
        """Limpia datos para que sean serializables a JSON (float32 a float, etc)"""
        if isinstance(obj, dict): return {k: self._sanitize(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)): return [self._sanitize(v) for v in obj]
        if isinstance(obj, (np.generic, np.float32, np.float64)): return float(obj)
        return self._nan_to_none(obj)

    def _write_json_snapshot(self, snapshot):
        try:
            with open(self.json_out, 'w', encoding='utf-8') as f:
                json.dump(self._sanitize(snapshot), f, ensure_ascii=False)
        except Exception:
            pass

    # --- LÓGICA DE API Y MOVIMIENTO ---

    def _send_api_async(self, payload):
        def worker():
            try:
                print("Intentando enviar a API...")  # DEBUG
                headers = {'Content-Type': 'application/json'}
                r = requests.post(self.api_url, json=payload, headers=headers, timeout=1.0)
                print(f"API Respondió: {r.status_code}")  # DEBUG
            except requests.exceptions.ConnectionError:
                print(f"ERROR: No se pudo conectar a {self.api_url}. ¿Está encendido el servidor?")
            except Exception as e:
                print(f"ERROR API: {e}")

        t = Thread(target=worker, daemon=True)
        t.start()

    def process_extremities(self, landmarks, width, height):
        """Calcula posición y velocidad de las extremidades clave."""
        if not landmarks: return None

        data_out = {}

        for name, idx in self.EXTREMITIES_IDX.items():
            if idx >= len(landmarks.landmark): continue

            lm = landmarks.landmark[idx]

            # Coordenadas Píxeles (Para dibujar en OpenCV)
            cx, cy = float(lm.x * width), float(lm.y * height)

            # Coordenadas Normalizadas 0.0 a 1.0 (Para enviar a Three.js/Django)
            norm_x, norm_y = float(lm.x), float(lm.y)

            vis = float(lm.visibility)

            if vis < 0.5: continue

            is_moving = False
            speed = 0.0

            if name in self.prev_extremities:
                prev_x, prev_y = self.prev_extremities[name]
                dist = math.sqrt((cx - prev_x) ** 2 + (cy - prev_y) ** 2)
                speed = dist
                if dist > self.movement_sensitivity:
                    is_moving = True

            self.prev_extremities[name] = (cx, cy)

            data_out[name] = {
                # IMPORTANTE: Enviamos las normalizadas como x e y para la API
                "x": norm_x,
                "y": norm_y,
                "z": lm.z,
                "pixel_x": cx,  # Guardamos pixel por si acaso se necesita debug
                "pixel_y": cy,
                "moving": is_moving,
                "speed": speed
            }

        return data_out

    def detect_pose(self, frame):
        """Detecta pose y devuelve payload + landmarks crudos."""
        if not self.pose or self.pose_backend != "mediapipe":
            return None, None

        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.pose.process(rgb)

        pose_payload = None
        raw_landmarks = None

        if result.pose_landmarks:
            raw_landmarks = result.pose_landmarks

            # Dibujo básico de esqueleto
            self.mp_drawing.draw_landmarks(
                frame,
                raw_landmarks,
                self.mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=self.mp_styles.get_default_pose_landmarks_style(),
            )

            # Payload estilo original (todos los landmarks)
            lm_list = []
            for idx, lm in enumerate(raw_landmarks.landmark):
                lm_list.append({
                    "id": idx, "x": lm.x * w, "y": lm.y * h, "z": lm.z * w, "visibility": lm.visibility
                })
            pose_payload = {"landmarks": lm_list}

        return pose_payload, raw_landmarks

    # --- BUCLE PRINCIPAL ---
    def run(self):
        if getattr(self, 'no_cameras', False): return

        print(f"Rastreando... Enviando a API: {self.api_url}")

        while True:
            # 1. Leer frames
            if self.use_single_camera:
                ret, frame = self.cap_left.read()
                if not ret: break
                frame_main = frame  # Usamos frame izquierdo/único para análisis
            else:
                ret1, frame_l = self.cap_left.read()
                ret2, frame_r = self.cap_right.read()
                if not ret1 or not ret2: break
                frame_main = frame_l

                # 2. Detección de Pose
            pose_payload, raw_landmarks = self.detect_pose(frame_main)
            h, w = frame_main.shape[:2]

            # 3. Análisis de Extremidades y API
            extremities_status = None
            if raw_landmarks:
                extremities_status = self.process_extremities(raw_landmarks, w, h)

                # Visualización en pantalla
                if extremities_status:
                    y_txt = 30
                    for part, info in extremities_status.items():
                        # Color: Verde si se mueve, Rojo si está quieto
                        color = (0, 255, 0) if info['moving'] else (0, 0, 255)

                        # Dibujar círculo en la articulación
                        cv2.circle(frame_main, (int(info['x']), int(info['y'])), 10, color, 2)

                        # Texto de estado
                        txt = f"{part}: {'MOVIENDO' if info['moving'] else 'QUIETO'} ({int(info['speed'])})"
                        cv2.putText(frame_main, txt, (10, y_txt), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                        y_txt += 20

                # Enviar a API (Rate limited)
                now = time.time()
                if (now - self.last_api_send_time > self.api_send_interval) and extremities_status:
                    api_data = {
                        "timestamp": now,
                        "camera_mode": "single" if self.use_single_camera else "stereo",
                        "extremities": extremities_status
                    }
                    # Sanitizar y enviar asíncronamente
                    self._send_api_async(self._sanitize(api_data))
                    self.last_api_send_time = now

            # 4. Mostrar ventanas
            cv2.imshow("Main Camera (Tracking)", frame_main)
            if not self.use_single_camera:
                cv2.imshow("Secondary Camera", frame_r)

            # 5. Guardar JSON local (funcionalidad original)
            try:
                full_snap = {"pose": pose_payload, "calibration": self.calibration}
                self._write_json_snapshot(full_snap)
            except Exception:
                pass

            # 6. Controles
            key = cv2.waitKey(1) & 0xFF
            if key in (ord('q'), ord('Q')):
                break
            # Calibración manual simple (tecla C)
            if key in (ord('c'), ord('C')) and raw_landmarks:
                self.calibration = {
                    "timestamp": time.time(),
                    "msg": "Calibracion manual disparada"
                }
                print("Calibración capturada.")

        # Limpieza
        if self.cap_left: self.cap_left.release()
        if self.cap_right: self.cap_right.release()
        if self.pose: self.pose.close()
        cv2.destroyAllWindows()


# --- ENTRY POINT ---
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--left", default="0", help="ID o URL camara izquierda")
    parser.add_argument("--right", default="1", help="ID o URL camara derecha")
    # CAMBIO AQUÍ: Apuntar a Django update-pose
    parser.add_argument("--api", default="http://127.0.0.1:8000/api/update-pose/", help="Endpoint API")
    args = parser.parse_args()


    # ... resto del código ...


    def parse_source(v):
        # Intenta convertir a entero (webcam USB)
        try:
            return int(v)
        except:
            pass

        # Limpieza básica de URL
        s = str(v).strip()
        if s.isdigit(): return int(s)
        # Si es HTTP sin ruta, agregar /video (común en IP Webcam android)
        if (s.startswith("http") and urlparse(s).path in ["", "/"]):
            return urlunparse(urlparse(s)._replace(path="/video"))
        return s


    tracker = StereoTracker(
        left_source=parse_source(args.left),
        right_source=parse_source(args.right),
        api_url=args.api
    )
    tracker.run()