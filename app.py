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
        .premium-banner {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 25px;
            border-radius: 12px;
            margin-top: 30px;
            text-align: center;
        }
        .premium-banner h3 {
            margin-bottom: 10px;
        }
        .premium-banner button {
            background: white;
            color: #f5576c;
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            font-weight: 600;
            cursor: pointer;
            margin-top: 15px;
        }
        .partners-section {
            margin-top: 25px;
        }
        .partners-section h3 {
            color: #333;
            margin-bottom: 15px;
        }
        .partner-card {
            background: white;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 10px;
            border: 1px solid #e0e0e0;
        }
        .partner-name {
            font-weight: 600;
            color: #667eea;
        }
        .partner-qualification {
            color: #666;
            font-size: 0.9rem;
            margin-top: 5px;
        }
        .cnpj-format {
            font-family: monospace;
            background: #e9ecef;
            padding: 2px 8px;
            border-radius: 4px;
        }
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
            
            <div class="premium-banner">
                <h3>⭐ Quer mais dados?</h3>
                <p>Versão Premium: Busca ilimitada, contatos de sócios, emails, telefones e exportação CSV.</p>
                <button>Ver Planos</button>
            </div>
        </div>
    </div>
    
    <script>
        // Format CNPJ as user types
        document.getElementById('cnpjInput').addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 14) value = value.slice(0, 14);
            
            // Format: XX.XXX.XXX/XXXX-XX
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
                result.innerHTML = `<div class="error-message">❌ Erro na busca. Tente novamente.</div>`;
            } finally {
                btn.disabled = false;
                btn.textContent = '🔍 Buscar';
            }
        }
        
        function displayResult(data) {
            const result = document.getElementById('result');
            
            const statusClass = data.situacao === 'ATIVA' ? 'status-active' : 'status-inactive';
            const statusText = data.situacao === 'ATIVA' ? 'Ativa' : 'Inativa';
            
            // Show data sources
            const sourcesHTML = data.sources ? `
                <div style="margin-bottom: 20px;">
                    <span style="color: #666; font-size: 0.9rem;">Fontes: ${data.sources.map(s => {
                        const names = {
                            'receita_federal': 'Receita Federal',
                            'minha_receita': 'Minha Receita',
                            'cnpj_ws': 'CNPJ.ws'
                        };
                        return names[s] || s;
                    }).join(', ')}</span>
                    ${data.enriched ? '<span style="background: #d4edda; color: #155724; padding: 3px 10px; border-radius: 10px; font-size: 0.8rem; margin-left: 10px;">✓ Enriquecido</span>' : ''}
                </div>
            ` : '';
            
            let partnersHTML = '';
            if (data.qsa && data.qsa.length > 0) {
                partnersHTML = `
                    <div class="partners-section">
                        <h3>👥 Sócios</h3>
                        ${data.qsa.map(partner => `
                            <div class="partner-card">
                                <div class="partner-name">${partner.nome_socio}</div>
                                <div class="partner-qualification">${partner.qualificacao_socio || 'Sócio'}</div>
                            </div>
                        `).join('')}
                    </div>
                `;
            }
            
            // Additional contact info
            let contactHTML = '';
            if (data.email || data.telefone) {
                contactHTML = `
                    <div class="info-row">
                        <div class="info-label">Contato</div>
                        <div class="info-value">
                            ${data.email ? `<div>📧 ${data.email}</div>` : ''}
                            ${data.telefone ? `<div>📞 ${data.telefone}</div>` : ''}
                        </div>
                    </div>
                `;
            }
            
            result.innerHTML = `
                <div class="result-card">
                    ${sourcesHTML}
                    
                    <h2>${data.nome_fantasia || data.razao_social}</h2>
                    
                    <div class="info-row">
                        <div class="info-label">Razão Social</div>
                        <div class="info-value">${data.razao_social}</div>
                    </div>
                    
                    <div class="info-row">
                        <div class="info-label">CNPJ</div>
                        <div class="info-value"><span class="cnpj-format">${formatCNPJ(data.cnpj)}</span></div>
                    </div>
                    
                    <div class="info-row">
                        <div class="info-label">Status</div>
                        <div class="info-value"><span class="status-badge ${statusClass}">${statusText}</span></div>
                    </div>
                    
                    <div class="info-row">
                        <div class="info-label">Data Abertura</div>
                        <div class="info-value">${data.data_inicio_atividade || 'N/A'}</div>
                    </div>
                    
                    <div class="info-row">
                        <div class="info-label">Natureza</div>
                        <div class="info-value">${data.natureza_juridica || 'N/A'}</div>
                    </div>
                    
                    <div class="info-row">
                        <div class="info-label">Atividade</div>
                        <div class="info-value">${data.cnae_fiscal_descricao || 'N/A'}</div>
                    </div>
                    
                    <div class="info-row">
                        <div class="info-label">Endereço</div>
                        <div class="info-value">
                            ${data.logradouro || ''} ${data.numero || ''} ${data.complemento || ''}<br>
                            ${data.bairro || ''} - ${data.municipio || ''}/${data.uf || ''}<br>
                            CEP: ${data.cep || 'N/A'}
                        </div>
                    </div>
                    
                    ${contactHTML}
                    
                    <div class="info-row">
                        <div class="info-label">Capital Social</div>
                        <div class="info-value">${data.capital_social ? 'R$ ' + parseFloat(data.capital_social).toLocaleString('pt-BR', {minimumFractionDigits: 2}) : 'N/A'}</div>
                    </div>
                    
                    ${partnersHTML}
                </div>
            `;
        }
        
        function formatCNPJ(cnpj) {
            return cnpj.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5');
        }
        
        // Enter key to search
        document.getElementById('cnpjInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') searchCNPJ();
        });
        
        document.getElementById('nameInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') searchByName();
        });
        
        // Tab switching
        function switchTab(tab) {
            document.querySelectorAll('.search-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.search-panel').forEach(p => p.classList.remove('active'));
            
            document.getElementById('tab-' + tab).classList.add('active');
            document.getElementById('panel-' + tab).classList.add('active');
            document.getElementById('result').innerHTML = '';
        }
        
        // Search by name
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
                result.innerHTML = `<div class="error-message">❌ Erro na busca. Tente novamente.</div>`;
            } finally {
                btn.disabled = false;
                btn.textContent = '🔍 Buscar';
            }
        }
        
        // Display name search results
        function displayNameResults(data) {
            const result = document.getElementById('result');
            
            if (!data.results || data.results.length === 0) {
                result.innerHTML = '<div class="error-message">❌ Nenhuma empresa encontrada</div>';
                return;
            }
            
            let html = `
                <div style="margin-bottom: 15px; color: #666;">
                    ${data.count} resultado(s) encontrado(s) 
                    ${data.sources && data.sources.length > 0 ? '(Fontes: ' + data.sources.join(', ') + ')' : ''}
                </div>
            `;
            
            data.results.forEach(company => {
                let sourceBadge;
                if (company.source === 'Google Search') {
                    sourceBadge = '<span class="source-badge source-gp">Google (Scraping)</span>';
                } else {
                    sourceBadge = '<span class="source-badge source-br">' + (company.source || 'BrasilAPI') + '</span>';
                }
                
                const cnpjLink = company.cnpj 
                    ? `<a href="#" onclick="document.getElementById('cnpjInput').value='${company.cnpj}'; switchTab('cnpj'); searchCNPJ(); return false;" style="color: #667eea;">${formatCNPJ(company.cnpj)}</a>`
                    : '';
                
                html += `
                    <div class="result-card" style="margin-bottom: 15px;">
                        <h3 style="margin-bottom: 10px;">${company.nome_fantasia || company.razao_social} ${sourceBadge}</h3>
                        ${company.razao_social && company.razao_social !== company.nome_fantasia ? `<div style="color: #666; margin-bottom: 10px;">${company.razao_social}</div>` : ''}
                        ${cnpjLink ? `<div style="margin-bottom: 10px;">📋 CNPJ: ${cnpjLink}</div>` : ''}
                        ${company.municipio ? `<div style="color: #666;">📍 ${company.municipio}${company.uf ? '/' + company.uf : ''}</div>` : ''}
                        ${company.endereco ? `<div style="color: #666;">📍 ${company.endereco}</div>` : ''}
                        ${company.snippet ? `<div style="color: #666; font-size: 0.9rem; margin-top: 10px; font-style: italic;">${company.snippet}</div>` : ''}
                    </div>
                `;
            });
            
            result.innerHTML = html;
        }
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
    # Clean CNPJ (remove non-digits)
    cnpj_clean = ''.join(c for c in cnpj if c.isdigit())
    
    if len(cnpj_clean) != 14:
        return jsonify({"error": "CNPJ deve ter 14 dígitos"})
    
    # Initialize combined data
    combined_data = {
        "cnpj": cnpj_clean,
        "sources": [],
        "enriched": False
    }
    
    # Source 1: BrasilAPI (Receita Federal)
    try:
        url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_clean}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            combined_data.update(data)
            combined_data["sources"].append("receita_federal")
    except:
        pass
    
    # Source 2: Minha Receita (alternative)
    try:
        url = f"https://minhareceita.org/{cnpj_clean}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            # Merge data, preferring existing values
            for key, value in data.items():
                if key not in combined_data or not combined_data[key]:
                    combined_data[key] = value
            combined_data["sources"].append("minha_receita")
    except:
        pass
    
    # Source 3: CNPJ.ws (another alternative)
    try:
        url = f"https://publica.cnpj.ws/cnpj/{cnpj_clean}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            # Extract useful data
            if "estabelecimento" in data:
                est = data["estabelecimento"]
                if "email" in est and not combined_data.get("email"):
                    combined_data["email"] = est["email"]
                if "telefone1" in est and not combined_data.get("telefone"):
                    combined_data["telefone"] = est["telefone1"]
            combined_data["sources"].append("cnpj_ws")
    except:
        pass
    
    # Check if we got any data
    if len(combined_data["sources"]) == 0:
        return jsonify({"error": "CNPJ não encontrado em nenhuma fonte"})
    
    combined_data["enriched"] = len(combined_data["sources"]) > 1
    return jsonify(combined_data)

@app.route('/api/search')
def search_companies():
    """Search companies by name - queries multiple APIs"""
    query = request.args.get('q', '').strip()
    
    if not query or len(query) < 3:
        return jsonify({"error": "Digite pelo menos 3 caracteres"})
    
    results = []
    sources_used = []
    
    # Source 1: BrasilAPI - search by name (returns list of CNPJs)
    try:
        url = f"https://brasilapi.com.br/api/cnpj/v1/empresas?q={requests.utils.quote(query)}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                for item in data[:5]:  # Limit to 5 results
                    results.append({
                        "cnpj": item.get("cnpj", ""),
                        "razao_social": item.get("razao_social", ""),
                        "nome_fantasia": item.get("nome_fantasia", ""),
                        "source": "BrasilAPI",
                        "type": "api"
                    })
                sources_used.append("brasilapi")
    except:
        pass
    
    # Source 2: Try to get details for found CNPJs from other sources
    enriched_results = []
    for company in results:
        if company.get("cnpj"):
            try:
                # Try Minha Receita for more details
                url = f"https://minhareceita.org/{company['cnpj']}"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    company["municipio"] = data.get("municipio", "")
                    company["uf"] = data.get("uf", "")
                    company["situacao"] = data.get("situacao", "")
            except:
                pass
        enriched_results.append(company)
    
    # Source 3: Web Scraping - Google Search
    try:
        # Scrape Google Search for company info
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        search_url = f"https://www.google.com/search?q={requests.utils.quote(query + ' empresa CNPJ Brazil')}"
        response = requests.get(search_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract company info from search results
            # Look for CNPJ patterns in results
            cnpj_pattern = r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}'
            found_cnpjs = re.findall(cnpj_pattern, response.text)
            
            # Look for company names in search results
            results_divs = soup.find_all('div', class_='g')
            for div in results_divs[:3]:
                title_elem = div.find('h3')
                if title_elem:
                    title = title_elem.get_text()
                    # Skip if already in results
                    if not any(r.get('nome_fantasia') == title or r.get('razao_social') == title for r in enriched_results):
                        snippet_elem = div.find('div', {'data-sncf': '1'})
                        snippet = snippet_elem.get_text() if snippet_elem else ''
                        
                        # Extract CNPJ from snippet if present
                        cnpj_in_snippet = re.findall(cnpj_pattern, snippet)
                        cnpj = cnpj_in_snippet[0].replace('.', '').replace('/', '').replace('-', '') if cnpj_in_snippet else ''
                        
                        enriched_results.append({
                            "nome_fantasia": title,
                            "razao_social": title,
                            "cnpj": cnpj,
                            "snippet": snippet[:200] + '...' if len(snippet) > 200 else snippet,
                            "source": "Google Search",
                            "type": "scraping"
                        })
            
            if found_cnpjs or results_divs:
                sources_used.append("google_scraping")
    except Exception as e:
        print(f"Scraping error: {e}")
        pass
    
    # Source 4: Web Scraping - LinkedIn (public pages)
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        linkedin_url = f"https://www.linkedin.com/company/{query.lower().replace(' ', '-')}"
        # Note: LinkedIn blocks most scraping, this is a placeholder for future implementation
        # Would need proper scraping tools or LinkedIn API
    except:
        pass
    
    return jsonify({
        "query": query,
        "count": len(enriched_results),
        "sources": sources_used,
        "results": enriched_results
    })

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))