import streamlit as st
import pandas as pd
import numpy as np
import os
import json
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

# ========== INITIALIZATION ==========
# Variáveis de estado para a Tabela 1 (Sugestão de Compras)
if 'arquivo_editando_t1' not in st.session_state:
    st.session_state.arquivo_editando_t1 = None
if 'grid_version_t1' not in st.session_state:
    st.session_state.grid_version_t1 = 0
if 'planilha_a_excluir_t1' not in st.session_state:
    st.session_state.planilha_a_excluir_t1 = None
if 'df_original_t1' not in st.session_state:
    st.session_state.df_original_t1 = None
if 'df_editado_t1' not in st.session_state:
    st.session_state.df_editado_t1 = None
if 'colunas_relevantes_t1' not in st.session_state:
    st.session_state.colunas_relevantes_t1 = None
if 'modificacoes_nao_salvas_t1' not in st.session_state:
    st.session_state.modificacoes_nao_salvas_t1 = False

# Variáveis de estado para a Tabela 2 (Purchase Order)
if 'arquivo_editando_t2' not in st.session_state:
    st.session_state.arquivo_editando_t2 = None
if 'grid_version_t2' not in st.session_state:
    st.session_state.grid_version_t2 = 0
if 'planilha_a_excluir_t2' not in st.session_state:
    st.session_state.planilha_a_excluir_t2 = None
if 'df_original_t2' not in st.session_state:
    st.session_state.df_original_t2 = None
if 'df_editado_t2' not in st.session_state:
    st.session_state.df_editado_t2 = None
if 'colunas_relevantes_t2' not in st.session_state:
    st.session_state.colunas_relevantes_t2 = None
if 'modificacoes_nao_salvas_t2' not in st.session_state:
    st.session_state.modificacoes_nao_salvas_t2 = False

# Variáveis de estado para a Tabela 3 (Purchase Invoice)
if 'arquivo_editando_t3' not in st.session_state:
    st.session_state.arquivo_editando_t3 = None
if 'grid_version_t3' not in st.session_state:
    st.session_state.grid_version_t3 = 0
if 'planilha_a_excluir_t3' not in st.session_state:
    st.session_state.planilha_a_excluir_t3 = None
if 'df_original_t3' not in st.session_state:
    st.session_state.df_original_t3 = None
if 'df_editado_t3' not in st.session_state:
    st.session_state.df_editado_t3 = None
if 'colunas_relevantes_t3' not in st.session_state:
    st.session_state.colunas_relevantes_t3 = None
if 'modificacoes_nao_salvas_t3' not in st.session_state:
    st.session_state.modificacoes_nao_salvas_t3 = False

# Configurações globais
if 'auto_save' not in st.session_state:
    st.session_state.auto_save = True

# ========== CONFIGURATION ==========
st.set_page_config(page_title="Sistema de Gestão de Compras", layout="wide")

# CSS para estilizar as abas
st.markdown("""
<style>
    /* Estilo para as abas principais */
    div[data-testid="stTabs"] {
        margin-top: -20px;
    }
    
    /* Estilo para os títulos dentro das abas */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 18px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Configurações específicas para cada aba
CONFIG_T1 = {
    'pasta_planilhas': "planilhas_t1",
    'arquivo_historico': "historico_t1.json",
    'titulo': "📋 Sugestão de Compras",
    'cor_primaria': "#2F75B5",
    'cor_secundaria': "#C00000",
    'sufixo': 't1'
}

CONFIG_T2 = {
    'pasta_planilhas': "planilhas_t2",
    'arquivo_historico': "historico_t2.json",
    'titulo': "🛒 Purchase Order",
    'cor_primaria': "#00B050",
    'cor_secundaria': "#FFC000",
    'sufixo': 't2'
}

CONFIG_T3 = {
    'pasta_planilhas': "planilhas_t3",
    'arquivo_historico': "historico_t3.json",
    'titulo': "🧾 Purchase Invoice",
    'cor_primaria': "#7030A0",
    'cor_secundaria': "#FF6600",
    'sufixo': 't3',
    'aba_especifica': "FÁBRICA + LISTA DE PI"
}

COLUNAS_EXCLUIR = list(range(16, 28)) + [29] + list(range(38, 43)) + list(range(49, 51)) + list(range(52, 54)) + list(range(55, 60))

COLOR_MAPPING = {
    (0, 3): '#C00000', (4, 15): '#2F75B5', 28: '#2F75B5', 30: '#2F75B5',
    (31, 37): '#00B050', (43, 48): '#FFC000', 51: '#002060', 54: '#262626', 60: '#3F7FFF'
}

# Colunas a serem mostradas na Purchase Order
PO_COLUMNS = [0, 1, 51]

# Criar pastas se não existirem
os.makedirs(CONFIG_T1['pasta_planilhas'], exist_ok=True)
os.makedirs(CONFIG_T2['pasta_planilhas'], exist_ok=True)
os.makedirs(CONFIG_T3['pasta_planilhas'], exist_ok=True)

# ========== HELPER FUNCTIONS ==========
def carregar_historico(pasta_historico):
    if os.path.exists(pasta_historico):
        if os.path.getsize(pasta_historico) > 0:
            with open(pasta_historico, "r") as f:
                return json.load(f)
    return {}

def salvar_historico(historico, pasta_historico):
    with open(pasta_historico, "w") as f:
        json.dump(historico, f, indent=4)

def formatar_decimais(df, casas_decimais=2):
    for col in df.select_dtypes(include=['float64']).columns:
        if col == df.columns[[i for i in range(61) if i not in COLUNAS_EXCLUIR].index(60)] if 60 in [i for i in range(61) if i not in COLUNAS_EXCLUIR] else "":
            df[col] = df[col].apply(lambda x: f"{x:.{casas_decimais}%}" if pd.notnull(x) else x)
        else:
            df[col] = df[col].apply(lambda x: f"{x:.{casas_decimais}f}" if pd.notnull(x) else x)
    return df

def converter_para_numerico(serie):
    """Converte coluna para numérico, tratando vírgulas e strings"""
    return pd.to_numeric(
        serie.astype(str).str.replace(',', '.').str.replace('%', ''),
        errors='coerce'
    )

def ajustar_quantidades(df, col_unidades, col_caixa):
    """Aplica a regra de negócio: arredonda para cima e recalcula unidades"""
    try:
        df = df.copy()
        df[col_unidades] = converter_para_numerico(df[col_unidades])
        df[col_caixa] = converter_para_numerico(df[col_caixa])
        
        condicao = (df[col_caixa].notna()) & (df[col_caixa] > 0)
        
        df.loc[condicao, col_unidades] = (
            np.ceil(df.loc[condicao, col_unidades] / df.loc[condicao, col_caixa]) * 
            df.loc[condicao, col_caixa]
        )
        
        return df
    except Exception as e:
        st.error(f"Erro no ajuste: {str(e)}")
        return df

def salvar_alteracoes(nome, df, finalizar=False, config=None):
    caminho = os.path.join(config['pasta_planilhas'], nome)
    
    if finalizar:
        with st.spinner('🔍 Aplicando ajustes finais...'):
            if config['sufixo'] == 't1':
                colunas_relevantes = st.session_state[f"colunas_relevantes_{config['sufixo']}"]
                df = ajustar_quantidades(
                    df,
                    colunas_relevantes['col_51'],
                    colunas_relevantes['col_2']
                )
    
    df.to_excel(caminho, index=False)
    historico = carregar_historico(config['arquivo_historico'])
    historico[nome]["finalizado"] = finalizar
    salvar_historico(historico, config['arquivo_historico'])
    st.session_state[f"modificacoes_nao_salvas_{config['sufixo']}"] = False
    st.toast(f"✅ {'Planilha finalizada!' if finalizar else 'Alterações salvas!'}")

def configurar_estilo_aggrid(df, config):
    """Configura o estilo do AgGrid com comportamento diferente para cada aba"""
    gb = GridOptionsBuilder.from_dataframe(df)
    
    if config['sufixo'] == 't1':
        original_cols = [i for i in range(61) if i not in COLUNAS_EXCLUIR]
    elif config['sufixo'] == 't2':
        original_cols = PO_COLUMNS
    else:  # Purchase Invoice - mostra todas colunas
        original_cols = list(range(len(df.columns)))
    
    gb.configure_default_column(
        editable=True,
        resizable=True,
        wrapText=True,
        autoHeight=True,
        sortable=True,
        filter=True,
        suppressSizeToFit=False,
        cellStyle={"textAlign": "center", "fontSize": "14px"}
    )
    
    gb.configure_side_bar(filters_panel=True, defaultToolPanel="")

    # Configuração especial para coluna 51 (Unidades) - se existir
    if config['sufixo'] in ['t1', 't2'] and 51 in original_cols:
        col_51_name = df.columns[original_cols.index(51)] if 51 in original_cols else None
        if col_51_name:
            gb.configure_column(
                col_51_name,
                sort="desc",
                editable=True,
                headerStyle={
                    "backgroundColor": "#002060",
                    "color": "white",
                    "fontWeight": "bold",
                    "textAlign": "center",
                    "fontSize": "14px"
                },
                cellStyle={
                    "backgroundColor": "#00206033",
                    "textAlign": "center",
                    "fontSize": "14px"
                },
                width=150
            )

    # Aplicar esquema de cores para os intervalos originais
    for col_rule, color in COLOR_MAPPING.items():
        if isinstance(col_rule, tuple):
            cols = range(col_rule[0], col_rule[1] + 1)
        else:
            cols = [col_rule]
            
        for col in cols:
            if col in original_cols and config['sufixo'] != 't3':  # Não aplica cores na Purchase Invoice
                col_name = df.columns[original_cols.index(col)]
                # Para PO, todas colunas editáveis exceto a 0 (se for a primeira)
                editable = True if config['sufixo'] == 't2' and col != original_cols[0] else True
                
                gb.configure_column(
                    col_name,
                    editable=editable,
                    headerStyle={
                        "backgroundColor": color,
                        "color": "white",
                        "fontWeight": "bold",
                        "textAlign": "center",
                        "fontSize": "14px"
                    },
                    cellStyle={
                        "backgroundColor": f"{color}33",
                        "textAlign": "center",
                        "fontSize": "14px"
                    },
                    width=150
                )
    
    return gb.build()

def excluir_planilha(nome, config):
    try:
        caminho = os.path.join(config['pasta_planilhas'], nome)
        if os.path.exists(caminho):
            os.remove(caminho)
        historico = carregar_historico(config['arquivo_historico'])
        if nome in historico:
            del historico[nome]
            salvar_historico(historico, config['arquivo_historico'])
        if st.session_state[f"arquivo_editando_{config['sufixo']}"] == nome:
            st.session_state[f"arquivo_editando_{config['sufixo']}"] = None
        st.session_state[f"planilha_a_excluir_{config['sufixo']}"] = None
        st.success(f"✅ '{nome}' excluída com sucesso!")
        st.rerun()
    except Exception as e:
        st.error(f"❌ Erro ao excluir: {str(e)}")

def carregar_planilha_invoice(uploaded_file):
    """Carrega a aba específica 'FÁBRICA + LISTA DE PI' de um arquivo Excel"""
    try:
        with pd.ExcelFile(uploaded_file) as xls:
            if CONFIG_T3['aba_especifica'] in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=CONFIG_T3['aba_especifica'])
                return df
            else:
                st.error(f"A aba '{CONFIG_T3['aba_especifica']}' não foi encontrada no arquivo.")
                return None
    except Exception as e:
        st.error(f"Erro ao carregar planilha: {str(e)}")
        return None

def render_admin_section(config):
    """Renderiza a seção administrativa exclusiva para cada aba"""
    with st.expander(f"🔧 Área Administrativa ({config['titulo']})", expanded=True):
        historico = carregar_historico(config['arquivo_historico'])
        
        # Upload de arquivo (comportamento diferente para cada aba)
        if config['sufixo'] == 't1':
            uploaded_file = st.file_uploader(
                "📥 Importar nova planilha de Sugestão de Compras", 
                type=["xlsx"], 
                key=f"file_uploader_{config['sufixo']}"
            )
            
            if uploaded_file:
                nome = uploaded_file.name
                caminho_salvo = os.path.join(config['pasta_planilhas'], nome)

                if nome not in historico:
                    df = pd.read_excel(uploaded_file)
                    colunas_manter = [col for i, col in enumerate(df.columns) if i not in COLUNAS_EXCLUIR]
                    df_filtrado = df[colunas_manter]
                    df_filtrado.to_excel(caminho_salvo, index=False)
                    historico[nome] = {"finalizado": False}
                    salvar_historico(historico, config['arquivo_historico'])
                    st.success(f"✅ '{nome}' importada com sucesso!")
                    st.rerun()
                else:
                    st.info(f"⚠️ '{nome}' já existe no histórico.")
        
        elif config['sufixo'] == 't2':
            # Para PO, carregamos apenas das sugestões finalizadas
            historico_t1 = carregar_historico(CONFIG_T1['arquivo_historico'])
            sugestoes_finalizadas = [n for n, d in historico_t1.items() if d.get("finalizado", False)]
            
            if sugestoes_finalizadas:
                nome_sugestao = st.selectbox(
                    "📋 Selecionar Sugestão de Compras Finalizada",
                    sugestoes_finalizadas,
                    key=f"select_sugestao_{config['sufixo']}"
                )
                
                # Botão para criar PO a partir da sugestão selecionada
                if st.button("➕ Criar Purchase Order", key=f"btn_criar_po_{config['sufixo']}"):
                    caminho_t1 = os.path.join(CONFIG_T1['pasta_planilhas'], nome_sugestao)
                    df = pd.read_excel(caminho_t1)
                    
                    # Obter índices das colunas originais que não estão excluídas
                    original_cols = [i for i in range(61) if i not in COLUNAS_EXCLUIR]
                    
                    # Filtrar apenas colunas 0, 1 e 51 (se existirem)
                    colunas_manter = []
                    for col in PO_COLUMNS:
                        if col in original_cols:
                            colunas_manter.append(df.columns[original_cols.index(col)])
                    
                    df_filtrado = df[colunas_manter]
                    
                    # Nome do arquivo PO
                    nome_po = f"PO_{nome_sugestao}"
                    caminho_po = os.path.join(config['pasta_planilhas'], nome_po)
                    
                    # Salvar PO
                    df_filtrado.to_excel(caminho_po, index=False)
                    historico[nome_po] = {"finalizado": False}
                    salvar_historico(historico, config['arquivo_historico'])
                    st.success(f"✅ '{nome_po}' criada com sucesso!")
                    st.rerun()
            else:
                st.info("Nenhuma sugestão de compras finalizada disponível.")
        
        elif config['sufixo'] == 't3':
            uploaded_file = st.file_uploader(
                f"📥 Importar nova planilha de {config['titulo']} (deve conter aba '{CONFIG_T3['aba_especifica']}')", 
                type=["xlsx"], 
                key=f"file_uploader_{config['sufixo']}"
            )
            
            if uploaded_file:
                nome = uploaded_file.name
                caminho_salvo = os.path.join(config['pasta_planilhas'], nome)

                if nome not in historico:
                    df = carregar_planilha_invoice(uploaded_file)
                    if df is not None:
                        df.to_excel(caminho_salvo, index=False)
                        historico[nome] = {"finalizado": False}
                        salvar_historico(historico, config['arquivo_historico'])
                        st.success(f"✅ '{nome}' importada com sucesso!")
                        st.rerun()
                else:
                    st.info(f"⚠️ '{nome}' já existe no histórico.")

        # Listagem de planilhas
        pendentes = [n for n, d in historico.items() if not d.get("finalizado", False)]
        finalizadas = [n for n, d in historico.items() if d.get("finalizado", False)]

        col1, col2 = st.columns(2)

        # --- COLUMN 1: Pending Spreadsheets ---
        with col1:
            st.markdown("### ✏️ Planilhas em Andamento")
            if pendentes:
                nome_selecionado = st.selectbox(
                    "Selecione para editar", 
                    pendentes, 
                    key=f"select_pendente_{config['sufixo']}"
                )
                btn_col1, btn_col2 = st.columns([3, 1])
                with btn_col1:
                    if st.button(
                        "🖊️ Abrir para Edição", 
                        key=f"btn_editar_pendente_{config['sufixo']}", 
                        type="primary"
                    ):
                        st.session_state[f"arquivo_editando_{config['sufixo']}"] = nome_selecionado
                        st.session_state[f"grid_version_{config['sufixo']}"] = 0
                        st.session_state[f"df_original_{config['sufixo']}"] = None
                        st.session_state[f"df_editado_{config['sufixo']}"] = None
                        st.rerun()
                with btn_col2:
                    if st.button(
                        "🗑️ Excluir", 
                        key=f"btn_excluir_pendente_{nome_selecionado}_{config['sufixo']}", 
                        type="secondary"
                    ):
                        st.session_state[f"planilha_a_excluir_{config['sufixo']}"] = nome_selecionado
            else:
                st.info("Nenhuma planilha pendente.")

        # --- COLUMN 2: Completed Spreadsheets ---
        with col2:
            st.markdown("### ✅ Planilhas Finalizadas")
            if finalizadas:
                for nome in finalizadas:
                    with st.expander(f"📄 {nome}", expanded=False):
                        col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 1])
                        with col_btn1:
                            with open(os.path.join(config['pasta_planilhas'], nome), "rb") as f:
                                st.download_button(
                                    "📥 Baixar", 
                                    f, 
                                    file_name=nome,
                                    key=f"btn_baixar_{nome}_{config['sufixo']}"
                                )
                        with col_btn2:
                            if st.button(
                                "🔄 Reabrir", 
                                key=f"btn_reabrir_{nome}_{config['sufixo']}"
                            ):
                                historico[nome]["finalizado"] = False
                                salvar_historico(historico, config['arquivo_historico'])
                                st.rerun()
                        with col_btn3:
                            if st.button(
                                "🗑️ Excluir", 
                                key=f"btn_excluir_{nome}_{config['sufixo']}", 
                                type="secondary"
                            ):
                                st.session_state[f"planilha_a_excluir_{config['sufixo']}"] = nome
            else:
                st.info("Nenhuma planilha finalizada.")

def render_edicao_section(config):
    """Renderiza a seção de edição para a aba atual"""
    if not st.session_state[f"arquivo_editando_{config['sufixo']}"]:
        return
    
    st.markdown("---")
    nome = st.session_state[f"arquivo_editando_{config['sufixo']}"]
    st.header(f"📝 Editando: {nome}")
    
    # Controles acima da tabela
    with st.container():
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button(
                "🧹 Limpar Filtros", 
                key=f"btn_limpar_{nome}_{config['sufixo']}"
            ):
                estado_ampliacao = st.session_state.get(f"expandir_{nome}_{config['sufixo']}", False)
                st.session_state[f"grid_version_{config['sufixo']}"] += 1
                st.session_state[f"expandir_{nome}_{config['sufixo']}"] = estado_ampliacao
                st.rerun()
    
    # Carregar dados
    caminho = os.path.join(config['pasta_planilhas'], nome)
    if st.session_state[f"df_original_{config['sufixo']}"] is None:
        st.session_state[f"df_original_{config['sufixo']}"] = pd.read_excel(caminho)
        st.session_state[f"df_original_{config['sufixo']}"] = formatar_decimais(st.session_state[f"df_original_{config['sufixo']}"])
        st.session_state[f"df_editado_{config['sufixo']}"] = st.session_state[f"df_original_{config['sufixo']}"].copy()
        
        # Identificar colunas relevantes (apenas para T1)
        if config['sufixo'] == 't1':
            original_cols = [i for i in range(61) if i not in COLUNAS_EXCLUIR]
            st.session_state[f"colunas_relevantes_{config['sufixo']}"] = {
                'col_51': st.session_state[f"df_original_{config['sufixo']}"].columns[original_cols.index(51)],
                'col_2': st.session_state[f"df_original_{config['sufixo']}"].columns[original_cols.index(2)]
            }
    
    # View controls
    expandir = st.checkbox(
        "Ampliar visualização da tabela", 
        value=st.session_state.get(f"expandir_{nome}_{config['sufixo']}", False),
        key=f"expandir_{nome}_{config['sufixo']}"
    )
    altura = 800 if expandir else 500
    
    # Renderização do grid
    grid_options = configurar_estilo_aggrid(st.session_state[f"df_original_{config['sufixo']}"], config)
    grid_response = AgGrid(
        st.session_state[f"df_editado_{config['sufixo']}"],
        gridOptions=grid_options,
        key=f"aggrid_{nome}_{st.session_state[f'grid_version_{config['sufixo']}']}_{config['sufixo']}",
        height=altura,
        update_mode=GridUpdateMode.VALUE_CHANGED,
        enable_enterprise_modules=True
    )
    
    # Processamento das edições
    if not grid_response['data'].equals(st.session_state[f"df_editado_{config['sufixo']}"]):
        novo_df = grid_response['data'].copy()
        
        if config['sufixo'] == 't1':
            colunas_relevantes = st.session_state[f"colunas_relevantes_{config['sufixo']}"]
            if not novo_df[colunas_relevantes['col_51']].equals(
                st.session_state[f"df_editado_{config['sufixo']}"][colunas_relevantes['col_51']]
            ):
                novo_df = ajustar_quantidades(
                    novo_df,
                    colunas_relevantes['col_51'],
                    colunas_relevantes['col_2']
                )
                
                if not novo_df.equals(st.session_state[f"df_editado_{config['sufixo']}"]):
                    st.session_state[f"df_editado_{config['sufixo']}"] = novo_df
                    st.session_state[f"grid_version_{config['sufixo']}"] += 1
                    st.rerun()
        
        st.session_state[f"modificacoes_nao_salvas_{config['sufixo']}"] = True
    
    # Status e botões de ação
    st.markdown("---")
    if st.session_state[f"modificacoes_nao_salvas_{config['sufixo']}"]:
        st.warning("⚠️ Modificações não salvas")
    else:
        st.success("✓ Todas alterações salvas")
    
    col1, col2 = st.columns([0.5, 2])
    with col1:
        if st.button(
            "💾 Salvar Alterações", 
            key=f"btn_salvar_{nome}_{config['sufixo']}",
            type="primary",
            help="Salva as alterações sem finalizar a planilha"
        ):
            salvar_alteracoes(nome, st.session_state[f"df_editado_{config['sufixo']}"], config=config)
    
    with col2:
        historico = carregar_historico(config['arquivo_historico'])
        status_atual = historico[nome]["finalizado"]
        btn_texto = "⏸️ Voltar para Andamento" if status_atual else "✅ Finalizar Planilha"
        if st.button(
            btn_texto, 
            key=f"btn_status_{nome}_{config['sufixo']}",
            help="Alterna entre status de andamento/finalizada"
        ):
            salvar_alteracoes(nome, st.session_state[f"df_editado_{config['sufixo']}"], finalizar=not status_atual, config=config)
            st.rerun()

def render_confirmacao_exclusao(config):
    """Renderiza a confirmação de exclusão se necessário"""
    if not st.session_state[f"planilha_a_excluir_{config['sufixo']}"]:
        return
    
    nome = st.session_state[f"planilha_a_excluir_{config['sufixo']}"]
    st.warning(f"⚠️ Tem certeza que deseja excluir '{nome}'?")
    col_conf1, col_conf2 = st.columns(2)
    with col_conf1:
        if st.button(
            "✅ Sim, excluir", 
            key=f"btn_confirmar_exclusao_{config['sufixo']}", 
            type="primary"
        ):
            excluir_planilha(nome, config)
    with col_conf2:
        if st.button(
            "❌ Cancelar", 
            key=f"btn_cancelar_exclusao_{config['sufixo']}"
        ):
            st.session_state[f"planilha_a_excluir_{config['sufixo']}"] = None
            st.rerun()

def render_tab_content(config):
    """Renderiza todo o conteúdo de uma aba"""
    st.title(config['titulo'])
    
    # Seção administrativa
    render_admin_section(config)
    
    # Seção de edição
    render_edicao_section(config)
    
    # Confirmação de exclusão (se necessário)
    render_confirmacao_exclusao(config)

# ========== MAIN INTERFACE ==========
def main():
    # Cria as abas PRINCIPAIS
    tab1, tab2, tab3 = st.tabs([CONFIG_T1['titulo'], CONFIG_T2['titulo'], CONFIG_T3['titulo']])
    
    with tab1:
        render_tab_content(CONFIG_T1)
    
    with tab2:
        render_tab_content(CONFIG_T2)
        
    with tab3:
        render_tab_content(CONFIG_T3)

# Executa o aplicativo
if __name__ == "__main__":
    main()