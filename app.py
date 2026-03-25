import streamlit as st
import gspread
import uuid
import requests
import time
from datetime import datetime
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="All the best, Anka!", page_icon="🎉", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    .message-card {
        background: white;
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        border-left: 5px solid #667eea;
        transition: transform 0.2s;
    }
    .message-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
    }
    .message-name {
        font-weight: bold;
        color: #667eea;
        font-size: 1.1em;
    }
    .message-text {
        margin-top: 10px;
        font-size: 1em;
        line-height: 1.6;
    }
    .header-container {
        text-align: center;
        padding: 20px 0;
    }
    .message-count {
        text-align: center;
        color: #667eea;
        font-size: 1.2em;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

GIPHY_API_KEY = st.secrets["giphy"]["api_key"]


@st.cache_resource
def get_gsheet_connection():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
    )
    client = gspread.authorize(credentials)
    sheet = client.open_by_key(st.secrets["spreadsheet"]["id"]).sheet1
    return sheet


def load_messages():
    try:
        sheet = get_gsheet_connection()
        records = sheet.get_all_records()
        return records
    except Exception:
        return []


def add_message(name, message, gif_url=None):
    try:
        sheet = get_gsheet_connection()
        sheet.append_row([
            str(uuid.uuid4()),
            name,
            message,
            gif_url or "",
            datetime.now().strftime("%d.%m.%Y %H:%M")
        ])
    except Exception as e:
        st.error(f"Could not save message: {e}")


def delete_message(msg_id):
    try:
        sheet = get_gsheet_connection()
        records = sheet.get_all_records()
        for i, record in enumerate(records):
            if record.get("id") == msg_id:
                sheet.delete_rows(i + 2)
                break
    except Exception as e:
        st.error(f"Could not delete message: {e}")

def update_message(msg_id, new_name, new_message):
    try:
        sheet = get_gsheet_connection()
        records = sheet.get_all_records()
        for i, record in enumerate(records):
            if record.get("id") == msg_id:
                sheet.update_cell(i + 2, 2, new_name)
                sheet.update_cell(i + 2, 3, new_message)
                break
    except Exception as e:
        st.error(f"Could not update message: {e}")

def search_gifs(query, limit=12):
    try:
        url = "https://api.giphy.com/v1/gifs/search"
        params = {
            "api_key": GIPHY_API_KEY,
            "q": query,
            "limit": limit,
            "rating": "g"
        }
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return [
                {
                    "preview": g["images"]["fixed_height_small"]["url"],
                    "full": g["images"]["fixed_height"]["url"],
                    "title": g.get("title", "")
                }
                for g in data["data"]
            ]
    except Exception:
        pass
    return []


def export_to_html(messages):
    html = """
    <html>
    <head>
        <meta charset="utf-8">
        <title>All the best, Marie! 🎉</title>
        <style>
            body {
                font-family: 'Segoe UI', Arial, sans-serif;
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                min-height: 100vh;
                margin: 0;
                padding: 20px;
            }
            .header { text-align: center; padding: 40px 0; }
            .header h1 { font-size: 2.5em; color: #333; }
            .header p { color: #667eea; font-size: 1.3em; font-weight: bold; }
            .board {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 20px;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }
            .card {
                background: white;
                border-radius: 15px;
                padding: 20px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                border-left: 5px solid #667eea;
                transition: transform 0.2s;
            }
            .card:hover {
                transform: translateY(-3px);
                box-shadow: 0 6px 12px rgba(0,0,0,0.15);
            }
            .card-name { font-weight: bold; color: #667eea; font-size: 1.1em; }
            .card-message { margin-top: 10px; line-height: 1.6; }
            .card img { width: 100%; border-radius: 10px; margin-top: 10px; }
            @media (max-width: 768px) { .board { grid-template-columns: 1fr; } }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>All the best, Marie! 🎉</h1>
            <p>💌 MESSAGECOUNT messages from the team</p>
        </div>
        <div class="board">
    """
    html = html.replace("MESSAGECOUNT", str(len(messages)))

    for msg in messages:
        gif_html = ""
        gif_val = msg.get("gif", "")
        if gif_val:
            gif_html = f'<img src="{gif_val}" alt="GIF">'
        html += f"""
            <div class="card">
                <div class="card-name">{msg["name"]}</div>
                <div class="card-message">{msg["message"]}</div>
                {gif_html}
            </div>
        """

    html += "</div></body></html>"
    return html


# Session state
if "selected_gif" not in st.session_state:
    st.session_state.selected_gif = None
if "gif_results" not in st.session_state:
    st.session_state.gif_results = []

# Header
st.markdown("<div class='header-container'>", unsafe_allow_html=True)
st.title("All the best, Marie! 🎉")
st.markdown("### Leave your farewell message 💬")
st.markdown("</div>", unsafe_allow_html=True)

# Message count
messages = load_messages()
st.markdown(
    f"<div class='message-count'>💌 {len(messages)} message{'s' if len(messages) != 1 else ''} so far</div>",
    unsafe_allow_html=True
)

st.divider()

# Name and message
name = st.text_input("Your name")
message = st.text_area("Your message for Marie")

# GIF search
st.markdown("**Add a GIF (optional)**")

gif_col1, gif_col2 = st.columns([3, 1])
with gif_col1:
    gif_search = st.text_input("Search GIFs", placeholder="e.g. goodbye, good luck, thank you, party...")
with gif_col2:
    st.markdown("<br>", unsafe_allow_html=True)
    search_clicked = st.button("🔍 Search", width="stretch")

if search_clicked and gif_search.strip():
    st.session_state.gif_results = search_gifs(gif_search.strip())
    st.session_state.selected_gif = None

# Quick searches
st.markdown("**Quick searches:**")
quick_cols = st.columns(6)
quick_searches = ["👋 Goodbye", "🍀 Good Luck", "🎉 Celebration", "🫶 Thank You", "😂 Funny", "💐 Flowers"]
for i, label in enumerate(quick_searches):
    with quick_cols[i]:
        if st.button(label, width="stretch"):
            st.session_state.gif_results = search_gifs(label)
            st.session_state.selected_gif = None

# GIF results
if st.session_state.gif_results:
    st.markdown("**Pick a GIF:**")
    gif_cols = st.columns(4)
    for i, gif in enumerate(st.session_state.gif_results):
        with gif_cols[i % 4]:
            st.image(gif["preview"], width="stretch")
            if st.button("Select", key=f"gif_{i}", width="stretch"):
                st.session_state.selected_gif = gif["full"]
                st.rerun()

# Selected GIF preview
if st.session_state.selected_gif:
    st.markdown("**Selected GIF:**")
    preview_col1, preview_col2 = st.columns([1, 3])
    with preview_col1:
        st.image(st.session_state.selected_gif, width=200)
    with preview_col2:
        if st.button("❌ Remove GIF"):
            st.session_state.selected_gif = None
            st.rerun()

# Submit
st.divider()
if st.button("Add message 🎉", type="primary", width="stretch"):
    if name.strip() and message.strip():
        try:
            add_message(name.strip(), message.strip(), st.session_state.selected_gif)
            st.session_state.selected_gif = None
            st.session_state.gif_results = []
            st.cache_resource.clear()
            st.success("Thank you for your message! 🙏")
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error(f"Something went wrong: {e}")
    else:
        st.warning("Please fill in both your name and message.")

# Display messages
st.divider()
st.markdown("### 💌 Messages")

if messages:
    cols = st.columns(3)
    for i, msg in enumerate(reversed(messages)):
        with cols[i % 3]:
            gif_html = ""
            gif_val = msg.get("gif", "")
            if gif_val:
                gif_html = f'<img src="{gif_val}" style="width:100%; border-radius:10px; margin-top:10px;">'
            st.markdown(f"""
                <div class="message-card">
                    <div class="message-name">{msg["name"]}</div>
                    <div class="message-text">{msg["message"]}</div>
                    {gif_html}
                </div>
            """, unsafe_allow_html=True)
else:
    st.markdown(
        "<p style='text-align:center; color:#999; font-size:1.2em;'>No messages yet – be the first! ✨</p>",
        unsafe_allow_html=True
    )

# Admin
st.divider()
with st.expander("⚙️ Admin"):
    if messages:
        # Initialize edit state
        if "editing_id" not in st.session_state:
            st.session_state.editing_id = None

        st.markdown("**Manage messages:**")
        for msg in reversed(messages):
            msg_id = msg.get("id", msg["timestamp"])

            # Editing mode
            if st.session_state.editing_id == msg_id:
                st.markdown("---")
                st.markdown("**✏️ Editing message:**")
                edited_name = st.text_input("Name", value=msg["name"], key=f"edit_name_{msg_id}")
                edited_message = st.text_area("Message", value=msg["message"], key=f"edit_msg_{msg_id}")

                save_col, cancel_col = st.columns(2)
                with save_col:
                    if st.button("💾 Save", key=f"save_{msg_id}", width="stretch"):
                        if edited_name.strip() and edited_message.strip():
                            update_message(msg_id, edited_name.strip(), edited_message.strip())
                            st.session_state.editing_id = None
                            st.cache_resource.clear()
                            st.rerun()
                        else:
                            st.warning("Name and message cannot be empty.")
                with cancel_col:
                    if st.button("❌ Cancel", key=f"cancel_{msg_id}", width="stretch"):
                        st.session_state.editing_id = None
                        st.rerun()
                st.markdown("---")

            # Normal display mode
            else:
                col1, col2, col3 = st.columns([4, 0.5, 0.5])
                with col1:
                    st.markdown(
                        f"**{msg['name']}** – _{str(msg['message'])[:50]}{'...' if len(str(msg['message'])) > 50 else ''}_")
                with col2:
                    if st.button("✏️", key=f"edit_{msg_id}"):
                        st.session_state.editing_id = msg_id
                        st.rerun()
                with col3:
                    if st.button("🗑️", key=f"del_{msg_id}"):
                        delete_message(msg_id)
                        st.cache_resource.clear()
                        st.rerun()

        st.divider()
        st.markdown("**Export board:**")
        html_export = export_to_html(messages)
        st.download_button(
            label="📥 Export as HTML (with animated GIFs)",
            data=html_export,
            file_name="farewell_marie.html",
            mime="text/html",
            width="stretch"
        )

        st.divider()
        if st.button("🗑️ Clear ALL messages", type="primary"):
            sheet = get_gsheet_connection()
            sheet.clear()
            sheet.append_row(["id", "name", "message", "gif", "timestamp"])
            st.cache_resource.clear()
            st.rerun()
    else:
        st.info("No messages to manage.")
