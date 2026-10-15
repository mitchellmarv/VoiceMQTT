import json

import paho.mqtt.client as paho
import streamlit as st
from bokeh.models import CustomJS
from bokeh.models.widgets import Button
from PIL import Image
from streamlit_bokeh_events import streamlit_bokeh_events

st.set_page_config(page_title="Control por voz", page_icon="🪐", layout="centered")

# ------------------------------------------------------------------
# Estilos: morado profundo, estrellas y nebulosa, minimalista
# ------------------------------------------------------------------
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600&display=swap');

:root {
    --bg: #0B0618;
    --panel: #150C2B;
    --accent: #A78BFA;
    --accent-2: #C084FC;
    --text: #F1EBFF;
    --muted: #A99BCB;
    --line: rgba(167, 139, 250, 0.25);
}

/* Fondo: nebulosa + estrellas (todo con CSS, sin imágenes) */
.stApp {
    background-color: var(--bg);
    background-image:
        radial-gradient(900px 500px at 80% -10%, rgba(139,92,246,0.35), transparent 60%),
        radial-gradient(700px 500px at 0% 105%, rgba(192,132,252,0.18), transparent 60%),
        radial-gradient(1px 1px at 20px 30px, #fff, transparent),
        radial-gradient(1.5px 1.5px at 90px 120px, #e9ddff, transparent),
        radial-gradient(1px 1px at 160px 60px, #fff, transparent),
        radial-gradient(2px 2px at 210px 170px, #fff, transparent),
        radial-gradient(1px 1px at 60px 200px, #cbb8ff, transparent),
        radial-gradient(1px 1px at 250px 20px, #fff, transparent);
    background-size: auto, auto, 230px 230px, 310px 310px, 270px 270px, 410px 410px, 350px 350px, 290px 290px;
    background-attachment: fixed;
    color: var(--text);
    font-family: 'Sora', sans-serif;
}

[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 3rem; max-width: 640px; }

h1, h2, h3, p, label, li, span { font-family: 'Sora', sans-serif; }

h1 {
    font-weight: 600 !important;
    font-size: 1.9rem !important;
    letter-spacing: 0.02em;
    background: linear-gradient(90deg, #FFFFFF, var(--accent-2));
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
}
h3 {
    font-weight: 300 !important;
    color: var(--accent) !important;
    letter-spacing: 0.25em;
    font-size: 0.85rem !important;
    text-transform: uppercase;
}

/* Tarjetas */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(21, 12, 43, 0.8);
    border: 1px solid var(--line) !important;
    border-radius: 14px !important;
}

/* Instrucciones */
[data-testid="stExpander"] {
    background: rgba(21, 12, 43, 0.6);
    border: 1px solid var(--line);
    border-radius: 14px;
}
[data-testid="stExpander"] summary { color: var(--text); }

/* Imagen */
[data-testid="stImage"] img {
    border-radius: 50%;
    border: 1px solid var(--line);
    box-shadow: 0 0 30px rgba(139,92,246,0.45);
}

/* El botón de Bokeh vive en un iframe: se deja transparente y se
   desplaza su color azul hacia morado con un filtro. */
iframe {
    color-scheme: normal;
    background: transparent;
    filter: hue-rotate(60deg) saturate(1.1);
}

/* Alertas */
[data-testid="stAlert"] {
    background: rgba(21, 12, 43, 0.85);
    border: 1px solid var(--line);
    border-radius: 12px;
    color: var(--text);
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ---------- Configuración MQTT (igual que en el ESP32 de Wokwi) ----------
BROKER = "broker.mqttdashboard.com"
PORT = 1883
# Distinto al ID del ESP32 ("Lizalda"): si fueran iguales, el broker
# desconectaría a uno de los dos cada vez que el otro entrara.
CLIENT_ID = "Lizalda_App"
TOPIC_VOICE = "lizalda/voice_ctrl"


def crear_cliente():
    """Compatible con paho-mqtt 1.x y 2.x."""
    try:
        return paho.Client(paho.CallbackAPIVersion.VERSION1, CLIENT_ID)
    except AttributeError:
        return paho.Client(CLIENT_ID)


def publicar(texto):
    """Conecta, publica, espera confirmación y se desconecta."""
    try:
        client = crear_cliente()
        client.connect(BROKER, PORT, keepalive=30)
        client.loop_start()
        info = client.publish(TOPIC_VOICE, json.dumps({"Act1": texto}))
        info.wait_for_publish(timeout=5)
        client.loop_stop()
        client.disconnect()
        st.success("Comando enviado")
    except Exception as e:
        st.error(f"No se pudo enviar: {e}")


# ------------------------------------------------------------------
# Interfaz
# ------------------------------------------------------------------
st.title("Interfaces multimodales")
st.subheader("Control por voz")

with st.expander("Instrucciones de uso", expanded=True):
    st.markdown(
        """
1. **Inicia la simulación en Wokwi** y espera a que el monitor serial muestre
   *conectado*.
2. **Usa Chrome o Edge.** El reconocimiento de voz no funciona en todos los navegadores.
3. Presiona **Inicio**, acepta el permiso del micrófono y **habla en español**.
4. Comandos disponibles:
   - *"Enciende las luces"* → enciende el LED
   - *"Apaga las luces"* → apaga el LED
   - *"Abre la puerta"* → servo a 180°
   - *"Cierra la puerta"* → servo a 90°
5. Verás el texto reconocido y el aviso **Comando enviado**. El monitor serial
   de Wokwi mostrará el comando recibido.

*Si no reacciona, revisa que la simulación siga activa y habla con frases cortas y claras.*
        """
    )

try:
    image = Image.open("voice_ctrl.jpg")
    col_a, col_b, col_c = st.columns([1, 1, 1])
    with col_b:
        st.image(image, use_container_width=True)
except Exception:
    pass

st.write("Toca el botón y habla")

stt_button = Button(label="🎙 Inicio", width=200)

stt_button.js_on_event("button_click", CustomJS(code="""
    var recognition = new webkitSpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'es-ES';

    recognition.onresult = function (e) {
        var value = "";
        for (var i = e.resultIndex; i < e.results.length; ++i) {
            if (e.results[i].isFinal) {
                value += e.results[i][0].transcript;
            }
        }
        if ( value != "") {
            document.dispatchEvent(new CustomEvent("GET_TEXT", {detail: value}));
        }
    }
    recognition.start();
    """))

result = streamlit_bokeh_events(
    stt_button,
    events="GET_TEXT",
    key="listen",
    refresh_on_update=False,
    override_height=75,
    debounce_time=0)

if result and "GET_TEXT" in result:
    texto = result.get("GET_TEXT").strip()
    with st.container(border=True):
        st.markdown(f"**Escuché:** {texto}")
        publicar(texto)
