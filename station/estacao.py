
import cv2
import json
import math
import queue
import time
import uuid
from pathlib import Path

import mediapipe as mp
import paho.mqtt.client as mqtt

BROKER = "3.135.234.101"
PORT = 1883

TOPIC_RFID = "smartgym/ali/cp05/rfid"
TOPIC_STATUS = "smartgym/ali/cp05/status"
TOPIC_PERFORMANCE = "smartgym/ali/cp05/performance"

ALUNOS = {
    "999FEF97": "Ali Andrea"
}

MODELO = (
    Path(__file__).resolve().parent.parent
    / "models"
    / "pose_landmarker_lite.task"
)

eventos = queue.Queue()

BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
RunningMode = mp.tasks.vision.RunningMode


def publicar(client, topico, dados, retain=False):
    client.publish(
        topico,
        json.dumps(dados),
        qos=1,
        retain=retain
    )


def status(client, estado, aluno="-"):
    publicar(
        client,
        TOPIC_STATUS,
        {"status": estado, "aluno": aluno},
        retain=True
    )
    print(f"Status: {estado} | Aluno: {aluno}")


def calcular_angulo(a, b, c):
    angulo = abs(math.degrees(
        math.atan2(c.y - b.y, c.x - b.x)
        - math.atan2(a.y - b.y, a.x - b.x)
    ))
    return 360 - angulo if angulo > 180 else angulo


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("Conectado ao MQTT!")
        client.subscribe(TOPIC_RFID)
    else:
        print("Falha MQTT:", reason_code)


def on_message(client, userdata, msg):
    try:
        dados = json.loads(msg.payload.decode("utf-8"))
        uid = str(dados.get("uid", "")).strip().upper()

        if uid:
            print("Cartao recebido:", uid)
            eventos.put(uid)
    except (ValueError, UnicodeDecodeError):
        print("Mensagem RFID invalida")


def desenhar_pontos(frame, pontos):
    altura, largura = frame.shape[:2]

    conexoes = [
        (11, 12),
        (11, 13), (13, 15),
        (12, 14), (14, 16),
        (11, 23), (12, 24),
        (23, 24)
    ]

    for inicio, fim in conexoes:
        a, b = pontos[inicio], pontos[fim]

        if a.visibility > 0.5 and b.visibility > 0.5:
            p1 = (int(a.x * largura), int(a.y * altura))
            p2 = (int(b.x * largura), int(b.y * altura))
            cv2.line(frame, p1, p2, (0, 255, 0), 2)

    for indice in [12, 14, 16]:
        p = pontos[indice]
        if p.visibility > 0.5:
            centro = (int(p.x * largura), int(p.y * altura))
            cv2.circle(frame, centro, 6, (0, 255, 255), -1)


def executar_camera(aluno, uid_aluno):
    if not MODELO.is_file():
        raise FileNotFoundError(
            f"Modelo nao encontrado: {MODELO}"
        )

    camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not camera.isOpened():
        raise RuntimeError("Nao foi possivel abrir a webcam")

    opcoes = PoseLandmarkerOptions(
        base_options=BaseOptions(
            model_asset_path=str(MODELO)
        ),
        running_mode=RunningMode.VIDEO,
        num_poses=1,
        min_pose_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

    repeticoes = 0
    fase = "AGUARDANDO EXTENSAO"
    ultimo_tempo = time.monotonic()
    inicio = time.monotonic()
    ultimo_timestamp = -1

    print("Camera iniciada!")
    print("Estenda, flexione e estenda o braco direito.")
    print("Passe o mesmo cartao para finalizar.")
    print("Ou pressione Q.")

    try:
        with PoseLandmarker.create_from_options(opcoes) as detector:
            while True:
                # O mesmo cartao encerra o treino.
                # Pequeno intervalo evita encerramento por leitura duplicada.
                while not eventos.empty():
                    uid = eventos.get_nowait()

                    if uid == uid_aluno:
                        if time.monotonic() - inicio >= 3:
                            print("Treino encerrado pelo RFID")
                            return repeticoes
                    else:
                        print("Maquina ocupada. Cartao ignorado.")

                ok, frame = camera.read()

                if not ok:
                    print("Erro ao capturar frame")
                    break

                frame = cv2.flip(frame, 1)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                imagem = mp.Image(
                    image_format=mp.ImageFormat.SRGB,
                    data=rgb
                )

                timestamp = int(
                    (time.monotonic() - inicio) * 1000
                )
                timestamp = max(timestamp, ultimo_timestamp + 1)
                ultimo_timestamp = timestamp

                resultado = detector.detect_for_video(
                    imagem, timestamp
                )

                angulo = None

                if resultado.pose_landmarks:
                    pontos = resultado.pose_landmarks[0]
                    desenhar_pontos(frame, pontos)

                    ombro = pontos[12]
                    cotovelo = pontos[14]
                    punho = pontos[16]

                    if min(
                        ombro.visibility,
                        cotovelo.visibility,
                        punho.visibility
                    ) > 0.5:
                        angulo = calcular_angulo(
                            ombro, cotovelo, punho
                        )

                        if angulo > 160:
                            if fase == "FLEXIONADO":
                                repeticoes += 1
                                print("Repeticao:", repeticoes)

                            fase = "ESTENDIDO"

                        elif angulo < 50 and fase == "ESTENDIDO":
                            fase = "FLEXIONADO"

                cv2.putText(
                    frame, f"Aluno: {aluno}", (20, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                    (255, 255, 255), 2
                )
                cv2.putText(
                    frame, f"Repeticoes: {repeticoes}", (20, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 1,
                    (0, 255, 0), 2
                )
                cv2.putText(
                    frame, f"Fase: {fase}", (20, 120),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                    (255, 255, 255), 2
                )

                if angulo is not None:
                    cv2.putText(
                        frame, f"Angulo: {angulo:.0f}",
                        (20, 155),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                        (0, 255, 255), 2
                    )

                cv2.imshow("SMART GYM - CAMERA", frame)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    print("Treino encerrado pelo teclado")
                    break

    finally:
        camera.release()
        cv2.destroyAllWindows()

    return repeticoes


def main():
    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=f"smartgym-{uuid.uuid4().hex[:8]}"
    )
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(BROKER, PORT, 60)
    client.loop_start()

    try:
        while not client.is_connected():
            time.sleep(0.2)

        status(client, "Livre")
        print("Aguardando cartao RFID...")

        while True:
            uid = eventos.get()

            if uid not in ALUNOS:
                print("Cartao nao cadastrado:", uid)
                continue

            aluno = ALUNOS[uid]
            print("Entrada autorizada:", aluno)
            status(client, "Ocupada", aluno)

            try:
                repeticoes = executar_camera(aluno, uid)

                publicar(
                    client,
                    TOPIC_PERFORMANCE,
                    {
                        "aluno": aluno,
                        "repeticoes": repeticoes,
                        "timestamp": time.strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                    }
                )

                print("Total de repeticoes:", repeticoes)

            except Exception as erro:
                print("Erro na camera:", erro)

            finally:
                status(client, "Livre")

                while not eventos.empty():
                    eventos.get_nowait()

                print("Aguardando cartao RFID...")

    except KeyboardInterrupt:
        print("Encerrando Smart Gym")

    finally:
        status(client, "Livre")
        client.disconnect()
        client.loop_stop()


if __name__ == "__main__":
    main()
