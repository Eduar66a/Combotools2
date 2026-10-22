import streamlit as st
import re
import io
import zipfile

# Configuración de página adaptada a móviles
st.set_page_config(
    page_title="ComboTool MWCMD 🥷",
    page_icon="🥷",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Inicializar estado en memoria
if "combo_lines" not in st.session_state:
    st.session_state.combo_lines = []

st.title("ComboTool MWCMD 🥷")

# Enlaces de la comunidad
col_links1, col_links2, col_links3 = st.columns(3)
with col_links1:
    st.link_button("📸 Instagram", "https://instagram.com/mwsers", use_container_width=True)
with col_links2:
    st.link_button("💬 Telegram", "https://t.me/mwcmd", use_container_width=True)
with col_links3:
    st.link_button("🌐 Academia", "https://academia.mwcmd.com/login", use_container_width=True)

st.divider()

# Subida de archivos (múltiple)
uploaded_files = st.file_uploader(
    "Sube tus archivos .txt de combo", 
    type=["txt"], 
    accept_multiple_files=True
)

if uploaded_files:
    if st.button("📥 Procesar Archivos Subidos", use_container_width=True):
        loaded = []
        for file in uploaded_files:
            content = file.read().decode("utf-8", errors="ignore")
            loaded.extend(content.splitlines())
        st.session_state.combo_lines = loaded
        st.success(f"{len(uploaded_files)} archivo(s) cargado(s). Total líneas: {len(loaded)}")

# Métricas actuales
total_lines = len(st.session_state.combo_lines)
st.metric(label="Líneas en memoria", value=total_lines)

if total_lines > 0:
    st.subheader("Herramientas de Limpieza")
    
    col1, col2 = st.columns(2)
    
    # Eliminar Vacíos
    with col1:
        if st.button("🗑️ Eliminar Vacíos", use_container_width=True):
            prev = len(st.session_state.combo_lines)
            st.session_state.combo_lines = [l for l in st.session_state.combo_lines if l.strip()]
            st.info(f"Se eliminaron {prev - len(st.session_state.combo_lines)} líneas vacías.")
            st.rerun()

    # Eliminar Duplicados
    with col2:
        if st.button("✂️ Eliminar Duplicados", use_container_width=True):
            prev = len(st.session_state.combo_lines)
            st.session_state.combo_lines = list(dict.fromkeys(st.session_state.combo_lines))
            st.info(f"Se eliminaron {prev - len(st.session_state.combo_lines)} duplicados.")
            st.rerun()

    col3, col4 = st.columns(2)

    # Extraer Email:Pass
    with col3:
        if st.button("📧 Extraer Email:Pass", use_container_width=True):
            extracted = []
            for line in st.session_state.combo_lines:
                line_str = line.strip()
                if not line_str.lower().startswith("http") and ":" in line_str:
                    parts = line_str.split(":", 1)
                    user_part, pass_part = parts[0].strip(), parts[1].strip()
                    if user_part.count("@") == 1 and pass_part:
                        extracted.append(f"{user_part}:{pass_part.split()[0]}")
            st.session_state.combo_lines = extracted
            st.info(f"{len(extracted)} líneas tipo email:pass listas.")
            st.rerun()

    # Extraer User:Pass
    with col4:
        if st.button("👤 Extraer User:Pass", use_container_width=True):
            extracted = []
            for line in st.session_state.combo_lines:
                line_str = line.strip()
                if ":" in line_str:
                    parts = line_str.split(":", 1)
                    user_part, pass_part = parts[0].strip(), parts[1].strip()
                    if "@" not in user_part and user_part and pass_part:
                        extracted.append(f"{user_part}:{pass_part.split()[0]}")
            st.session_state.combo_lines = extracted
            st.info(f"{len(extracted)} líneas tipo user:pass listas.")
            st.rerun()

    col5, col6 = st.columns(2)

    # Ordenar alfabéticamente
    with col5:
        if st.button("🔤 Ordenar A-Z", use_container_width=True):
            st.session_state.combo_lines.sort()
            st.info("Ordenado alfabéticamente.")
            st.rerun()

    # Reset
    with col6:
        if st.button("🔄 Reiniciar Todo", type="secondary", use_container_width=True):
            st.session_state.combo_lines = []
            st.rerun()

    # Filtrar por palabra clave (Regex avanzado)
    st.markdown("---")
    st.markdown("#### Filtrar por Palabra Clave")
    keyword = st.text_input("Ingresa la palabra clave (ej: netflix, canalplus):")
    
    if st.button("🔍 Filtrar", use_container_width=True):
        if keyword.strip():
            kw_clean = keyword.strip().lower()
            filtered = []
            regex_email = r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)'
            compiled_patterns = [
                re.compile(f'{regex_email}:([^\\s]+)'),
                re.compile(f'https?://[^ ]*({regex_email}):([^\\s]+)'),
                re.compile(f'email=({regex_email})[& ]+pass=([^\\s&]+)', re.IGNORECASE),
                re.compile(f'correo=({regex_email})[^\\n]*password=([^\\s&]+)', re.IGNORECASE),
                re.compile(f'{regex_email}\\|([^\\s]+)')
            ]

            for line in st.session_state.combo_lines:
                line_str = line.strip()
                if kw_clean in line_str.lower():
                    matched = False
                    for pattern in compiled_patterns:
                        m = pattern.search(line_str)
                        if m:
                            filtered.append(f"{m.group(1)}:{m.group(2)}")
                            matched = True
                            break
                    if not matched and ":" in line_str:
                        filtered.append(line_str)

            if filtered:
                st.session_state.combo_lines = filtered
                st.success(f"{len(filtered)} coincidencias encontradas.")
                st.rerun()
            else:
                st.warning(f"No se encontró ninguna línea con '{keyword}'.")

    # Separar por Dominio (Descarga como ZIP)
    st.markdown("---")
    st.markdown("#### Separar por Dominio")
    if st.button("📦 Generar ZIP por Dominios", use_container_width=True):
        domains = {}
        for line in st.session_state.combo_lines:
            if ":" in line and "@" in line:
                try:
                    user_part = line.split(":", 1)[0]
                    domain = user_part.split("@")[1].strip().lower()
                    clean_domain = re.sub(r'[\\/*?:"<>|]', '', domain)
                    if clean_domain:
                        domains.setdefault(clean_domain, []).append(line)
                except Exception:
                    continue

        if domains:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for dom, lines in domains.items():
                    zip_file.writestr(f"{dom}.txt", "\n".join(lines))
            
            st.download_button(
                label="⬇️ Descargar Dominios (.zip)",
                data=zip_buffer.getvalue(),
                file_name="dominios_separados.zip",
                mime="application/zip",
                use_container_width=True
            )
        else:
            st.warning("No se encontraron emails válidos para separar.")

    # Descarga directa del resultado actual
    st.markdown("---")
    st.markdown("#### Resultado Final")
    result_text = "\n".join(st.session_state.combo_lines)
    
    st.download_button(
        label="💾 Descargar Combo Limpio (.txt)",
        data=result_text,
        file_name="combo_limpio.txt",
        mime="text/plain",
        type="primary",
        use_container_width=True
    )

    with st.expander("👁️ Ver primeras 200 líneas"):
        st.text("\n".join(st.session_state.combo_lines[:200]))
