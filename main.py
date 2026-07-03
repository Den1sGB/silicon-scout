import time
import requests
from playwright.sync_api import sync_playwright
from database import listar_produtos_monitorados, salvar_preco, obter_configuracao_intervalo, obter_ultimo_preco_item
from scraper.pichau import raspar_pichau
from scraper.kabum import raspar_kabum
from scraper.terabyte import raspar_terabyte

# Configuração da Integração
DISCORD_WEBHOOK_URL = "SEU_WEBHOOK_DO_DISCORD_AQUI"

def notificar_discord(mensagem):
    """ Envia um payload via POST para o webhook configurado. """
    if not DISCORD_WEBHOOK_URL or DISCORD_WEBHOOK_URL == "SEU_WEBHOOK_DO_DISCORD_AQUI":
        return
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": mensagem})
    except Exception as e:
        print(f"[Aviso] Falha ao enviar notificacao para o Discord: {e}")

def auditar_resultado(resultado, produto):
    """ Avalia a variacao de preco e persiste os dados. Dispara alertas em caso de queda. """
    if resultado and resultado.get("preco_pix_centavos"):
        preco_pix = resultado["preco_pix_centavos"]
        ultimo_preco = obter_ultimo_preco_item(produto.nome_produto, resultado["url"])
        
        salvar_preco(produto.categoria, produto.nome_produto, preco_pix, resultado["preco_cartao_centavos"], resultado["status"], resultado["url"])
        
        if ultimo_preco and preco_pix < ultimo_preco:
            print("\a\a\a")  # ASCII Bell (Alarme do sistema)
            print("\n" + "="*60)
            print("ALERTA DE QUEDA DE PRECO DETECTADA")
            print(f"Produto: {produto.nome_produto}")
            print(f"Loja:    {resultado['loja']}")
            print(f"Antes:   R$ {ultimo_preco / 100:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            print(f"Atual:   R$ {preco_pix / 100:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            print(f"Link:    {resultado['url']}")
            print("="*60 + "\n")

            # Montagem do payload para o Discord (aqui podemos manter emojis para destaque visual na mensagem)
            msg_discord = (
                f"🚨 **QUEDA DE PREÇO DETECTADA!** 🚨\n\n"
                f"**Produto:** {produto.nome_produto}\n"
                f"**Loja:** {resultado['loja']}\n"
                f"**De:** R$ {ultimo_preco / 100:,.2f}\n"
                f"**Para:** R$ {preco_pix / 100:,.2f}\n"
                f"**Link:** {resultado['url']}"
            )
            notificar_discord(msg_discord)
        else:
            print(f"[{resultado['loja'].upper()}] Gravado: PIX R$ {preco_pix / 100:.2f} | {resultado.get('nome_encontrado', 'Direto da URL')}")

def dormir_inteligentemente():
    """ Gerencia o intervalo entre execucoes baseado na configuracao do banco. """
    inicio_sono = time.time()
    while True:
        intervalo_minutos = obter_configuracao_intervalo()
        if intervalo_minutos == 0:
            print("[Info] Modo Instantaneo ativo. Iniciando proximo ciclo imediatamente.")
            time.sleep(1) # Previne uso excessivo de CPU em loops vazios
            break
            
        if (time.time() - inicio_sono) >= (intervalo_minutos * 60):
            break
        time.sleep(5) 

def executar_ciclo_varredura(context, alvos):
    """ Itera sobre os alvos cadastrados reutilizando o contexto de sessao persistente. """
    for p_bd in alvos:
        print(f"\n[Scraper] Processando alvo: {p_bd.nome_produto} | Tipo: {p_bd.tipo_rastreio}")
        
        if p_bd.tipo_rastreio == "TERMO" or p_bd.loja_alvo == "PICHAU":
            page = context.new_page()
            auditar_resultado(raspar_pichau(page, p_bd), p_bd)
            page.close()
            
        if p_bd.tipo_rastreio == "TERMO" or p_bd.loja_alvo == "KABUM":
            page = context.new_page()
            auditar_resultado(raspar_kabum(page, p_bd), p_bd)
            page.close()
            
        if p_bd.tipo_rastreio == "TERMO" or p_bd.loja_alvo == "TERABYTE":
            page = context.new_page()
            auditar_resultado(raspar_terabyte(page, p_bd), p_bd)
            page.close()

if __name__ == "__main__":
    print("[Sistema] Iniciando motor do web scraper...")
    
    pasta_perfil = "./perfil_robo"
    
    with sync_playwright() as p:
        print("[Playwright] Inicializando contexto de navegador persistente...")
        context = p.chromium.launch_persistent_context(
            user_data_dir=pasta_perfil,
            headless=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            args=["--disable-blink-features=AutomationControlled", "--start-maximized"]
        )
        
        while True:
            alvos = listar_produtos_monitorados()
            if not alvos:
                time.sleep(5)
                continue
                
            intervalo_minutos = obter_configuracao_intervalo()
            modo_str = "Instantaneo" if intervalo_minutos == 0 else f"{intervalo_minutos} min"
            
            print(f"\n[Ciclo] Iniciando varredura. Alvos ativos: {len(alvos)} | Frequencia: {modo_str}")
            
            try:
                executar_ciclo_varredura(context, alvos)
                print("[Ciclo] Varredura finalizada com sucesso.")
            except Exception as e:
                print(f"[Erro] Falha critica durante a execucao do ciclo: {e}")
                
            dormir_inteligentemente()
            
        context.close()