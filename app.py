import streamlit as st
import base64
from cryptography.fernet import Fernet
import json
from datetime import datetime

st.set_page_config(page_title="E2EE Offline Server", page_icon="🔒")
st.title("E2EE Offline Messaging Server")
st.caption("Shared key से सिक्योर मैसेजिंग — सब ऑफलाइन, कोई सर्वर नहीं")

# ====================== Key Setup ======================
if 'shared_key' not in st.session_state:
    st.session_state.shared_key = None
    st.session_state.key_b64 = None

with st.sidebar:
    st.header("Shared Key")
    option = st.radio("Key Option", ["Generate New Key", "Load Existing Key"])

    if option == "Generate New Key":
        if st.button("Generate Key", type="primary"):
            st.session_state.shared_key = Fernet.generate_key()
            st.session_state.key_b64 = base64.urlsafe_b64encode(st.session_state.shared_key).decode()
            st.success("Key generated!")
        if st.session_state.key_b64:
            st.code(st.session_state.key_b64)
    else:
        key_input = st.text_area("Paste key here")
        if st.button("Load Key") and key_input:
            try:
                st.session_state.shared_key = base64.urlsafe_b64decode(key_input)
                st.session_state.key_b64 = key_input
                st.success("Key loaded!")
                st.rerun()
            except:
                st.error("Invalid key")

if not st.session_state.shared_key:
    st.warning("पहले key generate या load करो")
    st.stop()

f = Fernet(st.session_state.shared_key)

# ====================== Messages Storage ======================
if 'messages' not in st.session_state:
    st.session_state.messages = []

# ====================== UI ======================
col1, col2 = st.columns(2)

with col1:
    st.header("User A")
    msg_a = st.text_input("Message भेजो (User A)", key="input_a", placeholder="Type here...")
    if st.button("Send →", key="send_a") and msg_a.strip():
        enc = f.encrypt(f"A: {msg_a}".encode())
        b64 = base64.urlsafe_b64encode(enc).decode()
        st.session_state.messages.append({"user": "A", "data": b64, "time": datetime.now().strftime("%H:%M")})
        st.success("Sent!")
        st.rerun()

with col2:
    st.header("User B")
    msg_b = st.text_input("Message भेजो (User B)", key="input_b", placeholder="Type here...")
    if st.button("Send →", key="send_b") and msg_b.strip():
        enc = f.encrypt(f"B: {msg_b}".encode())
        b64 = base64.urlsafe_b64encode(enc).decode()
        st.session_state.messages.append({"user": "B", "data": b64, "time": datetime.now().strftime("%H:%M")})
        st.success("Sent!")
        st.rerun()

# ====================== Chat Display ======================
st.markdown("### Live Chat")
for m in st.session_state.messages:
    try:
        decrypted = f.decrypt(base64.urlsafe_b64decode(m["data"])).decode()
        if m["user"] == "A":
            st.success(f"**A** → {decrypted}  _{m['time']}_")
        else:
            st.info(f"**B** → {decrypted}  _{m['time']}_")
    except:
        st.error(f"**{m['user']}**: गलत key — मैसेज नहीं पढ़ सकते")

# ====================== Export / Import ======================
st.markdown("### Sync (Multi-device)")
c1, c2 = st.columns(2)
with c1:
    data = {"key": st.session_state.key_b64, "msgs": st.session_state.messages}
    st.download_button("Export Chat", json.dumps(data), "e2ee_chat.json", "application/json")
with c2:
    uploaded = st.file_uploader("Import Chat", type="json")
    if uploaded:
        d = json.load(uploaded)
        st.session_state.messages = d["msgs"]
        st.session_state.key_b64 = d["key"]
        st.session_state.shared_key = base64.urlsafe_b64decode(d["key"])
        f = Fernet(st.session_state.shared_key)
        st.success("Chat imported!")
        st.rerun()

st.caption("Key = पासवर्ड। इसे किसी के साथ शेयर करो, मैसेज अपने आप सिक्योर हो जाएंगे।")
