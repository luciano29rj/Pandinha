// ============================================
// CÓDIGO SIMPLIFICADO - PASSO A PASSO
// ============================================

// Variáveis globais
let usuarioAtual = null;
let materiasAssuntos = {};

// ============================================
// FUNÇÕES PARA O COMBOBOX COM AUTOCOMPLETE
// ============================================

let todosUsuariosLista = []; // Array com todos os usuários

// Função para inicializar o combobox
function inicializarCombobox() {
    const input = document.getElementById('usuarioSearch');
    const lista = document.getElementById('sugestoesLista');
    const toggleBtn = document.getElementById('toggleLista');
    
    if (!input || !lista) return;
    
    // 1. Quando digitar no input
    input.addEventListener('input', function() {
        const termo = this.value.toLowerCase().trim();
        
        if (termo.length === 0) {
            esconderLista();
            return;
        }
        
        // Filtrar usuários
        const filtrados = todosUsuariosLista.filter(usuario => {
            return usuario.nome.toLowerCase().includes(termo) || 
                   usuario.email.toLowerCase().includes(termo);
        });
        
        mostrarSugestoes(filtrados);
    });
    
    // 2. Quando clicar no botão da seta
    if (toggleBtn) {
        toggleBtn.addEventListener('click', function() {
            if (lista.classList.contains('hidden')) {
                mostrarSugestoes(todosUsuariosLista);
            } else {
                esconderLista();
            }
        });
    }
    
    // 3. Quando clicar fora, esconder lista
    document.addEventListener('click', function(event) {
        const comboboxContainer = document.getElementById('comboboxContainer');
        if (!comboboxContainer.contains(event.target)) {
            esconderLista();
        }
    });
    
    // 4. Teclas especiais
    input.addEventListener('keydown', function(event) {
        const itensVisiveis = lista.querySelectorAll('.sugestao-item:not(.hidden)');
        
        if (event.key === 'ArrowDown') {
            event.preventDefault();
            if (itensVisiveis.length > 0) {
                itensVisiveis[0].focus();
            }
        } else if (event.key === 'Escape') {
            esconderLista();
        }
    });
}

// Mostrar sugestões na lista
function mostrarSugestoes(usuarios) {
    const lista = document.getElementById('sugestoesLista');
    if (!lista) return;
    
    // Limpar lista
    lista.innerHTML = '';
    
    if (usuarios.length === 0) {
        lista.innerHTML = `
            <div class="p-3 text-gray-500 text-center">
                <i class="fas fa-user-times mr-2"></i>Nenhum usuário encontrado
            </div>
        `;
    } else {
        // Adicionar cada usuário
        usuarios.forEach(usuario => {
            const item = document.createElement('div');
            item.className = 'sugestao-item p-3 hover:bg-blue-50 cursor-pointer border-b border-gray-100 last:border-b-0 flex items-center gap-3';
            item.tabIndex = 0;
            
            item.innerHTML = `
                <div class="text-xl">${usuario.avatar || '👤'}</div>
                <div class="flex-1">
                    <div class="font-medium">${usuario.nome}</div>
                    <div class="text-xs text-gray-500">${usuario.email}</div>
                </div>
                <div class="text-xs px-2 py-1 rounded ${usuario.ativo ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}">
                    ${usuario.ativo ? 'Ativo' : 'Inativo'}
                </div>
            `;
            
            // Quando clicar no item
            item.addEventListener('click', function() {
                selecionarUsuarioCombobox(usuario);
            });
            
            // Navegação com teclado
            item.addEventListener('keydown', function(event) {
                if (event.key === 'Enter') {
                    selecionarUsuarioCombobox(usuario);
                } else if (event.key === 'ArrowDown') {
                    event.preventDefault();
                    const next = this.nextElementSibling;
                    if (next && next.classList.contains('sugestao-item')) {
                        next.focus();
                    }
                } else if (event.key === 'ArrowUp') {
                    event.preventDefault();
                    const prev = this.previousElementSibling;
                    if (prev && prev.classList.contains('sugestao-item')) {
                        prev.focus();
                    }
                }
            });
            
            lista.appendChild(item);
        });
    }
    
    // Mostrar lista
    lista.classList.remove('hidden');
    
    // Posicionar lista abaixo do input
    const input = document.getElementById('usuarioSearch');
    const inputRect = input.getBoundingClientRect();
    lista.style.width = inputRect.width + 'px';
    lista.style.top = (inputRect.height + 4) + 'px';
    lista.style.left = '0px';
}

// Esconder lista de sugestões
function esconderLista() {
    const lista = document.getElementById('sugestoesLista');
    if (lista) {
        lista.classList.add('hidden');
    }
}

// Selecionar usuário do combobox
function selecionarUsuarioCombobox(usuario) {
    const input = document.getElementById('usuarioSearch');
    const hiddenInput = document.getElementById('usuarioIdSelecionado');
    
    if (input) {
        input.value = usuario.nome + ' (' + usuario.email + ')';
    }
    
    if (hiddenInput) {
        hiddenInput.value = usuario.id;
    }
    
    // Esconder lista
    esconderLista();
    
    // Selecionar o usuário (usando a função existente)
    selecionarUsuario(usuario);
}

// Atualizar a função carregarUsuarios() para armazenar na lista global
async function carregarUsuarios() {
    try {
        const response = await fetch('/api/admin/usuarios');
        const usuarios = await response.json();
        
        // Armazenar na lista global para o combobox
        todosUsuariosLista = usuarios;
        
        // Inicializar combobox
        inicializarCombobox();
        
        // Atualizar contador
        const ativos = usuarios.filter(u => u.ativo).length;
        document.getElementById('contadorUsuarios').textContent = ativos + '/' + usuarios.length;
        
    } catch (error) {
        console.error('Erro usuários:', error);
        throw error;
    }
}

// REMOVA ou COMENTE a função antiga de selecionar usuário se existir
// e mantenha apenas esta versão simplificada:
function selecionarUsuario(usuario) {
    usuarioAtual = usuario;
    
    // Mostrar informações
    document.getElementById('usuarioNome').textContent = usuario.nome;
    document.getElementById('usuarioAvatar').textContent = usuario.avatar || '👤';
    document.getElementById('usuarioEmail').textContent = usuario.email;
    
    const statusEl = document.getElementById('usuarioStatus');
    statusEl.textContent = usuario.ativo ? 'Ativo' : 'Inativo';
    statusEl.className = usuario.ativo 
        ? 'text-xs px-2 py-1 rounded-full bg-green-100 text-green-700 inline-block'
        : 'text-xs px-2 py-1 rounded-full bg-red-100 text-red-700 inline-block';
    
    // Mostrar seção do usuário
    document.getElementById('usuarioInfo').classList.remove('hidden');
    document.getElementById('instrucoes').classList.add('hidden');
    
    // Carregar bloqueios
    carregarBloqueiosUsuario(usuario.id);
}

// Quando a página carrega
document.addEventListener('DOMContentLoaded', function() {
    console.log('Página ADMAT carregada');
    
    // Configurar ano atual
    document.getElementById('anoAtual').textContent = new Date().getFullYear();
    
    // Carregar tudo
    iniciarPagina();
});

// Função principal de inicialização
async function iniciarPagina() {
    try {
        // 1. Carregar usuários
        await carregarUsuarios();
        
        // 2. Carregar matérias
        await carregarMaterias();
        
        // 3. Esconder loading
        document.getElementById('loading').classList.add('hidden');
        
    } catch (error) {
        console.error('Erro:', error);
        mostrarErro('Erro ao carregar dados');
    }
}

// FUNÇÃO 1: Carregar usuários
async function carregarUsuarios() {
    try {
        const response = await fetch('/api/admin/usuarios');
        const usuarios = await response.json();
        
        const select = document.getElementById('usuarioSelect');
        select.innerHTML = '<option value="">Escolha um usuário...</option>';
        
        usuarios.forEach(usuario => {
            const option = document.createElement('option');
            option.value = usuario.id;
            option.textContent = usuario.nome + ' (' + usuario.email + ')';
            select.appendChild(option);
        });
        
        // Quando selecionar usuário
        select.addEventListener('change', function() {
            const usuarioId = this.value;
            if (usuarioId) {
                const usuario = usuarios.find(u => u.id == usuarioId);
                selecionarUsuario(usuario);
            } else {
                esconderUsuario();
            }
        });
        
        // Atualizar contador
        const ativos = usuarios.filter(u => u.ativo).length;
        document.getElementById('contadorUsuarios').textContent = ativos + '/' + usuarios.length;
        
    } catch (error) {
        console.error('Erro usuários:', error);
        throw error;
    }
}

// FUNÇÃO 2: Carregar matérias
async function carregarMaterias() {
    try {
        // Tentar carregar da nova rota
        const response = await fetch('/api/admin/materias-assuntos');
        materiasAssuntos = await response.json();
        
        // Se não funcionar, carregar do jeito antigo
        if (Object.keys(materiasAssuntos).length === 0) {
            await carregarMateriasAntigo();
        }
        
    } catch (error) {
        console.error('Erro matérias:', error);
        // Usar fallback
        await carregarMateriasFallback();
    }
}

// Fallback para matérias
async function carregarMateriasFallback() {
    try {
        const response = await fetch('/api/materias');
        const materias = await response.json();
        
        materiasAssuntos = {};
        
        for (const materia of materias) {
            const res = await fetch('/api/assuntos?materia=' + encodeURIComponent(materia));
            const assuntos = await res.json();
            
            // Converter para array de strings
            if (assuntos.length > 0 && typeof assuntos[0] === 'object') {
                materiasAssuntos[materia] = assuntos.map(a => a.nome);
            } else {
                materiasAssuntos[materia] = assuntos;
            }
        }
        
    } catch (error) {
        console.error('Erro fallback:', error);
        materiasAssuntos = {
            "Português": ["Gramática", "Interpretação", "Ortografia"],
            "Matemática": ["Operações", "Frações", "Geometria"],
            "História": ["Idade Média", "Brasil Colonial", "Revoluções"]
        };
    }
}

// Carregar matérias do jeito antigo
async function carregarMateriasAntigo() {
    try {
        // Buscar do banco de questões
        const response = await fetch('/api/materias');
        const materias = await response.json();
        
        materiasAssuntos = {};
        
        for (const materia of materias) {
            const res = await fetch(`/api/assuntos?materia=${encodeURIComponent(materia)}`);
            const assuntos = await res.json();
            
            materiasAssuntos[materia] = assuntos.map(a => {
                if (typeof a === 'object') return a.nome;
                return a;
            }).filter(a => a && a.trim() !== '');
        }
        
    } catch (error) {
        console.error('Erro método antigo:', error);
        throw error;
    }
}

// Quando seleciona um usuário
function selecionarUsuario(usuario) {
    usuarioAtual = usuario;
    
    // Mostrar informações
    document.getElementById('usuarioNome').textContent = usuario.nome;
    document.getElementById('usuarioAvatar').textContent = usuario.avatar || '👤';
    document.getElementById('usuarioEmail').textContent = usuario.email;
    
    const statusEl = document.getElementById('usuarioStatus');
    statusEl.textContent = usuario.ativo ? 'Ativo' : 'Inativo';
    statusEl.className = usuario.ativo 
        ? 'text-xs px-2 py-1 rounded-full bg-green-100 text-green-700 inline-block'
        : 'text-xs px-2 py-1 rounded-full bg-red-100 text-red-700 inline-block';
    
    // Mostrar seção do usuário
    document.getElementById('usuarioInfo').classList.remove('hidden');
    document.getElementById('instrucoes').classList.add('hidden');
    
    // Carregar bloqueios
    carregarBloqueiosUsuario(usuario.id);
}

// Esconder usuário
function esconderUsuario() {
    usuarioAtual = null;
    document.getElementById('usuarioInfo').classList.add('hidden');
    document.getElementById('instrucoes').classList.remove('hidden');
    document.getElementById('materiasContainer').innerHTML = '';
}

// Carregar bloqueios do usuário
async function carregarBloqueiosUsuario(usuarioId) {
    try {
        const response = await fetch('/api/admin/bloqueios/' + usuarioId);
        const bloqueios = await response.json();
        
        mostrarMateriasComBloqueios(bloqueios);
        
    } catch (error) {
        console.error('Erro bloqueios:', error);
        mostrarMateriasComBloqueios([]);
    }
}

// Mostrar matérias com bloqueios
function mostrarMateriasComBloqueios(bloqueios) {
    const container = document.getElementById('materiasContainer');
    container.innerHTML = '';
    container.classList.remove('hidden');
    
    // Converter bloqueios para objeto fácil
    const bloqueiosMap = {};
    bloqueios.forEach(b => {
        const chave = b.materia + '|' + b.assunto;
        bloqueiosMap[chave] = b.bloqueado;
    });
    
    // Para cada matéria
    Object.keys(materiasAssuntos).forEach(materia => {
        const card = criarCardMateria(materia, bloqueiosMap);
        container.appendChild(card);
    });
}

// Criar card de matéria
function criarCardMateria(materia, bloqueiosMap) {
    const assuntos = materiasAssuntos[materia] || [];
    
    const div = document.createElement('div');
    div.className = 'materia-card bg-white rounded-xl shadow-lg mb-6 overflow-hidden border-l-4 border-blue-500';
    
    // Contar bloqueados
    let bloqueados = 0;
    assuntos.forEach(assunto => {
        const chave = materia + '|' + assunto;
        if (bloqueiosMap[chave] === true) bloqueados++;
    });
    
    div.innerHTML = `
        <div class="bg-gradient-to-r from-blue-50 to-blue-100 p-4">
            <div class="flex justify-between items-center">
                <div class="flex items-center gap-3">
                    <div class="text-2xl bg-blue-100 p-2 rounded-lg">
                        ${obterIconeMateria(materia)}
                    </div>
                    <div>
                        <h3 class="font-bold text-lg">${materia}</h3>
                        <p class="text-sm text-gray-600">${bloqueados}/${assuntos.length} bloqueado(s)</p>
                    </div>
                </div>
                <div class="flex gap-2">
                    <button onclick="liberarTodos('${materia}')" 
                            class="bg-green-500 hover:bg-green-600 text-white px-3 py-1 rounded-lg text-sm">
                        ✅ Liberar Todos
                    </button>
                    <button onclick="bloquearTodos('${materia}')" 
                            class="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded-lg text-sm">
                        🔒 Bloquear Todos
                    </button>
                </div>
            </div>
        </div>
        <div class="p-4">
            <div class="space-y-2" id="assuntos-${materia.replace(/\s+/g, '-')}">
                <!-- Assuntos vão aqui -->
            </div>
        </div>
    `;
    
    // Adicionar assuntos
    const container = div.querySelector('#assuntos-' + materia.replace(/\s+/g, '-'));
    
    assuntos.forEach(assunto => {
        const chave = materia + '|' + assunto;
        const bloqueado = bloqueiosMap[chave] === true;
        
        const assuntoDiv = document.createElement('div');
        assuntoDiv.className = 'assunto-item p-3 rounded-lg flex justify-between items-center ' + 
                              (bloqueado ? 'bg-red-50 border-l-4 border-red-500' : 'bg-green-50 border-l-4 border-green-500');
        
        assuntoDiv.innerHTML = `
            <div class="flex items-center gap-3">
                <div class="${bloqueado ? 'text-red-600' : 'text-green-600'}">
                    ${bloqueado ? '🔒' : '🔓'}
                </div>
                <span class="font-medium">${assunto}</span>
            </div>
            <div class="flex items-center gap-3">
                <span class="text-sm ${bloqueado ? 'text-red-600' : 'text-green-600'}">
                    ${bloqueado ? 'Bloqueado' : 'Liberado'}
                </span>
                <label class="switch">
                    <input type="checkbox" ${bloqueado ? '' : 'checked'} 
                           onchange="alternarBloqueio('${materia}', '${assunto.replace(/'/g, "\\'")}', this.checked)">
                    <span class="slider round"></span>
                </label>
            </div>
        `;
        
        container.appendChild(assuntoDiv);
    });
    
    return div;
}

// Obter ícone da matéria
function obterIconeMateria(materia) {
    const icones = {
        "Português": "📖",
        "Matemática": "🔢", 
        "História": "🏛️",
        "Ciências": "🔬",
        "Geografia": "🌍",
        "Inglês": "🇬🇧"
    };
    return icones[materia] || "📄";
}

// Alternar bloqueio
async function alternarBloqueio(materia, assunto, liberar) {
    if (!usuarioAtual) {
        alert('Selecione um usuário primeiro!');
        return;
    }
    
    // Se liberar = true (checkbox marcado), então bloquear = false
    const bloquear = !liberar;
    
    try {
        const response = await fetch('/api/admin/bloquear', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                usuario_id: usuarioAtual.id,
                materia: materia,
                assunto: assunto,
                bloquear: bloquear
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            mostrarMensagem(data.message, 'success');
            // Recarregar
            await carregarBloqueiosUsuario(usuarioAtual.id);
        } else {
            mostrarMensagem(data.message, 'error');
        }
        
    } catch (error) {
        console.error('Erro:', error);
        mostrarMensagem('Erro de conexão', 'error');
    }
}

// Bloquear todos os assuntos de uma matéria
async function bloquearTodos(materia) {
    if (!usuarioAtual) {
        alert('Selecione um usuário primeiro!');
        return;
    }
    
    if (!confirm('Bloquear TODOS os assuntos de ' + materia + '?')) {
        return;
    }
    
    const assuntos = materiasAssuntos[materia] || [];
    
    for (const assunto of assuntos) {
        await alternarBloqueio(materia, assunto, false); // false = bloquear
    }
}

// Liberar todos os assuntos de uma matéria
async function liberarTodos(materia) {
    if (!usuarioAtual) {
        alert('Selecione um usuário primeiro!');
        return;
    }
    
    if (!confirm('Liberar TODOS os assuntos de ' + materia + '?')) {
        return;
    }
    
    const assuntos = materiasAssuntos[materia] || [];
    
    for (const assunto of assuntos) {
        await alternarBloqueio(materia, assunto, true); // true = liberar
    }
}

// Liberar TUDO para o usuário
async function liberarTudoUsuario() {
    if (!usuarioAtual) {
        alert('Selecione um usuário primeiro!');
        return;
    }
    
    if (!confirm('Liberar TODOS os assuntos para ' + usuarioAtual.nome + '?')) {
        return;
    }
    
    try {
        const response = await fetch('/api/admin/liberar-tudo/' + usuarioAtual.id, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            mostrarMensagem(data.message, 'success');
            await carregarBloqueiosUsuario(usuarioAtual.id);
        } else {
            mostrarMensagem(data.message, 'error');
        }
        
    } catch (error) {
        console.error('Erro:', error);
        mostrarMensagem('Erro de conexão', 'error');
    }
}

// Mostrar mensagem
function mostrarMensagem(texto, tipo) {
    // Remover anterior
    const anterior = document.getElementById('mensagem-flutuante');
    if (anterior) anterior.remove();
    
    // Criar nova
    const mensagem = document.createElement('div');
    mensagem.id = 'mensagem-flutuante';
    mensagem.className = 'fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 text-white ' + 
                        (tipo === 'success' ? 'bg-green-500' : 'bg-red-500');
    mensagem.textContent = texto;
    
    document.body.appendChild(mensagem);
    
    // Remover após 3 segundos
    setTimeout(() => {
        if (mensagem.parentNode) {
            mensagem.remove();
        }
    }, 3000);
}

// Mostrar erro
function mostrarErro(mensagem) {
    document.getElementById('loading').innerHTML = `
        <div class="text-red-500 p-8 text-center">
            <div class="text-4xl mb-4">⚠️</div>
            <p>${mensagem}</p>
            <button onclick="location.reload()" class="mt-4 bg-blue-500 text-white px-4 py-2 rounded">
                Recarregar
            </button>
        </div>
    `;
}

// Adicionar estilos CSS para os switches
function adicionarEstilosSwitch() {
    const style = document.createElement('style');
    style.textContent = `
        .switch {
            position: relative;
            display: inline-block;
            width: 50px;
            height: 26px;
        }
        .switch input {
            opacity: 0;
            width: 0;
            height: 0;
        }
        .slider {
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: #ef4444;
            transition: .4s;
            border-radius: 34px;
        }
        .slider:before {
            position: absolute;
            content: "";
            height: 18px;
            width: 18px;
            left: 4px;
            bottom: 4px;
            background-color: white;
            transition: .4s;
            border-radius: 50%;
        }
        input:checked + .slider {
            background-color: #10b981;
        }
        input:checked + .slider:before {
            transform: translateX(24px);
        }
    `;
    document.head.appendChild(style);
}

// Chamar para adicionar estilos
adicionarEstilosSwitch();

// Funções públicas (chamadas pelo HTML)
window.mostrarTodosUsuarios = mostrarTodosUsuarios;
window.recarregarTudo = function() {
    location.reload();
};
window.liberarTudoUsuario = liberarTudoUsuario;

// Função para mostrar todos os usuários
async function mostrarTodosUsuarios() {
    try {
        const response = await fetch('/api/admin/usuarios');
        const usuarios = await response.json();
        
        let mensagem = '📋 USUÁRIOS:\n\n';
        usuarios.forEach(u => {
            mensagem += u.avatar + ' ' + u.nome + ' - ' + (u.ativo ? '✅ Ativo' : '❌ Inativo') + '\n';
        });
        
        alert(mensagem);
        
    } catch (error) {
        alert('Erro ao carregar usuários');
    }
}

// ============================================
// FUNÇÕES PARA O CONTROLE GERAL
// ============================================

// Configurar os selects do controle geral
function configurarControleGeral() {
    console.log('Configurando controle geral...');
    
    // 1. Preencher selects de matérias
    const materiasSelects = [
        'materiaTodos',
        'materiaTodosLiberar'
    ];
    
    materiasSelects.forEach(selectId => {
        const select = document.getElementById(selectId);
        if (select) {
            select.innerHTML = '<option value="">Selecione matéria...</option>';
            
            // Adicionar matérias
            Object.keys(materiasAssuntos).forEach(materia => {
                const option = document.createElement('option');
                option.value = materia;
                option.textContent = materia;
                select.appendChild(option);
            });
            
            // Quando mudar a matéria, carregar assuntos
            select.addEventListener('change', function() {
                const targetId = selectId.includes('Liberar') ? 'assuntoTodosLiberar' : 'assuntoTodos';
                preencherAssuntosSelect(targetId, this.value);
            });
        }
    });
}

// Preencher select de assuntos
function preencherAssuntosSelect(selectId, materia) {
    const select = document.getElementById(selectId);
    if (!select) return;
    
    select.innerHTML = '<option value="">Selecione assunto...</option>';
    
    if (materia && materiasAssuntos[materia]) {
        materiasAssuntos[materia].forEach(assunto => {
            const option = document.createElement('option');
            option.value = assunto;
            option.textContent = assunto;
            select.appendChild(option);
        });
    }
}

// BLOQUEAR assunto para TODOS os usuários
async function bloquearParaTodos() {
    const materia = document.getElementById('materiaTodos').value;
    const assunto = document.getElementById('assuntoTodos').value;
    
    if (!materia || !assunto) {
        mostrarMensagem('Selecione uma matéria e um assunto!', 'error');
        return;
    }
    
    if (!confirm(`Deseja BLOQUEAR o assunto "${assunto}" da matéria "${materia}" para TODOS os usuários?`)) {
        return;
    }
    
    try {
        mostrarMensagem('Bloqueando para todos os usuários...', 'info');
        
        const response = await fetch('/api/admin/bloquear-todos-assuntos', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                materia: materia,
                assunto: assunto
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            mostrarMensagem(data.message, 'success');
            
            // Se tem um usuário selecionado, recarregar seus bloqueios
            if (usuarioAtual) {
                await carregarBloqueiosUsuario(usuarioAtual.id);
            }
        } else {
            mostrarMensagem(data.message || 'Erro ao bloquear para todos', 'error');
        }
        
    } catch (error) {
        console.error('Erro ao bloquear para todos:', error);
        mostrarMensagem('Erro de conexão com o servidor', 'error');
    }
}

// LIBERAR assunto para TODOS os usuários
async function liberarParaTodos() {
    const materia = document.getElementById('materiaTodosLiberar').value;
    const assunto = document.getElementById('assuntoTodosLiberar').value;
    
    if (!materia || !assunto) {
        mostrarMensagem('Selecione uma matéria e um assunto!', 'error');
        return;
    }
    
    if (!confirm(`Deseja LIBERAR o assunto "${assunto}" da matéria "${materia}" para TODOS os usuários?`)) {
        return;
    }
    
    try {
        mostrarMensagem('Liberando para todos os usuários...', 'info');
        
        const response = await fetch('/api/admin/liberar-todos-assuntos', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                materia: materia,
                assunto: assunto
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            mostrarMensagem(data.message, 'success');
            
            // Se tem um usuário selecionado, recarregar seus bloqueios
            if (usuarioAtual) {
                await carregarBloqueiosUsuario(usuarioAtual.id);
            }
        } else {
            mostrarMensagem(data.message || 'Erro ao liberar para todos', 'error');
        }
        
    } catch (error) {
        console.error('Erro ao liberar para todos:', error);
        mostrarMensagem('Erro de conexão com o servidor', 'error');
    }
}

// ============================================
// ATUALIZE A FUNÇÃO iniciarPagina() - Adicione esta linha:
// ============================================

// Na função iniciarPagina(), adicione depois de carregarMaterias():
async function iniciarPagina() {
    try {
        // 1. Carregar usuários
        await carregarUsuarios();
        
        // 2. Carregar matérias
        await carregarMaterias();
        
        // 3. Configurar controle geral ← ADICIONE ESTA LINHA
        configurarControleGeral();
        
        // 4. Esconder loading
        document.getElementById('loading').classList.add('hidden');
        
    } catch (error) {
        console.error('Erro:', error);
        mostrarErro('Erro ao carregar dados');
    }
}

// ============================================
// ATUALIZE A FUNÇÃO mostrarMensagem() - Corrija para:
// ============================================

function mostrarMensagem(texto, tipo) {
    // Remover anterior
    const anterior = document.getElementById('mensagem-flutuante');
    if (anterior) anterior.remove();
    
    // Definir cores
    let corFundo = 'bg-blue-500';
    if (tipo === 'success') corFundo = 'bg-green-500';
    if (tipo === 'error') corFundo = 'bg-red-500';
    if (tipo === 'info') corFundo = 'bg-blue-500';
    
    // Criar nova mensagem
    const mensagem = document.createElement('div');
    mensagem.id = 'mensagem-flutuante';
    mensagem.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 text-white ${corFundo}`;
    mensagem.innerHTML = `
        <div class="flex items-center gap-2">
            <span class="text-xl">${tipo === 'success' ? '✅' : tipo === 'error' ? '❌' : '⏳'}</span>
            <span>${texto}</span>
        </div>
    `;
    
    document.body.appendChild(mensagem);
    
    // Remover após 4 segundos
    setTimeout(() => {
        if (mensagem.parentNode) {
            mensagem.remove();
        }
    }, 4000);
}

// ============================================
// ADICIONE estas funções ao objeto window (para serem chamadas pelo HTML):
// ============================================

window.bloquearParaTodos = bloquearParaTodos;
window.liberarParaTodos = liberarParaTodos;
window.mostrarTodosUsuarios = mostrarTodosUsuarios;
window.recarregarTudo = function() { location.reload(); };
window.liberarTudoUsuario = liberarTudoUsuario;