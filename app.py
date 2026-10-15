import json

import paho.mqtt.client as paho
import streamlit as st
from bokeh.models import CustomJS
from bokeh.models.widgets import Button
from PIL import Image
from streamlit_bokeh_events import streamlit_bokeh_events

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


st.title("INTERFACES MULTIMODALES")
st.subheader("CONTROL POR VOZ")

try:
    image = Image.open("voice_ctrl.jpg")
    st.image(image, width=200)
except Exception as e:
    st.warning(f"No se pudo cargar la imagen: {e}")

st.write("Toca el Botón y habla ")

stt_button = Button(label=" Inicio ", width=200)

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
    st.write(texto)
    publicar(texto)
