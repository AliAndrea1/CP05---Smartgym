
import cv2

camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not camera.isOpened():
    print("ERRO: Nao foi possivel abrir a camera.")
else:
    print("Camera funcionando!")
    print("Pressione Q para fechar.")

    while True:
        sucesso, frame = camera.read()

        if not sucesso:
            print("Erro ao capturar imagem.")
            break

        cv2.imshow("Teste Camera - Smart Gym", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

camera.release()
cv2.destroyAllWindows()
