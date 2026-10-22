"""Simple local recording/chat interface. Run: streamlit run app.py"""
import json
import tempfile
from pathlib import Path
import streamlit as st
from src.config import dataset_path
from src.llm import API
from src.retrieval import Index
from src.agent import Agent
from src.voice import Voice

st.set_page_config(page_title='ZentroMart VoiceOps', page_icon='🎙️')
st.title('ZentroMart support')
st.caption('AI assistant • Synthetic capstone data • Made by Aditya Singhal')

@st.cache_resource
def setup():
    data = dataset_path()
    api = API()
    return data,api,Index(data,api)

try:
    data,api,index = setup()
except Exception as exc:
    st.error(str(exc))
    st.stop()
if 'agent' not in st.session_state:
    st.session_state.agent = Agent(data,index,api)
    st.session_state.replies = []
if st.sidebar.button('New conversation'):
    st.session_state.agent = Agent(data,index,api)
    st.session_state.replies = []
    st.rerun()
st.sidebar.write('Dataset reference date: 20 October 2026')
listen = st.sidebar.selectbox('Listen in', ['en-IN','hi-IN','gu-IN','ta-IN','kn-IN','te-IN','mr-IN','bn-IN','ml-IN','pa-IN'])
speak = st.sidebar.selectbox('Speak in', ['en-IN','hi-IN','hi-en','gu-IN','ta-IN','kn-IN','te-IN','mr-IN','bn-IN','ml-IN','pa-IN'])
for r in st.session_state.replies:
    with st.chat_message('assistant'):
        st.write(r['answer'])
        if r.get('_audio'):
            st.audio(r['_audio'],format='audio/wav')
        with st.expander('Sources and tool actions'):
            st.json({k:v for k,v in r.items() if k!='_audio'})
text = st.chat_input('Ask about deliveries, returns or refunds')
audio = st.audio_input('Or record a short customer turn (up to 60 seconds)')
if st.button('Send recorded turn',disabled=audio is None) or text:
    try:
        with st.spinner('Listening and checking company documents…'):
            if text:
                result = st.session_state.agent.respond(text)
            else:
                voice = Voice()
                with tempfile.TemporaryDirectory() as tmp:
                    source,reply = Path(tmp)/'input.wav',Path(tmp)/'reply.wav'
                    source.write_bytes(audio.getvalue())
                    result = voice.turn(source,st.session_state.agent,reply,listen,speak)
                    result['_audio'] = reply.read_bytes()
            st.session_state.replies.append(result)
        st.rerun()
    except Exception:
        st.error('This turn failed. Check local configuration, key quota and network, then retry. No successful action is claimed.')
