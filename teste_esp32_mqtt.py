
import json
import paho.mqtt.client as mqtt

BROKER = "3.135.234.101"
PORT = 1883
TOPIC_RFID = "smartgym/ali/cp05/rfid"


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("Conectado ao MQTT!")
        client.subscribe(TOPIC_RFID)
        print("Aguardando cartao RFID...")
    else:
        print(f"Falha na conexao: {reason_code}")


def on_message(client, userdata, msg):
    try:
        dados = json.loads(msg.payload.decode("utf-8"))
        uid = dados.get("uid", "")

        print("-------------------------")
        print(f"Cartao recebido: {uid}")
        print(f"Origem: {dados.get('origem', 'desconhecida')}")
        print("-------------------------")

    except Exception as erro:
        print(f"Erro ao processar mensagem: {erro}")


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

client.on_connect = on_connect
client.on_message = on_message

print("Conectando ao broker MQTT...")
client.connect(BROKER, PORT, 60)
client.loop_forever()
