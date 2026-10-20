
import json
import time
from collections import deque
from datetime import datetime
from threading import Lock

import streamlit as st
import paho.mqtt.client as mqtt


BROKER = "3.135.234.101"
PORT = 1883

TOPIC_STATUS = "smartgym/ali/cp05/status"
TOPIC_PERFORMANCE = "smartgym/ali/cp05/performance"


st.set_page_config(
    page_title="Smart Gym | Dashboard",
    page_icon="🏋️",
    layout="wide"
)


@st.cache_resource
def iniciar_mqtt():
    dados = {
        "status": "Livre",
        "aluno": "-",
        "repeticoes": 0,
        "historico": deque(maxlen=20),
        "conectado": False,
        "lock": Lock()
    }

    def on_connect(client, userdata, flags, reason_code, properties):
        with dados["lock"]:
            dados["conectado"] = reason_code == 0

        if reason_code == 0:
            client.subscribe([
                (TOPIC_STATUS, 0),
                (TOPIC_PERFORMANCE, 0)
            ])

    def on_disconnect(client, userdata, flags,
                      reason_code, properties):
        with dados["lock"]:
            dados["conectado"] = False

    def on_message(client, userdata, msg):
        try:
            mensagem = json.loads(
                msg.payload.decode("utf-8")
            )

            if not isinstance(mensagem, dict):
                return

            with dados["lock"]:
                if msg.topic == TOPIC_STATUS:
                    status = str(
                        mensagem.get(
                            "status",
                            mensagem.get("estado", "Livre")
                        )
                    )

                    dados["status"] = status
                    dados["aluno"] = mensagem.get(
                        "aluno",
                        mensagem.get("nome", "-")
                    ) or "-"

                elif msg.topic == TOPIC_PERFORMANCE:
                    aluno = mensagem.get(
                        "aluno",
                        mensagem.get("nome", "-")
                    )

                    repeticoes = mensagem.get(
                        "repeticoes",
                        mensagem.get("reps", 0)
                    )

                    try:
                        repeticoes = int(repeticoes)
                    except (ValueError, TypeError):
                        repeticoes = 0

                    dados["repeticoes"] = repeticoes

                    dados["historico"].appendleft({
                        "Horário": datetime.now().strftime(
                            "%d/%m/%Y %H:%M:%S"
                        ),
                        "Aluno": aluno,
                        "Repetições": repeticoes
                    })

        except (json.JSONDecodeError, UnicodeDecodeError):
            pass

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2
    )

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    client.connect_async(BROKER, PORT, 60)
    client.loop_start()

    return dados, client


dados, cliente = iniciar_mqtt()


st.markdown("""
<style>
.stApp {
    background: #0B0D12;
    color: #F5F5F5;
}

[data-testid="stMetric"] {
    background: #191D27;
    padding: 20px;
    border-radius: 14px;
    border: 1px solid #303643;
}

[data-testid="stMetricLabel"] {
    color: #B9C0CD;
}

h1, h2, h3 {
    color: #FFFFFF;
}
</style>
""", unsafe_allow_html=True)


st.title("🏋️ SMART GYM")
st.caption("Monitoramento de equipamentos em tempo real • MQTT")


@st.fragment(run_every="1s")
def painel():
    with dados["lock"]:
        status = dados["status"]
        aluno = dados["aluno"]
        repeticoes = dados["repeticoes"]
        conectado = dados["conectado"]
        historico = list(dados["historico"])

    if conectado:
        st.success("● Broker MQTT conectado")
    else:
        st.warning("● Aguardando conexão com o broker MQTT")

    status_normalizado = status.strip().lower()
    ocupado = status_normalizado in (
        "ocupada", "ocupado", "busy", "occupied"
    )

    cor = "#EF4444" if ocupado else "#22C55E"
    titulo = "OCUPADA" if ocupado else "LIVRE"

    st.markdown(
        f"""
        <div style="
            background:#191D27;
            border:2px solid {cor};
            border-radius:16px;
            padding:24px;
            margin:16px 0;
            text-align:center;
        ">
            <div style="color:#B9C0CD;font-size:17px;">
                STATUS DO EQUIPAMENTO
            </div>
            <div style="
                color:{cor};
                font-size:38px;
                font-weight:800;
            ">
                {titulo}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:
        st.metric("👤 Aluno atual", str(aluno))

    with col2:
        st.metric("🔢 Última série", repeticoes)

    st.subheader("📋 Histórico de treinos")

    if historico:
        st.dataframe(
            historico,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Nenhuma série registrada nesta sessão.")

    st.caption(
        "Atualização automática a cada 1 segundo."
    )


painel()
