# MAPRE IDS — v0.2.0

MAPRE é um protótipo acadêmico de IDS/monitoramento local com interface PySide6, identidade visual escura e detalhes verde-turquesa, inspirado no macaco-prego brasileiro.

## Funcionalidades
- Painel de monitoramento, ameaças, eventos, conexões e configurações.
- Monitoramento de metadados de conexões com `psutil` durante uma sessão ativa.
- Gatilho configurável por nome/caminho de processo; o processo é observado enquanto o aplicativo está aberto.
- Regras heurísticas para volume elevado de conexões e eventos em sequência.
- SQLite para eventos, logs rotativos e exportação CSV.
- Captura de tela opcional, desabilitada por padrão, configurável na interface e ativa apenas durante sessão de monitoramento. A tela exibe o estado do recurso.
- Testes automatizados básicos.

## Requisitos
Python 3.10+ (recomendado Python 3.12), Windows 10/11 para o cenário-alvo. Algumas conexões podem exigir execução elevada para serem enumeradas. Execute apenas em máquinas e sessões autorizadas.

## Instalação no Windows / VS Code
Abra PowerShell na pasta `MAPRE_IDS`:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

Se o PowerShell bloquear a ativação do ambiente, use `Set-ExecutionPolicy -Scope Process Bypass` apenas na janela atual e tente novamente, ou execute `.venv\Scripts\python.exe main.py` sem ativar o ambiente.

## Testes
```powershell
pytest -q
```

## Capturas de tela opcionais
A captura é desligada por padrão. Para habilitá-la, abra Configurações, marque a opção, salve e inicie uma sessão. Para ativar esse recurso, instale as dependências opcionais:

```powershell
pip install pyautogui Pillow
```

As capturas são gravadas em `evidence/screenshots` (relativo à pasta do projeto), com retenção configurada na interface. Use apenas em ambiente de teste ou com autorização e aviso aos usuários. Não habilite a opção em estações compartilhadas sem uma política aprovada.

## Empacotamento Windows
```powershell
pip install pyinstaller
pyinstaller --noconfirm --windowed --name MAPRE-IDS main.py
```
O executável ficará em `dist\MAPRE-IDS`. Teste em uma máquina limpa antes de distribuir. O banco/logs são criados em `logs` ao lado dos arquivos do projeto; para distribuição corporativa, configure um diretório de dados gravável e proteja o acesso.

## Arquitetura
- `main.py`: entrada do aplicativo.
- `gui/main_window.py`: interface e controles.
- `core/`: sessão, gatilho e logging.
- `modules/`: conexões, regras de detecção e captura opcional.
- `storage/event_store.py`: banco SQLite.
- `config/settings.json`: configurações locais.
- `tests/`: testes automatizados.

## Limitações importantes
- `psutil.net_connections()` mostra metadados disponíveis ao sistema; pode não listar todas as conexões sem privilégios adequados.
- Conexões IP não revelam necessariamente URLs ou páginas visitadas, sobretudo com HTTPS, VPN ou DNS criptografado. Este protótipo não intercepta conteúdo criptografado nem captura payloads de pacotes.
- As regras são heurísticas didáticas e podem produzir falsos positivos; não constituem confirmação de intrusão.
- O gatilho depende de o MAPRE estar aberto. A inicialização automática como serviço ou persistência não está implementada.
- A captura de tela é sensível: mantenha-a desativada por padrão e use consentimento, controle de acesso e retenção compatíveis com as políticas da organização.


### Captura opcional pela webcam

Na página **Configurações**, marque “Autorizar captura pela webcam durante sessão ativa” e salve. Com a opção explicitamente habilitada, o MAPRE abre a webcam durante uma sessão ativa (manual ou disparada pelo processo configurado) e salva uma imagem a cada 10 segundos em `evidence/webcam/`. O estado da webcam é exibido na interface. Encerrar a sessão ou fechar o aplicativo libera a câmera. A opção vem desativada por padrão.

A captura requer OpenCV (`pip install opencv-python`) e permissão de câmera no Windows. Use somente em dispositivos e cenários autorizados, informando os usuários aplicáveis. As imagens seguem a retenção configurada.

## Execução em segundo plano (área de notificação)

- O botão de fechar a janela minimiza o MAPRE para a área de notificação do Windows; o ícone permanece visível e mostra o estado do monitoramento.
- Clique duas vezes no ícone para reabrir a janela. Clique com o botão direito para abrir o menu, ver o status ou escolher **Encerrar MAPRE IDS**.
- Quando o processo configurado em **Configurações** é detectado, o MAPRE exibe uma notificação e inicia uma sessão. Quando esse processo fecha, uma sessão iniciada pelo gatilho é encerrada.
- As capturas de tela e webcam continuam opcionais e precisam estar explicitamente habilitadas na interface. Use apenas em computadores e sessões autorizados.

Para dependências de captura de tela, instale com `python -m pip install pyautogui Pillow` no mesmo ambiente virtual do projeto.
