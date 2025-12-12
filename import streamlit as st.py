import streamlit as st
from PIL import Image
import io

st.set_page_config(page_title="Gerar PDF com imagens", layout="centered")

st.title("📄 Gerar PDF a partir de imagens")
st.write("Envie imagens, defina a ordem e rotacione se necessário.")

uploaded_files = st.file_uploader(
    "Selecione os arquivos",
    accept_multiple_files=True
)

if uploaded_files:
    st.subheader("📑 Organização das imagens")

    files_config = []

    for i, file in enumerate(uploaded_files):
        st.markdown("---")

        col1, col2 = st.columns([2, 2])

        with col1:
            st.write(f"**Arquivo:** {file.name}")

            order = st.number_input(
                "Ordem no PDF",
                min_value=1,
                value=i + 1,
                key=f"order_{file.name}"
            )

            rotation = st.selectbox(
                "Rotação",
                options=[0, 90, 180, 270],
                format_func=lambda x: f"{x}°",
                key=f"rot_{file.name}"
            )

        with col2:
            try:
                img_preview = Image.open(file)
                if rotation != 0:
                    img_preview = img_preview.rotate(-rotation, expand=True)
                st.image(img_preview, use_container_width=True)
            except:
                st.warning("Não foi possível visualizar este arquivo")

        files_config.append((order, rotation, file))

    if st.button("📄 Gerar PDF"):
        files_config.sort(key=lambda x: x[0])

        images = []

        for order, rotation, file in files_config:
            try:
                img = Image.open(file).convert("RGB")
                if rotation != 0:
                    img = img.rotate(-rotation, expand=True)
                images.append(img)
            except Exception as e:
                st.error(f"Erro ao processar {file.name}: {e}")
                st.stop()

        if images:
            pdf_buffer = io.BytesIO()

            images[0].save(
                pdf_buffer,
                format="PDF",
                save_all=True,
                append_images=images[1:]
            )

            pdf_buffer.seek(0)

            st.success("✅ PDF gerado com sucesso!")

            st.download_button(
                "⬇️ Baixar PDF",
                data=pdf_buffer,
                file_name="arquivo_final.pdf",
                mime="application/pdf"
            )
