import streamlit as st
from PIL import Image
import io
from pypdf import PdfReader, PdfWriter
import fitz  # pymupdf

st.set_page_config(page_title="Ferramentas de PDF", layout="centered")

st.title("📄 Ferramentas de PDF")

aba_imagens, aba_pdfs = st.tabs(["🖼️ Imagens → PDF", "📚 Juntar PDFs"])

# ---------------- ABA 1: IMAGENS -> PDF ----------------
with aba_imagens:
    st.write("Envie imagens, defina a ordem e rotacione se necessário.")

    uploaded_files = st.file_uploader(
        "Selecione os arquivos",
        accept_multiple_files=True,
        type=["png", "jpg", "jpeg", "webp", "bmp", "tiff"],
        key="uploader_imgs"
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
                    key=f"order_img_{i}"
                )

                rotation = st.selectbox(
                    "Rotação",
                    options=[0, 90, 180, 270],
                    format_func=lambda x: f"{x}°",
                    key=f"rot_img_{i}"
                )

            with col2:
                try:
                    file.seek(0)
                    img_preview = Image.open(file)
                    if rotation != 0:
                        img_preview = img_preview.rotate(-rotation, expand=True)
                    st.image(img_preview, use_container_width=True)
                except Exception:
                    st.warning("Não foi possível visualizar este arquivo")

            files_config.append((order, rotation, file))

        if st.button("📄 Gerar PDF", key="btn_gerar_img"):
            files_config.sort(key=lambda x: x[0])
            images = []

            for order, rotation, file in files_config:
                try:
                    file.seek(0)
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

# ---------------- ABA 2: JUNTAR PDFS (por página) ----------------
with aba_pdfs:
    st.write("Envie um ou mais PDFs. Cada página pode ser ordenada e rotacionada individualmente.")

    uploaded_pdfs = st.file_uploader(
        "Selecione os PDFs",
        accept_multiple_files=True,
        type=["pdf"],
        key="uploader_pdfs"
    )

    if uploaded_pdfs:
        st.subheader("📑 Organização das páginas")

        pages_config = []
        global_idx = 0

        # carrega os bytes de cada PDF uma única vez
        pdfs_data = []
        for file_idx, file in enumerate(uploaded_pdfs):
            file.seek(0)
            pdf_bytes = file.read()
            try:
                doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                pdfs_data.append({
                    "file_idx": file_idx,
                    "name": file.name,
                    "bytes": pdf_bytes,
                    "doc": doc,
                })
            except Exception as e:
                st.error(f"Não foi possível ler {file.name}: {e}")
                continue

        for pdf in pdfs_data:
            doc = pdf["doc"]
            for page_idx in range(len(doc)):
                global_idx += 1
                st.markdown("---")
                col1, col2 = st.columns([2, 2])

                key_suffix = f"{pdf['file_idx']}_{page_idx}"

                with col1:
                    st.write(f"**Arquivo:** {pdf['name']}")
                    st.caption(f"Página {page_idx + 1} de {len(doc)}")

                    order = st.number_input(
                        "Ordem no PDF final",
                        min_value=1,
                        value=global_idx,
                        key=f"order_page_{key_suffix}"
                    )

                    rotation = st.selectbox(
                        "Rotação",
                        options=[0, 90, 180, 270],
                        format_func=lambda x: f"{x}°",
                        key=f"rot_page_{key_suffix}"
                    )

                with col2:
                    try:
                        page = doc[page_idx]
                        mat = fitz.Matrix(1.5, 1.5)
                        if rotation != 0:
                            mat = mat.prerotate(rotation)
                        pix = page.get_pixmap(matrix=mat)
                        st.image(pix.tobytes("png"), use_container_width=True)
                    except Exception:
                        st.warning("Não foi possível visualizar esta página")

                pages_config.append({
                    "order": order,
                    "rotation": rotation,
                    "file_idx": pdf["file_idx"],
                    "page_idx": page_idx,
                })

        if st.button("📚 Gerar PDF consolidado", key="btn_juntar_pdfs"):
            if not pages_config:
                st.warning("Nenhuma página disponível.")
                st.stop()

            pages_config.sort(key=lambda x: x["order"])
            writer = PdfWriter()

            # mapa de file_idx -> bytes para evitar replicar
            bytes_por_arquivo = {p["file_idx"]: p["bytes"] for p in pdfs_data}
            readers_cache = {}

            for cfg in pages_config:
                try:
                    fidx = cfg["file_idx"]
                    if fidx not in readers_cache:
                        readers_cache[fidx] = PdfReader(io.BytesIO(bytes_por_arquivo[fidx]))
                    reader = readers_cache[fidx]
                    page = reader.pages[cfg["page_idx"]]
                    if cfg["rotation"] != 0:
                        page.rotate(cfg["rotation"])
                    writer.add_page(page)
                except Exception as e:
                    st.error(f"Erro ao processar página: {e}")
                    st.stop()

            pdf_buffer = io.BytesIO()
            writer.write(pdf_buffer)
            pdf_buffer.seek(0)

            # fecha docs do pymupdf
            for pdf in pdfs_data:
                pdf["doc"].close()

            st.success("✅ PDF consolidado gerado com sucesso!")
            st.download_button(
                "⬇️ Baixar PDF consolidado",
                data=pdf_buffer,
                file_name="pdf_consolidado.pdf",
                mime="application/pdf"
            )
