from database import engine, Base

def resetar_banco_de_dados():
    """
    Script de emergência para limpar completamente o banco de dados.
    Utiliza DROP ALL para destruir a estrutura antiga e CREATE ALL para montar a nova.
    """
    print("🧹 Iniciando a limpeza profunda e recriação do Silicon Scout...")
    try:
        # Destrói todas as tabelas antigas (Apaga a estrutura)
        Base.metadata.drop_all(bind=engine)
        print("💥 Tabelas antigas destruídas com sucesso.")
        
        # Recria as tabelas com as colunas novas da arquitetura Híbrida
        Base.metadata.create_all(bind=engine)
        print("✨ Banco de dados 100% recriado e atualizado para a nova arquitetura Híbrida!")
    except Exception as e:
        print(f"❌ Erro crítico ao resetar o banco de dados: {e}")

if __name__ == "__main__":
    resetar_banco_de_dados()