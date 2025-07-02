import streamlit as st
import os
import openpyxl
from openpyxl.utils import get_column_letter
import io # Para lidar com arquivos em memória
import zipfile # Para compactar as imagens para download

# --- IMPORTAÇÕES DAS BIBLIOTERAS DE CÓDIGOS DE BARRAS ---
from aztec_code_generator import AztecCode
# As bibliotecas 'barcode' e 'qrcode' não são mais estritamente necessárias se for apenas Aztec,
# mas as manteremos no requirements.txt por consistência e futuras expansões.
from PIL import Image 
# --- FIM DAS IMPORTAÇÕES ---

def generate_aztec_codes_streamlit(input_file_content):
    """
    Gera códigos Aztec e um arquivo Excel a partir de um conteúdo de arquivo TXT,
    retornando os dados em memória.

    Args:
        input_file_content (bytes): Conteúdo do arquivo TXT de entrada como bytes.

    Returns:
        tuple: (excel_buffer, image_buffers)
               excel_buffer (io.BytesIO): Buffer contendo o arquivo Excel.
               image_buffers (list): Lista de tuplas (filename, io.BytesIO) para as imagens.
    """
    # Decodifica o conteúdo do arquivo de bytes para string, depois divide em linhas
    lines = input_file_content.decode('utf-8').splitlines()

    excel_data = []
    excel_data.append(["Dado Original", "Tipo de Código", "Nome do Arquivo Gerado"])

    image_buffers = [] # Lista para armazenar as imagens em memória

    if not lines:
        st.warning("O arquivo TXT está vazio. Nenhum código Aztec para gerar.")
        return None, []

    st.info(f"Lendo {len(lines)} linhas do arquivo...")

    for i, line in enumerate(lines):
        code_data = line.strip()

        if not code_data:
            st.warning(f"Linha {i+1} está vazia, pulando.")
            continue

        generated_filename = None
        image_buffer = io.BytesIO() # Buffer para a imagem atual
        
        try:
            aztec_code = AztecCode(code_data)
            generated_filename = f"aztec_code_{i+1}.png"
            # Salva no buffer em vez de um arquivo no disco
            aztec_code.save(image_buffer, module_size=4, border=1)
            st.write(f"Aztec Code gerado para '{code_data}'")

            if generated_filename:
                # Resetar o ponteiro do buffer para o início antes de ler ou adicionar ao ZIP
                image_buffer.seek(0)
                image_buffers.append((generated_filename, image_buffer))
                excel_data.append([code_data, "AZTEC", generated_filename])

        except Exception as e:
            st.error(f"Erro ao gerar Aztec Code para '{code_data}' (linha {i+1}): {e}")
            # Em Streamlit, queremos ver esses erros na interface

    # Cria o arquivo Excel em memória
    excel_buffer = io.BytesIO()
    if len(excel_data) > 1: # Verifica se há dados além do cabeçalho
        try:
            workbook = openpyxl.Workbook()
            sheet = workbook.active
            sheet.title = "Códigos Aztec Gerados" 

            for row_data in excel_data:
                sheet.append(row_data)

            for col in range(1, sheet.max_column + 1):
                sheet.column_dimensions[get_column_letter(col)].auto_size = True

            workbook.save(excel_buffer)
            excel_buffer.seek(0) # Resetar o ponteiro para o início
            st.success("Arquivo Excel criado com sucesso!")
        except Exception as e:
            st.error(f"Erro ao criar o arquivo Excel: {e}")
            excel_buffer = None # Indica que o Excel não foi criado
    else:
        st.warning("Nenhum dado válido para ser salvo no arquivo Excel.")
        excel_buffer = None

    return excel_buffer, image_buffers


# --- Interface do Streamlit ---
st.set_page_config(
    page_title="Prometheus Aztec Generator",
    page_icon="🏗️", # Um emoji ou caminho para um arquivo .ico/png para o ícone da aba do navegador
    layout="centered"
)

st.title("🏗️ Prometheus Aztec Generator")
st.markdown("---")

st.markdown("""
Esta ferramenta gera **Códigos Aztec** a partir de um arquivo de texto.
""")

# 1. Upload do arquivo TXT
st.header("1. Carregar Arquivo de Dados")
uploaded_file = st.file_uploader(
    "Arraste e solte ou clique para carregar seu arquivo `.txt` (um dado por linha)",
    type=["txt"]
)

# Botão para iniciar a geração
st.header("2. Gerar Códigos Aztec e Excel")
if st.button("Gerar Códigos Aztec"):
    if uploaded_file is not None:
        with st.spinner("Gerando códigos Aztec e arquivo Excel..."):
            file_contents = uploaded_file.read()
            excel_buffer, image_buffers = generate_aztec_codes_streamlit(file_contents)
        
        st.markdown("---")
        st.header("3. Download dos Resultados")

        # Botão de download do Excel
        if excel_buffer:
            st.download_button(
                label="📥 Baixar Arquivo Excel (Aztec)",
                data=excel_buffer,
                file_name=f"aztec_codes_summary.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        # Botão de download das Imagens (compactadas em ZIP)
        if image_buffers:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                for filename, img_buf in image_buffers:
                    zf.writestr(filename, img_buf.getvalue())
            
            zip_buffer.seek(0) # Resetar o ponteiro
            st.download_button(
                label="📦 Baixar Imagens Aztec (ZIP)",
                data=zip_buffer,
                file_name=f"aztec_images.zip",
                mime="application/zip"
            )
        
        if not excel_buffer and not image_buffers:
            st.warning("Nenhum arquivo gerado. Verifique o arquivo de entrada e as mensagens de erro acima.")

    else:
        st.warning("Por favor, carregue um arquivo TXT para começar.")

st.markdown("---")
st.info("Desenvolvido por Rinalanc. Data: 30/06/2025")
