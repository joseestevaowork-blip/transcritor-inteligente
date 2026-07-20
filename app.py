import streamlit as st
import whisper
import tempfile
import os
import google.generativeai as genai

st.set_page_config(page_title="Transcritor Inteligente", page_icon="🎙️", layout="wide")
st.title("🎙️ Transcrição e Inteligência de Áudio")

# Barra lateral para inserir a Chave do Gemini
with st.sidebar:
    st.header("⚙️ Configurações")
    api_key = st.text_input("Insira a sua API Key do Gemini:", type="password")
    st.write("Sem a chave, o sistema fará apenas a transcrição normal.")

@st.cache_resource
def load_model():
    return whisper.load_model("medium")

model = load_model()

audio_file = st.file_uploader("Envie seu arquivo M4A", type=["m4a"])

if audio_file is not None:
    st.audio(audio_file, format='audio/m4a')
    
    if st.button("Iniciar Processamento"):
        with st.spinner("1/2 - Ouvindo e Transcrevendo (Isso pode demorar um pouco)..."):
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".m4a") as tmp_file:
                tmp_file.write(audio_file.read())
                tmp_file_path = tmp_file.name

            try:
                # Transcrição travada em Português para evitar alucinações
                result = model.transcribe(tmp_file_path, language="pt", temperature=0, beam_size=10, best_of=10, fp16=False)
                
                texto_formatado = ""
                texto_puro = "" # O texto puro vai ser enviado para o Gemini ler melhor
                
                for segment in result["segments"]:
                    start_time = int(segment["start"])
                    minutos = start_time // 60
                    segundos = start_time % 60
                    
                    linha = f"({minutos:02d}:{segundos:02d}) {segment['text'].strip()}"
                    texto_formatado += linha + "\n"
                    texto_puro += segment['text'].strip() + " "
                
                # Exibe a transcrição na tela
                st.success("✅ Transcrição Concluída!")
                st.text_area("Texto Transcrito Original:", value=texto_formatado, height=300)
                
                # --- INÍCIO DA INTELIGÊNCIA COM O GEMINI ---
                if api_key:
                    with st.spinner("2/2 - A Inteligência Artificial está a analisar a reunião..."):
                        # Configura o Gemini com a sua chave
                        genai.configure(api_key=api_key)
                        
                        # Escolhe o modelo do Gemini
                        llm = genai.GenerativeModel('gemini-2.5-flash')
                        
                        # O comando (Prompt) estruturado para o perfil da reunião
                        prompt = f"""
                        Você é um assistente especializado em análise de dados e gestão florestal/silvicultura. 
                        Analise a seguinte transcrição de uma reunião operacional e extraia as informações de forma estruturada:
                        
                        1. RESUMO EXECUTIVO: Um resumo de 1 ou 2 parágrafos sobre o tema central da reunião.
                        2. INDICADORES E DADOS: Liste em tópicos (bullet points) quaisquer números, percentagens de qualidade (ex: desvios, volume de calda), maquinário, ou métricas operacionais que foram citados.
                        3. PLANO DE AÇÃO: O que ficou decidido? Quem precisa fazer o quê? (Liste em formato de tarefas).
                        4. PONTOS DE ATENÇÃO: Desafios, gargalos ou problemas de segurança relatados no campo.
                        
                        Aqui está a transcrição:
                        {texto_puro}
                        """
                        
                        # Envia para o Gemini e recebe a resposta
                        resposta_ia = llm.generate_content(prompt)
                        
                        st.success("✅ Análise Concluída!")
                        st.markdown("### 📊 Relatório Inteligente da Reunião")
                        st.info(resposta_ia.text)
                else:
                    st.warning("⚠️ Adicione a API Key do Gemini no menu lateral para gerar o Resumo Inteligente.")
                
            except Exception as e:
                st.error(f"Ocorreu um erro durante o processamento: {e}")
                
            finally:
                if os.path.exists(tmp_file_path):
                    os.remove(tmp_file_path)
