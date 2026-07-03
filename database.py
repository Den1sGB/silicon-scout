from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timedelta

# Configuracao do pool de conexao com o banco de dados
DATABASE_URL = "postgresql://admin:adminpassword@localhost:5432/silicon_scout"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class ProdutoMonitorado(Base):
    """ Entidade representativa dos itens cadastrados para varredura. """
    __tablename__ = "produtos_monitorados"
    id = Column(Integer, primary_key=True, index=True)
    categoria = Column(String, index=True)      
    nome_produto = Column(String, index=True)
    
    # Parametros de rastreamento
    tipo_rastreio = Column(String, default="TERMO") # Opcoes: 'TERMO', 'LINK'
    loja_alvo = Column(String, default="TODAS")     # Opcoes: 'KABUM', 'PICHAU', 'TERABYTE', 'TODAS'
    termo_busca = Column(String, nullable=True)     
    url_direta = Column(String, nullable=True)      

class HistoricoPreco(Base):
    """ Entidade de auditoria para persistencia da linha do tempo de precos. """
    __tablename__ = "historico_precos"
    id = Column(Integer, primary_key=True, index=True)
    categoria = Column(String, index=True)     
    nome_produto = Column(String)              
    preco_pix_centavos = Column(Integer)       
    preco_cartao_centavos = Column(Integer, nullable=True) 
    status = Column(String)                    
    url_produto = Column(String)               
    data_coleta = Column(DateTime, default=lambda: datetime.utcnow() - timedelta(hours=3))

class ConfiguracaoSistema(Base):
    """ Armazena variaveis de ambiente dinâmicas e metricas de execucao. """
    __tablename__ = "configuracoes"
    id = Column(Integer, primary_key=True, index=True)
    intervalo_minutos = Column(Integer, default=5)

Base.metadata.create_all(bind=engine)


def obter_configuracao_intervalo() -> int:
    db = SessionLocal()
    try:
        config = db.query(ConfiguracaoSistema).first()
        if not config:
            config = ConfiguracaoSistema(intervalo_minutos=5)
            db.add(config)
            db.commit()
        return config.intervalo_minutos
    finally:
        db.close()

def atualizar_configuracao_intervalo(minutos: int) -> bool:
    db = SessionLocal()
    try:
        config = db.query(ConfiguracaoSistema).first()
        if config:
            config.intervalo_minutos = minutos
        else:
            db.add(ConfiguracaoSistema(intervalo_minutos=minutos))
        db.commit()
        return True
    finally:
        db.close()

def cadastrar_produto_por_termo(categoria: str, nome: str, termo_busca: str):
    db = SessionLocal()
    try:
        db.add(ProdutoMonitorado(categoria=categoria.upper(), nome_produto=nome, tipo_rastreio="TERMO", loja_alvo="TODAS", termo_busca=termo_busca))
        db.commit()
        return True
    except: 
        return False
    finally: 
        db.close()

def cadastrar_produto_por_link(categoria: str, nome: str, loja_alvo: str, url_direta: str):
    db = SessionLocal()
    try:
        db.add(ProdutoMonitorado(categoria=categoria.upper(), nome_produto=nome, tipo_rastreio="LINK", loja_alvo=loja_alvo.upper(), url_direta=url_direta))
        db.commit()
        return True
    except: 
        return False
    finally: 
        db.close()

def listar_produtos_monitorados():
    db = SessionLocal()
    try: 
        return db.query(ProdutoMonitorado).all()
    finally: 
        db.close()

def deletar_produto(produto_id: int):
    db = SessionLocal()
    try:
        produto = db.query(ProdutoMonitorado).filter(ProdutoMonitorado.id == produto_id).first()
        if produto:
            db.delete(produto)
            db.commit()
            return True
        return False
    finally: 
        db.close()

def salvar_preco(categoria: str, nome: str, preco_pix: int, preco_cartao: int, status: str, url: str):
    db = SessionLocal()
    try:
        db.add(HistoricoPreco(categoria=categoria, nome_produto=nome, preco_pix_centavos=preco_pix, preco_cartao_centavos=preco_cartao, status=status, url_produto=url))
        db.commit()
    except: 
        pass
    finally: 
        db.close()

def obter_historico_formatado():
    db = SessionLocal()
    try:
        registros = db.query(HistoricoPreco).order_by(HistoricoPreco.data_coleta.desc()).all()
        dados = []
        for r in registros:
            loja = "Desconhecida"
            if "kabum.com" in r.url_produto: loja = "KaBuM"
            elif "terabyteshop.com" in r.url_produto: loja = "Terabyte"
            elif "pichau.com" in r.url_produto: loja = "Pichau"

            dados.append({
                "Data": r.data_coleta, "Categoria": r.categoria, "Hardware": r.nome_produto,
                "Loja": loja, "Status": r.status,
                "Valor PIX": (r.preco_pix_centavos / 100) if r.preco_pix_centavos else None,
                "Valor Cartão": (r.preco_cartao_centavos / 100) if r.preco_cartao_centavos else None,
                "Link": r.url_produto
            })
        return dados
    finally: 
        db.close()
    
def obter_ultimo_preco_item(nome_produto: str, url_produto: str):
    """ Retorna o snapshot do ultimo preco registrado para cruzamento de dados. """
    db = SessionLocal()
    try:
        ultimo = db.query(HistoricoPreco).filter(
            HistoricoPreco.nome_produto == nome_produto,
            HistoricoPreco.url_produto == url_produto
        ).order_by(HistoricoPreco.data_coleta.desc()).first()
        return ultimo.preco_pix_centavos if ultimo else None
    finally:
        db.close()