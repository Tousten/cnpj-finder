# CNPJ Finder - B2B Lead Generation Tool for Brazil
# Multi-source data enrichment

from flask import Flask, render_template_string, request, jsonify
import requests
import os
import re
from bs4 import BeautifulSoup

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'cnpj-finder-key')

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CNPJ Finder - Busca de Empresas</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            min-height: 100vh; 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            padding: 20px; 
        }
        .container { 
            width: 100%; 
            max-width: 800px; 
            background: white; 
            border-radius: 20px; 
            box-shadow: 0 25px 80px rgba(0,0,0,0.3); 
            overflow: hidden; 
        }
        .header { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
            padding: 40px; 
            text-align: center; 
        }
        .header h1 { font-size: 2rem; margin-bottom: 10px; }
        .header p { opacity: 0.9; font-size: 1.1rem; }
        .content { padding: 40px; }
        .search-tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        .search-tab {
            flex: 1;
            padding: 15px;
            background: #f0f0f0;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s;
        }
        .search-tab.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .search-panel {
            display: none;
        }
        .search-panel.active {
            display: block;
        }
        .search-box {
            display: flex;
            gap: 15px;
            margin-bottom: 30px;
        }
        .search-box input {
            flex: 1;
            padding: 18px 25px;
            border: 2px solid #e0e0e0;
            border-radius: 12px;
            font-size: 1.1rem;
            outline: none;
            transition: border-color 0.3s;
        }
        .search-box input:focus {
            border-color: #667eea;
        }
        .search-box button {
            padding: 18px 35px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .search-box button:hover {
            transform: translateY(-2px);
        }
        .search-box button:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        .result-card {
            background: #f8f9fa;
            border-radius: 16px;
            padding: 30px;
            margin-top: 20px;
            border-left: 5px solid #667eea;
        }
        .result-card h2 {
            color: #333;
            margin-bottom: 20px;
            font-size: 1.5rem;
        }
        .info-row {
            display: flex;
            padding: 12px 0;
            border-bottom: 1px solid #e0e0e0;
        }
        .info-row:last-child {
            border-bottom: none;
        }
        .info-label {
            width: 150px;
            color: #666;
            font-weight: 600;
        }
        .info-value {
            flex: 1;
            color: #333;
        }
        .status-badge {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
        }
        .status-active {
            background: #d4edda;
            color: #155724;
        }
        .status-inactive {
            background: #f8d7da;
            color: #721c24;
        }
        .error-message {
            background: #f8d7da;
            color: #721c24;
            padding: 20px;
            border-radius: 12px;
            margin-top: 20px;
        }
        .source-badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 15px;
            font-size: 0.75rem;
            margin-left: 10px;
        }
        .source-br {
            background: #e3f2fd;
            color: #1565c0;
        }
        .source-gp {
            background: #fff3e0;
            color: #ef6c00;
        }
        .cnpj-format {
            font-family: monospace;
            background: #e9ecef;
            padding: 2px 8px;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 CNPJ Finder</h1>
            <p>Busque informações de empresas brasileiras</p>
        </div>
        <div class="content">
            <div class="search-tabs">
                <button class="search-tab active" onclick="switchTab('cnpj')" id="tab-cnpj">Buscar por CNPJ</button>
                <button class="search-tab" onclick="switchTab('name')" id="tab-name">Buscar por Nome</button>
            </div>
            
            <div class="search-panel active" id="panel-cnpj">
                <div class="search-box">
                    <input type="text" id="cnpjInput" placeholder="Digite o CNPJ (apenas números)" maxlength="18">
                    <button onclick="searchCNPJ()" id="searchBtn">🔍 Buscar</button>
                </div>
            </div>
            
            <div class="search-panel" id="panel-name">
                <div class="search-box">
                    <input type="text" id="nameInput" placeholder="Digite o nome da empresa">
                    <button onclick="searchByName()" id="searchNameBtn">🔍 Buscar</button>
                </div>
            </div>
            
            <div id="result"></div>
        </div>
    </div>
    
    <script>
        // Format CNPJ as user types
        document.getElementById('cnpjInput').addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 14) value = value.slice(0, 14);
            if (value.length > 12) {
                value = value.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5');
            } else if (value.length > 8) {
                value = value.replace(/(\d{2})(\d{3})(\d{3})(\d+)/, '$1.$2.$3/$4');
            } else if (value.length > 5) {
                value = value.replace(/(\d{2})(\d{3})(\d+)/, '$1.$2.$3');
            } else if (value.length > 2) {
                value = value.replace(/(\d{2})(\d+)/, '$1.$2');
            }
            e.target.value = value;
        });
        
        async function searchCNPJ() {
            const input = document.getElementById('cnpjInput');
            const btn = document.getElementById('searchBtn');
            const result = document.getElementById('result');
            const cnpj = input.value.replace(/\D/g, '');
            
            if (cnpj.length !== 14) {
                result.innerHTML = '<div class="error-message">❌ CNPJ deve ter 14 dígitos</div>';
                return;
            }
            
            btn.disabled = true;
            btn.textContent = '⏳ Buscando...';
            result.innerHTML = '';
            
            try {
                const response = await fetch('/api/cnpj/' + cnpj);
                const data = await response.json();
                if (data.error) {
                    result.innerHTML = `<div class="error-message">❌ ${data.error}</div>`;
                } else {
                    displayResult(data);
                }
            } catch (error) {
                result.innerHTML = `<div class="error-message">❌ Erro na busca</div>`;
            } finally {
                btn.disabled = false;
                btn.textContent = '🔍 Buscar';
            }
        }
        
        function displayResult(data) {
            const result = document.getElementById('result');
            
            let partnersHTML = '';
            if (data.qsa && data.qsa.length > 0) {
                partnersHTML = `<div style="margin-top: 20px;"><h3>👥 Sócios</h3>` + 
                    data.qsa.map(p => `<div style="padding: 10px; background: white; border-radius: 8px; margin-top: 10px;">
                        <strong>${p.nome_socio}</strong><br><small>${p.qualificacao_socio || 'Sócio'}</small>
                    </div>`).join('') + `</div>`;
            }
            
            result.innerHTML = `
                <div class="result-card">
                    <h2>${data.nome_fantasia || data.razao_social}</h2>
                    <div class="info-row"><div class="info-label">CNPJ</div><div class="info-value"><span class="cnpj-format">${formatCNPJ(data.cnpj)}</span></div></div>
                    <div class="info-row"><div class="info-label">Razão Social</div><div class="info-value">${data.razao_social}</div></div>
                    <div class="info-row"><div class="info-label">Atividade</div><div class="info-value">${data.cnae_fiscal_descricao || 'N/A'}</div></div>
                    <div class="info-row"><div class="info-label">Endereço</div><div class="info-value">${data.logradouro || ''} ${data.numero || ''}<br>${data.municipio || ''}/${data.uf || ''}</div></div>
                    ${partnersHTML}
                </div>
            `;
        }
        
        function switchTab(tab) {
            document.querySelectorAll('.search-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.search-panel').forEach(p => p.classList.remove('active'));
            document.getElementById('tab-' + tab).classList.add('active');
            document.getElementById('panel-' + tab).classList.add('active');
            document.getElementById('result').innerHTML = '';
        }
        
        async function searchByName() {
            const input = document.getElementById('nameInput');
            const btn = document.getElementById('searchNameBtn');
            const result = document.getElementById('result');
            const query = input.value.trim();
            
            if (query.length < 3) {
                result.innerHTML = '<div class="error-message">❌ Digite pelo menos 3 caracteres</div>';
                return;
            }
            
            btn.disabled = true;
            btn.textContent = '⏳ Buscando...';
            result.innerHTML = '';
            
            try {
                const response = await fetch('/api/search?q=' + encodeURIComponent(query));
                const data = await response.json();
                if (data.error) {
                    result.innerHTML = `<div class="error-message">❌ ${data.error}</div>`;
                } else {
                    displayNameResults(data);
                }
            } catch (error) {
                result.innerHTML = `<div class="error-message">❌ Erro na busca</div>`;
            } finally {
                btn.disabled = false;
                btn.textContent = '🔍 Buscar';
            }
        }
        
        function displayNameResults(data) {
            const result = document.getElementById('result');
            if (!data.results || data.results.length === 0) {
                result.innerHTML = '<div class="error-message">❌ Nenhuma empresa encontrada. Tente buscar pelo CNPJ diretamente.</div>';
                return;
            }
            
            let html = `<div style="margin-bottom: 15px; color: #666;">${data.count} resultado(s)</div>`;
            
            data.results.forEach(company => {
                const sourceBadge = company.source === 'Google Search' 
                    ? '<span class="source-badge source-gp">Google</span>'
                    : '<span class="source-badge source-br">' + (company.source || 'API') + '</span>';
                
                const cnpjLink = company.cnpj 
                    ? `<a href="#" onclick="document.getElementById('cnpjInput').value='${company.cnpj}'; switchTab('cnpj'); searchCNPJ(); return false;" style="color: #667eea;">${formatCNPJ(company.cnpj)}</a>`
                    : '';
                
                html += `
                    <div class="result-card" style="margin-bottom: 15px;">
                        <h3>${company.nome_fantasia || company.razao_social} ${sourceBadge}</h3>
                        ${cnpjLink ? `<div style="margin: 10px 0;">📋 CNPJ: ${cnpjLink}</div>` : ''}
                        ${company.municipio ? `<div style="color: #666;">📍 ${company.municipio}${company.uf ? '/' + company.uf : ''}</div>` : ''}
                    </div>
                `;
            });
            
            result.innerHTML = html;
        }
        
        function formatCNPJ(cnpj) {
            return cnpj.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5');
        }
        
        document.getElementById('cnpjInput').addEventListener('keypress', e => { if (e.key === 'Enter') searchCNPJ(); });
        document.getElementById('nameInput').addEventListener('keypress', e => { if (e.key === 'Enter') searchByName(); });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/cnpj/<cnpj>')
def get_cnpj(cnpj):
    """Fetch CNPJ data from multiple sources"""
    cnpj_clean = ''.join(c for c in cnpj if c.isdigit())
    if len(cnpj_clean) != 14:
        return jsonify({"error": "CNPJ deve ter 14 dígitos"})
    
    combined_data = {"cnpj": cnpj_clean, "sources": [], "enriched": False}
    
    # Source 1: BrasilAPI
    try:
        url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_clean}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            combined_data.update(response.json())
            combined_data["sources"].append("brasilapi")
    except:
        pass
    
    # Source 2: Minha Receita
    try:
        url = f"https://minhareceita.org/{cnpj_clean}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            for key, value in data.items():
                if key not in combined_data or not combined_data[key]:
                    combined_data[key] = value
            combined_data["sources"].append("minha_receita")
    except:
        pass
    
    if len(combined_data["sources"]) == 0:
        return jsonify({"error": "CNPJ não encontrado"})
    
    combined_data["enriched"] = len(combined_data["sources"]) > 1
    return jsonify(combined_data)

@app.route('/api/search')
def search_companies():
    """Search companies by name"""
    query = request.args.get('q', '').strip()
    if not query or len(query) < 3:
        return jsonify({"error": "Digite pelo menos 3 caracteres"})
    
    results = []
    sources_used = []
    
    # Try name variations
    search_terms = [query]
    base_name = re.sub(r'\s+(brasil|brazil|ltda|me|sa)\s*$', '', query, flags=re.IGNORECASE).strip()
    if base_name and base_name != query:
        search_terms.append(base_name)
    
    for term in search_terms[:2]:
        # BrasilAPI
        try:
            url = f"https://brasilapi.com.br/api/cnpj/v1/empresas?q={requests.utils.quote(term)}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    for item in data[:5]:
                        cnpj = item.get("cnpj", "")
                        if cnpj and not any(r.get("cnpj") == cnpj for r in results):
                            results.append({
                                "cnpj": cnpj,
                                "razao_social": item.get("razao_social", ""),
                                "nome_fantasia": item.get("nome_fantasia", ""),
                                "source": "BrasilAPI"
                            })
                    if "brasilapi" not in sources_used:
                        sources_used.append("brasilapi")
        except:
            pass
        
        # ReceitaWS
        try:
            url = f"https://www.receitaws.com.br/v1/cnpj/search?q={requests.utils.quote(term)}"
            response = requests.get(url, headers={'Accept': 'application/json'}, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("data"):
                    for item in data["data"][:5]:
                        cnpj_clean = item.get("cnpj", "").replace(".", "").replace("/", "").replace("-", "")
                        if cnpj_clean and not any(r.get("cnpj") == cnpj_clean for r in results):
                            results.append({
                                "cnpj": cnpj_clean,
                                "razao_social": item.get("nome", ""),
                                "nome_fantasia": item.get("fantasia", ""),
                                "municipio": item.get("municipio", ""),
                                "uf": item.get("uf", ""),
                                "source": "ReceitaWS"
                            })
                    if "receitaws" not in sources_used:
                        sources_used.append("receitaws")
        except:
            pass
    
    # Google scraping as fallback - IMPROVED
    if len(results) == 0:
        try:
            # More realistic browser headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': 'https://www.google.com/',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Cache-Control': 'max-age=0',
            }
            
            # Try different search queries
            search_queries = [
                query + ' CNPJ',
                query + ' empresa',
                query,
                '"' + query + '"'
            ]
            
            for search_query in search_queries:
                if len(results) > 0:
                    break
                    
                url = f"https://www.google.com/search?q={requests.utils.quote(search_query)}&hl=pt-BR"
                session = requests.Session()
                response = session.get(url, headers=headers, timeout=15, allow_redirects=True)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Look for CNPJ in entire page
                    cnpj_pattern = r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}'
                    found_cnpjs = re.findall(cnpj_pattern, response.text)
                    
                    # Multiple ways to find company names
                    # Method 1: Look for h3 tags (common in Google results)
                    for h3 in soup.find_all('h3'):
                        text = h3.get_text().strip()
                        # Filter out generic titles
                        if len(text) > 5 and len(text) < 100 and not any(x in text.lower() for x in ['google', 'pesquisa', 'search', 'resultados']):
                            if not any(r.get('nome_fantasia') == text or r.get('razao_social') == text for r in results):
                                cnpj = found_cnpjs.pop(0) if found_cnpjs else ''
                                cnpj_clean = cnpj.replace('.', '').replace('/', '').replace('-', '') if cnpj else ''
                                results.append({
                                    "nome_fantasia": text,
                                    "razao_social": text,
                                    "cnpj": cnpj_clean,
                                    "source": "Google Search",
                                    "type": "scraping"
                                })
                    
                    # Method 2: Look for divs with specific classes
                    if len(results) == 0:
                        for div in soup.find_all(['div', 'span']):
                            text = div.get_text().strip()
                            # Check if it looks like a company name
                            if query.lower() in text.lower() and len(text) > 10 and len(text) < 150:
                                if not any(r.get('nome_fantasia') == text or r.get('razao_social') == text for r in results):
                                    cnpj = found_cnpjs.pop(0) if found_cnpjs else ''
                                    cnpj_clean = cnpj.replace('.', '').replace('/', '').replace('-', '') if cnpj else ''
                                    results.append({
                                        "nome_fantasia": text[:100],
                                        "razao_social": text[:100],
                                        "cnpj": cnpj_clean,
                                        "source": "Google Search",
                                        "type": "scraping"
                                    })
                                    break
                    
                    if results and "google" not in sources_used:
                        sources_used.append("google")
                        break
                        
        except Exception as e:
            print(f"Google scraping error: {e}")
            pass
    
    # Yahoo search scraping as another fallback - IMPROVED
    if len(results) == 0:
        try:
            # Better headers to mimic real browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': 'https://search.yahoo.com/',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            # Try different Yahoo search queries
            yahoo_queries = [
                query + ' CNPJ',
                query + ' empresa Brazil',
                query
            ]
            
            for yahoo_query in yahoo_queries:
                if len(results) > 0:
                    break
                    
                yahoo_url = f"https://search.yahoo.com/search?p={requests.utils.quote(yahoo_query)}"
                session = requests.Session()
                response = session.get(yahoo_url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Look for CNPJ patterns
                    cnpj_pattern = r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}'
                    found_cnpjs = re.findall(cnpj_pattern, response.text)
                    
                    # Multiple parsing strategies for Yahoo
                    # Strategy 1: Look for h3 tags
                    for h3 in soup.find_all('h3'):
                        text = h3.get_text().strip()
                        if len(text) > 5 and len(text) < 100:
                            if query.lower() in text.lower() or any(word in text.lower() for word in query.lower().split()):
                                if not any(r.get('nome_fantasia') == text or r.get('razao_social') == text for r in results):
                                    cnpj = found_cnpjs.pop(0) if found_cnpjs else ''
                                    cnpj_clean = cnpj.replace('.', '').replace('/', '').replace('-', '') if cnpj else ''
                                    results.append({
                                        "nome_fantasia": text,
                                        "razao_social": text,
                                        "cnpj": cnpj_clean,
                                        "source": "Yahoo Search",
                                        "type": "scraping"
                                    })
                    
                    # Strategy 2: Look for specific Yahoo result classes
                    if len(results) == 0:
                        yahoo_classes = ['algo', 'ov-a', 'searchCenterMiddle', 'title', 'd-ib', 'ls0']
                        for class_name in yahoo_classes:
                            elements = soup.find_all(['div', 'li', 'h3', 'a'], class_=class_name)
                            for elem in elements[:3]:
                                text = elem.get_text().strip()
                                if len(text) > 5 and len(text) < 150:
                                    if query.lower() in text.lower():
                                        if not any(r.get('nome_fantasia') == text or r.get('razao_social') == text for r in results):
                                            cnpj = found_cnpjs.pop(0) if found_cnpjs else ''
                                            cnpj_clean = cnpj.replace('.', '').replace('/', '').replace('-', '') if cnpj else ''
                                            results.append({
                                                "nome_fantasia": text[:100],
                                                "razao_social": text[:100],
                                                "cnpj": cnpj_clean,
                                                "source": "Yahoo Search",
                                                "type": "scraping"
                                            })
                                            break
                            if len(results) > 0:
                                break
                    
                    # Strategy 3: Look for any text containing the query
                    if len(results) == 0:
                        for elem in soup.find_all(['div', 'span', 'a', 'h3']):
                            text = elem.get_text().strip()
                            if query.lower() in text.lower() and len(text) > 10 and len(text) < 200:
                                if not any(r.get('nome_fantasia') == text or r.get('razao_social') == text for r in results):
                                    cnpj = found_cnpjs.pop(0) if found_cnpjs else ''
                                    cnpj_clean = cnpj.replace('.', '').replace('/', '').replace('-', '') if cnpj else ''
                                    results.append({
                                        "nome_fantasia": text[:100],
                                        "razao_social": text[:100],
                                        "cnpj": cnpj_clean,
                                        "source": "Yahoo Search",
                                        "type": "scraping"
                                    })
                                    break
                    
                    if results and any(r.get('source') == 'Yahoo Search' for r in results):
                        if "yahoo" not in sources_used:
                            sources_used.append("yahoo")
                        break
                        
        except Exception as e:
            print(f"Yahoo search error: {e}")
            pass
    
    # Bing search scraping as yet another fallback
    if len(results) == 0:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            bing_url = f"https://www.bing.com/search?q={requests.utils.quote(query + ' empresa CNPJ')}"
            response = requests.get(bing_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                cnpj_pattern = r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}'
                found_cnpjs = re.findall(cnpj_pattern, response.text)
                
                for cnpj in found_cnpjs[:2]:
                    cnpj_clean = cnpj.replace('.', '').replace('/', '').replace('-', '')
                    if not any(r.get("cnpj") == cnpj_clean for r in results):
                        results.append({
                            "nome_fantasia": f"Empresa encontrada (Bing)",
                            "razao_social": query,
                            "cnpj": cnpj_clean,
                            "source": "Bing Search"
                        })
                
                if found_cnpjs and "bing" not in sources_used:
                    sources_used.append("bing")
        except:
            pass
    
    return jsonify({
        "query": query,
        "count": len(results),
        "sources": sources_used,
        "results": results
    })

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
