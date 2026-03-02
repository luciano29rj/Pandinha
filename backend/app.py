from flask import Flask, jsonify, request, send_from_directory, send_file, g, render_template
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime, timedelta
import hashlib
import pandas as pd
import secrets
import io
import sys
import platform
import shutil
import psutil
import subprocess
import threading
import time

# ======================================================
# CAMINHOS
# ======================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")
PAGES_DIR = os.path.join(FRONTEND_DIR, "pages")
LARANJA_DIR = os.path.join(FRONTEND_DIR, "laranja")
LARANJA_TEMPLATES_DIR = os.path.join(LARANJA_DIR, "templates")  
LARANJA_SRC_DIR = os.path.join(LARANJA_DIR, "src")  
MIDIA_DIR = os.path.join(FRONTEND_DIR, "midia")
IMAGENS_DIR = os.path.join(MIDIA_DIR, "imagens")
AUDIOS_DIR = os.path.join(MIDIA_DIR, "audios")
PRONUNCIAS_DIR = os.path.join(AUDIOS_DIR, "pronuncias")
BASE_MIDIA = r"C:\Users\lucia\Desktop\Panda\frontend\midia"

DB_QUESTOES = os.path.join(BASE_DIR, "panda_db_questoes.db")
DB_USUARIOS = os.path.join(BASE_DIR, "panda_usuarios.db")
DB_ESTATISTICAS = os.path.join(BASE_DIR, "panda_estatisticas.db")

print(f"BASE_DIR = {BASE_DIR}")
print(f"FRONTEND_DIR = {FRONTEND_DIR}")
print(f"PAGES_DIR = {PAGES_DIR}")
print(f"LARANJA_DIR = {LARANJA_DIR}")
print(f"LARANJA_TEMPLATES_DIR = {LARANJA_TEMPLATES_DIR}")
print(f"LARANJA_SRC_DIR = {LARANJA_SRC_DIR}")
print(f"📁 FRONTEND_DIR: {FRONTEND_DIR}")
print(f"📁 MIDIA_DIR: {MIDIA_DIR}")
print(f"📁 IMAGENS_DIR: {IMAGENS_DIR}")
print(f"📁 PRONUNCIAS_DIR: {PRONUNCIAS_DIR}")
print("="*50)

# ======================================================
# VERIFICAR PASTAS DE MÍDIA
# ======================================================
print("\n" + "="*60)
print("VERIFICANDO PASTAS DE MÍDIA")
print("="*60)

# Caminhos
MIDIA_PATH = os.path.join(FRONTEND_DIR, 'midia')
IMAGENS_PATH = os.path.join(MIDIA_PATH, 'imagens')
ANIMAIS_PATH = os.path.join(IMAGENS_PATH, 'animais')
AUDIOS_PATH = os.path.join(MIDIA_PATH, 'audios', 'pronuncias')

print(f"📁 FRONTEND_DIR: {FRONTEND_DIR}")
print(f"📁 MIDIA_PATH: {MIDIA_PATH}")
print(f"📁 ANIMAIS_PATH: {ANIMAIS_PATH}")
print(f"📁 AUDIOS_PATH: {AUDIOS_PATH}")

# Verificar se as pastas existem
print(f"\n📌 Verificando existência:")
print(f"   MIDIA_PATH existe: {os.path.exists(MIDIA_PATH)}")
print(f"   IMAGENS_PATH existe: {os.path.exists(IMAGENS_PATH)}")
print(f"   ANIMAIS_PATH existe: {os.path.exists(ANIMAIS_PATH)}")
print(f"   AUDIOS_PATH existe: {os.path.exists(AUDIOS_PATH)}")

# Listar arquivos se existirem
if os.path.exists(ANIMAIS_PATH):
    arquivos = os.listdir(ANIMAIS_PATH)
    print(f"\n📄 Arquivos em animais/: {arquivos}")

if os.path.exists(AUDIOS_PATH):
    arquivos = os.listdir(AUDIOS_PATH)
    print(f"📄 Arquivos em pronuncias/: {arquivos[:10]}...")  # Mostra só os 10 primeiros

print("="*60 + "\n")


# ======================================================
# CONFIGURAÇÃO DA APLICAÇÃO FLASK
# ======================================================
app = Flask(__name__, 
           static_folder=FRONTEND_DIR, 
           static_url_path="",
           template_folder=FRONTEND_DIR)  
CORS(app)

# ======================================================
# ATUALIZAR BANCO PARA SUPORTAR MÍDIA E VOZ
# ======================================================

def adicionar_campos_midia():
    """Adicionar campos para imagem, áudio e voz no banco de questões"""
    try:
        conn = sqlite3.connect(DB_QUESTOES)
        cur = conn.cursor()
        
        # Verificar colunas existentes
        cur.execute("PRAGMA table_info(questoes)")
        colunas_existentes = [col[1] for col in cur.fetchall()]
        
        print("\n📊 Verificando colunas do banco de questões...")
        
        # Novas colunas necessárias
        novas_colunas = {
            'tipo_questao': 'TEXT DEFAULT "multipla_escolha"',
            'imagem_path': 'TEXT',
            'imagem_url': 'TEXT', 
            'audio_path': 'TEXT',
            'audio_url': 'TEXT',
            'resposta_voz': 'TEXT',
            'opcoes_voz': 'TEXT'
        }
        
        colunas_adicionadas = 0
        for coluna, tipo in novas_colunas.items():
            if coluna not in colunas_existentes:
                print(f"   ➕ Adicionando coluna: {coluna}")
                cur.execute(f"ALTER TABLE questoes ADD COLUMN {coluna} {tipo}")
                colunas_adicionadas += 1
        
        conn.commit()
        conn.close()
        
        if colunas_adicionadas > 0:
            print(f"✅ {colunas_adicionadas} novas colunas adicionadas ao banco!")
        else:
            print("✅ Banco já está atualizado com todos os campos necessários")
            
    except Exception as e:
        print(f"⚠️ Erro ao adicionar campos: {e}")

def buscar_arquivo(nome_arquivo, tipo):
    pasta_base = os.path.join(BASE_MIDIA, tipo)

    for raiz, dirs, arquivos in os.walk(pasta_base):
        if nome_arquivo in arquivos:
            caminho_relativo = os.path.relpath(
                os.path.join(raiz, nome_arquivo),
                BASE_MIDIA
            )
            return caminho_relativo.replace("\\", "/")

    return None        

# ======================================================
# INTEGRAÇÃO DO MÓDULO LARANJA (orange.py)
# ======================================================
try:
    # Adicionar caminho do src do Laranja ao Python path
    sys.path.append(LARANJA_SRC_DIR)
    
    print("\n" + "="*50)
    print("CARREGANDO MÓDULO LARANJA")
    print("="*50)
    print(f"Caminho do módulo: {LARANJA_SRC_DIR}")
    print(f"Conteúdo: {os.listdir(LARANJA_SRC_DIR) if os.path.exists(LARANJA_SRC_DIR) else 'Diretório não existe'}")
    
    # Forçar o Flask a usar templates do Laranja também
    from jinja2 import ChoiceLoader, FileSystemLoader
    
    # Adicionar o loader do Laranja ao loader principal
    app.jinja_loader = ChoiceLoader([
        app.jinja_loader,
        FileSystemLoader(LARANJA_TEMPLATES_DIR)
    ])
    
    print(f"✅ Loader do Laranja adicionado: {LARANJA_TEMPLATES_DIR}")
    
    # Importar blueprint do Laranja
    from orange import laranja_bp
    
    # Registrar blueprint do Laranja com prefixo '/laranja'
    app.register_blueprint(laranja_bp, url_prefix='/laranja')
    
    print("✅ Módulo Laranja registrado com sucesso!")
    print(f"   Acesse: http://localhost:5000/laranja/")
    print(f"   Teste: http://localhost:5000/laranja/teste")
    print("="*50 + "\n")
    
except ImportError as e:
    print(f"\n⚠️  AVISO: Módulo Laranja não encontrado: {e}")
    print(f"   Diretório LARANJA_SRC_DIR: {LARANJA_SRC_DIR}")
    if os.path.exists(LARANJA_SRC_DIR):
        print(f"   Conteúdo: {os.listdir(LARANJA_SRC_DIR)}")
    else:
        print(f"   ⚠️ Diretório não existe")
except Exception as e:
    print(f"\n⚠️  AVISO: Erro ao carregar módulo Laranja: {e}")
    import traceback
    traceback.print_exc()

# ======================================================
# CONEXÕES COM BANCOS DE DADOS
# ======================================================
def db_questoes():
    conn = sqlite3.connect(DB_QUESTOES)
    conn.row_factory = sqlite3.Row
    return conn

def db_usuarios():
    conn = sqlite3.connect(DB_USUARIOS)
    conn.row_factory = sqlite3.Row
    return conn

def db_estatisticas():
    conn = sqlite3.connect(DB_ESTATISTICAS)
    conn.row_factory = sqlite3.Row
    return conn

# ======================================================
# FUNÇÕES PARA TOKENS DE SESSÃO
# ======================================================
def gerar_token():
    return secrets.token_urlsafe(32)

def criar_token_sessao(usuario_id, dispositivo="web"):
    conn = db_usuarios()
    cur = conn.cursor()
    
    # Limpar tokens expirados
    cur.execute("UPDATE tokens_sessao SET ativo = 0 WHERE expira_em < datetime('now')")
    
    token = gerar_token()
    expira_em = datetime.now() + timedelta(days=30)
    
    cur.execute("""
        INSERT INTO tokens_sessao (usuario_id, token, dispositivo, expira_em, ativo)
        VALUES (?, ?, ?, ?, 1)  -- <-- ADICIONE ', 1' NO FINAL
    """, (usuario_id, token, dispositivo, expira_em.isoformat()))
    
    conn.commit()
    conn.close()
    return token

def validar_token(token):
    if not token:
        return None
    
    conn = db_usuarios()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            t.usuario_id, 
            t.expira_em, 
            t.dispositivo,
            u.nome, 
            u.avatar, 
            u.email,
            u.total_questoes,
            u.total_acertos,
            u.total_erros
        FROM tokens_sessao t
        JOIN usuarios u ON t.usuario_id = u.id
        WHERE t.token = ? AND t.ativo = 1
    """, (token,))
    
    resultado = cur.fetchone()
    
    if not resultado:
        conn.close()
        return None
    
    expira_em = datetime.fromisoformat(resultado["expira_em"])
    if datetime.now() > expira_em:
        cur.execute("UPDATE tokens_sessao SET ativo = 0 WHERE token = ?", (token,))
        conn.commit()
        conn.close()
        return None
    
    # Atualizar último login (apenas uma vez por hora para não sobrecarregar)
    cur.execute("""
        UPDATE usuarios 
        SET ultimo_login = ?
        WHERE id = ? AND (
            ultimo_login IS NULL OR 
            datetime(ultimo_login) < datetime('now', '-1 hour')
        )
    """, (datetime.now().isoformat(), resultado["usuario_id"]))
    
    conn.commit()
    conn.close()
    
    return {
        "id": resultado["usuario_id"],
        "nome": resultado["nome"],
        "email": resultado["email"],
        "avatar": resultado["avatar"],
        "token": token,
        "dispositivo": resultado["dispositivo"],
        "total_questoes": resultado["total_questoes"],
        "total_acertos": resultado["total_acertos"],
        "total_erros": resultado["total_erros"]
    }

def invalidar_tokens_usuario(usuario_id):
    conn = db_usuarios()
    cur = conn.cursor()
    cur.execute("UPDATE tokens_sessao SET ativo = 0 WHERE usuario_id = ?", (usuario_id,))
    conn.commit()
    conn.close()
    return True

def logout_usuario(token):
    conn = db_usuarios()
    cur = conn.cursor()
    cur.execute("UPDATE tokens_sessao SET ativo = 0 WHERE token = ?", (token,))
    conn.commit()
    conn.close()
    return True

# ======================================================
# MIDDLEWARE PARA PROTEGER ROTAS
# ======================================================
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Verificar token no header Authorization
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        # Se não tiver no header, verificar no JSON
        if not token and request.is_json:
            data = request.get_json(silent=True)
            if data and 'token' in data:
                token = data['token']
        
        if not token:
            return jsonify({"success": False, "message": "Token não fornecido"}), 401
        
        # Validar token
        usuario = validar_token(token)
        if not usuario:
            return jsonify({"success": False, "message": "Token inválido ou expirado"}), 401
        
        # Adicionar usuário ao contexto (g) do Flask
        g.usuario = usuario
        
        return f(*args, **kwargs)
    return decorated_function

# ======================================================
# ROTAS PARA O MÓDULO LARANJA (TEMPLATES)
# ======================================================
@app.route("/laranja/templates/<path:filename>")
def laranja_static(filename):
    """Servir arquivos estáticos do Laranja (CSS, JS, imagens)"""
    return send_from_directory(os.path.join(LARANJA_DIR, 'templates'), filename)

# ======================================================
# INICIALIZAÇÃO DOS BANCOS DE DADOS (AJUSTADO PARA SEU BANCO)
# ======================================================
def init_dbs():
    print("\nInicializando bancos de dados...")
    
    # Banco de usuários (panda_usuarios.db)
    conn = db_usuarios()
    cur = conn.cursor()
    
    # Verificar e criar tabela usuarios se não existir
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            email TEXT UNIQUE,
            senha TEXT,
            avatar TEXT DEFAULT '🐼',
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
            ultimo_login TEXT,
            total_questoes INTEGER DEFAULT 0,
            total_acertos INTEGER DEFAULT 0,
            total_erros INTEGER DEFAULT 0,
            ativo INTEGER DEFAULT 1
        )
    """)
    
    # Criar tabela de tokens de sessão se não existir
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tokens_sessao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            token TEXT UNIQUE NOT NULL,
            dispositivo TEXT,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expira_em TIMESTAMP,
            ativo INTEGER DEFAULT 1,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
        )
    """)
    
    # Criar índices
    cur.execute("CREATE INDEX IF NOT EXISTS idx_token ON tokens_sessao(token)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_usuario ON tokens_sessao(usuario_id)")
    
    conn.commit()
    conn.close()
    print("✓ Banco 'usuarios' inicializado")
    
    # Banco de questões (panda_db_questoes.db) - ADICIONAR COLUNAS FALTANTES
    conn = db_questoes()
    cur = conn.cursor()
    
    # Verificar se colunas ativo, dificuldade e dica existem
    cur.execute("PRAGMA table_info(questoes)")
    colunas_existentes = [col[1] for col in cur.fetchall()]
    
    colunas_faltantes = {
        'ativo': 'INTEGER DEFAULT 1',
        'dificuldade': 'TEXT DEFAULT "Médio"',
        'dica': 'TEXT'
    }
    
    for coluna, tipo in colunas_faltantes.items():
        if coluna not in colunas_existentes:
            print(f"Adicionando coluna {coluna} à tabela questoes...")
            cur.execute(f"ALTER TABLE questoes ADD COLUMN {coluna} {tipo}")
    
    conn.commit()
    conn.close()
    print("✓ Banco 'questoes' inicializado")
    
    # Banco de estatísticas
    conn = db_estatisticas()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS estatisticas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            materia TEXT,
            assunto TEXT,
            acertou INTEGER,
            tempo INTEGER,
            data TEXT
        )
    """)
    conn.commit()
    conn.close()
    print("✓ Banco 'estatisticas' inicializado")
    
    # ✅ AGORA CHAMAMOS AQUI (depois de tudo inicializado)
    adicionar_campos_midia()

# ======================================================
# FUNÇÃO DE BUSCA RECURSIVA (ADICIONAR NO INÍCIO DO ARQUIVO)
# ======================================================

def buscar_arquivo_recursivo(nome_arquivo, pasta_raiz):
    """
    Busca um arquivo recursivamente em todas as subpastas
    Retorna o caminho relativo se encontrar, None se não encontrar
    """
    if not nome_arquivo or nome_arquivo.strip() == '':
        return None
    
    nome_arquivo = nome_arquivo.strip()
    
    # Se já é caminho completo, retorna ele mesmo
    if nome_arquivo.startswith('/') or nome_arquivo.startswith('http'):
        return nome_arquivo
    
    # Se tem barras, já é um caminho relativo
    if '/' in nome_arquivo or '\\' in nome_arquivo:
        caminho_completo = os.path.join(pasta_raiz, nome_arquivo.lstrip('/').replace('/', os.sep))
        if os.path.exists(caminho_completo):
            return '/' + nome_arquivo.lstrip('/').replace('\\', '/')
        return nome_arquivo
    
    # Preparar variações do nome
    nome_base, extensao = os.path.splitext(nome_arquivo)
    
    nomes_tentar = [nome_arquivo]
    
    if not extensao:
        extensoes = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', 
                    '.mp3', '.wav', '.ogg', '.m4a', '.aac', '.flac']
        for ext in extensoes:
            nomes_tentar.append(nome_arquivo + ext)
            if ' ' in nome_arquivo:
                nomes_tentar.append(nome_arquivo.replace(' ', '_') + ext)
    else:
        if ' ' in nome_arquivo:
            nomes_tentar.append(nome_arquivo.replace(' ', '_'))
    
    # Busca recursiva
    for raiz, dirs, arquivos in os.walk(pasta_raiz):
        for arquivo in arquivos:
            for nome_tentativa in nomes_tentar:
                if arquivo.lower() == nome_tentativa.lower():
                    caminho_relativo = os.path.relpath(os.path.join(raiz, arquivo), pasta_raiz)
                    caminho_web = '/midia/' + caminho_relativo.replace('\\', '/')
                    return caminho_web
    
    return None

def buscar_na_pasta_midia(nome_arquivo):
    """Busca um arquivo em toda a pasta midia e subpastas"""
    if not nome_arquivo:
        return None
    pasta_midia = os.path.join(FRONTEND_DIR, 'midia')
    return buscar_arquivo_recursivo(nome_arquivo, pasta_midia)

# ======================================================
# FUNÇÕES AUXILIARES
# ======================================================
def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def get_icone_materia(materia):
    icones = {
        'Português': '📚',
        'Matemática': '🔢',
        'História': '🏛️',
        'Ciências': '🔬',
        'Geografia': '🌍',
        'Inglês': '🗽',
        'Artes': '🎨',
        'Educação Física': '⚽',
        'Física': '⚛️',
        'Química': '🧪',
        'Biologia': '🧬'
    }
    return icones.get(materia, '📄')

def get_cor_materia(materia):
    cores = {
        'Português': '#4CAF50',
        'Matemática': '#2196F3',
        'História': '#FF9800',
        'Ciências': '#9C27B0',
        'Geografia': '#795548',
        'Inglês': '#FF5722',
        'Artes': '#E91E63',
        'Educação Física': '#00BCD4',
        'Física': '#3F51B5',
        'Química': '#009688',
        'Biologia': '#8BC34A'
    }
    return cores.get(materia, '#FF9800')

# ======================================================
# INICIALIZAR BANCOS
# ======================================================
init_dbs()

# ======================================================
# ROTAS PRINCIPAIS
# ======================================================
@app.route("/")
def index():
    return send_from_directory(PAGES_DIR, "index.html")

@app.route("/<page>")
def pages(page):
    return send_from_directory(PAGES_DIR, page)

@app.route("/sounds/<path:filename>")
def serve_sound(filename):
    """Servir arquivos de som da pasta frontend/sounds"""
    try:
        sounds_dir = os.path.join(FRONTEND_DIR, "sounds")
        print(f"[SOUNDS] Servindo: {filename} de {sounds_dir}")
        
        if not os.path.exists(sounds_dir):
            print(f"[ERRO] Pasta sounds não existe: {sounds_dir}")
            return "Pasta não encontrada", 404
            
        return send_from_directory(sounds_dir, filename)
    except Exception as e:
        print(f"[ERRO serve_sound]: {e}")
        return str(e), 500
    
@app.route("/api/test-sounds")
def test_sounds():
    """Testar se os sons estão acessíveis"""
    sounds_dir = os.path.join(FRONTEND_DIR, "sounds")
    
    info = {
        "frontend_dir": FRONTEND_DIR,
        "sounds_dir": sounds_dir,
        "sounds_dir_exists": os.path.exists(sounds_dir),
    }
    
    if os.path.exists(sounds_dir):
        files = os.listdir(sounds_dir)
        info["files"] = files
        info["acerto_exists"] = "acerto.mp3" in files
        info["erro_exists"] = "erro.mp3" in files
        
        # Testar acesso aos arquivos
        acerto_path = os.path.join(sounds_dir, "acerto.mp3")
        erro_path = os.path.join(sounds_dir, "erro.mp3")
        info["acerto_readable"] = os.access(acerto_path, os.R_OK) if os.path.exists(acerto_path) else False
        info["erro_readable"] = os.access(erro_path, os.R_OK) if os.path.exists(erro_path) else False
    
    return jsonify(info)

# ======================================================
# ROTAS DE AUTENTICAÇÃO
# ======================================================
@app.route("/api/auth/login", methods=["POST"])
def auth_login():
    data = request.json
    identificador = data.get("identificador")
    senha = data.get("senha")
    lembrar = data.get("lembrar", True)
    dispositivo = data.get("dispositivo", "web")
    
    if not identificador or not senha:
        return jsonify({"success": False, "message": "Dados obrigatórios"})
    
    senha_hash = hash_senha(senha)
    conn = db_usuarios()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT id, nome, email, avatar
        FROM usuarios
        WHERE (nome=? OR email=?) AND senha=?
    """, (identificador, identificador, senha_hash))
    
    user = cur.fetchone()
    
    if not user:
        conn.close()
        return jsonify({"success": False, "message": "Login inválido ou conta desativada"})
    
    token = criar_token_sessao(user["id"], dispositivo)
    
    if not lembrar:
        expira_em = datetime.now() + timedelta(hours=24)
        cur.execute("UPDATE tokens_sessao SET expira_em = ? WHERE token = ?", 
                   (expira_em.isoformat(), token))
        conn.commit()
    
    conn.close()
    
    return jsonify({
        "success": True,
        "user": {
            "id": user["id"],
            "nome": user["nome"],
            "avatar": user["avatar"],
            "email": user["email"]
        },
        "token": token,
        "lembrar": lembrar
    })

@app.route("/api/auth/register", methods=["POST"])
def auth_register():
    """Registrar novo usuário"""
    try:
        data = request.json
        nome = data.get("nome", "").strip()
        email = data.get("email", "").strip()
        senha = data.get("senha", "").strip()
        avatar = data.get("avatar", "🐼")
        
        # Validações
        if not nome:
            return jsonify({"success": False, "message": "Nome é obrigatório"}), 400
        if not email:
            return jsonify({"success": False, "message": "Email é obrigatório"}), 400
        if not senha:
            return jsonify({"success": False, "message": "Senha é obrigatória"}), 400
        if len(senha) < 6:
            return jsonify({"success": False, "message": "Senha deve ter pelo menos 6 caracteres"}), 400
        
        senha_hash = hash_senha(senha)
        conn = db_usuarios()
        cur = conn.cursor()
        
        # Verificar se email já existe
        cur.execute("SELECT id FROM usuarios WHERE email = ?", (email,))
        if cur.fetchone():
            conn.close()
            return jsonify({"success": False, "message": "Email já cadastrado"}), 400
        
        # Inserir novo usuário
        cur.execute("""
            INSERT INTO usuarios (nome, email, senha, avatar, criado_em, ativo)
            VALUES (?, ?, ?, ?, datetime('now'), 1)
        """, (nome, email, senha_hash, avatar))
        
        user_id = cur.lastrowid
        conn.commit()
        
        # Criar token automaticamente
        token = criar_token_sessao(user_id, "web")
        
        cur.execute("""
            SELECT id, nome, email, avatar 
            FROM usuarios WHERE id = ?
        """, (user_id,))
        
        user = cur.fetchone()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "Usuário registrado com sucesso",
            "user": dict(user),
            "token": token
        })
        
    except Exception as e:
        print(f"[ERRO /api/auth/register]: {e}")
        return jsonify({"success": False, "message": "Erro ao registrar usuário"}), 500

@app.route("/api/auth/check", methods=["POST"])
def auth_check():
    data = request.json
    token = data.get("token")
    
    if not token:
        return jsonify({"success": False, "message": "Token não fornecido"})
    
    usuario = validar_token(token)
    
    if usuario:
        return jsonify({
            "success": True,
            "user": {
                "id": usuario["id"],
                "nome": usuario["nome"],
                "avatar": usuario["avatar"],
                "email": usuario["email"]
            },
            "token": usuario["token"]
        })
    else:
        return jsonify({"success": False, "message": "Sessão expirada ou inválida"})

@app.route("/api/auth/logout", methods=["POST"])
def auth_logout():
    data = request.json
    token = data.get("token")
    
    if not token:
        return jsonify({"success": False, "message": "Token não fornecido"})
    
    logout_usuario(token)
    
    return jsonify({
        "success": True,
        "message": "Logout realizado"
    })

# ======================================================
# ROTAS DE PERFIL E GERENCIAMENTO (NOVAS)
# ======================================================

@app.route("/api/auth/perfil", methods=["GET"])
@login_required
def auth_perfil():
    """Obter dados completos do perfil do usuário logado"""
    try:
        conn = db_usuarios()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                id, nome, email, avatar, 
                criado_em, ultimo_login,
                total_questoes, total_acertos, total_erros
            FROM usuarios 
            WHERE id = ?
        """, (g.usuario["id"],))
        
        usuario = cur.fetchone()
        conn.close()
        
        if not usuario:
            return jsonify({"success": False, "message": "Usuário não encontrado"}), 404
        
        # Calcular porcentagem de acertos
        total = usuario["total_acertos"] + usuario["total_erros"]
        porcentagem = 0
        if total > 0:
            porcentagem = round((usuario["total_acertos"] / total) * 100, 2)
        
        return jsonify({
            "success": True,
            "usuario": {
                "id": usuario["id"],
                "nome": usuario["nome"],
                "email": usuario["email"],
                "avatar": usuario["avatar"],
                "criado_em": usuario["criado_em"],
                "ultimo_login": usuario["ultimo_login"],
                "total_questoes": usuario["total_questoes"],
                "total_acertos": usuario["total_acertos"],
                "total_erros": usuario["total_erros"],
                "porcentagem_acertos": porcentagem,
                "total_tentativas": total
            }
        })
        
    except Exception as e:
        print(f"[ERRO /api/auth/perfil]: {e}")
        return jsonify({"success": False, "message": "Erro ao buscar perfil"}), 500

@app.route("/api/auth/atualizar-perfil", methods=["PUT"])
@login_required
def auth_atualizar_perfil():
    """Atualizar nome e avatar do usuário"""
    try:
        data = request.json
        nome = data.get("nome")
        avatar = data.get("avatar")
        
        if not nome:
            return jsonify({"success": False, "message": "Nome é obrigatório"}), 400
        
        conn = db_usuarios()
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE usuarios 
            SET nome = ?, avatar = ?
            WHERE id = ?
        """, (nome, avatar, g.usuario["id"]))
        
        conn.commit()
        conn.close()
        
        # Atualizar dados na sessão atual
        g.usuario["nome"] = nome
        g.usuario["avatar"] = avatar
        
        return jsonify({
            "success": True,
            "message": "Perfil atualizado com sucesso",
            "usuario": {
                "id": g.usuario["id"],
                "nome": nome,
                "avatar": avatar,
                "email": g.usuario["email"]
            }
        })
        
    except Exception as e:
        print(f"[ERRO /api/auth/atualizar-perfil]: {e}")
        return jsonify({"success": False, "message": "Erro ao atualizar perfil"}), 500

@app.route("/api/auth/alterar-senha", methods=["PUT"])
@login_required
def auth_alterar_senha():
    """Alterar senha do usuário"""
    try:
        data = request.json
        senha_atual = data.get("senha_atual")
        nova_senha = data.get("nova_senha")
        
        if not senha_atual or not nova_senha:
            return jsonify({
                "success": False, 
                "message": "Senha atual e nova senha são obrigatórias"
            }), 400
        
        if len(nova_senha) < 6:
            return jsonify({
                "success": False, 
                "message": "A nova senha deve ter pelo menos 6 caracteres"
            }), 400
        
        # Verificar senha atual
        senha_atual_hash = hash_senha(senha_atual)
        
        conn = db_usuarios()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id FROM usuarios 
            WHERE id = ? AND senha = ?
        """, (g.usuario["id"], senha_atual_hash))
        
        if not cur.fetchone():
            conn.close()
            return jsonify({
                "success": False, 
                "message": "Senha atual incorreta"
            }), 401
        
        # Atualizar senha
        nova_senha_hash = hash_senha(nova_senha)
        
        cur.execute("""
            UPDATE usuarios 
            SET senha = ?
            WHERE id = ?
        """, (nova_senha_hash, g.usuario["id"]))
        
        # Invalidar TODAS as sessões do usuário (por segurança)
        cur.execute("""
            UPDATE tokens_sessao 
            SET ativo = 0 
            WHERE usuario_id = ?
        """, (g.usuario["id"],))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "Senha alterada com sucesso. Faça login novamente."
        })
        
    except Exception as e:
        print(f"[ERRO /api/auth/alterar-senha]: {e}")
        return jsonify({"success": False, "message": "Erro ao alterar senha"}), 500

@app.route("/api/auth/sessoes", methods=["GET"])
@login_required
def auth_sessoes():
    """Listar todas as sessões ativas do usuário"""
    try:
        conn = db_usuarios()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                token,
                dispositivo,
                criado_em,
                expira_em,
                ativo
            FROM tokens_sessao
            WHERE usuario_id = ?
            ORDER BY criado_em DESC
        """, (g.usuario["id"],))
        
        sessoes = cur.fetchall()
        conn.close()
        
        sessoes_list = []
        for sessao in sessoes:
            expira_em = datetime.fromisoformat(sessao["expira_em"])
            expirada = datetime.now() > expira_em
            
            sessoes_list.append({
                "token": sessao["token"],
                "dispositivo": sessao["dispositivo"],
                "criado_em": sessao["criado_em"],
                "expira_em": sessao["expira_em"],
                "ativo": bool(sessao["ativo"] and not expirada),
                "expirada": expirada,
                "atual": sessao["token"] == g.usuario.get("token", "")
            })
        
        return jsonify({
            "success": True,
            "sessoes": sessoes_list,
            "total": len(sessoes_list)
        })
        
    except Exception as e:
        print(f"[ERRO /api/auth/sessoes]: {e}")
        return jsonify({"success": False, "message": "Erro ao listar sessões"}), 500

@app.route("/api/auth/logout-todos", methods=["POST"])
@login_required
def auth_logout_todos():
    """Fazer logout de todos os dispositivos (exceto o atual)"""
    try:
        token_atual = g.usuario.get("token")
        
        conn = db_usuarios()
        cur = conn.cursor()
        
        if token_atual:
            # Invalidar todas as sessões exceto a atual
            cur.execute("""
                UPDATE tokens_sessao 
                SET ativo = 0 
                WHERE usuario_id = ? AND token != ?
            """, (g.usuario["id"], token_atual))
        else:
            # Invalidar todas as sessões
            cur.execute("""
                UPDATE tokens_sessao 
                SET ativo = 0 
                WHERE usuario_id = ?
            """, (g.usuario["id"],))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "Todas as outras sessões foram encerradas"
        })
        
    except Exception as e:
        print(f"[ERRO /api/auth/logout-todos]: {e}")
        return jsonify({"success": False, "message": "Erro ao encerrar sessões"}), 500

@app.route("/api/auth/encerrar-sessao", methods=["POST"])
@login_required
def auth_encerrar_sessao():
    """Encerrar uma sessão específica (por token)"""
    try:
        data = request.json
        token_encerrar = data.get("token")
        
        if not token_encerrar:
            return jsonify({
                "success": False, 
                "message": "Token da sessão é obrigatório"
            }), 400
        
        # Não permitir encerrar a sessão atual (use logout normal)
        if token_encerrar == g.usuario.get("token"):
            return jsonify({
                "success": False, 
                "message": "Use a rota /api/auth/logout para encerrar a sessão atual"
            }), 400
        
        conn = db_usuarios()
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE tokens_sessao 
            SET ativo = 0 
            WHERE usuario_id = ? AND token = ?
        """, (g.usuario["id"], token_encerrar))
        
        rows = cur.rowcount
        conn.commit()
        conn.close()
        
        if rows > 0:
            return jsonify({
                "success": True,
                "message": "Sessão encerrada com sucesso"
            })
        else:
            return jsonify({
                "success": False,
                "message": "Sessão não encontrada ou não pertence ao usuário"
            }), 404
            
    except Exception as e:
        print(f"[ERRO /api/auth/encerrar-sessao]: {e}")
        return jsonify({"success": False, "message": "Erro ao encerrar sessão"}), 500

@app.route("/api/auth/limpar-sessoes-expiradas", methods=["POST"])
@login_required
def auth_limpar_sessoes_expiradas():
    """Limpar sessões expiradas do usuário"""
    try:
        conn = db_usuarios()
        cur = conn.cursor()
        
        # Marcar como inativas as sessões expiradas
        cur.execute("""
            UPDATE tokens_sessao 
            SET ativo = 0 
            WHERE usuario_id = ? 
            AND datetime(expira_em) < datetime('now')
        """, (g.usuario["id"],))
        
        removidas = cur.rowcount
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": f"{removidas} sessões expiradas foram removidas",
            "removidas": removidas
        })
        
    except Exception as e:
        print(f"[ERRO /api/auth/limpar-sessoes-expiradas]: {e}")
        return jsonify({"success": False, "message": "Erro ao limpar sessões"}), 500

# ======================================================
# ROTAS PARA MATÉRIAS - SIMPLIFICADO
# ======================================================
@app.route("/api/materias")
def materias():
    try:
        conn = db_questoes()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT DISTINCT materia 
            FROM questoes 
            WHERE materia IS NOT NULL AND TRIM(materia) != ''
            ORDER BY materia
        """)
        
        materias_list = [row["materia"] for row in cur.fetchall()]
        conn.close()
        
        if not materias_list:
            materias_list = ["Português", "Matemática", "Ciências", "História", "Geografia"]
        
        return jsonify(materias_list)
    except Exception as e:
        print(f"[ERRO /api/materias]: {e}")
        return jsonify(["Português", "Matemática", "Ciências", "História", "Geografia"])

@app.route("/api/materias/detalhes")
def materias_detalhes():
    try:
        conn = db_questoes()
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT materia 
            FROM questoes 
            WHERE materia IS NOT NULL AND TRIM(materia) != ''
            ORDER BY materia
        """)
        
        materias_list = []
        for row in cur.fetchall():
            materia = row["materia"]
            materias_list.append({
                "nome": materia,
                "icone": get_icone_materia(materia),
                "cor": get_cor_materia(materia)
            })
        
        conn.close()
        
        if not materias_list:
            materias_list = [
                {"nome": "Português", "icone": "📚", "cor": "#4CAF50"},
                {"nome": "Matemática", "icone": "🔢", "cor": "#2196F3"},
                {"nome": "Ciências", "icone": "🔬", "cor": "#9C27B0"},
                {"nome": "História", "icone": "🏛️", "cor": "#FF9800"},
                {"nome": "Geografia", "icone": "🌍", "cor": "#795548"}
            ]
        
        return jsonify(materias_list)
    except Exception as e:
        print(f"[ERRO /api/materias/detalhes]: {e}")
        return jsonify([
            {"nome": "Português", "icone": "📚", "cor": "#4CAF50"},
            {"nome": "Matemática", "icone": "🔢", "cor": "#2196F3"},
            {"nome": "Ciências", "icone": "🔬", "cor": "#9C27B0"},
            {"nome": "História", "icone": "🏛️", "cor": "#FF9800"},
            {"nome": "Geografia", "icone": "🌍", "cor": "#795548"}
        ])

# ======================================================
# ROTAS PARA ASSUNTOS - CORRIGIDO PARA SEU BANCO
# ======================================================
@app.route("/api/assuntos")
def assuntos():
    materia = request.args.get("materia")
    
    if not materia:
        return jsonify([])
    
    try:
        conn = db_questoes()
        cur = conn.cursor()
        
        # 1. Buscar todos os assuntos da matéria
        cur.execute("""
            SELECT DISTINCT assunto 
            FROM questoes 
            WHERE materia = ? 
            AND assunto IS NOT NULL 
            AND TRIM(assunto) != ''
            ORDER BY assunto
        """, (materia,))
        
        # 2. Obter lista de assuntos
        assuntos_list = []
        for row in cur.fetchall():
            assunto = row["assunto"]
            if assunto and assunto.strip():
                assuntos_list.append(assunto.strip())
        
        conn.close()
        
        # Se não houver assuntos, retorna pelo menos "Geral"
        if not assuntos_list:
            assuntos_list = ["Geral"]
        
        # 3. Tentar obter o usuário logado
        usuario_id = None
        
        # Primeiro tentar pelo token
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        # Se não tiver no header, tentar no parâmetro
        if not token:
            token = request.args.get('token')
        
        # Validar token e obter ID do usuário
        if token:
            conn_usuarios = db_usuarios()
            cur_usuarios = conn_usuarios.cursor()
            
            cur_usuarios.execute("""
                SELECT usuario_id FROM tokens_sessao 
                WHERE token = ? AND ativo = 1 
                AND datetime(expira_em) > datetime('now')
            """, (token,))
            
            token_data = cur_usuarios.fetchone()
            if token_data:
                usuario_id = token_data["usuario_id"]
            
            conn_usuarios.close()
        
        # Se não conseguiu pelo token, tentar pelo localStorage (para testes)
        if not usuario_id and request.args.get('usuario_id'):
            usuario_id = request.args.get('usuario_id')
        
        # 4. Preparar resultado
        resultado = []
        
        # Se tiver usuário, verificar bloqueios
        if usuario_id:
            conn_usuarios = db_usuarios()
            cur_usuarios = conn_usuarios.cursor()
            
            for assunto_nome in assuntos_list:
                # Verificar se está bloqueado
                cur_usuarios.execute("""
                    SELECT bloqueado FROM bloqueios_assuntos 
                    WHERE usuario_id = ? AND materia = ? AND assunto = ?
                """, (usuario_id, materia, assunto_nome))
                
                bloqueio = cur_usuarios.fetchone()
                
                # Se encontrar registro e bloqueado = 1, então está bloqueado
                bloqueado = False
                if bloqueio:
                    bloqueado = bloqueio["bloqueado"] == 1
                
                resultado.append({
                    "nome": assunto_nome,
                    "bloqueado": bloqueado  # True se bloqueado, False se desbloqueado
                })
            
            conn_usuarios.close()
        else:
            # Se não tiver usuário, todos desbloqueados
            for assunto_nome in assuntos_list:
                resultado.append({
                    "nome": assunto_nome,
                    "bloqueado": False
                })
        
        return jsonify(resultado)
        
    except Exception as e:
        print(f"[ERRO /api/assuntos]: {e}")
        import traceback
        traceback.print_exc()
        # Fallback: retornar como array de strings (compatibilidade)
        conn = db_questoes()
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT assunto 
            FROM questoes 
            WHERE materia = ? 
            AND assunto IS NOT NULL 
            AND TRIM(assunto) != ''
            ORDER BY assunto
        """, (materia,))
        
        fallback_list = [row["assunto"].strip() for row in cur.fetchall() if row["assunto"]]
        conn.close()
        
        if not fallback_list:
            fallback_list = ["Geral"]
        
        return jsonify(fallback_list)

# ======================================================
# ROTAS PARA QUESTÕES - CORRIGIDO PARA SEU BANCO
# ======================================================
@app.route("/api/questoes")
def questoes():
    materia = request.args.get("materia")
    assunto = request.args.get("assunto")
    
    try:
        conn = db_questoes()
        cur = conn.cursor()
        
        # Construir query base
        query = "SELECT * FROM questoes WHERE ativo = 1"
        params = []
        
        if materia:
            query += " AND materia = ?"
            params.append(materia)
        
        if assunto and assunto != "undefined" and assunto != "null" and assunto != "":
            query += " AND assunto = ?"
            params.append(assunto)
        
        query += " ORDER BY RANDOM() LIMIT 50"
        
        print(f"📥 Query: {query}")
        print(f"📥 Params: {params}")
        
        cur.execute(query, params)
        rows = cur.fetchall()
        
        print(f"📥 Questões encontradas: {len(rows)}")
        
        questoes_list = []
        
        for row in rows:
            questao = dict(row)
            
            # Converter resposta_correta para letra minúscula
            resposta = questao.get("resposta_correta", "a")
            if resposta:
                resposta = resposta.strip().lower()
            
            # 🔥 AGORA RETORNA TODOS OS CAMPOS!
            questoes_list.append({
                "id": questao.get("id"),
                "materia": questao.get("materia", ""),
                "assunto": questao.get("assunto", ""),
                "pergunta": questao.get("pergunta", ""),
                "a": questao.get("opcao_a", ""),
                "b": questao.get("opcao_b", ""),
                "c": questao.get("opcao_c", ""),
                "d": questao.get("opcao_d", ""),  
                "correta": resposta,
                "dificuldade": questao.get("dificuldade", "Médio"),
                "dica": questao.get("dica", ""),
                "tipo_questao": questao.get("tipo_questao", "multipla_escolha"),
                "imagem_url": questao.get("imagem_url", ""),
                "imagem_path": questao.get("imagem_path", ""),
                "audio_url": questao.get("audio_url", ""),
                "audio_path": questao.get("audio_path", ""),
                "resposta_voz": questao.get("resposta_voz", "")
            })
        
        conn.close()
        
        print(f"📤 Retornando {len(questoes_list)} questões")
        if len(questoes_list) > 0:
            print(f"📤 Primeira questão: {questoes_list[0]}")
        
        return jsonify(questoes_list)
        
    except Exception as e:
        print(f"[ERRO /api/questoes]: {e}")
        import traceback
        traceback.print_exc()
        return jsonify([])
    
# ======================================================
# ROTAS PARA O PAINEL ADMIN DE QUESTÕES
# ======================================================
@app.route("/api/excluir-questao/<int:id>", methods=["DELETE"])
def excluir_questao(id):
    try:
        conn = db_questoes()
        cur = conn.cursor()
        
        cur.execute("DELETE FROM questoes WHERE id = ?", (id,))
        conn.commit()
        
        if cur.rowcount > 0:
            conn.close()
            return jsonify({"success": True, "message": "Questão excluída com sucesso"})
        else:
            conn.close()
            return jsonify({"success": False, "message": "Questão não encontrada"}), 404
    except Exception as e:
        print(f"[ERRO /api/excluir-questao]: {e}")
        return jsonify({"success": False, "message": f"Erro: {str(e)}"}), 500
    
@app.route("/api/excluir-multiplas-questoes", methods=["POST"])
def excluir_multiplas_questoes():
    try:
        data = request.json
        ids = data.get("ids", [])
        
        if not ids:
            return jsonify({"success": False, "message": "Nenhuma questão selecionada"}), 400
        
        conn = db_questoes()
        cur = conn.cursor()
        
        # Criar placeholders para a query
        placeholders = ','.join(['?' for _ in ids])
        
        # Excluir as questões
        cur.execute(f"DELETE FROM questoes WHERE id IN ({placeholders})", ids)
        
        excluidas = cur.rowcount
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True, 
            "message": f"{excluidas} questão(ões) excluída(s) com sucesso",
            "excluidas": excluidas
        })
        
    except Exception as e:
        print(f"[ERRO /api/excluir-multiplas-questoes]: {e}")
        return jsonify({"success": False, "message": f"Erro ao excluir questões: {str(e)}"}), 500

# ======================================================
# ROTAS DE EXPORTAÇÃO/IMPORTAÇÃO
# ======================================================
@app.route("/api/exportar-excel")
def exportar_excel():
    try:
        conn = db_questoes()
        
        # Selecionar APENAS as colunas que existem no banco (SEM path)
        query = "SELECT id, materia, assunto, pergunta, tipo_questao, opcao_a, opcao_b, opcao_c, opcao_d, resposta_correta, imagem_url, audio_url, resposta_voz, dificuldade, dica, ativo FROM questoes ORDER BY id"
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            return jsonify({"error": "Nenhuma questão encontrada"}), 404
        
        # Renomear colunas para o padrão da planilha
        df = df.rename(columns={
            'id': 'ID',
            'materia': 'Matéria',
            'assunto': 'Assunto',
            'pergunta': 'Pergunta',
            'tipo_questao': 'Tipo',
            'opcao_a': 'A',
            'opcao_b': 'B',
            'opcao_c': 'C',
            'opcao_d': 'D',
            'resposta_correta': 'Resposta Correta',
            'imagem_url': 'Imagem URL',
            'audio_url': 'Áudio URL',
            'resposta_voz': 'Resposta Voz',
            'dificuldade': 'Dificuldade',
            'dica': 'Explicação',
            'ativo': 'Ativo'
        })
        
        # Garantir que todas as colunas necessárias existam
        colunas_necessarias = [
            'ID', 'Matéria', 'Assunto', 'Pergunta', 'Tipo',
            'A', 'B', 'C', 'D', 'Resposta Correta',
            'Imagem URL', 'Áudio URL', 'Resposta Voz',
            'Dificuldade', 'Explicação', 'Ativo'
        ]
        
        # Preencher colunas faltantes com string vazia
        for col in colunas_necessarias:
            if col not in df.columns:
                df[col] = ''
        
        # Reordenar colunas
        df = df[colunas_necessarias]
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Questões')
            
            # Ajustar largura das colunas
            worksheet = writer.sheets['Questões']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='questoes_panda_estudos.xlsx'
        )
    except Exception as e:
        print(f"[ERRO /api/exportar-excel]: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/importar-questoes", methods=["POST"])
def importar_questoes():
    """Importar questões de planilha"""
    try:
        if 'file' not in request.files:
            return jsonify({"success": False, "message": "Nenhum arquivo enviado"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"success": False, "message": "Nenhum arquivo selecionado"}), 400
        
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({"success": False, "message": "Formato inválido. Use .xlsx ou .xls"}), 400
        
        # Ler arquivo
        df = pd.read_excel(file, dtype=str, keep_default_na=False)
        
        print("\n" + "="*60)
        print("📥 IMPORTANDO PLANILHA")
        print("="*60)
        print(f"📊 Linhas: {len(df)}")
        print(f"📋 Colunas encontradas: {list(df.columns)}")
        
        # MAPEAMENTO EXATO para sua planilha
        mapeamento = {
            'ID': 'id',
            'Matéria': 'materia',
            'Assunto': 'assunto',
            'Pergunta': 'pergunta',
            'Tipo': 'tipo_questao',
            'A': 'opcao_a',
            'B': 'opcao_b',
            'C': 'opcao_c',
            'D': 'opcao_d',
            'Resposta Correta': 'resposta_correta',
            'Imagem URL': 'imagem_url',
            'Áudio URL': 'audio_url',
            'Resposta Voz': 'resposta_voz',
            'Dificuldade': 'dificuldade',
            'Explicação': 'dica',
            'Ativo': 'ativo'
        }
        
        # Renomear colunas
        colunas_renomeadas = {}
        for col in df.columns:
            col_clean = str(col).strip()
            if col_clean in mapeamento:
                colunas_renomeadas[col] = mapeamento[col_clean]
                print(f"  📌 Mapeado: '{col}' -> '{mapeamento[col_clean]}'")
        
        df = df.rename(columns=colunas_renomeadas)
        
        print("\n📋 Colunas após mapeamento:", list(df.columns))
        
        conn = db_questoes()
        cur = conn.cursor()
        
        importadas = 0
        erros = 0
        
        for index, row in df.iterrows():
            linha_num = index + 2
            
            try:
                # Valores básicos
                materia = str(row.get('materia', '')).strip()
                pergunta = str(row.get('pergunta', '')).strip()
                
                if not materia or not pergunta:
                    print(f"⚠️ Linha {linha_num}: Sem matéria ou pergunta, ignorando")
                    erros += 1
                    continue
                
                # Tipo
                tipo = str(row.get('tipo_questao', 'multipla_escolha')).strip().lower()
                
                # Valores padrão para campos vazios
                opcao_a = str(row.get('opcao_a', '')).strip()
                opcao_b = str(row.get('opcao_b', '')).strip()
                opcao_c = str(row.get('opcao_c', '')).strip()
                opcao_d = str(row.get('opcao_d', '')).strip()
                resposta_correta = str(row.get('resposta_correta', 'a')).strip().lower()
                imagem_url = str(row.get('imagem_url', '')).strip()
                audio_url = str(row.get('audio_url', '')).strip()
                resposta_voz = str(row.get('resposta_voz', '')).strip().lower()
                dificuldade = str(row.get('dificuldade', 'Médio')).strip()
                dica = str(row.get('dica', '')).strip()
                ativo = 1  # Sempre 1 por padrão
                
                print(f"\n📌 Linha {linha_num}:")
                print(f"  Matéria: {materia}")
                print(f"  Tipo: {tipo}")
                print(f"  Imagem URL: {imagem_url}")
                print(f"  Áudio URL: {audio_url}")
                print(f"  Resposta Voz: {resposta_voz}")
                
                # Inserir no banco (SEM os campos path)
                cur.execute("""
                    INSERT INTO questoes (
                        materia, assunto, pergunta, tipo_questao,
                        opcao_a, opcao_b, opcao_c, opcao_d,
                        resposta_correta, imagem_url, audio_url,
                        resposta_voz, dificuldade, dica, ativo
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    materia,
                    str(row.get('assunto', '')).strip(),
                    pergunta,
                    tipo,
                    opcao_a, opcao_b, opcao_c, opcao_d,
                    resposta_correta,
                    imagem_url,
                    audio_url,
                    resposta_voz,
                    dificuldade,
                    dica,
                    ativo
                ))
                
                importadas += 1
                print(f"  ✅ IMPORTADA!")
                
            except Exception as e:
                print(f"❌ Linha {linha_num}: ERRO - {str(e)}")
                erros += 1
        
        conn.commit()
        
        # Verificar total
        cur.execute("SELECT COUNT(*) as total FROM questoes")
        total_final = cur.fetchone()["total"]
        conn.close()
        
        print("\n" + "="*60)
        print("📊 RESUMO DA IMPORTAÇÃO")
        print("="*60)
        print(f"✅ Importadas: {importadas}")
        print(f"❌ Erros: {erros}")
        print(f"📊 Total no banco: {total_final}")
        print("="*60)
        
        return jsonify({
            "success": True,
            "message": f"✅ {importadas} importadas, {erros} erros",
            "importadas": importadas,
            "erros": erros,
            "total_banco": total_final
        })
        
    except Exception as e:
        print(f"❌ ERRO FATAL: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "message": f"Erro ao importar: {str(e)}"
        }), 500

@app.route("/api/salvar-questao", methods=["POST"])
def salvar_questao():  
    try:
        data = request.json
        print(f"📥 Recebendo dados para salvar: {data}")
        
        if not data.get("materia") or not data.get("pergunta"):
            return jsonify({"success": False, "message": "Matéria e pergunta são obrigatórios"})
        
        conn = db_questoes()
        cur = conn.cursor()
        
        # Determinar tipo de questão
        tipo_questao = data.get("tipo_questao", "multipla_escolha")
        
        if data.get("id"):  # UPDATE
            cur.execute("""
                UPDATE questoes SET
                materia = ?, 
                assunto = ?, 
                pergunta = ?, 
                tipo_questao = ?,
                opcao_a = ?, 
                opcao_b = ?, 
                opcao_c = ?, 
                opcao_d = ?,
                resposta_correta = ?, 
                dificuldade = ?, 
                dica = ?, 
                imagem_url = ?,
                audio_url = ?,
                resposta_voz = ?,
                ativo = 1
                WHERE id = ?
            """, (
                data.get("materia"),
                data.get("assunto", ""),
                data.get("pergunta"),
                tipo_questao,
                data.get("a", ""),
                data.get("b", ""),
                data.get("c", ""),
                data.get("d", ""),
                data.get("correta", "a"),
                data.get("dificuldade", "Médio"),
                data.get("explicacao", ""),
                data.get("imagem_url", ""),
                data.get("audio_url", ""),
                data.get("resposta_voz", ""),
                data.get("id")
            ))
            mensagem = "Questão atualizada com sucesso!"
            print(f"✅ Questão {data.get('id')} atualizada")
            
        else:  # INSERT
            cur.execute("""
                INSERT INTO questoes 
                (materia, assunto, pergunta, tipo_questao, 
                 opcao_a, opcao_b, opcao_c, opcao_d, 
                 resposta_correta, dificuldade, dica, 
                 imagem_url, audio_url, resposta_voz, ativo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                data.get("materia"),
                data.get("assunto", ""),
                data.get("pergunta"),
                tipo_questao,
                data.get("a", ""),
                data.get("b", ""),
                data.get("c", ""),
                data.get("d", ""),
                data.get("correta", "a"),
                data.get("dificuldade", "Médio"),
                data.get("explicacao", ""),
                data.get("imagem_url", ""),
                data.get("audio_url", ""),
                data.get("resposta_voz", "")
            ))
            mensagem = "Questão criada com sucesso!"
            print(f"✅ Nova questão inserida, ID: {cur.lastrowid}")
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": mensagem})
        
    except Exception as e:
        print(f"[ERRO /api/salvar-questao]: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"Erro: {str(e)}"}), 500

@app.route("/api/todas-questoes")
def todas_questoes():
    try:
        conn = db_questoes()
        # SELECIONAR APENAS AS COLUNAS QUE EXISTEM (SEM path)
        cur = conn.cursor()
        cur.execute("SELECT id, materia, assunto, pergunta, tipo_questao, opcao_a, opcao_b, opcao_c, opcao_d, resposta_correta, dificuldade, dica, imagem_url, audio_url, resposta_voz, ativo FROM questoes ORDER BY id")
        
        rows = cur.fetchall()
        questoes_list = []
        
        for row in rows:
            questao = dict(row)
            questoes_list.append({
                "id": questao.get("id"),
                "materia": questao.get("materia", ""),
                "assunto": questao.get("assunto", ""),
                "pergunta": questao.get("pergunta", ""),
                "tipo_questao": questao.get("tipo_questao", "multipla_escolha"),
                "a": questao.get("opcao_a", ""),
                "b": questao.get("opcao_b", ""),
                "c": questao.get("opcao_c", ""),
                "d": questao.get("opcao_d", ""),
                "correta": questao.get("resposta_correta", "a"),
                "dificuldade": questao.get("dificuldade", "Médio"),
                "explicacao": questao.get("dica", ""),
                "imagem_url": questao.get("imagem_url", ""),
                "audio_url": questao.get("audio_url", ""),
                "resposta_voz": questao.get("resposta_voz", ""),
                "ativo": questao.get("ativo", 1)
            })
        
        conn.close()
        print(f"📤 Retornando {len(questoes_list)} questões")
        return jsonify(questoes_list)
        
    except Exception as e:
        print(f"[ERRO /api/todas-questoes]: {e}")
        import traceback
        traceback.print_exc()
        return jsonify([])

# ======================================================
# ROTAS PARA USUÁRIOS - SIMPLIFICADO
# ======================================================
@app.route("/api/usuarios", methods=["GET"])
def listar_usuarios():
    try:
        apenas_ativos = request.args.get("ativos") == "1"
        conn = db_usuarios()
        cur = conn.cursor()
        
        if apenas_ativos:
            cur.execute("""
                SELECT id, nome, email, avatar, total_acertos, total_erros, 
                       ativo, ultimo_login, criado_em
                FROM usuarios 
                WHERE ativo = 1
                ORDER BY nome
            """)
        else:
            cur.execute("""
                SELECT id, nome, email, avatar, total_acertos, total_erros, 
                       ativo, ultimo_login, criado_em
                FROM usuarios 
                ORDER BY nome
            """)
        
        usuarios = [dict(row) for row in cur.fetchall()]
        conn.close()
        
        if apenas_ativos:
            return jsonify(usuarios)
        else:
            return jsonify({"success": True, "usuarios": usuarios})
            
    except Exception as e:
        print(f"[ERRO listar_usuarios]: {e}")
        return jsonify([])

@app.route("/api/usuarios/contar")
def contar_usuarios():
    try:
        conn = db_usuarios()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as total FROM usuarios")
        total = cur.fetchone()["total"]
        conn.close()
        
        return jsonify(total)
    except Exception as e:
        print(f"[ERRO contar_usuarios]: {e}")
        return jsonify(0)

@app.route("/api/contar-perfis")
def contar_perfis():
    try:
        conn = db_usuarios()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as total FROM usuarios")
        total = cur.fetchone()["total"]
        conn.close()
        return jsonify({"total": total})
    except Exception as e:
        print(f"[ERRO contar_perfis]: {e}")
        return jsonify({"total": 0})

@app.route("/api/usuarios/<int:usuario_id>", methods=["GET"])
def get_usuario(usuario_id):
    try:
        conn = db_usuarios()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, nome, email, avatar, total_acertos, total_erros, 
                   ativo, ultimo_login, criado_em
            FROM usuarios
            WHERE id = ?
        """, (usuario_id,))
        
        user = cur.fetchone()
        conn.close()
        
        if not user:
            return jsonify({"success": False, "message": "Usuário não encontrado"}), 404
        
        return jsonify({"success": True, "user": dict(user)})
    except Exception as e:
        print(f"[ERRO get_usuario]: {e}")
        return jsonify({"success": False, "message": "Erro ao buscar usuário"}), 500

@app.route("/api/usuarios/criar", methods=["POST"])
def criar_usuario():
    try:
        data = request.json
        
        if not data:
            return jsonify({"success": False, "message": "Dados não fornecidos"}), 400
        
        nome = data.get("nome", "").strip()
        email = data.get("email", "").strip()
        senha = data.get("senha", "").strip()
        avatar = data.get("avatar", "🐼")
        
        if not nome:
            return jsonify({"success": False, "message": "Nome é obrigatório"}), 400
        if not email:
            return jsonify({"success": False, "message": "E-mail é obrigatório"}), 400
        if not senha:
            return jsonify({"success": False, "message": "Senha é obrigatória"}), 400
        if len(senha) < 6:
            return jsonify({"success": False, "message": "Senha deve ter pelo menos 6 caracteres"}), 400
        
        senha_hash = hash_senha(senha)
        conn = db_usuarios()
        cur = conn.cursor()
        
        try:
            # CORREÇÃO: Usar `criado_em` em vez de `data_criacao`
            cur.execute("""
                INSERT INTO usuarios
                (nome, email, senha, avatar, criado_em, ativo)
                VALUES (?, ?, ?, ?, datetime('now'), 1)
            """, (
                nome,
                email,
                senha_hash,
                avatar
            ))
            
            conn.commit()
            user_id = cur.lastrowid
            
            cur.execute("""
                SELECT id, nome, email, avatar, ativo, criado_em
                FROM usuarios WHERE id = ?
            """, (user_id,))
            
            user = cur.fetchone()
            conn.close()
            
            return jsonify({
                "success": True,
                "message": "Usuário criado com sucesso",
                "user": dict(user)
            })
            
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({"success": False, "message": "E-mail já cadastrado"}), 400
        except Exception as e:
            conn.close()
            print(f"[ERRO criar_usuario DB]: {e}")
            return jsonify({"success": False, "message": f"Erro no banco: {str(e)}"}), 500
            
    except Exception as e:
        print(f"[ERRO criar_usuario]: {e}")
        return jsonify({"success": False, "message": "Erro interno do servidor"}), 500

@app.route("/api/usuarios/<int:usuario_id>", methods=["PUT"])
def atualizar_usuario(usuario_id):
    try:
        data = request.json
        
        if not data:
            return jsonify({"success": False, "message": "Dados não fornecidos"}), 400
        
        conn = db_usuarios()
        cur = conn.cursor()
        
        cur.execute("SELECT id, email FROM usuarios WHERE id = ?", (usuario_id,))
        usuario_existente = cur.fetchone()
        
        if not usuario_existente:
            conn.close()
            return jsonify({"success": False, "message": "Usuário não encontrado"}), 404
        
        updates = []
        params = []
        
        if 'nome' in data and data['nome']:
            nome = str(data['nome']).strip()
            if nome:
                updates.append("nome = ?")
                params.append(nome)
        
        if 'email' in data and data['email']:
            email = str(data['email']).strip()
            if email:
                cur.execute("SELECT id FROM usuarios WHERE email = ? AND id != ?", (email, usuario_id))
                if cur.fetchone():
                    conn.close()
                    return jsonify({"success": False, "message": "E-mail já está em uso por outro usuário"}), 400
                
                updates.append("email = ?")
                params.append(email)
        
        if 'avatar' in data and data['avatar']:
            updates.append("avatar = ?")
            params.append(data['avatar'])
        
        if 'senha' in data and data['senha']:
            nova_senha = str(data['senha']).strip()
            if nova_senha:
                if len(nova_senha) < 6:
                    conn.close()
                    return jsonify({"success": False, "message": "A nova senha deve ter pelo menos 6 caracteres"}), 400
                
                senha_hash = hash_senha(nova_senha)
                updates.append("senha = ?")
                params.append(senha_hash)
        
        if not updates:
            conn.close()
            return jsonify({"success": False, "message": "Nenhuma alteração fornecida"}), 400
        
        params.append(usuario_id)
        
        sql = f"UPDATE usuarios SET {', '.join(updates)} WHERE id = ?"
        cur.execute(sql, params)
        
        if cur.rowcount == 0:
            conn.close()
            return jsonify({"success": False, "message": "Nenhuma alteração realizada"}), 400
        
        conn.commit()
        
        cur.execute("""
            SELECT id, nome, email, avatar, total_acertos, total_erros
            FROM usuarios WHERE id = ?
        """, (usuario_id,))
        
        usuario_atualizado = cur.fetchone()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "Usuário atualizado com sucesso",
            "user": dict(usuario_atualizado)
        })
        
    except Exception as e:
        print(f"[ERRO atualizar_usuario]: {e}")
        if 'conn' in locals():
            conn.close()
        return jsonify({"success": False, "message": f"Erro interno: {str(e)}"}), 500

@app.route("/api/usuarios/<int:usuario_id>", methods=["DELETE"])
def excluir_usuario(usuario_id):
    try:
        conn = db_usuarios()
        cur = conn.cursor()
        
        cur.execute("SELECT id FROM usuarios WHERE id = ?", (usuario_id,))
        if not cur.fetchone():
            conn.close()
            return jsonify({"success": False, "message": "Usuário não encontrado"}), 404
        
        cur.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "Usuário excluído com sucesso"})
        
    except Exception as e:
        print(f"[ERRO excluir_usuario]: {e}")
        if 'conn' in locals():
            conn.close()
        return jsonify({"success": False, "message": "Erro ao excluir usuário"}), 500

# ======================================================
# ROTA DE VERIFICAÇÃO DE SAÚDE DA API
# ======================================================
@app.route("/api/health", methods=["GET"])
def health_check():
    """Verificar se a API e bancos estão funcionando"""
    try:
        status = {
            "status": "online",
            "timestamp": datetime.now().isoformat(),
            "servidor": "Flask",
            "banco_usuarios": "ok",
            "banco_questoes": "ok",
            "banco_estatisticas": "ok"
        }
        
        # Testar conexão com cada banco
        try:
            conn = db_usuarios()
            conn.execute("SELECT 1")
            conn.close()
        except:
            status["banco_usuarios"] = "erro"
        
        try:
            conn = db_questoes()
            conn.execute("SELECT 1")
            conn.close()
        except:
            status["banco_questoes"] = "erro"
        
        try:
            conn = db_estatisticas()
            conn.execute("SELECT 1")
            conn.close()
        except:
            status["banco_estatisticas"] = "erro"
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({
            "status": "online",
            "erro": str(e),
            "timestamp": datetime.now().isoformat()
        })

# ======================================================
# INICIAR SERVIDOR
# ======================================================
@app.route("/api/usuarios/<int:usuario_id>/toggle-ativo", methods=["POST"])
def toggle_usuario_ativo(usuario_id):
    """Alternar status ativo/inativo do usuário"""
    try:
        conn = db_usuarios()
        cur = conn.cursor()
        
        # Primeiro verificar se o usuário existe
        cur.execute("SELECT id, ativo FROM usuarios WHERE id = ?", (usuario_id,))
        usuario = cur.fetchone()
        
        if not usuario:
            conn.close()
            return jsonify({"success": False, "message": "Usuário não encontrado"}), 404
        
        # Alternar o status (1 -> 0, 0 -> 1)
        novo_status = 0 if usuario["ativo"] == 1 else 1
        novo_status_texto = "ativado" if novo_status == 1 else "desativado"
        
        cur.execute("UPDATE usuarios SET ativo = ? WHERE id = ?", (novo_status, usuario_id))
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": f"Usuário {novo_status_texto} com sucesso",
            "ativo": novo_status == 1
        })
        
    except Exception as e:
        print(f"[ERRO toggle_usuario_ativo]: {e}")
        return jsonify({"success": False, "message": "Erro ao alterar status"}), 500

# ======================================================
# ROTAS PARA ESTATÍSTICAS NA PÁGINA MATÉRIAS
# ======================================================
@app.route('/api/usuarios/<int:usuario_id>/estatisticas', methods=['GET'])
def get_estatisticas_usuario(usuario_id):
    # Lógica para buscar do banco (exemplo fictício)
    # Deve retornar algo como:
    # total_questoes, acertos, erros
    # Você pode calcular a partir da tabela de respostas / tentativas
    
    # Exemplo mock:
    stats = {
        "total_questoes": 248,
        "acertos": 178,
        "erros": 70
    }
    
    return jsonify({"success": True, "stats": stats})

# ======================================================
# ROTAS PARA ESTATÍSTICAS (VERSÃO FINAL E COMPATÍVEL)
# ======================================================

@app.route("/api/estatisticas", methods=["POST"])
def salvar_estatistica():
    try:
        data = request.json

        usuario_id = data.get("usuario_id")
        nome = data.get("nome", "")

        if not usuario_id:
            return jsonify({
                "success": False,
                "message": "usuario_id é obrigatório"
            }), 400

        materia = data.get("materia", "Não especificada")
        assunto = data.get("assunto", "Não especificado")
        acertou = 1 if data.get("acertou") else 0
        tempo = int(data.get("tempo", 0))
        data_registro = data.get("data", datetime.now().isoformat())

        conn = db_estatisticas()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO estatisticas
            (usuario_id, nome, materia, assunto, acertou, tempo, data)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            usuario_id,
            nome,
            materia,
            assunto,
            acertou,
            tempo,
            data_registro
        ))

        conn.commit()
        conn.close()

        print(f"[OK] Estatística salva | usuário {usuario_id} | {materia} - {assunto}")

        return jsonify({"success": True})

    except Exception as e:
        print("[ERRO SALVAR ESTATISTICA]", e)
        return jsonify({"success": False, "message": str(e)}), 500

# ======================================================
# DADOS PARA A PÁGINA estatisticas.html
# ======================================================

@app.route("/api/estatisticas/usuario/<int:usuario_id>")
def estatisticas_usuario(usuario_id):
    try:
        conn = db_estatisticas()
        cur = conn.cursor()

        cur.execute("""
            SELECT materia, assunto, acertou, date(data) as dia
            FROM estatisticas
            WHERE usuario_id = ?
        """, (usuario_id,))

        rows = cur.fetchall()
        conn.close()

        total = len(rows)
        acertos = sum(1 for r in rows if r["acertou"] == 1)
        erros = total - acertos
        percentual = round((acertos / total) * 100, 2) if total > 0 else 0

        # =============================
        # POR MATÉRIA
        # =============================
        materias_raw = {}
        for r in rows:
            materia = r["materia"] or "Não especificada"
            materias_raw.setdefault(materia, {"total": 0, "acertos": 0})
            materias_raw[materia]["total"] += 1
            if r["acertou"] == 1:
                materias_raw[materia]["acertos"] += 1

        materias = {
            m: round((d["acertos"] / d["total"]) * 100, 2)
            for m, d in materias_raw.items()
        }

        # =============================
        # POR ASSUNTO
        # =============================
        assuntos = {}
        for r in rows:
            materia = r["materia"] or "Não especificada"
            assunto = r["assunto"] or "Não especificado"

            if assunto not in assuntos:
                assuntos[assunto] = {
                    "materia": materia,
                    "total": 0,
                    "acertos": 0
                }

            assuntos[assunto]["total"] += 1
            if r["acertou"] == 1:
                assuntos[assunto]["acertos"] += 1

        for assunto in assuntos:
            dados = assuntos[assunto]
            dados["percentual"] = round(
                (dados["acertos"] / dados["total"]) * 100, 2
            ) if dados["total"] > 0 else 0

        # =============================
        # EVOLUÇÃO
        # =============================
        evolucao_raw = {}
        for r in rows:
            dia = r["dia"]
            if dia not in evolucao_raw:
                evolucao_raw[dia] = 0
            if r["acertou"] == 1:
                evolucao_raw[dia] += 1

        evolucao_ordenada = dict(sorted(evolucao_raw.items()))

        return jsonify({
            "total": total,
            "acertos": acertos,
            "erros": erros,
            "percentual": percentual,
            "materias": materias,
            "assuntos": assuntos,
            "evolucao": {
                "labels": list(evolucao_ordenada.keys()),
                "valores": list(evolucao_ordenada.values())
            }
        })

    except Exception as e:
        print("[ERRO estatisticas_usuario]", e)
        return jsonify({
            "total": 0,
            "acertos": 0,
            "erros": 0,
            "percentual": 0,
            "materias": {},
            "assuntos": {},
            "evolucao": {"labels": [], "valores": []}
        })

# ======================================================
# ZERAR ESTATÍSTICAS DO PERFIL
# ======================================================
@app.route("/api/admin/estatisticas/zerar/<int:usuario_id>", methods=["DELETE"])
def admin_zerar_estatisticas(usuario_id):
    try:
        # Apagar estatísticas
        conn = db_estatisticas()
        cur = conn.cursor()
        cur.execute("DELETE FROM estatisticas WHERE usuario_id = ?", (usuario_id,))
        conn.commit()
        conn.close()

        # Resetar contadores do usuário
        conn_u = db_usuarios()
        cur_u = conn_u.cursor()
        cur_u.execute("""
            UPDATE usuarios
            SET total_questoes = 0,
                total_acertos = 0,
                total_erros = 0
            WHERE id = ?
        """, (usuario_id,))
        conn_u.commit()
        conn_u.close()

        return jsonify({
            "success": True,
            "message": "Estatísticas zeradas pelo admin"
        })

    except Exception as e:
        print("[ERRO ADMIN ZERAR]", e)
        return jsonify({
            "success": False,
            "message": "Erro interno ao zerar estatísticas"
        }), 500

# ======================================================
# MEU DESEMPENHO - MATERIAS.HTML
# ======================================================
@app.route("/api/desempenho/<int:usuario_id>", methods=["GET"])
def desempenho_usuario(usuario_id):
    try:
        conn = db_estatisticas()
        cur = conn.cursor()

        # Totais gerais
        cur.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(acerto) as acertos,
                SUM(erro) as erros
            FROM estatisticas
            WHERE usuario_id = ?
        """, (usuario_id,))
        geral = cur.fetchone()

        # Por matéria
        cur.execute("""
            SELECT 
                materia,
                COUNT(*) as total,
                SUM(acerto) as acertos
            FROM estatisticas
            WHERE usuario_id = ?
            GROUP BY materia
        """, (usuario_id,))
        materias = cur.fetchall()

        conn.close()

        return jsonify({
            "success": True,
            "total": geral["total"] or 0,
            "acertos": geral["acertos"] or 0,
            "erros": geral["erros"] or 0,
            "materias": [
                {
                    "nome": m["materia"],
                    "total": m["total"],
                    "acertos": m["acertos"]
                } for m in materias
            ]
        })

    except Exception as e:
        print("[ERRO DESEMPENHO]", e)
        return jsonify({"success": False}), 500

@app.route("/api/estatisticas/<int:usuario_id>")
def api_estatisticas(usuario_id):
    try:
        conn = db_estatisticas()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                COUNT(*) AS total,
                COALESCE(SUM(acertou), 0) AS acertos
            FROM estatisticas
            WHERE usuario_id = ?
        """, (usuario_id,))

        row = cur.fetchone()
        conn.close()

        total = row["total"] or 0
        acertos = row["acertos"] or 0
        erros = total - acertos

        return jsonify({
            "success": True,
            "stats": {
                "total_questoes": total,
                "acertos": acertos,
                "erros": erros
            }
        })

    except Exception as e:
        print("❌ ERRO API ESTATISTICAS:", e)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

@app.route("/api/estatisticas/<int:usuario_id>/materias")
def estatisticas_por_materia(usuario_id):
    conn = db_estatisticas()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            materia,
            COUNT(*) AS total,
            SUM(acertou) AS acertos
        FROM estatisticas
        WHERE usuario_id = ?
        GROUP BY materia
        ORDER BY materia
    """, (usuario_id,))

    dados = []
    for row in cur.fetchall():
        total = row["total"]
        acertos = row["acertos"] or 0
        erros = total - acertos
        percentual = round((acertos / total) * 100) if total > 0 else 0

        dados.append({
            "materia": row["materia"],
            "total": total,
            "acertos": acertos,
            "erros": erros,
            "percentual": percentual
        })

    conn.close()
    return jsonify({"success": True, "materias": dados})

# ======================================================
# ROTAS PARA O PAINEL ADMIN DE BLOQUEIOS (ADMAT.HTML)
# ======================================================
@app.route("/api/admin/usuarios")
def admin_usuarios():
    """Listar todos os usuários para o painel admin"""
    try:
        conn = db_usuarios()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, nome, email, avatar, ativo
            FROM usuarios
            ORDER BY nome
        """)
        
        usuarios = []
        for row in cur.fetchall():
            usuarios.append({
                "id": row["id"],
                "nome": row["nome"],
                "email": row["email"],
                "avatar": row["avatar"] or "👤",
                "ativo": row["ativo"] == 1
            })
        
        conn.close()
        
        return jsonify(usuarios)  # Retorna array direto
        
    except Exception as e:
        print(f"[ERRO admin_usuarios]: {e}")
        return jsonify([])

@app.route("/api/admin/materias-assuntos")
def admin_materias_assuntos():
    """Carregar todas as matérias e assuntos do banco de questões"""
    try:
        conn = db_questoes()
        cur = conn.cursor()
        
        # Primeiro, buscar todas as matérias únicas
        cur.execute("""
            SELECT DISTINCT materia 
            FROM questoes 
            WHERE materia IS NOT NULL AND TRIM(materia) != ''
            ORDER BY materia
        """)
        
        materias_list = [row["materia"] for row in cur.fetchall()]
        
        # Agora, para cada matéria, buscar seus assuntos
        resultado = {}
        
        for materia in materias_list:
            cur.execute("""
                SELECT DISTINCT assunto 
                FROM questoes 
                WHERE materia = ? 
                AND assunto IS NOT NULL 
                AND TRIM(assunto) != ''
                ORDER BY assunto
            """, (materia,))
            
            assuntos = [row["assunto"] for row in cur.fetchall()]
            if assuntos:
                resultado[materia] = assuntos
        
        conn.close()
        
        return jsonify(resultado)  # Retorna objeto direto: {materia: [assuntos]}
        
    except Exception as e:
        print(f"[ERRO admin_materias_assuntos]: {e}")
        return jsonify({})

@app.route("/api/admin/bloqueios/<int:usuario_id>")
def admin_get_bloqueios(usuario_id):
    """Obter todos os bloqueios de um usuário"""
    try:
        conn = db_usuarios()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT materia, assunto, bloqueado
            FROM bloqueios_assuntos
            WHERE usuario_id = ?
        """, (usuario_id,))
        
        bloqueios = []
        for row in cur.fetchall():
            bloqueios.append({
                "materia": row["materia"],
                "assunto": row["assunto"],
                "bloqueado": bool(row["bloqueado"])
            })
        
        conn.close()
        
        return jsonify(bloqueios)
        
    except Exception as e:
        print(f"[ERRO admin_get_bloqueios]: {e}")
        return jsonify([])

# ======================================================
# ROTAS ESPECÍFICAS PARA O ADMAT.HTML (NOVAS)
# ======================================================
@app.route("/api/admin/liberar-tudo/<int:usuario_id>", methods=["POST"])
def admin_liberar_tudo(usuario_id):
    """Liberar todos os assuntos para um usuário"""
    try:
        conn = db_usuarios()
        cur = conn.cursor()
        
        cur.execute("""
            DELETE FROM bloqueios_assuntos 
            WHERE usuario_id = ?
        """, (usuario_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": "Todos os assuntos foram liberados!"
        })
        
    except Exception as e:
        print(f"[ERRO admin_liberar_tudo]: {e}")
        return jsonify({
            "success": False,
            "message": "Erro ao liberar assuntos"
        }), 500

@app.route("/api/admin/bloquear-todos", methods=["POST"])
def admin_bloquear_todos():
    """Bloquear um assunto para todos os usuários ativos"""
    try:
        data = request.json
        materia = data.get("materia")
        assunto = data.get("assunto")
        
        if not materia or not assunto:
            return jsonify({
                "success": False,
                "message": "Matéria e assunto são obrigatórios"
            }), 400
        
        # 1. Buscar todos os usuários ativos
        conn = db_usuarios()
        cur = conn.cursor()
        
        cur.execute("SELECT id FROM usuarios WHERE ativo = 1")
        usuarios = cur.fetchall()
        
        # 2. Bloquear para cada usuário
        for usuario in usuarios:
            usuario_id = usuario["id"]
            
            # Verificar se já existe
            cur.execute("""
                SELECT id FROM bloqueios_assuntos 
                WHERE usuario_id = ? AND materia = ? AND assunto = ?
            """, (usuario_id, materia, assunto))
            
            existe = cur.fetchone()
            
            if existe:
                # Atualizar para bloqueado
                cur.execute("""
                    UPDATE bloqueios_assuntos 
                    SET bloqueado = 1
                    WHERE usuario_id = ? AND materia = ? AND assunto = ?
                """, (usuario_id, materia, assunto))
            else:
                # Inserir novo
                cur.execute("""
                    INSERT INTO bloqueios_assuntos (usuario_id, materia, assunto, bloqueado)
                    VALUES (?, ?, ?, 1)
                """, (usuario_id, materia, assunto))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": f"Assunto '{assunto}' bloqueado para {len(usuarios)} usuários ativos!"
        })
        
    except Exception as e:
        print(f"[ERRO admin_bloquear_todos]: {e}")
        return jsonify({
            "success": False,
            "message": "Erro ao bloquear para todos"
        }), 500

# ======================================================
# ROTA FALTANTE: BLOQUEAR ASSUNTO ESPECÍFICO
# ======================================================

@app.route("/api/admin/bloquear", methods=["POST"])
def admin_bloquear():
    """Bloquear ou desbloquear um assunto para um usuário específico"""
    try:
        data = request.json
        
        usuario_id = data.get("usuario_id")
        materia = data.get("materia")
        assunto = data.get("assunto")
        bloquear = data.get("bloquear", True)  # True = bloquear, False = desbloquear
        
        if not usuario_id or not materia or not assunto:
            return jsonify({
                "success": False,
                "message": "Dados incompletos"
            }), 400
        
        conn = db_usuarios()
        cur = conn.cursor()
        
        # Converter para inteiro (1 = bloqueado, 0 = desbloqueado)
        bloqueado_int = 1 if bloquear else 0
        
        # Verificar se já existe
        cur.execute("""
            SELECT id FROM bloqueios_assuntos 
            WHERE usuario_id = ? AND materia = ? AND assunto = ?
        """, (usuario_id, materia, assunto))
        
        existe = cur.fetchone()
        
        if existe:
            # Atualizar
            cur.execute("""
                UPDATE bloqueios_assuntos 
                SET bloqueado = ?
                WHERE usuario_id = ? AND materia = ? AND assunto = ?
            """, (bloqueado_int, usuario_id, materia, assunto))
        else:
            # Inserir novo
            cur.execute("""
                INSERT INTO bloqueios_assuntos (usuario_id, materia, assunto, bloqueado)
                VALUES (?, ?, ?, ?)
            """, (usuario_id, materia, assunto, bloqueado_int))
        
        conn.commit()
        conn.close()
        
        acao = "bloqueado" if bloquear else "desbloqueado"
        return jsonify({
            "success": True,
            "message": f"Assunto '{assunto}' {acao} com sucesso!"
        })
        
    except Exception as e:
        print(f"[ERRO /api/admin/bloquear]: {e}")
        return jsonify({
            "success": False,
            "message": f"Erro: {str(e)}"
        }), 500

@app.route("/api/admin/liberar-todos", methods=["POST"])
def admin_liberar_todos():
    """Liberar um assunto para todos os usuários"""
    try:
        data = request.json
        materia = data.get("materia")
        assunto = data.get("assunto")
        
        if not materia or not assunto:
            return jsonify({
                "success": False,
                "message": "Matéria e assunto são obrigatórios"
            }), 400
        
        conn = db_usuarios()
        cur = conn.cursor()
        
        # Remover todos os registros deste assunto
        cur.execute("""
            DELETE FROM bloqueios_assuntos 
            WHERE materia = ? AND assunto = ?
        """, (materia, assunto))
        
        removidos = cur.rowcount
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": f"Assunto '{assunto}' liberado para todos os usuários! ({removidos} registros removidos)"
        })
        
    except Exception as e:
        print(f"[ERRO admin_liberar_todos]: {e}")
        return jsonify({
            "success": False,
            "message": "Erro ao liberar para todos"
        }), 500
    
# ======================================================
# ROTAS PARA BLOQUEAR ASSUNTO P/ TODOS
# ======================================================  
@app.route("/api/admin/bloquear-todos-assuntos", methods=["POST"])
def admin_bloquear_todos_assuntos():
    """Bloquear um assunto para TODOS os usuários ativos"""
    try:
        data = request.json
        materia = data.get("materia")
        assunto = data.get("assunto")
        
        if not materia or not assunto:
            return jsonify({
                "success": False,
                "message": "Matéria e assunto são obrigatórios"
            }), 400
        
        conn = db_usuarios()
        cur = conn.cursor()
        
        # 1. Buscar todos os usuários ativos
        cur.execute("SELECT id FROM usuarios WHERE ativo = 1")
        usuarios = cur.fetchall()
        
        if not usuarios:
            conn.close()
            return jsonify({
                "success": False,
                "message": "Nenhum usuário ativo encontrado"
            })
        
        # 2. Bloquear para cada usuário
        for usuario in usuarios:
            usuario_id = usuario["id"]
            
            # Verificar se já existe
            cur.execute("""
                SELECT id FROM bloqueios_assuntos 
                WHERE usuario_id = ? AND materia = ? AND assunto = ?
            """, (usuario_id, materia, assunto))
            
            existe = cur.fetchone()
            
            if existe:
                # Atualizar para bloqueado
                cur.execute("""
                    UPDATE bloqueios_assuntos 
                    SET bloqueado = 1
                    WHERE usuario_id = ? AND materia = ? AND assunto = ?
                """, (usuario_id, materia, assunto))
            else:
                # Inserir novo
                cur.execute("""
                    INSERT INTO bloqueios_assuntos (usuario_id, materia, assunto, bloqueado)
                    VALUES (?, ?, ?, 1)
                """, (usuario_id, materia, assunto))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": f"Assunto '{assunto}' bloqueado para {len(usuarios)} usuários ativos!",
            "usuarios_afetados": len(usuarios)
        })
        
    except Exception as e:
        print(f"[ERRO admin_bloquear_todos_assuntos]: {e}")
        return jsonify({
            "success": False,
            "message": f"Erro ao bloquear para todos: {str(e)}"
        }), 500

# Rota para liberar assunto para TODOS os usuários
@app.route("/api/admin/liberar-todos-assuntos", methods=["POST"])
def admin_liberar_todos_assuntos():
    """Liberar um assunto para TODOS os usuários"""
    try:
        data = request.json
        materia = data.get("materia")
        assunto = data.get("assunto")
        
        if not materia or not assunto:
            return jsonify({
                "success": False,
                "message": "Matéria e assunto são obrigatórios"
            }), 400
        
        conn = db_usuarios()
        cur = conn.cursor()
        
        # Remover todos os registros deste assunto
        cur.execute("""
            DELETE FROM bloqueios_assuntos 
            WHERE materia = ? AND assunto = ?
        """, (materia, assunto))
        
        removidos = cur.rowcount
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "message": f"Assunto '{assunto}' liberado para todos os usuários! ({removidos} registros removidos)",
            "removidos": removidos
        })
        
    except Exception as e:
        print(f"[ERRO admin_liberar_todos_assuntos]: {e}")
        return jsonify({
            "success": False,
            "message": f"Erro ao liberar para todos: {str(e)}"
        }), 500

# ======================================================
# ROTAS PARA ESTATÍSTICAS DA PÁGINA ADMIN DE USUÁRIOS
# ======================================================
@app.route("/api/admin/estatisticas", methods=["GET"])
def admin_estatisticas():
    """Retornar estatísticas gerais para o painel admin"""
    try:
        # 1. Total de perfis (usuários)
        conn_usuarios = db_usuarios()
        cur_usuarios = conn_usuarios.cursor()
        cur_usuarios.execute("SELECT COUNT(*) as total FROM usuarios")
        total_perfis = cur_usuarios.fetchone()["total"]
        conn_usuarios.close()
        
        # 2. Total de questões no banco principal (panda_db_questoes.db)
        conn_principal = db_questoes()
        cur_principal = conn_principal.cursor()
        cur_principal.execute("SELECT COUNT(*) as total FROM questoes")
        total_questoes_principal = cur_principal.fetchone()["total"]
        conn_principal.close()
        
        # 3. Total de questões no bank.db (módulo Laranja)
        total_questoes_bank = 0
        bank_db_path = os.path.join(LARANJA_DIR, "bank.db")
        
        if os.path.exists(bank_db_path):
            try:
                import sqlite3
                conn_bank = sqlite3.connect(bank_db_path)
                cur_bank = conn_bank.cursor()
                
                # Tentar várias possibilidades de nome de tabela
                tabelas_tentativas = ['questions', 'questoes', 'questao', 'perguntas', 'pergunta']
                
                for tabela in tabelas_tentativas:
                    try:
                        cur_bank.execute(f"SELECT COUNT(*) as total FROM {tabela}")
                        resultado = cur_bank.fetchone()
                        if resultado:
                            total_questoes_bank = resultado[0]
                            break
                    except:
                        continue
                
                # Se não encontrou com os nomes padrão, listar tabelas existentes
                if total_questoes_bank == 0:
                    cur_bank.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tabelas_existentes = [t[0] for t in cur_bank.fetchall()]
                    if tabelas_existentes:
                        # Usar a primeira tabela
                        primeira_tabela = tabelas_existentes[0]
                        try:
                            cur_bank.execute(f"SELECT COUNT(*) as total FROM {primeira_tabela}")
                            resultado = cur_bank.fetchone()
                            if resultado:
                                total_questoes_bank = resultado[0]
                        except:
                            pass
                
                conn_bank.close()
            except Exception as e:
                print(f"[INFO] Não foi possível contar questões no bank.db: {e}")
        
        return jsonify({
            "success": True,
            "total_usuarios": total_perfis,
            "total_questoes_principal": total_questoes_principal,
            "total_questoes_bank": total_questoes_bank
        })
        
    except Exception as e:
        print(f"[ERRO /api/admin/estatisticas]: {e}")
        return jsonify({
            "success": False,
            "total_usuarios": 0,
            "total_questoes_principal": 0,
            "total_questoes_bank": 0
        })

@app.route("/api/estatisticas/questoes-principal", methods=["GET"])
def estatisticas_questoes_principal():
    """Retornar apenas o total de questões do banco principal"""
    try:
        conn = db_questoes()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as total FROM questoes")
        total = cur.fetchone()["total"]
        conn.close()
        
        return jsonify({
            "success": True,
            "total": total
        })
        
    except Exception as e:
        print(f"[ERRO /api/estatisticas/questoes-principal]: {e}")
        return jsonify({
            "success": False,
            "total": 0
        })

@app.route("/api/estatisticas/questoes-bank", methods=["GET"])
def estatisticas_questoes_bank():
    """Retornar total de questões do bank.db (módulo Laranja)"""
    try:
        total = 0
        
        # Caminho correto para o bank.db
        bank_db_path = os.path.join(LARANJA_DIR, "bank.db")
        
        print(f"[DEBUG] Procurando bank.db em: {bank_db_path}")
        print(f"[DEBUG] Caminho LARANJA_DIR: {LARANJA_DIR}")
        
        if os.path.exists(bank_db_path):
            print(f"[DEBUG] bank.db encontrado!")
            
            # Conectar ao bank.db
            import sqlite3
            conn_bank = sqlite3.connect(bank_db_path)
            cur_bank = conn_bank.cursor()
            
            # Listar todas as tabelas para diagnóstico
            cur_bank.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tabelas = cur_bank.fetchall()
            print(f"[DEBUG] Tabelas encontradas em bank.db: {tabelas}")
            
            # Primeiro tentar a tabela 'questions' (mais comum)
            cur_bank.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='questions'")
            if cur_bank.fetchone():
                cur_bank.execute("SELECT COUNT(*) as total FROM questions")
                total = cur_bank.fetchone()[0]
                print(f"[DEBUG] Total de questões na tabela 'questions': {total}")
            else:
                # Se não tiver tabela 'questions', tentar outras possíveis
                # Verificar se tem alguma tabela que parece ser de questões
                for tabela_info in tabelas:
                    tabela = tabela_info[0]
                    tabela_lower = tabela.lower()
                    
                    # Verificar se o nome da tabela parece ser de questões
                    if 'question' in tabela_lower or 'quest' in tabela_lower or 'pergunta' in tabela_lower:
                        try:
                            cur_bank.execute(f"SELECT COUNT(*) as total FROM {tabela}")
                            total_temp = cur_bank.fetchone()[0]
                            print(f"[DEBUG] Tabela '{tabela}' tem {total_temp} registros")
                            
                            # Se tem muitos registros, provavelmente é a tabela de questões
                            if total_temp > 0:
                                total = total_temp
                                print(f"[DEBUG] Usando tabela '{tabela}' com {total} registros")
                                break
                        except:
                            continue
                
                # Se ainda não encontrou, contar registros na primeira tabela
                if total == 0 and tabelas:
                    primeira_tabela = tabelas[0][0]
                    try:
                        cur_bank.execute(f"SELECT COUNT(*) as total FROM {primeira_tabela}")
                        total = cur_bank.fetchone()[0]
                        print(f"[DEBUG] Usando primeira tabela '{primeira_tabela}' com {total} registros")
                    except:
                        pass
            
            conn_bank.close()
        else:
            print(f"[DEBUG] bank.db NÃO encontrado em: {bank_db_path}")
            # Verificar o que existe no diretório
            if os.path.exists(LARANJA_DIR):
                arquivos = os.listdir(LARANJA_DIR)
                print(f"[DEBUG] Arquivos em {LARANJA_DIR}: {arquivos}")
        
        print(f"[DEBUG] Retornando total: {total}")
        return jsonify({
            "success": True,
            "total": total
        })
        
    except Exception as e:
        print(f"[ERRO /api/estatisticas/questoes-bank]: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "total": 0,
            "erro": str(e)
        })

@app.route("/api/estatisticas/evolucao/<int:usuario_id>")
def estatisticas_evolucao(usuario_id):
    """Retornar dados de evolução com acertos e erros por dia para os últimos 31 dias"""
    try:
        conn = db_estatisticas()
        cur = conn.cursor()
        
        # Buscar dados dos últimos 31 dias
        cur.execute("""
            SELECT 
                DATE(data) as dia,
                SUM(CASE WHEN acertou = 1 THEN 1 ELSE 0 END) as acertos,
                SUM(CASE WHEN acertou = 0 THEN 1 ELSE 0 END) as erros,
                COUNT(*) as total
            FROM estatisticas
            WHERE usuario_id = ? 
            AND DATE(data) >= DATE('now', '-31 days')
            GROUP BY DATE(data)
            ORDER BY dia ASC
        """, (usuario_id,))
        
        rows = cur.fetchall()
        conn.close()
        
        # Criar arrays com os dados
        labels = []
        acertos = []
        erros = []
        
        for row in rows:
            # Converter data de YYYY-MM-DD para DD/MM
            data_completa = row["dia"]
            if data_completa:
                partes = data_completa.split('-')
                if len(partes) == 3:
                    dia = partes[2]
                    mes = partes[1]
                    labels.append(f"{dia}/{mes}")
                else:
                    labels.append(data_completa)
            else:
                labels.append("Data inválida")
            
            acertos.append(row["acertos"])
            erros.append(row["erros"])
        
        print(f"✅ Dados de evolução para usuário {usuario_id}: {len(labels)} dias encontrados")
        print(f"📊 Datas: {labels}")
        print(f"📊 Acertos: {acertos}")
        print(f"📊 Erros: {erros}")
        
        return jsonify({
            "success": True,
            "labels": labels,
            "acertos": acertos,
            "erros": erros
        })
        
    except Exception as e:
        print(f"[ERRO] /api/estatisticas/evolucao/{usuario_id}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "labels": [],
            "acertos": [],
            "erros": []
        })

# ======================================================
# CONFIGURAÇÕES DE MÍDIA (MOVER PARA CIMA)
# ======================================================

# Pastas para mídia (imagens e áudios)
MIDIA_DIR = os.path.join(FRONTEND_DIR, "midia")
IMAGENS_DIR = os.path.join(MIDIA_DIR, "imagens")
AUDIOS_DIR = os.path.join(MIDIA_DIR, "audios")
PRONUNCIAS_DIR = os.path.join(AUDIOS_DIR, "pronuncias")

# Criar pastas se não existirem
for pasta in [MIDIA_DIR, IMAGENS_DIR, AUDIOS_DIR, PRONUNCIAS_DIR]:
    os.makedirs(pasta, exist_ok=True)
    print(f"📁 Pasta criada/verificada: {pasta}")


# ======================================================
# ROTA PARA QUESTÕES DE VOZ
# ======================================================
@app.route("/api/questoes-voz")
def questoes_voz():
    """Buscar questões do tipo VOZ para a página de voz"""
    materia = request.args.get("materia")
    assunto = request.args.get("assunto")
    
    try:
        conn = db_questoes()
        cur = conn.cursor()
        
        query = "SELECT * FROM questoes WHERE (tipo_questao = 'voz' OR tipo_questao = 'voz_multipla') AND ativo = 1"
        params = []
        
        if materia:
            query += " AND materia = ?"
            params.append(materia)
        
        if assunto:
            query += " AND assunto = ?"
            params.append(assunto)
        
        query += " ORDER BY RANDOM() LIMIT 50"
        
        cur.execute(query, params)
        
        questoes = []
        for row in cur.fetchall():
            q = dict(row)
            
            questao = {
                "id": q["id"],
                "tipo": q["tipo_questao"],
                "materia": q["materia"],
                "assunto": q["assunto"],
                "pergunta": q["pergunta"],
                "imagem_url": q["imagem_url"] or q["imagem_path"],
                "audio_url": q["audio_url"] or q["audio_path"],
                "resposta_voz": q["resposta_voz"] or q.get("resposta_correta", ""),
                "opcoes": [
                    q["opcao_a"], q["opcao_b"], q["opcao_c"], q["opcao_d"]
                ] if q["opcao_a"] else [],
                "correta": q["resposta_correta"]
            }
            
            questoes.append(questao)
        
        conn.close()
        return jsonify(questoes)
        
    except Exception as e:
        print(f"[ERRO /api/questoes-voz]: {e}")
        return jsonify([])

@app.route("/audios/<path:filename>")
def servir_audio(filename):
    """Servir áudios (alias para midia/audios)"""
    return servir_midia(f"audios/{filename}")

# ======================================================
# ROTAS DO INGLES
# ======================================================
@app.route('/ingles/<int:id>')
def ingles(id):
    conn = sqlite3.connect('panda_db_questoes.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM questoes WHERE id = ?", (id,))
    questao = cursor.fetchone()
    conn.close()

    if questao:
        imagem = buscar_arquivo(questao['imagem'], "imagens") if questao['imagem'] else None
        audio = buscar_arquivo(questao['audio'], "audios") if questao['audio'] else None
    else:
        imagem = None
        audio = None

    return render_template("ingles.html", questao=questao, imagem=imagem, audio=audio)

@app.route('/midia/<path:filename>')
def servir_midia(filename):
    """Servir arquivos da pasta midia (imagens, áudios, etc.)"""
    try:
        # Caminho completo para a pasta midia
        midia_path = os.path.join(FRONTEND_DIR, 'midia')
        print(f"📁 Servindo mídia: {filename} de {midia_path}")
        
        # Verificar se o arquivo existe
        arquivo_path = os.path.join(midia_path, filename)
        if os.path.exists(arquivo_path):
            print(f"✅ Arquivo encontrado: {arquivo_path}")
            return send_from_directory(midia_path, filename)
        else:
            print(f"❌ Arquivo NÃO encontrado: {arquivo_path}")
            return "Arquivo não encontrado", 404
            
    except Exception as e:
        print(f"❌ Erro ao servir mídia: {e}")
        return str(e), 500

# ======================================================
# INICIALIZAÇÃO DO SERVIDOR
# ======================================================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("PANDA ESTUDOS - SERVIDOR FLASK INICIANDO")
    print("="*60)
    print(f"📱 Sistema Principal: http://localhost:5000")
    print(f"📚 Matérias: http://localhost:5000/materias.html")
    print(f"📖 Assuntos: http://localhost:5000/assuntos.html")
    print(f"❓ Questões: http://localhost:5000/questoes.html")
    print(f"📊 Painel Admin Questões: http://localhost:5000/dbquestoes.html")
    print(f"👥 Gestão de Usuários: http://localhost:5000/usuarios-admin.html")
    print(f"📈 Estatísticas: http://localhost:5000/estatisticas.html")
    print(f"🍊 Módulo Laranja: http://localhost:5000/laranja/")
    print("="*60)
    print("Pressione CTRL+C para parar o servidor")
    print("="*60 + "\n")
        
    app.run(host='127.0.0.1', port=5000, debug=True)