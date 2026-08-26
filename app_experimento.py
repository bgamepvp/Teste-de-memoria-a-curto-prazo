import streamlit as st
import time
import random
import pandas as pd
import unicodedata
import os

# Configuração da página do Streamlit
st.set_page_config(
    page_title="Experimento de Memória de Trabalho",
    page_icon="🧠",
    layout="centered"
)

# Palavras originais do experimento (10 do grupo + 5 adicionais para completar as 15 planejadas)
# As adicionais foram selecionadas para serem substantivos concretos simples de extensão similar
PALAVRAS_ALVO = [
    "Livro", "Janela", "Violino", "Bússola", "Cogumelo", 
    "Escada", "Relógio", "Borboleta", "Montanha", "Abelha",
    "Cadeira", "Caneta", "Garrafa", "Prato", "Chave"
]

# Função para normalizar strings (remover acentos, converter para minúsculas e limpar espaços)
def normalizar_palavra(texto):
    if not texto:
        return ""
    texto = str(texto).strip().lower()
    # Remove acentos
    texto = "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )
    return texto

LISTA_ALVO_NORMALIZADA = [normalizar_palavra(w) for w in PALAVRAS_ALVO]

# Inicialização do estado da sessão do Streamlit
if "etapa" not in st.session_state:
    st.session_state.etapa = "inicio"
if "nome" not in st.session_state:
    st.session_state.nome = ""
if "grupo" not in st.session_state:
    st.session_state.grupo = ""
if "tempo_restante" not in st.session_state:
    st.session_state.tempo_restante = 30
if "respostas_manual_pesquisador" not in st.session_state:
    st.session_state.respostas_manual_pesquisador = []

# Caminho do arquivo de banco de dados local (caso rode localmente com persistência)
DB_FILE = "resultados_experimento.csv"

def salvar_resultado_local(nome, grupo, acertos, palavras_digitadas):
    novo_dado = pd.DataFrame([{
        "Data": pd.Timestamp.now().strftime("%d/%m/%Y %H:%M:%S"),
        "Nome": nome,
        "Grupo": grupo,
        "Acertos": acertos,
        "Palavras Digitadas": ", ".join(palavras_digitadas)
    }])
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            df = pd.concat([df, novo_dado], ignore_index=True)
            df.to_csv(DB_FILE, index=False)
        except Exception:
            pass
    else:
        try:
            novo_dado.to_csv(DB_FILE, index=False)
        except Exception:
            pass

# --- INTERFACE PRINCIPAL ---

# Sidebar para o Painel do Pesquisador
with st.sidebar:
    st.title("⚙️ Área de Controle")
    st.markdown("Acesso exclusivo para os pesquisadores do grupo.")
    
    # Checkbox para habilitar painel administrativo
    ver_painel = st.checkbox("Acessar Painel do Pesquisador")
    
    if ver_painel:
        senha = st.text_input("Senha de Acesso", type="password")
        if senha == "psicologia2026":
            st.success("Acesso Autorizado!")
            st.session_state.ver_pesquisador = True
        elif senha != "":
            st.error("Senha incorreta.")
            st.session_state.ver_pesquisador = False
        else:
            st.session_state.ver_pesquisador = False
    else:
        st.session_state.ver_pesquisador = False

# Se a área do pesquisador estiver ativa, mostra a análise de dados
if st.session_state.get("ver_pesquisador", False):
    st.title("📊 Painel de Análise do Pesquisador")
    st.markdown("""
    Este painel compila os resultados do experimento online. Ele calcula automaticamente as médias
    e desvios padrões de cada grupo para testar a hipótese de que a **supressão articulatória (distração)**
    prejudica a codificação na Memória de Trabalho.
    """)
    
    # Carrega dados do CSV ou do estado temporário de colagem
    dados_totais = []
    
    # 1. Tentar ler do arquivo local CSV
    if os.path.exists(DB_FILE):
        try:
            df_csv = pd.read_csv(DB_FILE)
            for _, row in df_csv.iterrows():
                dados_totais.append({
                    "Nome": row["Nome"],
                    "Grupo": row["Grupo"],
                    "Acertos": int(row["Acertos"]),
                    "Palavras": row["Palavras Digitadas"]
                })
        except Exception:
            pass
            
    # 2. Adicionar dados colados manualmente (útil para Streamlit Cloud efêmero)
    for dado in st.session_state.respostas_manual_pesquisador:
        dados_totais.append(dado)
        
    st.subheader("📥 Adicionar Resposta de Participante manualmente")
    st.markdown("Se os participantes realizaram o teste e enviaram o **Comprovante de Participação**, cole o texto completo do comprovante abaixo para incluí-lo na análise estatística:")
    
    texto_comprovante = st.text_area("Cole o Comprovante aqui:", height=120)
    if st.button("Processar e Adicionar à Análise"):
        if texto_comprovante:
            try:
                linhas = texto_comprovante.split("\n")
                nome_part = ""
                grupo_part = ""
                pontos_part = 0
                palavras_part = ""
                
                for linha in linhas:
                    if "Participante:" in linha or "Nome:" in linha:
                        nome_part = linha.split(":")[1].strip()
                    elif "Grupo:" in linha:
                        grupo_part = linha.split(":")[1].strip()
                    elif "Pontuação:" in linha:
                        pontos_part = int(linha.split(":")[1].split("/")[0].strip())
                    elif "Palavras Lembradas:" in linha or "Palavras Digitadas:" in linha:
                        palavras_part = linha.split(":")[1].strip()
                
                if nome_part and grupo_part:
                    st.session_state.respostas_manual_pesquisador.append({
                        "Nome": nome_part,
                        "Grupo": grupo_part,
                        "Acertos": pontos_part,
                        "Palavras": palavras_part
                    })
                    st.success(f"Participante {nome_part} adicionado com sucesso para esta sessão!")
                    st.rerun()
                else:
                    st.error("Formato de comprovante inválido. Certifique-se de copiar o texto completo gerado pelo app.")
            except Exception as e:
                st.error(f"Erro ao processar comprovante: {e}")
                
    st.divider()
    
    if len(dados_totais) > 0:
        df_analise = pd.DataFrame(dados_totais)
        
        st.subheader("📋 Tabela Geral de Resultados")
        st.dataframe(df_analise)
        
        # Cálculos de Estatística Descritiva
        st.subheader("📈 Estatísticas por Grupo")
        
        summary = df_analise.groupby("Grupo")["Acertos"].agg(["count", "mean", "std"]).reset_index()
        summary.columns = ["Grupo", "N (Participantes)", "Média de Acertos", "Desvio Padrão"]
        st.table(summary)
        
        # Gráfico comparativo de médias
        st.subheader("📊 Comparação Visual das Médias")
        chart_data = pd.DataFrame({
            "Grupo": summary["Grupo"],
            "Média de Palavras Lembradas": summary["Média de Acertos"]
        }).set_index("Grupo")
        
        st.bar_chart(chart_data)
        
        # Explicação teórica do efeito para o relatório científico do grupo
        st.subheader("💡 Fundamentação Teórica para o seu Trabalho")
        st.markdown("""
        **Interpretação Baseada no Modelo de Baddeley & Hitch:**
        
        * **A Alça Fonológica:** É o componente da memória de trabalho responsável por reter informação baseada em fala e sons de linguagem. Ela é composta pelo *armazenamento fonológico* (passivo, dura cerca de 2 segundos) e pelo *mecanismo de ensaio articulatório* (ativo, que 'recicla' a informação silenciosamente na mente).
        * **A Supressão Articulatória (Grupo 1):** Ao forçar o participante do Grupo 1 a repetir "1, 2, 3" em voz alta enquanto memorizava as palavras, o **mecanismo de ensaio articulatório** foi totalmente ocupado com uma tarefa irrelevante. Isso impediu que as palavras alvo fossem ensaiadas mentalmente, levando ao rápido decaimento de seus traços de memória.
        * **A Hipótese Confirmada:** Espera-se que a média de acertos do **Grupo 2 (Sem Distração)** seja significativamente maior do que a do **Grupo 1 (Com Distração)**, demonstrando empiricamente o limite de capacidade e a natureza multicomponente do modelo de memória de trabalho.
        """)
        
        if st.button("Limpar dados colados manualmente nesta sessão"):
            st.session_state.respostas_manual_pesquisador = []
            st.success("Dados da sessão limpos!")
            st.rerun()
            
    else:
        st.info("Nenhum dado registrado ainda. Realize o teste ou cole os comprovantes dos participantes acima para visualizar as análises estatísticas e gráficos!")

# Se o painel do pesquisador não estiver na tela cheia, mostra o teste para o participante
else:
    # Cabeçalho do Experimento Acadêmico
    st.title("🧠 Teste de Memória e Atenção")
    st.markdown("### Experimento de Psicologia Cognitiva")
    st.caption("Trabalho Prático de Processos Psicológicos Básicos — Ano 2026")
    st.divider()

    # --- ETAPA: INÍCIO E TERMO DE CONSENTIMENTO ---
    if st.session_state.etapa == "inicio":
        st.write("""
        Olá! Agradecemos muito a sua disponibilidade para participar deste estudo acadêmico simples 
        sobre memória de curto prazo e processos de atenção.
        
        **Instruções de Confidencialidade:**
        * Este teste é totalmente voluntário e anônimo.
        * Os dados coletados serão utilizados estritamente para fins de análise estatística acadêmica no trabalho de nossa disciplina de Psicologia.
        * O teste dura cerca de **2 a 3 minutos** no total.
        """)
        
        nome_input = st.text_input("Digite seu Nome, Apelido ou Iniciais:", max_chars=40)
        
        st.subheader("Escolha o método de participação:")
        metodo = st.radio(
            "Selecione uma opção:",
            ["Atribuição Automática (Recomendado para balancear os grupos)", 
             "Selecionar Grupo Manualmente (Use apenas se instruído pelos pesquisadores)"]
        )
        
        grupo_selecionado = None
        if metodo == "Selecionar Grupo Manualmente (Use apenas se instruído pelos pesquisadores)":
            grupo_selecionado = st.selectbox("Selecione o seu grupo:", ["Grupo 1 (Com Distração)", "Grupo 2 (Sem Distração)"])
            
        if st.button("Iniciar Experimento 🚀"):
            if not nome_input.strip():
                st.warning("Por favor, insira seu nome ou apelido para prosseguir.")
            else:
                st.session_state.nome = nome_input.strip()
                if metodo == "Atribuição Automática (Recomendado para balancear os grupos)":
                    # Atribuição aleatória simples para equilibrar os grupos
                    st.session_state.grupo = random.choice(["Grupo 1 (Com Distração)", "Grupo 2 (Sem Distração)"])
                else:
                    st.session_state.grupo = grupo_selecionado
                
                st.session_state.etapa = "instrucoes"
                st.rerun()

    # --- ETAPA: INSTRUÇÕES ESPECÍFICAS DO GRUPO ---
    elif st.session_state.etapa == "instrucoes":
        st.subheader("📋 Instruções do seu Teste")
        st.markdown(f"Olá, **{st.session_state.nome}**! Você foi designado para o **{st.session_state.grupo}**.")
        
        if st.session_state.grupo == "Grupo 1 (Com Distração)":
            st.error("⚠️ LEIA COM MUITA ATENÇÃO ESTA REGRA:")
            st.markdown("""
            Na próxima tela, você verá uma lista de **15 palavras** por exatamente **30 segundos**.
            
            Sua tarefa é memorizar o máximo de palavras possível, mas **COM UMA CONDIÇÃO OBRIGATÓRIA**:
            
            * Durante os 30 segundos em que as palavras estiverem na tela, você deve **REPETIR EM VOZ ALTA E DE FORMA SEGUIDA E CONSTANTE** os números:
              
              **"um, dois, três, um, dois, três, um, dois, três..."**
            
            * Você deve falar em voz alta de forma audível e contínua, sem parar um segundo sequer, enquanto lê as palavras na tela.
            * Não vale ficar em silêncio! A repetição falada é essencial para o experimento.
            """)
        else:
            st.success("✨ INSTRUÇÕES DO SEU TESTE:")
            st.markdown("""
            Na próxima tela, você verá uma lista de **15 palavras** por exatamente **30 segundos**.
            
            Sua tarefa é memorizar o máximo de palavras possível, sob a seguinte condição:
            
            * Durante os 30 segundos, você deve fazer a tarefa em **SILÊNCIO ABSOLUTO**.
            * Concentre-se apenas nas palavras na tela, sem emitir nenhum som e sem escrever nada.
            """)
            
        st.markdown("---")
        st.warning("Certifique-se de que está em um ambiente tranquilo e sem outras interrupções antes de clicar abaixo. O tempo começará a correr imediatamente!")
        
        if st.button("Estou Pronto, Mostrar Palavras! ⏱️"):
            st.session_state.etapa = "exposicao"
            st.session_state.tempo_restante = 30
            st.rerun()

    # --- ETAPA: EXPOSIÇÃO DAS PALAVRAS COM CONTADOR ---
    elif st.session_state.etapa == "exposicao":
        st.subheader("⏱️ Memorize as palavras abaixo!")
        
        # Lembrança da instrução de distração para o Grupo 1
        if st.session_state.grupo == "Grupo 1 (Com Distração)":
            st.markdown("🔊 **RECORDE-SE:** Continue repetindo **'UM, DOIS, TRÊS...' em voz alta** sem parar!")
        else:
            st.markdown("🤫 **RECORDE-SE:** Faça a memorização em **silêncio absoluto**.")
            
        st.divider()
        
        # Renderização visual das palavras em colunas bonitas para leitura rápida
        cols = st.columns(3)
        for i, palavra in enumerate(PALAVRAS_ALVO):
            with cols[i % 3]:
                st.markdown(f"### 📦 **{palavra}**")
                
        st.divider()
        
        # Espaço reservado para o cronômetro ativo
        placeholder_timer = st.empty()
        
        # Loop do cronômetro de 30 segundos
        for t in range(st.session_state.tempo_restante, -1, -1):
            st.session_state.tempo_restante = t
            placeholder_timer.markdown(f"<h2 style='text-align: center; color: #ff4b4b;'>Tempo Restante: {t} segundos</h2>", unsafe_allow_html=True)
            time.sleep(1)
            
        # Ao término do tempo, avança automaticamente
        st.session_state.etapa = "recuperacao"
        st.rerun()

    # --- ETAPA: RECUPERAÇÃO (DIGITAÇÃO DAS RESPOSTAS) ---
    elif st.session_state.etapa == "recuperacao":
        st.subheader("✏️ Fase de Recuperação: O que você lembra?")
        st.markdown("""
        Agora, digite as palavras que você se lembra de ter visto na tela.
        
        **Regras de integridade científica:**
        * NÃO consulte nenhuma anotação ou volte para a tela anterior.
        * NÃO pesquise na internet. Dependemos da sua honestidade acadêmica para que os resultados do nosso grupo sejam válidos!
        * Escreva **uma palavra por linha** ou separe as palavras por **vírgulas**.
        """)
        
        # Entrada de texto para as palavras lembradas
        resposta_usuario = st.text_area("Digite as palavras de que se lembra abaixo:", height=200, placeholder="Exemplo:\nLivro\nJanela\nViolino")
        
        if st.button("Finalizar Teste e Ver Resultados 🏁"):
            # Processamento de respostas
            # Divide por linhas ou por vírgulas
            linhas_cruas = resposta_usuario.replace(",", "\n").split("\n")
            palavras_digitadas = [w.strip() for w in linhas_cruas if w.strip()]
            
            # Análise de acertos
            acertos = 0
            palavras_corretas = []
            palavras_incorretas = []
            
            # Conjunto de palavras digitadas normalizadas para evitar duplicidade na contagem de acertos
            digitadas_normalizadas_set = set()
            
            for pal in palavras_digitadas:
                norm = normalizar_palavra(pal)
                if norm:
                    digitadas_normalizadas_set.add(norm)
            
            # Verifica quais palavras alvo estão no conjunto de palavras digitadas
            for original_idx, alvo_norm in enumerate(LISTA_ALVO_NORMALIZADA):
                if alvo_norm in digitadas_normalizadas_set:
                    acertos += 1
                    palavras_corretas.append(PALAVRAS_ALVO[original_idx])
                    
            # Verifica quais palavras digitadas pelo usuário não estavam na lista alvo (intrusões)
            for pal in palavras_digitadas:
                norm = normalizar_palavra(pal)
                if norm not in LISTA_ALVO_NORMALIZADA:
                    palavras_incorretas.append(pal)
                    
            # Armazena as estatísticas e respostas
            st.session_state.acertos = acertos
            st.session_state.palavras_corretas = palavras_corretas
            st.session_state.palavras_incorretas = palavras_incorretas
            st.session_state.palavras_digitadas = palavras_digitadas
            
            # Salva no arquivo de dados local para persistência de dados agregados
            salvar_resultado_local(st.session_state.nome, st.session_state.grupo, acertos, palavras_digitadas)
            
            st.session_state.etapa = "resultado"
            st.rerun()

    # --- ETAPA: RESULTADO FINAL E COMPROVANTE ---
    elif st.session_state.etapa == "resultado":
        st.success("🎉 Experimento Concluído com Sucesso!")
        st.markdown(f"Muito obrigado por sua participação, **{st.session_state.nome}**!")
        
        st.subheader("📊 Seu Desempenho:")
        st.metric(label="Palavras Lembradas Corretamente", value=f"{st.session_state.acertos} de 15")
        
        # Exibe o feedback das palavras lembradas
        col_esq, col_dir = st.columns(2)
        with col_esq:
            st.write("**✅ Palavras que você acertou:**")
            if st.session_state.palavras_corretas:
                for p in st.session_state.palavras_corretas:
                    st.write(f"- {p}")
            else:
                st.write("Nenhuma palavra da lista alvo.")
                
        with col_dir:
            st.write("**❌ Outras palavras digitadas (intrusões):**")
            if st.session_state.palavras_incorretas:
                for p in st.session_state.palavras_incorretas:
                    st.write(f"- {p}")
            else:
                st.write("Nenhuma palavra fora da lista.")
                
        st.divider()
        st.subheader("📋 Envie seu resultado para o grupo!")
        st.markdown("""
        Para que o nosso grupo de psicologia possa coletar e analisar os dados agregados deste experimento assíncrono,
        **copie o bloco de texto abaixo** e envie para a pessoa que te convidou para o teste (via WhatsApp ou e-mail):
        """)
        
        # Gera o comprovante formatado para cópia fácil
        comprovante = f"""=== COMPROVANTE DE PARTICIPAÇÃO ===
Nome: {st.session_state.nome}
Grupo: {st.session_state.grupo}
Pontuação: {st.session_state.acertos}/15
Palavras Lembradas: {", ".join(st.session_state.palavras_corretas)}
Palavras Digitadas: {", ".join(st.session_state.palavras_digitadas)}
Data/Hora: {pd.Timestamp.now().strftime("%d/%m/%Y %H:%M:%S")}
=================================="""

        st.code(comprovante, language="text")
        
        st.info("💡 Dica: Você pode simplesmente clicar no ícone de cópia localizado no canto superior direito do bloco cinza acima!")
        
        if st.button("Voltar ao Início (Reiniciar Teste)"):
            # Limpa sessão para novo participante
            st.session_state.etapa = "inicio"
            st.session_state.nome = ""
            st.session_state.grupo = ""
            st.session_state.tempo_restante = 30
            st.rerun()
