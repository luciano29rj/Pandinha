from flask import Blueprint, render_template, jsonify, request, send_from_directory, send_file, make_response
import sqlite3
import os
import pandas as pd
import io
import json
from datetime import datetime
import tempfile
import sys
import uuid

# ========== CONFIGURAÇÃO DE CAMINHOS ABSOLUTOS ==========
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LARANJA_DIR = os.path.join(BASE_DIR, '..')
LARANJA_TEMPLATES_DIR = os.path.join(LARANJA_DIR, 'templates')
LARANJA_STATIC_DIR = os.path.join(LARANJA_DIR, 'static')
DATA_DIR = os.path.join(LARANJA_DIR, 'data')
DB_PATH = os.path.join(DATA_DIR, 'bank.db')

# ========== PASTA PARA IMAGENS ==========
# Usar a pasta img dentro do diretório laranja
LARANJA_IMG_DIR = os.path.join(LARANJA_DIR, 'img')

print("="*60)
print("🍊 SISTEMA LARANJA - CONFIGURAÇÃO ABSOLUTA")
print("="*60)
print(f"BASE_DIR (orange.py): {BASE_DIR}")
print(f"LARANJA_DIR: {LARANJA_DIR}")
print(f"LARANJA_TEMPLATES_DIR: {LARANJA_TEMPLATES_DIR}")
print(f"LARANJA_STATIC_DIR: {LARANJA_STATIC_DIR}")
print(f"LARANJA_IMG_DIR: {LARANJA_IMG_DIR}")
print(f"DATA_DIR: {DATA_DIR}")
print(f"DB_PATH: {DB_PATH}")
print("="*60)

laranja_bp = Blueprint('laranja', __name__,
                     static_folder=LARANJA_STATIC_DIR,
                     static_url_path='/laranja/static',
                     template_folder=LARANJA_TEMPLATES_DIR)

os.makedirs(LARANJA_TEMPLATES_DIR, exist_ok=True)
os.makedirs(LARANJA_STATIC_DIR, exist_ok=True)
os.makedirs(LARANJA_IMG_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# ========== FUNÇÕES DO BANCO DE DADOS ==========

def get_db():
    """Conectar ao banco de dados Laranja (bank.db)"""
    if not os.path.exists(DB_PATH):
        print(f"⚠️  Banco de dados não encontrado em {DB_PATH}")
        print("   Criando banco vazio...")
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS questoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ano INTEGER,
                banca TEXT,
                orgao TEXT,
                cargo TEXT,
                nivel TEXT,
                area TEXT,
                materia TEXT,
                assunto TEXT,
                sub_assunto TEXT,
                pergunta TEXT,
                opcao_1 TEXT,
                opcao_2 TEXT,
                opcao_3 TEXT,
                opcao_4 TEXT,
                opcao_5 TEXT,
                tipo TEXT,
                gabarito TEXT,
                dica TEXT,
                dificuldade TEXT,
                imagem TEXT  -- NOVA COLUNA PARA IMAGEM
            )
        ''')
        
        print("✅ Tabela 'questoes' criada com suporte a imagens")
        conn.commit()
        conn.close()
    else:
        # Verificar se a coluna 'imagem' existe, se não, adicionar
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Verificar as colunas existentes
        c.execute("PRAGMA table_info(questoes)")
        colunas = [coluna[1] for coluna in c.fetchall()]
        
        if 'imagem' not in colunas:
            print("📸 Adicionando coluna 'imagem' à tabela questoes...")
            c.execute("ALTER TABLE questoes ADD COLUMN imagem TEXT")
            conn.commit()
            print("✅ Coluna 'imagem' adicionada com sucesso!")
        
        conn.close()
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ========== FUNÇÃO PARA LISTAR TEMPLATES ==========

def listar_templates():
    if os.path.exists(LARANJA_TEMPLATES_DIR):
        templates = os.listdir(LARANJA_TEMPLATES_DIR)
        print(f"📄 Templates disponíveis: {templates}")
        return templates
    else:
        print(f"❌ Pasta de templates não encontrada: {LARANJA_TEMPLATES_DIR}")
        return []

# ========== ROTAS DO LARANJA ==========

@laranja_bp.route('/teste')
def teste():
    templates = listar_templates()
    html = f"""
    <html>
    <head><title>Teste Laranja</title></head>
    <body>
        <h1>✅ Sistema Laranja está funcionando!</h1>
        <p><strong>Caminho templates:</strong> {LARANJA_TEMPLATES_DIR}</p>
        <p><strong>Templates encontrados ({len(templates)}):</strong></p>
        <ul>
    """
    for template in templates:
        html += f"<li>{template}</li>"
    
    html += """
        </ul>
        <p><a href='/laranja/'>Ir para página principal</a></p>
    </body>
    </html>
    """
    return html

@laranja_bp.route('/')
def index():
    template_path = os.path.join(LARANJA_TEMPLATES_DIR, 'subject.html')
    if not os.path.exists(template_path):
        return f"""
        <html>
        <head><title>Erro - Template não encontrado</title></head>
        <body>
            <h1>❌ Template não encontrado!</h1>
            <p>O arquivo <strong>subject.html</strong> não foi encontrado em:</p>
            <p><code>{LARANJA_TEMPLATES_DIR}</code></p>
            <p>Por favor, coloque o arquivo subject.html nesta pasta.</p>
            <p><a href='/laranja/teste'>Voltar para teste</a></p>
        </body>
        </html>
        """, 404
    
    return render_template('subject.html')

@laranja_bp.route('/subject')
@laranja_bp.route('/subject.html')
def subject():
    template_path = os.path.join(LARANJA_TEMPLATES_DIR, 'subject.html')
    if not os.path.exists(template_path):
        return "Template subject.html não encontrado!", 404
    return render_template('subject.html')

@laranja_bp.route('/topic')
@laranja_bp.route('/topic.html')
def topic():
    materia = request.args.get('materia', '')
    return render_template('topic.html', materia=materia)

@laranja_bp.route('/quest')
@laranja_bp.route('/quest.html')
def quest():
    assunto = request.args.get('assunto_nome', '')
    materia = request.args.get('materia', '')
    return render_template('quiz.html', assunto=assunto, materia=materia)

@laranja_bp.route('/import')
@laranja_bp.route('/import.html')
def import_page():
    return render_template('import.html')

@laranja_bp.route('/imgaztec')
@laranja_bp.route('/imgaztec.html')
def imgaztec():
    """Página de administração de imagens"""
    template_path = os.path.join(LARANJA_TEMPLATES_DIR, 'imgaztec.html')
    if not os.path.exists(template_path):
        return f"Template imgaztec.html não encontrado em {template_path}", 404
    return render_template('imgaztec.html')

# ========== NOVA ROTA PARA SERVIR IMAGENS ==========
@laranja_bp.route('/img/<path:filename>')
def serve_laranja_img(filename):
    """Serve imagens da pasta img do Laranja"""
    img_path = os.path.join(LARANJA_IMG_DIR, filename)
    
    # Se o arquivo não existir na pasta img, tentar na pasta uploads
    if not os.path.exists(img_path):
        upload_path = os.path.join(LARANJA_STATIC_DIR, 'uploads', filename)
        if os.path.exists(upload_path):
            return send_from_directory(os.path.join(LARANJA_STATIC_DIR, 'uploads'), filename)
        else:
            return "Imagem não encontrada", 404
    
    return send_from_directory(LARANJA_IMG_DIR, filename)

# ========== APIs DO LARANJA ==========

@laranja_bp.route('/api/materias')
def api_materias():
    try:
        conn = get_db()
        c = conn.cursor()
        
        query = '''
            SELECT materia, COUNT(*) as total
            FROM questoes 
            WHERE materia IS NOT NULL AND TRIM(materia) != ''
            GROUP BY materia 
            ORDER BY materia
        '''
        
        c.execute(query)
        results = c.fetchall()
        
        materias = []
        for row in results:
            materia_nome = row[0] if row[0] else "Sem matéria"
            total = row[1]
            
            materias.append({
                'nome': materia_nome,
                'quantidade': total
            })
        
        conn.close()
        
        print(f"✅ Encontradas {len(materias)} matérias no banco")
        return jsonify(materias)
        
    except Exception as e:
        print(f"❌ Erro em /laranja/api/materias: {e}")
        import traceback
        traceback.print_exc()
        return jsonify([])

@laranja_bp.route('/api/assuntos')
def api_assuntos():
    try:
        materia = request.args.get('materia', '')
        
        if not materia:
            print("❌ Erro: Parâmetro 'materia' não fornecido")
            return jsonify([])
        
        print(f"📝 Buscando assuntos para matéria: {materia}")
        
        conn = get_db()
        c = conn.cursor()
        
        query = '''
            SELECT assunto, COUNT(*) as total
            FROM questoes 
            WHERE materia = ? AND assunto IS NOT NULL AND TRIM(assunto) != ''
            GROUP BY assunto 
            ORDER BY assunto
        '''
        
        c.execute(query, (materia,))
        results = c.fetchall()
        
        assuntos = []
        for row in results:
            assunto_nome = row[0] if row[0] else "Sem assunto"
            total = row[1]
            
            assuntos.append({
                'nome': assunto_nome,
                'quantidade': total
            })
        
        conn.close()
        
        print(f"✅ Encontrados {len(assuntos)} assuntos para matéria: {materia}")
        return jsonify(assuntos)
        
    except Exception as e:
        print(f"❌ Erro em /laranja/api/assuntos: {e}")
        import traceback
        traceback.print_exc()
        return jsonify([])

@laranja_bp.route('/api/questoes-admin')
def api_questoes_admin():
    try:
        print(f"\n" + "="*50)
        print("🔍 API QUESTOES-ADMIN CHAMADA")
        print("="*50)
        
        conn = get_db()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute('SELECT COUNT(*) as total FROM questoes')
        total = c.fetchone()[0]
        print(f"📊 Total de questões no banco: {total}")
        
        if total == 0:
            print("⚠️  Banco vazio")
            conn.close()
            return jsonify([])
        
        # Buscar todas as questões
        c.execute('''
            SELECT * FROM questoes 
            ORDER BY materia, assunto, id
        ''')
        rows = c.fetchall()
        
        questoes = []
        for row in rows:
            questao = dict(row)
            
            # Garantir que todos os campos existam
            for key in ['materia', 'assunto', 'sub_assunto', 'pergunta', 'gabarito', 'dificuldade', 'nivel', 'tipo', 'ano', 'banca', 'orgao', 'cargo', 'opcao_1', 'opcao_2', 'opcao_3', 'opcao_4', 'opcao_5', 'dica', 'imagem']:
                if key not in questao or questao[key] is None:
                    questao[key] = ''
            
            # Garantir que o tipo seja uma string e normalizar
            if questao['tipo']:
                questao['tipo'] = str(questao['tipo']).strip()
            else:
                questao['tipo'] = 'Múltipla Escolha'
            
            questoes.append(questao)
        
        conn.close()
        
        # Contar questões por tipo para debug
        total_multipla = sum(1 for q in questoes if q['tipo'] == 'Múltipla Escolha')
        total_certo_errado = sum(1 for q in questoes if q['tipo'] == 'Certo/Errado')
        total_com_imagem = sum(1 for q in questoes if q['imagem'])
        
        print(f"✅ Retornando {len(questoes)} questões")
        print(f"📊 Múltipla Escolha: {total_multipla}, Certo/Errado: {total_certo_errado}")
        print(f"📸 Questões com imagem: {total_com_imagem}")
        if len(questoes) > 0:
            print(f"📄 Exemplo: {questoes[0]['materia']} - {questoes[0]['assunto']} - Tipo: {questao['tipo']}")
        print("="*50 + "\n")
        
        return jsonify(questoes)
        
    except Exception as e:
        print(f"❌ ERRO em api_questoes_admin: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@laranja_bp.route('/api/verificar-banco')
def api_verificar_banco():
    try:
        conn = get_db()
        c = conn.cursor()
        
        c.execute('SELECT COUNT(*) as total FROM questoes')
        total_questoes = c.fetchone()[0]
        
        c.execute('SELECT COUNT(DISTINCT materia) FROM questoes WHERE materia IS NOT NULL AND materia != ""')
        total_materias = c.fetchone()[0]
        
        c.execute('SELECT COUNT(DISTINCT assunto) FROM questoes WHERE assunto IS NOT NULL AND assunto != ""')
        total_assuntos = c.fetchone()[0]
        
        c.execute('SELECT COUNT(DISTINCT banca) FROM questoes WHERE banca IS NOT NULL AND banca != ""')
        total_bancas = c.fetchone()[0]
        
        # Contar por tipo
        c.execute('SELECT COUNT(*) FROM questoes WHERE tipo = "Certo/Errado"')
        total_certo_errado = c.fetchone()[0]
        
        # Contar questões com imagem
        c.execute('SELECT COUNT(*) FROM questoes WHERE imagem IS NOT NULL AND imagem != ""')
        total_com_imagem = c.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'total_questoes': total_questoes,
            'total_materias': total_materias,
            'total_assuntos': total_assuntos,
            'total_bancas': total_bancas,
            'total_certo_errado': total_certo_errado,
            'total_com_imagem': total_com_imagem
        })
        
    except Exception as e:
        print(f"❌ Erro em verificar-banco: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@laranja_bp.route('/api/exportar-excel')
def api_exportar_excel():
    try:
        print("📤 Exportando para Excel...")
        
        conn = get_db()
        c = conn.cursor()
        
        # ========== Incluir coluna imagem na exportação ==========
        c.execute('''
            SELECT 
                id, 
                materia, 
                assunto, 
                sub_assunto, 
                banca, 
                orgao, 
                cargo,          
                ano, 
                nivel, 
                dificuldade, 
                pergunta,
                opcao_1, 
                opcao_2, 
                opcao_3, 
                opcao_4, 
                opcao_5, 
                gabarito, 
                dica, 
                tipo,
                imagem  -- NOVA COLUNA
            FROM questoes 
            ORDER BY materia, assunto, sub_assunto, id
        ''')
        rows = c.fetchall()
        
        if not rows:
            conn.close()
            return jsonify({'success': False, 'error': 'Nenhuma questão encontrada'}), 404
        
        print(f"✅ Encontradas {len(rows)} questões para exportar")
        
        # Contar por tipo para debug
        tipo_counts = {}
        for row in rows:
            tipo = row[18] if len(row) > 18 else 'Múltipla Escolha'
            tipo_counts[tipo] = tipo_counts.get(tipo, 0) + 1
        
        print(f"📊 Tipos na exportação: {tipo_counts}")
        
        try:
            import pandas as pd
            
            # ========== DataFrame com coluna imagem ==========
            df = pd.DataFrame(rows, columns=[
                'ID', 
                'Matéria', 
                'Assunto', 
                'Sub Assunto', 
                'Banca', 
                'Órgão', 
                'Cargo',          
                'Ano', 
                'Nível', 
                'Dificuldade', 
                'Pergunta',
                'Opção 1',         
                'Opção 2', 
                'Opção 3', 
                'Opção 4', 
                'Opção 5', 
                'Gabarito', 
                'Dica/Explicação', 
                'Tipo',
                'Imagem'  # NOVA COLUNA
            ])
            
            output = io.BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Questões', index=False)
                
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
            excel_data = output.getvalue()
            content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            file_extension = '.xlsx'
            
            print("✅ Excel gerado com pandas/openpyxl")
            
        except Exception as excel_error:
            print(f"⚠️  Erro com pandas/openpyxl: {excel_error}. Usando CSV como fallback...")
            
            output = io.StringIO()
            import csv
            writer = csv.writer(output, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            
            writer.writerow([
                'ID', 'Matéria', 'Assunto', 'Sub Assunto', 'Banca', 'Órgão', 'Cargo',
                'Ano', 'Nível', 'Dificuldade', 'Pergunta',
                'Opção 1', 'Opção 2', 'Opção 3', 'Opção 4', 'Opção 5',
                'Gabarito', 'Dica/Explicação', 'Tipo', 'Imagem'
            ])
            
            for row in rows:
                writer.writerow([str(cell) if cell is not None else '' for cell in row])
            
            excel_data = output.getvalue().encode('utf-8')
            content_type = 'text/csv; charset=utf-8'
            file_extension = '.csv'
            print("✅ CSV gerado como fallback")
        
        conn.close()
        
        data_atual = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        nome_arquivo = f'banco_questoes_completo_{data_atual}{file_extension}'
        
        response = make_response(excel_data)
        response.headers['Content-Type'] = content_type
        response.headers['Content-Disposition'] = f'attachment; filename="{nome_arquivo}"'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        print(f"✅ Arquivo gerado: {nome_arquivo} ({len(rows)} questões)")
        return response
        
    except Exception as e:
        print(f"❌ ERRO CRÍTICO na exportação: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Erro na exportação: {str(e)}'}), 500

@laranja_bp.route('/api/exportar-csv')
def api_exportar_csv():
    try:
        print("📤 Exportando para CSV...")
        
        conn = get_db()
        
        # ========== Incluir coluna imagem na exportação ==========
        query = '''
            SELECT 
                id, 
                materia, 
                assunto, 
                sub_assunto, 
                banca, 
                orgao, 
                cargo, 
                ano, 
                nivel, 
                dificuldade, 
                pergunta,
                opcao_1, 
                opcao_2, 
                opcao_3, 
                opcao_4, 
                opcao_5, 
                gabarito, 
                dica, 
                tipo,
                imagem
            FROM questoes 
            ORDER BY id
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            return jsonify({'success': False, 'error': 'Nenhuma questão encontrada'}), 404
        
        # ========== Renomear colunas ==========
        df.columns = [
            'ID', 'Matéria', 'Assunto', 'Sub Assunto', 'Banca', 'Órgão', 'Cargo', 'Ano',
            'Nível', 'Dificuldade', 'Pergunta',
            'Opção A', 'Opção B', 'Opção C', 'Opção D', 'Opção E',
            'Gabarito', 'Dica/Explicação', 'Tipo', 'Imagem'
        ]
        
        output = io.StringIO()
        df.to_csv(output, index=False, encoding='utf-8-sig', sep=';')
        
        data_atual = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        nome_arquivo = f'banco_questoes_completo_{data_atual}.csv'
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename="{nome_arquivo}"'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        print(f"✅ Arquivo CSV gerado: {nome_arquivo} ({len(df)} questões)")
        return response
        
    except Exception as e:
        print(f"❌ Erro na exportação CSV: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@laranja_bp.route('/api/questoes')
def api_questoes():
    try:
        assunto = request.args.get('assunto', '')
        materia = request.args.get('materia', '')
        modo = request.args.get('modo', 'todas')
        limit = int(request.args.get('limit', 50))
        
        print(f"📝 Buscando questões - Assunto: {assunto}, Matéria: {materia}")
        
        conn = get_db()
        c = conn.cursor()
        
        # ========== Incluir coluna imagem na consulta ==========
        query = '''
            SELECT id, ano, banca, orgao, cargo, nivel, area, 
                   materia, assunto, pergunta, 
                   opcao_1, opcao_2, opcao_3, opcao_4, opcao_5,
                   tipo, gabarito, dica, imagem
            FROM questoes 
            WHERE 1=1
        '''
        params = []
        
        if assunto and assunto != 'todas':
            query += ' AND (assunto = ? OR sub_assunto = ?)'
            params.append(assunto)
            params.append(assunto)
        
        if materia:
            query += ' AND materia = ?'
            params.append(materia)
        
        if modo == 'aleatorio':
            query += ' ORDER BY RANDOM()'
        elif modo == 'recentes':
            query += ' ORDER BY ano DESC'
        else:
            query += ' ORDER BY id'
        
        query += ' LIMIT ?'
        params.append(limit)
        
        c.execute(query, params)
        results = c.fetchall()
        
        questoes = []
        for row in results:
            questao = {
                'id': row[0],
                'metadata': {
                    'ano': row[1],
                    'banca': row[2],
                    'orgao': row[3],
                    'cargo': row[4],
                    'nivel': row[5],
                    'area': row[6],
                    'materia': row[7],
                    'assunto': row[8]
                },
                'pergunta': row[9],
                'opcoes': [],
                'resposta_correta': row[16] if row[16] else '',
                'explicacao': row[17] if row[17] else '',
                'imagem': row[18] if len(row) > 18 and row[18] else ''  # NOVO CAMPO
            }
            
            opcoes_disponiveis = ['A', 'B', 'C', 'D', 'E']
            for i in range(5):
                texto_opcao = row[10 + i]
                if texto_opcao and texto_opcao.strip():
                    questao['opcoes'].append({
                        'letra': opcoes_disponiveis[i],
                        'texto': texto_opcao
                    })
            
            questoes.append(questao)
        
        conn.close()
        
        print(f"✅ Encontradas {len(questoes)} questões")
        return jsonify({
            'total': len(questoes),
            'questoes': questoes
        })
        
    except Exception as e:
        print(f"❌ Erro em /laranja/api/questoes: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'total': 0, 'questoes': []})

@laranja_bp.route('/api/salvar-questao', methods=['POST'])
def api_salvar_questao():
    try:
        data = request.json
        
        print(f"📝 Recebendo questão para salvar: {data.get('materia')} - {data.get('assunto')} - Tipo: {data.get('tipo')}")
        
        # Validação básica
        if not data.get('materia') or not data.get('pergunta'):
            return jsonify({'success': False, 'error': 'Campos obrigatórios: matéria e pergunta'}), 400
        
        conn = get_db()
        c = conn.cursor()
        
        # Verificar duplicata (apenas para novas questões)
        if not data.get('id'):
            c.execute('''
                SELECT COUNT(*) FROM questoes 
                WHERE materia = ? AND pergunta LIKE ?
            ''', (data['materia'], f"%{data['pergunta'][:50]}%"))
            
            if c.fetchone()[0] > 0:
                conn.close()
                return jsonify({'success': False, 'error': 'Questão semelhante já existe no banco de dados'}), 400
        
        if data.get('id'):
            # ========== UPDATE com coluna imagem ==========
            c.execute('''
                UPDATE questoes SET
                    materia = ?,
                    assunto = ?,
                    sub_assunto = ?,
                    banca = ?,
                    orgao = ?,
                    cargo = ?,
                    nivel = ?,
                    pergunta = ?,
                    opcao_1 = ?,
                    opcao_2 = ?,
                    opcao_3 = ?,
                    opcao_4 = ?,
                    opcao_5 = ?,
                    tipo = ?,
                    gabarito = ?,
                    dica = ?,
                    ano = ?,
                    dificuldade = ?,
                    imagem = ?
                WHERE id = ?
            ''', (
                data.get('materia', ''),
                data.get('assunto', ''),
                data.get('sub_assunto', ''),
                data.get('banca', ''),
                data.get('orgao', ''),
                data.get('cargo', ''),
                data.get('nivel', 'Médio'),
                data.get('pergunta', ''),
                data.get('opcao_1', ''),
                data.get('opcao_2', ''),
                data.get('opcao_3', ''),
                data.get('opcao_4', ''),
                data.get('opcao_5', ''),
                data.get('tipo', 'Múltipla Escolha'),
                data.get('gabarito', 'A').upper(),
                data.get('dica', ''),
                data.get('ano', datetime.now().year),
                data.get('dificuldade', 'Média'),
                data.get('imagem', ''),  # NOVO CAMPO
                data['id']
            ))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Questão {data['id']} atualizada")
            return jsonify({'success': True, 'id': data['id']})
            
        else:
            # ========== INSERT com coluna imagem ==========
            c.execute('''
                INSERT INTO questoes (
                    materia, assunto, sub_assunto, banca, orgao, cargo,
                    nivel, pergunta, opcao_1, opcao_2, opcao_3,
                    opcao_4, opcao_5, tipo, gabarito, dica, ano,
                    dificuldade, imagem
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('materia', ''),
                data.get('assunto', ''),
                data.get('sub_assunto', ''),
                data.get('banca', ''),
                data.get('orgao', ''),
                data.get('cargo', ''),
                data.get('nivel', 'Médio'),
                data.get('pergunta', ''),
                data.get('opcao_1', ''),
                data.get('opcao_2', ''),
                data.get('opcao_3', ''),
                data.get('opcao_4', ''),
                data.get('opcao_5', ''),
                data.get('tipo', 'Múltipla Escolha'),
                data.get('gabarito', 'A').upper(),
                data.get('dica', ''),
                data.get('ano', datetime.now().year),
                data.get('dificuldade', 'Média'),
                data.get('imagem', '')  # NOVO CAMPO
            ))
            
            conn.commit()
            questao_id = c.lastrowid
            conn.close()
            
            print(f"✅ Questão criada com ID: {questao_id}")
            return jsonify({'success': True, 'id': questao_id})
        
    except Exception as e:
        print(f"❌ Erro em /laranja/api/salvar-questao: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@laranja_bp.route('/api/criar-questao', methods=['POST'])
def api_criar_questao():
    return api_salvar_questao()

@laranja_bp.route('/api/atualizar-questao/<int:questao_id>', methods=['PUT'])
def api_atualizar_questao(questao_id):
    try:
        data = request.json
        data['id'] = questao_id
        return api_salvar_questao()
    except Exception as e:
        print(f"❌ Erro em /laranja/api/atualizar-questao: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@laranja_bp.route('/api/deletar-questao/<int:questao_id>', methods=['DELETE'])
def api_deletar_questao(questao_id):
    try:
        conn = get_db()
        c = conn.cursor()
        
        c.execute('SELECT COUNT(*) FROM questoes WHERE id = ?', (questao_id,))
        if c.fetchone()[0] == 0:
            conn.close()
            return jsonify({'success': False, 'error': 'Questão não encontrada'}), 404
        
        c.execute('DELETE FROM questoes WHERE id = ?', (questao_id,))
        conn.commit()
        conn.close()
        
        print(f"✅ Questão {questao_id} deletada")
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"❌ Erro em /laranja/api/deletar-questao: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@laranja_bp.route('/api/questao/<int:questao_id>')
def api_questao_detalhe(questao_id):
    try:
        conn = get_db()
        c = conn.cursor()
        
        c.execute('SELECT * FROM questoes WHERE id = ?', (questao_id,))
        row = c.fetchone()
        
        if not row:
            conn.close()
            return jsonify({'success': False, 'error': 'Questão não encontrada'}), 404
        
        questao = dict(row)
        
        for key in questao:
            if questao[key] is None:
                questao[key] = ''
        
        conn.close()
        
        return jsonify({'success': True, 'questao': questao})
        
    except Exception as e:
        print(f"❌ Erro em /laranja/api/questao/{questao_id}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@laranja_bp.route('/api/importar-excel', methods=['POST'])
def api_importar_excel():
    try:
        print("="*60)
        print("📥 IMPORTANDO EXCEL PARA BANCO DE DADOS")
        print("="*60)
        
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Content-Type deve ser application/json'}), 400
        
        dados = request.get_json()
        
        if not dados or not isinstance(dados, list):
            return jsonify({'success': False, 'error': 'Dados inválidos. Esperado uma lista de questões.'}), 400
        
        print(f"📄 Número de questões recebidas: {len(dados)}")
        
        conn = get_db()
        c = conn.cursor()
        
        inseridas = 0
        duplicadas = 0
        erros = 0
        
        for i, item in enumerate(dados):
            try:
                # ========== Capturar campos ==========
                materia = (item.get('Matéria') or item.get('materia') or item.get('Materia') or '').strip()
                assunto = (item.get('Assunto') or item.get('assunto') or '').strip()
                
                sub_assunto = ''
                possiveis_nomes = [
                    'Sub Assunto', 'SubAssunto', 'Sub_Assunto', 'SUB_ASSUNTO', 
                    'sub_assunto', 'Subassunto', 'SUBASSUNTO', 'Sub - Assunto',
                    'Sub‑Assunto', 'Sub – Assunto', 'Sub. Assunto', 'Sub.assunto',
                    'Sub', 'Sub-tópico', 'Subtópico', 'Subtopico'
                ]
                
                for nome in possiveis_nomes:
                    valor = item.get(nome)
                    if valor is not None and valor != '':
                        sub_assunto = str(valor).strip()
                        break
                
                banca = (item.get('Banca') or item.get('banca') or '').strip()
                orgao = (item.get('Órgão') or item.get('orgao') or item.get('Orgao') or '').strip()
                cargo = (item.get('Cargo') or item.get('cargo') or '').strip()
                ano = item.get('Ano') or item.get('ano') or datetime.now().year
                nivel = (item.get('Nível') or item.get('nivel') or item.get('Nivel') or 'Médio').strip()
                dificuldade = (item.get('Dificuldade') or item.get('dificuldade') or 'Média').strip()
                pergunta = (item.get('Pergunta') or item.get('pergunta') or '').strip()
                
                # ========== Capturar opções ==========
                opcao_1 = (item.get('Opção A') or item.get('opcao_1') or item.get('Opção 1') or '').strip()
                opcao_2 = (item.get('Opção B') or item.get('opcao_2') or item.get('Opção 2') or '').strip()
                opcao_3 = (item.get('Opção C') or item.get('opcao_3') or item.get('Opção 3') or '').strip()
                opcao_4 = (item.get('Opção D') or item.get('opcao_4') or item.get('Opção 4') or '').strip()
                opcao_5 = (item.get('Opção E') or item.get('opcao_5') or item.get('Opção 5') or '').strip()
                
                gabarito_raw = (item.get('Gabarito') or item.get('gabarito') or item.get('Resposta') or 'A')
                if isinstance(gabarito_raw, (int, float)) or (isinstance(gabarito_raw, str) and gabarito_raw.isdigit()):
                    valor_num = int(float(gabarito_raw))
                    if 1 <= valor_num <= 5:
                        gabarito = chr(64 + valor_num)
                    else:
                        gabarito = 'A'
                else:
                    gabarito = str(gabarito_raw).strip().upper()[:1]
                    if gabarito not in ['A', 'B', 'C', 'D', 'E']:
                        gabarito = 'A'
                
                dica = (item.get('Dica/Explicação') or item.get('Dica') or item.get('dica') or item.get('Explicação') or '').strip()
                tipo = (item.get('Tipo') or item.get('tipo') or 'Múltipla Escolha').strip()
                
                # ========== NOVO: Capturar imagem ==========
                imagem = ''
                possiveis_nomes_imagem = [
                    'Imagem', 'IMAGEM', 'imagem', 'Image', 'IMAGE', 'image',
                    'URL Imagem', 'URL_IMAGEM', 'url_imagem',
                    'Caminho Imagem', 'CAMINHO_IMAGEM', 'caminho_imagem'
                ]
                
                for nome in possiveis_nomes_imagem:
                    valor = item.get(nome)
                    if valor is not None and valor != '':
                        imagem = str(valor).strip()
                        break
                
                # Validar campos obrigatórios
                if not materia or not pergunta:
                    print(f"⚠️  Questão {i+1}: Campos obrigatórios faltando (Matéria e Pergunta)")
                    erros += 1
                    continue
                
                # Verificar duplicata
                pergunta_limpa = pergunta.lower().strip()
                c.execute('''
                    SELECT COUNT(*) FROM questoes 
                    WHERE LOWER(pergunta) LIKE ? 
                    AND LOWER(materia) = ?
                ''', (f'%{pergunta_limpa[:100]}%', materia.lower()))
                
                if c.fetchone()[0] > 0:
                    print(f"⚠️  Questão {i+1}: Duplicada encontrada")
                    duplicadas += 1
                    continue
                
                # Inserir questão com imagem
                c.execute('''
                    INSERT INTO questoes (
                        materia, assunto, sub_assunto, banca, orgao, cargo,
                        nivel, pergunta, opcao_1, opcao_2, opcao_3,
                        opcao_4, opcao_5, tipo, gabarito, dica, ano,
                        dificuldade, imagem
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    materia,
                    assunto,
                    sub_assunto,
                    banca,
                    orgao,
                    cargo,
                    nivel,
                    pergunta,
                    opcao_1,
                    opcao_2,
                    opcao_3,
                    opcao_4,
                    opcao_5,
                    tipo,
                    gabarito,
                    dica,
                    ano,
                    dificuldade,
                    imagem  # NOVO CAMPO
                ))
                
                inseridas += 1
                
                if inseridas % 20 == 0:
                    print(f"📝 {inseridas} questões processadas...")
                
            except Exception as e:
                print(f"❌ Erro na questão {i+1}: {str(e)[:100]}...")
                import traceback
                traceback.print_exc()
                erros += 1
                continue
        
        conn.commit()
        conn.close()
        
        print("="*60)
        print("📊 RESUMO DA IMPORTAÇÃO:")
        print(f"✅ Questões inseridas: {inseridas}")
        print(f"⚠️  Questões duplicadas (ignoradas): {duplicadas}")
        print(f"❌ Questões com erro: {erros}")
        print(f"📄 Total processado: {len(dados)}")
        print("="*60)
        
        return jsonify({
            'success': True,
            'inseridas': inseridas,
            'duplicadas': duplicadas,
            'erros': erros,
            'total_processado': len(dados),
            'mensagem': f'Importação concluída: {inseridas} novas questões adicionadas'
        })
        
    except Exception as e:
        print(f"❌ ERRO CRÍTICO em importar-excel: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@laranja_bp.route('/api/upload-imagem', methods=['POST'])
def api_upload_imagem():
    """Upload de imagem para uma pasta específica"""
    try:
        print("📤 API upload-imagem chamada")
        
        if 'imagem' not in request.files:
            return jsonify({'success': False, 'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['imagem']
        pasta_destino = request.form.get('pasta', '')
        
        print(f"📁 Arquivo: {file.filename}")
        print(f"📁 Pasta destino: {pasta_destino}")
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Nome de arquivo vazio'}), 400
        
        # Validar tipo de arquivo
        if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.svg')):
            return jsonify({'success': False, 'error': 'Tipo de arquivo não suportado'}), 400
        
        # Usar o nome original do arquivo (sem UUID)
        nome_original = file.filename
        
        # Construir caminho de destino
        if pasta_destino and pasta_destino.strip():
            pasta_completa = os.path.join(LARANJA_IMG_DIR, pasta_destino)
            os.makedirs(pasta_completa, exist_ok=True)
            filepath = os.path.join(pasta_completa, nome_original)
            caminho_relativo = f"{pasta_destino}/{nome_original}"
        else:
            # Pasta raiz
            os.makedirs(LARANJA_IMG_DIR, exist_ok=True)
            filepath = os.path.join(LARANJA_IMG_DIR, nome_original)
            caminho_relativo = nome_original
        
        # Verificar se o arquivo já existe
        if os.path.exists(filepath):
            print(f"⚠️ Arquivo já existe: {filepath}")
            return jsonify({
                'success': True,
                'caminho': caminho_relativo,
                'nome': nome_original,
                'mensagem': 'Arquivo já existe'
            })
        
        # Salvar arquivo
        file.save(filepath)
        print(f"✅ Arquivo salvo em: {filepath}")
        print(f"✅ Caminho relativo: {caminho_relativo}")
        
        return jsonify({
            'success': True,
            'caminho': caminho_relativo,
            'nome': nome_original
        })
        
    except Exception as e:
        print(f"❌ Erro no upload: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@laranja_bp.route('/api/diagnostico')
def api_diagnostico():
    try:
        conn = get_db()
        c = conn.cursor()
        
        c.execute('SELECT COUNT(*) FROM questoes')
        total_questoes = c.fetchone()[0]
        
        c.execute("PRAGMA table_info(questoes)")
        colunas = c.fetchall()
        
        c.execute('SELECT materia, assunto, COUNT(*) FROM questoes GROUP BY materia, assunto LIMIT 10')
        exemplos = c.fetchall()
        
        # Contar por tipo
        c.execute('SELECT tipo, COUNT(*) FROM questoes GROUP BY tipo')
        tipos = c.fetchall()
        
        # Contar questões com imagem
        c.execute('SELECT COUNT(*) FROM questoes WHERE imagem IS NOT NULL AND imagem != ""')
        total_com_imagem = c.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'status': 'ok',
            'total_questoes': total_questoes,
            'colunas': [{'name': col[1], 'type': col[2]} for col in colunas],
            'exemplos': [{'materia': e[0], 'assunto': e[1], 'quantidade': e[2]} for e in exemplos],
            'tipos': [{'tipo': t[0], 'quantidade': t[1]} for t in tipos],
            'total_com_imagem': total_com_imagem,
            'db_path': DB_PATH,
            'img_dir': LARANJA_IMG_DIR,
            'db_exists': os.path.exists(DB_PATH),
            'img_dir_exists': os.path.exists(LARANJA_IMG_DIR)
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        })

@laranja_bp.route('/static/<path:filename>')
def serve_laranja_static(filename):
    static_dir = LARANJA_STATIC_DIR
    if os.path.exists(static_dir):
        return send_from_directory(static_dir, filename)
    return "Arquivo estático não encontrado", 404

def init_laranja():
    print("\n" + "="*60)
    print("🍊 INICIALIZANDO SISTEMA LARANJA")
    print("="*60)
    
    try:
        import pandas
        print(f"✅ pandas {pandas.__version__} instalado")
    except ImportError:
        print("❌ pandas NÃO instalado")
        print("   Execute: pip install pandas")
    
    try:
        import openpyxl
        print(f"✅ openpyxl {openpyxl.__version__} instalado")
    except ImportError:
        print("❌ openpyxl NÃO instalado")
        print("   Execute: pip install openpyxl")
    
    # Verificar pasta de imagens
    if os.path.exists(LARANJA_IMG_DIR):
        print(f"📸 Pasta de imagens: {LARANJA_IMG_DIR} (ok)")
        imagens = os.listdir(LARANJA_IMG_DIR)
        print(f"   {len(imagens)} arquivos encontrados")
    else:
        print(f"📸 Pasta de imagens: {LARANJA_IMG_DIR} (criando...)")
        os.makedirs(LARANJA_IMG_DIR, exist_ok=True)
    
    if os.path.exists(DB_PATH):
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM questoes')
        total = c.fetchone()[0]
        
        # Contar por tipo
        c.execute('SELECT tipo, COUNT(*) FROM questoes GROUP BY tipo')
        tipos = c.fetchall()
        
        # Contar questões com imagem
        c.execute('SELECT COUNT(*) FROM questoes WHERE imagem IS NOT NULL AND imagem != ""')
        total_com_imagem = c.fetchone()[0]
        
        conn.close()
        
        print(f"📊 Banco de dados: {DB_PATH}")
        print(f"📊 Total de questões: {total}")
        for tipo, qtde in tipos:
            print(f"   - {tipo}: {qtde}")
        print(f"📸 Questões com imagem: {total_com_imagem}")
    else:
        print(f"📊 Banco de dados: {DB_PATH} (não existe ainda)")
    
    print(f"✅ Sistema Laranja inicializado!")
    print(f"🔗 Acesse: http://localhost:5000/laranja/")
    print("="*60)

init_laranja()