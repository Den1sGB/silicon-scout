import re
import time
import urllib.parse
from typing import Dict, Any

MAX_TENTATIVAS_POLLING = 45
TEMPO_ESPERA_POLLING_SEG = 1

def limpar_preco(texto: str) -> int:
    limpo = re.sub(r"[^\d,]", "", texto).replace(",", ".")
    return int(float(limpo) * 100) if limpo else None

def raspar_terabyte(page, produto_db) -> Dict[str, Any]:
    print("[Terabyte] Extraindo dados da pagina alvo...")
    
    is_link_direto = produto_db.tipo_rastreio == "LINK"
    url_alvo = produto_db.url_direta if is_link_direto else f"https://www.terabyteshop.com.br/busca?str={urllib.parse.quote(produto_db.termo_busca)}"
    res = {"loja": "Terabyte", "nome_produto": produto_db.nome_produto, "preco_pix_centavos": None, "preco_cartao_centavos": None, "status": "ESGOTADO", "url": url_alvo, "nome_encontrado": None}
    
    try:
        print("[Terabyte] Navegando direto para a rota alvo...")
        page.goto(url_alvo, wait_until="domcontentloaded", timeout=45000)
        
        cards = []
        tentativas = 0
        while tentativas < MAX_TENTATIVAS_POLLING:
            page.mouse.wheel(0, 800)
            time.sleep(TEMPO_ESPERA_POLLING_SEG)
            
            seletor_base = '#produto-detalhes, .col-md-9' if is_link_direto else '.pbox, [class*="product-item" i], a'
            elementos = page.locator(seletor_base).filter(has_text="R$").all()
            
            if len(elementos) > 0:
                print(f"[Terabyte] Elementos renderizados em {tentativas + 1}s. Analisando {len(elementos)} bloco(s)...")
                cards = elementos
                break
            tentativas += 1
            
        if not cards:
            print("[Terabyte] [Aviso] O site nao renderizou produtos no tempo limite.")
            return res
        
        produtos_validos = []
        for card in cards:
            try: 
                dados = card.evaluate("""el => {
                    let anchor = el.tagName === 'A' ? el : el.querySelector('a');
                    let h1 = document.querySelector('h1');
                    let titleEl = h1 ? h1 : (el.querySelector('.prod-name') || el.querySelector('h2'));
                    return { txt: el.innerText || '', title: titleEl ? titleEl.innerText.trim() : document.title, href: el.href || (anchor ? anchor.href : '') }
                }""")
                txt = dados['txt'].lower().replace('\n', ' ').replace('\r', '')
                titulo_limpo = dados['title'].split('\n')[0]
                link_extraido = dados['href']
            except: continue
            
            if not is_link_direto:
                lixo = ["pc gamer", "computador", "t-gamer", "mancer", "kit upgrade", "ryzen", "intel core"]
                if produto_db.categoria == "PLACA DE VÍDEO" and any(x in txt for x in lixo): continue
                if not all(p in txt for p in produto_db.termo_busca.lower().split()): continue
                
            precos_grandes = [limpar_preco(pr) for pr in re.findall(r"r\$\s*[\d\.]+\,\d{2}", txt) if limpar_preco(pr) and limpar_preco(pr) > 100000]
            if precos_grandes:
                preco_pix = min(precos_grandes)
                preco_cartao = max(precos_grandes)
                
                match_parcela = re.search(r"\b(\d{1,2})\s*x.{0,30}?r\$\s*([\d\.]+\,\d{2})", txt)
                if match_parcela:
                    vezes = int(match_parcela.group(1)); valor_parcela = limpar_preco(match_parcela.group(2))
                    if valor_parcela: preco_cartao = vezes * valor_parcela
                
                link_final = url_alvo
                if not is_link_direto and link_extraido: link_final = link_extraido
                if link_final.startswith("/"): link_final = f"https://www.terabyteshop.com.br{link_final}"
                
                produtos_validos.append({"pix": preco_pix, "cartao": preco_cartao, "url": link_final, "titulo": titulo_limpo})
                
        if produtos_validos:
            produtos_validos.sort(key=lambda x: x["pix"])
            res["preco_pix_centavos"], res["preco_cartao_centavos"], res["url"], res["nome_encontrado"], res["status"] = produtos_validos[0]["pix"], produtos_validos[0]["cartao"], produtos_validos[0]["url"], produtos_validos[0]["titulo"], "DISPONÍVEL"
    except Exception as e: 
        print(f"[Terabyte] [Erro] Falha na execucao: {e}")
    return res