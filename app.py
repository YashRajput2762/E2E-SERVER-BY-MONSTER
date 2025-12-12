import streamlit as st
from cryptography.fernet import Fernet
import base64
import json
from datetime import datetime

# ऐप टाइटल और डिस्क्रिप्शन
st.set_page_config(page_title="E2EE Offline Server", page_icon="🔒")
st.title("🔒 E2EE Offline Messaging Server")
st.write("ऑफलाइन E2EE चैट—Shared Key से मैसेज सिक्योर भेजो। रीयल-टाइम अपडेट, सब लोकल!")

# साइडबार: Key Management (Shared for both users)
with st.sidebar:
    st.header("🔑 Shared Key Setup")
    if 'shared_key' not in st.session_state:
        st.session_state.shared_key = None
        st.session_state.key_b64 = None
    
    key_option = st.selectbox("Key Option:", ["1. Generate New Key", "2. Load Existing Key"])
    
    if key_option == "1. Generate New Key":
        if st.button("Generate Key", type="primary"):
            st.session_state.shared_key = Fernet.generate_key()
            st.session_state.key_b64 = base64.urlsafe_b64encode(st.session_state.shared_key).decode()
            st.success("Key Generated! इसे दूसरे user/device को share करो।")
        if st.session_state.key_b64:
            st.code(st.session_state.key_b64, language="text")
            st.info("Copy this key for sharing.")
    else:
        custom_key = st.text_area("Paste Shared Key (Base64):", height=100)
        if st.button("Load Key") and custom_key:
            try:
                st.session_state.shared_key = base64.urlsafe_b64decode(custom_key)
                st.session_state.key_b64 = custom_key
                st.success("Key Loaded Successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Invalid Key: {str(e)}")

# Check if key is set
if not st.session_state.shared_key:
    st.warning("⚠️ पहले Sidebar से Key Generate या Load करो!")
    st.stop()

f = Fernet(st.session_state.shared_key)

# Messages storage (encrypted in session state - offline)
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'counter' not in st.session_state:
    st.session_state.counter = 0

# Main Chat Interface: Two columns for Users A & B
col1, col2 = st.columns(2, gap="medium")

# User A Panel
with col1:
    st.header("👤 User A")
    # Input for User A
    msg_a = st.text_input("Type your message:", placeholder="Enter message to send...")
    if st.button("📤 Send (User A)", type="secondary") and msg_a.strip():
        timestamp = datetime.now().strftime("%H:%M:%S")
        enc_msg = f.encrypt(f"User A: {msg_a}".encode())
        enc_b64 = base64.urlsafe_b64encode(enc_msg).decode()
        st.session_state.messages.append({
            'user': 'A',
            'enc_msg': enc_b64,
            'timestamp': timestamp
        })
        st.session_state.counter += 1
        st.success("Message Sent!")
        st.rerun()

    # Display messages for User A (only outgoing, but full history below)
    st.subheader("📝 Your Messages:")
    for msg in st.session_state.messages:
        if msg['user'] == 'A':
            try:
                dec_msg = f.decrypt(base64.urlsafe_b64decode(msg['enc_msg'])).decode()
                st.write(f"**Sent:** {dec_msg} ({msg['timestamp']})")
            except:
                st.write(f"**Sent:** [Decryption Error] ({msg['timestamp']})")

# User B Panel
with col2:
    st.header("👤 User B")
    # Input for User B
    msg_b = st.text_input("Type your message:", placeholder="Enter message to send...")
    if st.button("📤 Send (User B)", type="secondary") and msg_b.strip():
        timestamp = datetime.now().strftime("%H:%M:%S")
        enc_msg = f.encrypt(f"User B: {msg_b}".encode())
        enc_b64 = base64.urlsafe_b64encode(enc_msg).decode()
        st.session_state.messages.append({
            'user': 'B',
            'enc_msg': enc_b64,
            'timestamp': timestamp
        })
        st.session_state.counter += 1
        st.success("Message Sent!")
        st.rerun()

    # Display messages for User B
    st.subheader("📝 Your Messages:")
    for msg in st.session_state.messages:
        if msg['user'] == 'B':
            try:
                dec_msg = f.decrypt(base64.urlsafe_b64decode(msg['enc_msg'])).decode()
                st.write(f"**Sent:** {dec_msg} ({msg['timestamp']})")
            except:
                st.write(f"**Sent:** [Decryption Error] ({msg['timestamp']})")

# Shared Full Chat History (visible to both - simulates received messages)
st.header("💬 Full Encrypted Chat History")
st.write("*सभी messages यहां दिखेंगे (decrypted if key correct). Refresh पर persist नहीं—export for multi-device.*")
chat_container = st.container()
with chat_container:
    if st.session_state.messages:
        for msg in sorted(st.session_state.messages, key=lambda x: x['timestamp']):
            try:
                dec_msg = f.decrypt(base64.urlsafe_b64decode(msg['enc_msg'])).decode()
                user_icon = "🟢" if msg['user'] == 'A' else "🔴"
                st.write(f"{user_icon} **{dec_msg}**  _{msg['timestamp']}_")
            except:
                st.error(f"**{msg['user']}:** [Can't Decrypt - Check Key] ({msg['timestamp']})")
    else:
        st.info("कोई message नहीं। Send करके शुरू करो!")

# Export/Import for Multi-Device (Offline Sync)
st.header("🔄 Sync History (Multi-Device)")
col_exp, col_imp = st.columns(2)
with col_exp:
    export_data = {
        'key_b64': st.session_state.key_b64,
        'messages': st.session_state.messages
    }
    st.download_button(
        label="📥 Export Chat (JSON)",
        data=json.dumps(export_data, indent=2),
        file_name="e2ee_chat_backup.json",
        mime="application/json"
    )
with col_imp:
    uploaded_file = st.file_uploader("📤 Import Chat JSON", type="json")
    if uploaded_file:
        try:
            data = json.load(uploaded_file)
            st.session_state.messages = data['messages']
            if data.get('key_b64') != st.session_state.key_b64:
                st.warning("Key mismatch—using current key for decryption.")
            st.success("History Imported! Check chat above.")
            st.rerun()
        except Exception as e:
            st.error(f"Import Error: {str(e)}")

# Footer Info
st.info("""
**कैसे काम करता है?**
- Key share करके दोनों users setup करो (same key both sides).
- Messages encrypt होकर store होते हैं—केवल correct key से decrypt.
- Offline: सब browser session में। Multi-device: Export/Import use करो.
- Real-time: Send पर auto-update।
Deploy: GitHub पर push करके streamlit.io पर host—URL वैसा ही मिलेगा!

अगर issue: Terminal में error बताओ।
""")
