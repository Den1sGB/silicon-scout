import streamlit as st
import pandas as pd
import sys, os
from streamlit_autorefresh import st_autorefresh

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database import (cadastrar_produto_por_termo, cadastrar_produto_por_link, listar_produtos_monitorados, 
                      deletar_produto, obter_historico_formatado, obter_configuracao_intervalo, atualizar_configuracao_intervalo)

st.set_page_config(page_title="Silicon Scout", layout="wide")
count = st_autorefresh(interval=10000, limit=None, key="frequencia_radar")

st.title("Silicon Scout")
st.markdown("Painel de Controle e Monitoramento")
st.divider()

aba_dashboard, aba_cadastro, aba_sistema, aba_gerenciar = st.tabs(["Dashboard", "Novo Rastreio", "Configurações", "Gerenciar Alvos"])

with aba_dashboard:
    dados_historico = obter_historico_formatado()
    if dados_historico:
        df = pd.DataFrame(dados_historico).drop_duplicates(subset=["Hardware", "Loja"], keep="first")
        
        def formatar_moeda(valor): 
            return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if not pd.isna(valor) else "Indisponível"
        
        df["PIX (À Vista)"] = df["Valor PIX"].apply(formatar_moeda)
        df["Cartão (Parcelado)"] = df["Valor Cartão"].apply(formatar_moeda)
        
        st.dataframe(
            df[["Categoria", "Hardware", "Loja", "Status", "PIX (À Vista)", "Cartão (Parcelado)", "Data", "Link"]], 
            use_container_width=True, 
            hide_index=True, 
            column_config={"Link": st.column_config.LinkColumn("Ação", display_text="Acessar Loja")}
        )
    else: 
        st.info("O banco de dados está vazio. Nenhum registro encontrado.")

with aba_cadastro:
    tipo_cadastro = st.radio("Método de Rastreamento:", ["Busca Dinâmica (Termo)", "Busca Direta (URL)"], horizontal=True)
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        categoria = st.selectbox("Categoria", ["PLACA DE VÍDEO", "PROCESSADOR", "PLACA MÃE", "MEMÓRIA RAM", "OUTROS"])
        modelo = st.text_input("Identificador / Modelo")
    
    with col2:
        if "Termo" in tipo_cadastro:
            st.info("Busca Dinâmica: O scraper analisará os resultados da pesquisa para encontrar o menor valor correspondente.")
            termo_busca = st.text_input("Termo de Busca Exato", placeholder="Ex: rx 9060 xt asrock")
            if st.button("Ativar Busca Dinâmica", type="primary"):
                if modelo and termo_busca:
                    if cadastrar_produto_por_termo(categoria, modelo, termo_busca.strip()):
                        st.success("Alvo dinâmico registrado com sucesso.")
                else: 
                    st.error("Preencha todos os campos obrigatórios.")
        else:
            st.warning("Busca Direta: O scraper acessará exclusivamente a URL informada.")
            loja_alvo = st.selectbox("Loja", ["KABUM", "PICHAU", "TERABYTE"])
            url_direta = st.text_input("URL Direta do Produto")
            if st.button("Ativar Busca Direta", type="primary"):
                if modelo and url_direta:
                    if cadastrar_produto_por_link(categoria, modelo, loja_alvo, url_direta.strip()):
                        st.success("Alvo direto registrado com sucesso.")
                else: 
                    st.error("Insira a URL do produto.")

with aba_sistema:
    st.subheader("Parâmetros de Execução")
    st.markdown("Atenção: Intervalos muito curtos ou ausentes aumentarão o consumo de hardware e o risco de bloqueio por rate-limiting.")
    
    intervalo_atual = obter_configuracao_intervalo()
    is_instantaneo = (intervalo_atual == 0)
    
    modo_instantaneo = st.toggle("Modo Contínuo (Sem intervalo de espera)", value=is_instantaneo)
    
    if modo_instantaneo:
        st.error("Modo Contínuo Ativado: As requisições ocorrerão em loop sequencial.")
        novo_intervalo = 0
    else:
        slider_val = intervalo_atual if intervalo_atual > 0 else 5
        novo_intervalo = st.slider("Intervalo entre execuções (Minutos)", min_value=1, max_value=60, value=slider_val)
    
    if st.button("Salvar Configuração", type="primary"):
        atualizar_configuracao_intervalo(novo_intervalo)
        st.success("Configuração atualizada. O scraper adotará os novos parâmetros no próximo ciclo.")

with aba_gerenciar:
    produtos = listar_produtos_monitorados()
    if produtos:
        df_prods = pd.DataFrame([{"ID": p.id, "Tipo": p.tipo_rastreio, "Produto": p.nome_produto, "Alvo": p.termo_busca if p.tipo_rastreio == 'TERMO' else p.url_direta} for p in produtos])
        st.dataframe(df_prods, use_container_width=True, hide_index=True)
        alvo = st.selectbox("Selecione um alvo para remoção:", {f"ID {p.id} | {p.nome_produto}": p.id for p in produtos}.keys())
        if st.button("Excluir Alvo", type="primary"): 
            deletar_produto({f"ID {p.id} | {p.nome_produto}": p.id for p in produtos}[alvo])
            st.rerun()