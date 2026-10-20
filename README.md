# Smart Gym — Checkpoint 5

## Sobre o projeto

O **Smart Gym** é um sistema de academia inteligente desenvolvido para integrar dispositivos IoT, identificação por RFID, visão computacional e monitoramento de dados em tempo real.

A solução permite identificar alunos por meio de cartões RFID, controlar a ocupação de uma estação de exercícios e realizar a contagem automática de repetições utilizando uma webcam.

As informações são transmitidas por meio do protocolo MQTT e apresentadas em um dashboard desenvolvido com Streamlit.

## Objetivo

Desenvolver um protótipo de estação inteligente de academia capaz de:

- Identificar alunos utilizando cartões RFID.
- Autorizar o acesso de alunos cadastrados.
- Controlar o estado da estação (Livre/Ocupada).
- Abrir a câmera durante a execução do exercício.
- Detectar movimentos corporais utilizando visão computacional.
- Contabilizar automaticamente as repetições.
- Enviar informações por MQTT.
- Apresentar os resultados em um dashboard.

## Tecnologias utilizadas

| Tecnologia | Utilização |
|---|---|
| ESP32 | Microcontrolador responsável pela leitura RFID e comunicação Wi-Fi |
| RFID RC522 | Leitura dos cartões de identificação |
| Arduino IDE | Desenvolvimento e upload do firmware |
| Python | Processamento e gerenciamento da estação |
| OpenCV | Captura e exibição da webcam |
| MediaPipe | Identificação dos pontos corporais |
| MQTT | Comunicação entre os componentes |
| PubSubClient | Cliente MQTT utilizado no ESP32 |
| Paho MQTT | Cliente MQTT utilizado no Python |
| Streamlit | Interface do dashboard |
| VS Code | Ambiente de desenvolvimento |

## Arquitetura da solução

O sistema utiliza uma arquitetura integrada entre hardware, comunicação MQTT e processamento em Python.

```text
          CARTÃO RFID
               |
               v
         RFID RC522
               |
               v
             ESP32
               |
           Wi-Fi
               |
               v
          BROKER MQTT
               |
               v
        ESTAÇÃO PYTHON
          /         \
         v           v
  IDENTIFICAÇÃO    WEBCAM
     DO ALUNO         |
         |            v
         |      OPENCV + MEDIAPIPE
         |            |
         |            v
         |      CONTAGEM DE REPS
         \           /
          \         /
           v       v
          BROKER MQTT
               |
               v
        DASHBOARD STREAMLIT
```

## Estrutura do projeto

```text
Smart-Gym-Cp5/
│
├── dashboard/
│   └── app.py
│
├── station/
│   └── estacao.py
│
├── models/
│   └── pose_landmarker_lite.task
│
├── teste_camera.py
├── teste_esp32_mqtt.py
├── requirements.txt
└── README.md
```

O firmware do ESP32 é desenvolvido e carregado pelo Arduino IDE.

Os arquivos de teste e `requirements.txt` podem ser adicionados conforme a organização final do projeto.

## Conexões do RFID RC522 com ESP32

| RFID RC522 | ESP32 |
|---|---|
| SDA / SS | GPIO 5 |
| SCK | GPIO 18 |
| MOSI | GPIO 23 |
| MISO | GPIO 19 |
| RST | GPIO 22 |
| 3.3V | 3V3 |
| GND | GND |
| IRQ | Não conectado |

**Atenção:** o módulo RC522 deve ser alimentado com 3,3 V.

## ⚙️ Funcionamento do sistema

### 1. Identificação por RFID

O aluno aproxima seu cartão RFID do leitor RC522.

O ESP32 realiza a leitura do UID e publica a identificação no broker MQTT.

Exemplo:

```json
{
  "uid": "999FEF97",
  "origem": "ESP32_WIFI"
}
```

### 2. Validação do aluno

A estação Python recebe o UID e verifica se ele está cadastrado.

Quando o cartão é reconhecido, a entrada é autorizada e a estação passa para o estado **Ocupada**.

### 3. Abertura da câmera

Após a identificação, o sistema abre a webcam utilizando OpenCV.

O MediaPipe Pose Landmarker identifica os pontos corporais necessários para acompanhar o movimento.

### 4. Contagem automática de repetições

A contagem considera o ângulo formado entre ombro, cotovelo e punho do braço direito.

O movimento esperado é:

**Braço estendido → Braço flexionado → Braço estendido**

Uma repetição é contabilizada quando o ciclo é concluído.

Os limites iniciais utilizados são:

- Braço flexionado: ângulo inferior a 50°.
- Braço estendido: ângulo superior a 160°.

Esses limites podem ser ajustados de acordo com o exercício e a posição da câmera.

### 5. Finalização do treino

O treino pode ser finalizado quando o aluno aproxima novamente o mesmo cartão RFID ou pressiona a tecla `Q` na janela da câmera.

A estação publica o total de repetições e retorna ao estado **Livre**.

### 6. Dashboard

O dashboard desenvolvido em Streamlit apresenta:

- Estado atual da estação.
- Aluno identificado.
- Total de repetições do último treino.
- Histórico de eventos e resultados recebidos.

## Comunicação MQTT

Broker utilizado no protótipo:

```text
3.135.234.101
```

Porta:

```text
1883
```

### Tópicos utilizados

| Tópico | Finalidade |
|---|---|
| `smartgym/ali/cp05/rfid` | Recebimento dos UIDs enviados pelo ESP32 |
| `smartgym/ali/cp05/status` | Publicação do estado Livre/Ocupada |
| `smartgym/ali/cp05/performance` | Publicação das repetições realizadas |

### Exemplo de mensagem de status

```json
{
  "status": "Ocupada",
  "aluno": "Ali Andrea"
}
```

### Exemplo de resultado do treino

```json
{
  "aluno": "Ali Andrea",
  "repeticoes": 12,
  "timestamp": "2026-10-19 15:30:00"
}
```

Os dados apresentados são exemplos ilustrativos do formato utilizado pelo sistema.

## Instalação e execução

### Pré-requisitos

- Python compatível com as bibliotecas utilizadas.
- Arduino IDE com suporte ao ESP32.
- ESP32 e leitor RFID RC522.
- Cartão ou tag RFID.
- Webcam funcional.
- Acesso à rede Wi-Fi e ao broker MQTT.

### 1. Clonar o repositório

```bash
git clone URL_DO_REPOSITORIO
cd Smart-Gym-Cp5
```

### 2. Criar um ambiente virtual

No Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Instalar as dependências

```powershell
python -m pip install opencv-python numpy paho-mqtt streamlit "mediapipe==0.10.35"
```

Versões utilizadas no ambiente de desenvolvimento:

- Python 3.14.6
- OpenCV 5.0.0
- MediaPipe 0.10.35

### 4. Configurar o modelo MediaPipe

Baixe o modelo oficial:

[Pose Landmarker Lite](https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task)

Salve em:

```text
models/pose_landmarker_lite.task
```

### 5. Configurar o ESP32

No Arduino IDE:

1. Selecionar a placa **ESP32 Dev Module**.
2. Selecionar a porta COM correspondente.
3. Configurar a rede Wi-Fi e o broker MQTT no firmware.
4. Realizar o upload.
5. Abrir o Serial Monitor em `115200 baud`.

A conexão e a leitura podem ser verificadas pelas mensagens:

```text
Wi-Fi conectado!
Conectando ao MQTT... conectado!
SMART GYM PRONTO!
Cartao identificado: 999FEF97
UID enviado ao MQTT!
```

**Segurança:** não publique senhas de Wi-Fi ou credenciais privadas no repositório.

### 6. Executar a estação

```powershell
python station/estacao.py
```

O terminal aguardará a leitura de um cartão RFID.

Após a identificação de um aluno cadastrado, a webcam será aberta para iniciar a contagem.

### 7. Executar o dashboard

Em outro terminal:

```powershell
python -m streamlit run dashboard/app.py
```

Acesse:

```text
http://localhost:8501
```

## 🧪 Testes

Os seguintes cenários fazem parte da validação do protótipo:

| Teste | Resultado esperado |
|---|---|
| Conexão do ESP32 ao Wi-Fi | Conexão estabelecida |
| Conexão ao MQTT | Cliente conectado |
| Leitura do cartão RFID | UID identificado |
| Envio do UID por MQTT | Mensagem recebida no Python |
| Cartão não cadastrado | Acesso não autorizado |
| Cartão cadastrado | Estação muda para Ocupada |
| Abertura da webcam | Imagem exibida |
| Execução do exercício | Repetições contabilizadas |
| Finalização do treino | Resultado publicado |
| Atualização do dashboard | Exibição do status e das repetições |

A leitura do cartão `999FEF97` e a comunicação MQTT foram verificadas durante o desenvolvimento. A validação completa da câmera, da contagem automática e do dashboard depende dos testes finais de integração.

## Considerações de segurança

O protótipo utiliza comunicação MQTT na porta 1883, sem configuração de criptografia no código apresentado.

Para uma implantação real, recomenda-se utilizar autenticação no broker, comunicação criptografada, armazenamento seguro de credenciais e controle de acesso aos dados dos alunos.


