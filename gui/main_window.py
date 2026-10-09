import csv
from datetime import datetime
from pathlib import Path
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QIcon
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QStackedWidget, QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QSpinBox, QCheckBox, QFileDialog,
    QMessageBox, QGridLayout, QAbstractItemView, QSystemTrayIcon, QMenu, QStyle, QApplication)
from config_loader import load_config, save_config
from core.session_manager import SessionManager
from core.trigger_monitor import TriggerMonitor
from core.event_logger import log
from modules.network_monitor import NetworkMonitor
from modules.intrusion_detector import IntrusionDetector
from modules.screenshot_monitor import ScreenshotMonitor
from modules.webcam_monitor import WebcamMonitor
from storage.event_store import EventStore

BG = '#07111b'; PANEL = '#0d1a26'; PANEL2 = '#101f2c'; BORDER = '#203342'; TEXT = '#e7f0f7'; MUTED = '#8ca4b8'; TEAL = '#00c99a'; BLUE = '#2587ff'; RED = '#ff4d5a'; AMBER = '#ffb02e'

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('MAPRE IDS — Vigilância • Proteção')
        self.resize(1440, 900); self.setMinimumSize(1100, 700)
        self.config = load_config(); self.store = EventStore(); self.session = SessionManager()
        self.network = NetworkMonitor(); self.detector = IntrusionDetector()
        self.screenshot = ScreenshotMonitor(self.config['screenshot_directory'], self.config['screenshot_retention_days'])
        self.webcam = WebcamMonitor(self.config.get('webcam_directory', 'evidence/webcam'), self.config['screenshot_retention_days'])
        self.last_webcam = 0
        self.last_screenshot = 0; self._trigger_was_running = False
        self._build_ui(); self._apply_style(); self._setup_tray(); self._refresh()
        self._allow_exit = False
        self.timer = QTimer(self); self.timer.timeout.connect(self._tick); self.timer.start(max(1, int(self.config['poll_interval_seconds'])) * 1000)
        self._event('Sistema', 'Info', 'MAPRE IDS iniciado', 'Aplicativo', 'Local', 'Ícone visível na área de notificação; monitoramento aguardando gatilho')

    def _setup_tray(self):
        # O MAPRE permanece visível na área de notificação; não é executado de forma oculta.
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
        self.tray.setToolTip('MAPRE IDS — monitoramento visível')
        menu = QMenu()
        show_action = menu.addAction('Abrir MAPRE IDS')
        show_action.triggered.connect(self._restore_from_tray)
        menu.addSeparator()
        self.tray_status_action = menu.addAction('Status: aguardando gatilho')
        self.tray_status_action.setEnabled(False)
        menu.addSeparator()
        exit_action = menu.addAction('Encerrar MAPRE IDS')
        exit_action.triggered.connect(self._quit_application)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._tray_activated)
        self.tray.show()
        if not QSystemTrayIcon.isSystemTrayAvailable():
            QMessageBox.warning(self, 'Área de notificação indisponível',
                'O Windows não informou uma área de notificação disponível. Mantenha a janela aberta para acompanhar o status do MAPRE.')

    def _tray_activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self._restore_from_tray()

    def _restore_from_tray(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _quit_application(self):
        self._allow_exit = True
        self.close()

    def _build_ui(self):
        root = QWidget(); self.setCentralWidget(root); outer = QVBoxLayout(root); outer.setContentsMargins(0,0,0,0); outer.setSpacing(0)
        header = QFrame(); header.setObjectName('header'); hl = QHBoxLayout(header); hl.setContentsMargins(28,14,28,14)
        logo = QLabel('🐒'); logo.setStyleSheet('font-size:38px;')
        brand = QVBoxLayout(); title = QLabel('MAPRE'); title.setObjectName('brand'); subtitle = QLabel('IDS  •  Vigilância  •  Proteção'); subtitle.setObjectName('muted')
        brand.addWidget(title); brand.addWidget(subtitle); hl.addWidget(logo); hl.addLayout(brand); hl.addStretch()
        self.status_label = QLabel('● Sistema Pronto'); self.status_label.setObjectName('status'); hl.addWidget(self.status_label)
        self.clock = QLabel(); self.clock.setObjectName('muted'); hl.addWidget(self.clock); outer.addWidget(header)
        body = QHBoxLayout(); body.setContentsMargins(0,0,0,0); body.setSpacing(0); outer.addLayout(body,1)
        side = QFrame(); side.setObjectName('sidebar'); side.setFixedWidth(220); sv = QVBoxLayout(side); sv.setContentsMargins(12,22,12,12); sv.setSpacing(8)
        self.stack = QStackedWidget(); self.nav_buttons=[]
        for i,(label, page) in enumerate([('⌂   Painel', self._dashboard_page()),('◇   Ameaças', self._threats_page()),('▤   Eventos', self._events_page()),('⌘   Rede', self._network_page()),('⚙   Configurações', self._settings_page())]):
            btn=QPushButton(label); btn.setObjectName('nav'); btn.setCheckable(True); btn.clicked.connect(lambda checked=False, idx=i:self._navigate(idx)); sv.addWidget(btn); self.nav_buttons.append(btn); self.stack.addWidget(page)
        sv.addStretch(); monkey = QLabel('PEQUENO NO TAMANHO,\nGIGANTE NA VIGILÂNCIA.'); monkey.setObjectName('monkeytag'); monkey.setWordWrap(True); sv.addWidget(monkey)
        body.addWidget(side); content=QFrame(); content.setObjectName('content'); cv=QVBoxLayout(content); cv.setContentsMargins(22,22,22,12); cv.addWidget(self.stack); body.addWidget(content,1)
        footer=QLabel('● MAPRE — Sistema de Detecção de Intrusos                                                     Monitoramento local e autorizado  •  v0.2.0'); footer.setObjectName('footer'); outer.addWidget(footer)
        self._navigate(0)

    def _page(self, title, subtitle=None):
        w=QWidget(); l=QVBoxLayout(w); l.setContentsMargins(0,0,0,0); l.setSpacing(16)
        h=QLabel(title); h.setObjectName('pageTitle'); l.addWidget(h)
        if subtitle: s=QLabel(subtitle); s.setObjectName('muted'); l.addWidget(s)
        return w,l

    def _card(self, title, value='—', detail=''):
        f=QFrame(); f.setObjectName('panel'); l=QVBoxLayout(f); l.setContentsMargins(18,16,18,16)
        t=QLabel(title.upper()); t.setObjectName('muted'); v=QLabel(value); v.setObjectName('metric'); d=QLabel(detail); d.setObjectName('muted'); l.addWidget(t); l.addWidget(v); l.addWidget(d); return f,v,d

    def _dashboard_page(self):
        w,l=self._page('Painel de monitoramento','Visão geral da atividade observada neste dispositivo')
        cards=QGridLayout(); cards.setSpacing(12); l.addLayout(cards)
        self.metric_alerts=self._card('Alertas registrados','0','Histórico local')[0:2]
        self.metric_conn=self._card('Conexões ativas','0','Metadados do sistema')[0:2]
        self.metric_devices=self._card('Processos monitorados','—','Visibilidade conforme permissões')[0:2]
        self.metric_session=self._card('Sessão','Inativa','Aguardando início')[0:2]
        for i,item in enumerate([self.metric_alerts,self.metric_conn,self.metric_devices,self.metric_session]): cards.addWidget(item[0],0,i)
        self.metric_alerts_value=self.metric_alerts[1]; self.metric_conn_value=self.metric_conn[1]; self.metric_devices_value=self.metric_devices[1]; self.metric_session_value=self.metric_session[1]
        row=QHBoxLayout(); l.addLayout(row,2)
        net=QFrame(); net.setObjectName('panel'); nl=QVBoxLayout(net); nl.addWidget(self._heading('Mapa de rede — conexões observadas'))
        self.net_summary=QLabel('Aguardando dados do sistema…'); self.net_summary.setObjectName('networkmap'); self.net_summary.setWordWrap(True); nl.addWidget(self.net_summary,1)
        controls=QHBoxLayout(); self.start_btn=QPushButton('▶  Iniciar sessão'); self.start_btn.setObjectName('primary'); self.start_btn.clicked.connect(self._start_session)
        self.stop_btn=QPushButton('■  Encerrar sessão'); self.stop_btn.clicked.connect(self._stop_session)
        self.export_btn=QPushButton('⇩  Exportar eventos'); self.export_btn.clicked.connect(self._export_csv)
        controls.addWidget(self.start_btn); controls.addWidget(self.stop_btn); controls.addWidget(self.export_btn); nl.addLayout(controls); row.addWidget(net,3)
        alerts=QFrame(); alerts.setObjectName('panel'); al=QVBoxLayout(alerts); al.addWidget(self._heading('Alertas recentes')); self.alert_table=self._table(['Horário','Gravidade','Evento','Origem']); al.addWidget(self.alert_table); row.addWidget(alerts,2)
        bottom=QFrame(); bottom.setObjectName('panel'); bl=QVBoxLayout(bottom); bl.addWidget(self._heading('Eventos em tempo real')); self.recent_table=self._table(['Data/Hora','Tipo','Origem','Destino','Descrição']); bl.addWidget(self.recent_table); l.addWidget(bottom,2)
        return w

    def _threats_page(self):
        w,l=self._page('Ameaças e alertas','Alertas são indicadores para investigação, não confirmação automática de invasão.')
        self.threat_table=self._table(['Data/Hora','Gravidade','Categoria','Origem','Destino','Descrição']); l.addWidget(self.threat_table,1)
        b=QPushButton('Atualizar alertas'); b.clicked.connect(self._refresh); l.addWidget(b); return w

    def _events_page(self):
        w,l=self._page('Histórico de eventos','Eventos observados pelo MAPRE e regras heurísticas aplicadas')
        row=QHBoxLayout(); b=QPushButton('Exportar CSV'); b.clicked.connect(self._export_csv); row.addWidget(b); row.addStretch(); l.addLayout(row)
        self.events_table=self._table(['Data/Hora','Tipo','Gravidade','Origem','Destino','Descrição']); l.addWidget(self.events_table,1); return w

    def _network_page(self):
        w,l=self._page('Rede e conexões','Metadados fornecidos pelo sistema operacional; conteúdo de pacotes não é coletado.')
        self.network_table=self._table(['Protocolo','Estado','Endereço local','Endereço remoto','PID','Processo']); l.addWidget(self.network_table,1)
        note=QLabel('Observação: no Windows, algumas conexões podem exigir execução elevada para serem listadas.'); note.setObjectName('muted'); l.addWidget(note); return w

    def _settings_page(self):
        w,l=self._page('Configurações','Configure o gatilho e os recursos opcionais de monitoramento.')
        panel=QFrame(); panel.setObjectName('panel'); form=QVBoxLayout(panel); form.setContentsMargins(24,24,24,24); form.setSpacing(14)
        form.addWidget(self._heading('Ativação por processo'))
        form.addWidget(QLabel('Nome do processo ou caminho do executável (ex.: notepad.exe)'))
        self.trigger_input=QLineEdit(self.config['trigger_process']); form.addWidget(self.trigger_input)
        form.addWidget(self._heading('Captura visual opcional'))
        self.capture_check=QCheckBox('Habilitar capturas de tela durante sessão ativa (indicador visível)'); self.capture_check.setChecked(bool(self.config['screenshot_enabled'])); form.addWidget(self.capture_check)
        r=QHBoxLayout(); r.addWidget(QLabel('Intervalo de captura (segundos)')); self.capture_interval=QSpinBox(); self.capture_interval.setRange(10,3600); self.capture_interval.setValue(int(self.config['screenshot_interval_seconds'])); r.addWidget(self.capture_interval); r.addStretch(); form.addLayout(r)
        r2=QHBoxLayout(); r2.addWidget(QLabel('Retenção de evidências (dias)')); self.retention=QSpinBox(); self.retention.setRange(1,365); self.retention.setValue(int(self.config['screenshot_retention_days'])); r2.addWidget(self.retention); r2.addStretch(); form.addLayout(r2)
        self.capture_state=QLabel('Captura de tela: desativada'); self.capture_state.setObjectName('muted'); form.addWidget(self.capture_state)
        form.addWidget(self._heading('Webcam — evidências opcionais'))
        self.webcam_check=QCheckBox('Autorizar captura pela webcam durante sessão ativa (indicador visível)'); self.webcam_check.setChecked(bool(self.config.get('webcam_enabled', False))); form.addWidget(self.webcam_check)
        self.webcam_state=QLabel('Webcam: desativada'); self.webcam_state.setObjectName('muted'); form.addWidget(self.webcam_state)
        note=QLabel('A câmera só será aberta após autorização explícita aqui e durante uma sessão ativa. As imagens são salvas localmente a cada 10 segundos.'); note.setObjectName('muted'); note.setWordWrap(True); form.addWidget(note)
        save=QPushButton('Salvar configurações'); save.setObjectName('primary'); save.clicked.connect(self._save_settings); form.addWidget(save); l.addWidget(panel); l.addStretch(); return w

    def _heading(self,text):
        label=QLabel(text); label.setObjectName('sectionTitle'); return label

    def _table(self, headers):
        t=QTableWidget(0,len(headers)); t.setHorizontalHeaderLabels(headers); t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers); t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows); t.setAlternatingRowColors(False); t.verticalHeader().setVisible(False); t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch); t.setShowGrid(False); t.setMinimumHeight(200); return t

    def _apply_style(self):
        self.setStyleSheet(f"""
        QMainWindow, QWidget {{ background:{BG}; color:{TEXT}; font-family:'Segoe UI'; font-size:13px; }}
        #header {{ background:#08131e; border-bottom:1px solid {BORDER}; }} #brand {{font-size:30px;font-weight:800;letter-spacing:2px;color:#f5eee2;}} #muted {{color:{MUTED};}} #status {{color:{TEAL};padding:8px 12px;background:#0c2929;border-radius:8px;}} #sidebar {{background:#08131d;border-right:1px solid {BORDER};}} #nav {{text-align:left;padding:14px 12px;border:0;border-radius:7px;color:#91a9bc;background:transparent;font-size:14px;}} #nav:hover,#nav:checked {{background:#122532;color:{TEAL};border-left:3px solid {TEAL};}} #monkeytag {{color:#6e8292;font-size:12px;letter-spacing:1px;padding:18px 8px;}} #content {{background:{BG};}} #pageTitle {{font-size:24px;font-weight:700;}} #panel {{background:{PANEL};border:1px solid {BORDER};border-radius:10px;}} #metric {{font-size:28px;font-weight:700;color:#f4f8fb;padding:5px 0;}} #sectionTitle {{font-size:16px;font-weight:650;}} #networkmap {{font-size:15px;line-height:1.8;color:#9be8d5;padding:12px;}} QPushButton {{background:{PANEL2};border:1px solid {BORDER};border-radius:7px;padding:10px 13px;color:{TEXT};}} QPushButton:hover {{border-color:{TEAL};}} QPushButton#primary {{background:#087e68;border-color:#0aa987;font-weight:700;}} QLineEdit,QSpinBox {{background:#08131d;border:1px solid {BORDER};border-radius:6px;padding:9px;color:{TEXT};}} QTableWidget {{background:{PANEL};border:0;alternate-background-color:#0b1722;selection-background-color:#173d45;}} QHeaderView::section {{background:#122230;color:#a9bfce;padding:10px;border:0;font-weight:600;}} QTableWidget::item {{padding:8px;border-bottom:1px solid #172b39;}} #footer {{background:#08131d;color:#7891a5;padding:10px 22px;border-top:1px solid {BORDER};}} QCheckBox {{spacing:10px;}} """)

    def _navigate(self, idx):
        self.stack.setCurrentIndex(idx)
        for i,b in enumerate(self.nav_buttons): b.setChecked(i==idx)
        self._refresh()

    def _event(self, category, severity, description, source='', destination='', details=''):
        self.store.add(category,severity,description,source,destination,details); log('info',f'{category} [{severity}] {description} | {source} -> {destination}')

    def _start_session(self, reason='manual'):
        if self.session.start(reason):
            self._event('Sessão','Info',f'Monitoramento iniciado: {reason}','MAPRE','Local', 'Sessão visível e controlável pelo usuário')
            self.status_label.setText('● Monitoramento Ativo'); self.status_label.setStyleSheet(f'color:{TEAL};padding:8px 12px;background:#0c2929;border-radius:8px;')
        self._refresh()

    def _stop_session(self):
        if self.session.stop(): self._event('Sessão','Info','Monitoramento encerrado pelo operador','MAPRE','Local')
        self.webcam.stop()
        self.status_label.setText('● Sistema Pronto'); self._refresh()

    def _save_settings(self):
        trigger=self.trigger_input.text().strip()
        if not trigger:
            QMessageBox.warning(self,'Configuração inválida','Informe o nome ou caminho de um processo.'); return
        self.config.update({'trigger_process':trigger,'screenshot_enabled':self.capture_check.isChecked(),
            'screenshot_interval_seconds':self.capture_interval.value(),'screenshot_retention_days':self.retention.value(),'webcam_enabled':self.webcam_check.isChecked()})
        save_config(self.config); self.screenshot=ScreenshotMonitor(self.config['screenshot_directory'],self.config['screenshot_retention_days'])
        self.webcam.stop(); self.webcam=WebcamMonitor(self.config.get('webcam_directory','evidence/webcam'),self.config['screenshot_retention_days'])
        self._event('Configuração','Info','Configurações salvas','MAPRE','Local',f"Gatilho={trigger}; captura de tela={'ativa' if self.config['screenshot_enabled'] else 'inativa'}; webcam={'autorizada' if self.config.get('webcam_enabled') else 'desativada'}")
        QMessageBox.information(self,'MAPRE','Configurações salvas com sucesso. A captura só ocorrerá durante uma sessão ativa.'); self._refresh()

    def _tick(self):
        self.clock.setText(datetime.now().astimezone().strftime('%d/%m/%Y %H:%M:%S'))
        trigger_running=TriggerMonitor.is_running(self.config.get('trigger_process',''))
        if trigger_running and not self._trigger_was_running and not self.session.active:
            self._start_session(f"gatilho: {self.config['trigger_process']}")
            self.tray.showMessage('MAPRE IDS — gatilho detectado',
                f"O processo {self.config['trigger_process']} foi aberto. A sessão autorizada começou.",
                QSystemTrayIcon.MessageIcon.Information, 5000)
        elif not trigger_running and self._trigger_was_running and self.session.active and self.session.reason.startswith('gatilho:'):
            self._stop_session()
            self.tray.showMessage('MAPRE IDS — sessão encerrada',
                'O processo configurado foi fechado; a sessão de monitoramento foi encerrada.',
                QSystemTrayIcon.MessageIcon.Information, 5000)
        self._trigger_was_running=trigger_running
        if self.session.active:
            if self.config.get('webcam_enabled'):
                try:
                    if not self.webcam.active:
                        self.webcam.start(); self._event('Webcam','Info','Webcam autorizada aberta para a sessão','MAPRE','Webcam local')
                    if datetime.now().timestamp()-self.last_webcam >= 10:
                        path=self.webcam.capture(); self.last_webcam=datetime.now().timestamp()
                        self._event('Evidência','Info','Imagem da webcam registrada','MAPRE',str(path),'Captura autorizada; retenção configurada')
                except Exception as exc:
                    self.config['webcam_enabled']=False; save_config(self.config); self.webcam.stop()
                    self._event('Erro','Média','Captura pela webcam desativada após falha','MAPRE','Local',str(exc)); log('error',f'Falha na webcam: {exc}')
            elif self.webcam.active:
                self.webcam.stop()
            rows=self.network.snapshot()
            for ev in self.network.new_events(rows,int(self.config['alert_connection_threshold']),int(self.config['alert_window_seconds'])):
                self._event(ev['category'],ev['severity'],ev['description'],ev['source'],ev['destination'],ev['details'])
            for r in rows:
                alert=self.detector.observe(r['process'],r['remote']) if r['remote']!='—' else None
                if alert: self._event(alert['category'],alert['severity'],alert['description'],alert['source'],alert['destination'],alert['details'])
            if self.config.get('screenshot_enabled') and datetime.now().timestamp()-self.last_screenshot >= int(self.config['screenshot_interval_seconds']):
                try:
                    path=self.screenshot.capture(); self.last_screenshot=datetime.now().timestamp()
                    self._event('Evidência','Info','Captura de tela realizada com recurso habilitado','MAPRE',str(path),'Captura visível; revisar política de privacidade')
                except Exception as exc:
                    self.config['screenshot_enabled']=False; save_config(self.config); self._event('Erro','Média','Captura visual desativada após falha','MAPRE','Local',str(exc))
                    log('error',f'Falha na captura: {exc}')
        self._refresh()

    def _refresh(self):
        if not hasattr(self,'clock'): return
        self.clock.setText(datetime.now().astimezone().strftime('%d/%m/%Y %H:%M:%S'))
        events=self.store.recent(300); connections=self.network.snapshot()
        if hasattr(self,'metric_alerts_value'):
            self.metric_alerts_value.setText(str(sum(1 for e in events if e['severity'] in ('Alta','Crítica','Média'))))
            self.metric_conn_value.setText(str(len(connections))); self.metric_devices_value.setText(str(len({c['process'] for c in connections if c['process']!='—'})))
            self.metric_session_value.setText('Ativa' if self.session.active else 'Inativa')
            self.net_summary.setText('MAPRE central\n      │\n'+'\n'.join(f"  ├── {c['process']}  ·  {c['remote']}  ·  {c['status']}" for c in connections[:10]) if connections else 'Nenhuma conexão disponível no momento.\nInicie uma sessão para registrar alterações e gerar alertas.')
            self._fill(self.alert_table,[e for e in events if e['severity'] in ('Alta','Crítica','Média')][:8],['timestamp','severity','description','source'])
            self._fill(self.recent_table,events[:10],['timestamp','category','source','destination','description'])
        if hasattr(self,'threat_table'): self._fill(self.threat_table,[e for e in events if e['severity'] in ('Alta','Crítica','Média')],['timestamp','severity','category','source','destination','description'])
        if hasattr(self,'events_table'): self._fill(self.events_table,events,['timestamp','category','severity','source','destination','description'])
        if hasattr(self,'network_table'):
            self.network_table.setRowCount(len(connections))
            for i,r in enumerate(connections):
                for j,k in enumerate(['protocol','status','local','remote','pid','process']): self.network_table.setItem(i,j,QTableWidgetItem(str(r[k])))
        if hasattr(self,'capture_state'):
            self.capture_state.setText('Captura de tela: habilitada — sessão ativa' if self.config.get('screenshot_enabled') and self.session.active else 'Captura de tela: habilitada, aguardando sessão' if self.config.get('screenshot_enabled') else 'Captura de tela: desativada')
        if hasattr(self,'webcam_state'):
            self.webcam_state.setText('● WEBCAM ATIVA — capturas a cada 10 s' if self.webcam.active else 'Webcam: autorizada, aguardando sessão' if self.config.get('webcam_enabled') else 'Webcam: desativada')
        if hasattr(self, 'tray_status_action'):
            status = 'SESSÃO ATIVA' if self.session.active else 'AGUARDANDO GATILHO'
            self.tray_status_action.setText(f'Status: {status}')
            self.tray.setToolTip(f'MAPRE IDS — {status.lower()} — ícone visível')

    @staticmethod
    def _fill(table, rows, keys):
        table.setRowCount(len(rows))
        for i,row in enumerate(rows):
            for j,key in enumerate(keys):
                value=str(row.get(key,'—') or '—'); item=QTableWidgetItem(value)
                if key=='severity': item.setForeground(QColor(RED if value in ('Alta','Crítica') else AMBER if value=='Média' else TEAL))
                table.setItem(i,j,item)

    def _export_csv(self):
        path,_=QFileDialog.getSaveFileName(self,'Exportar eventos MAPRE','mapre_eventos.csv','CSV (*.csv)')
        if not path: return
        rows=self.store.recent(10000)
        try:
            with open(path,'w',newline='',encoding='utf-8-sig') as f:
                writer=csv.DictWriter(f,fieldnames=['id','timestamp','category','severity','source','destination','description','details']); writer.writeheader(); writer.writerows(rows)
            QMessageBox.information(self,'Exportação concluída',f'{len(rows)} eventos exportados para:\n{path}')
        except OSError as exc: QMessageBox.critical(self,'Erro na exportação',str(exc))

    def closeEvent(self, event):
        if not getattr(self, '_allow_exit', False):
            event.ignore()
            self.hide()
            if self.tray.isVisible():
                self.tray.showMessage('MAPRE IDS continua ativo',
                    'O MAPRE foi minimizado para a área de notificação. Clique no ícone para reabrir ou use “Encerrar MAPRE IDS” para sair.',
                    QSystemTrayIcon.MessageIcon.Information, 5000)
            return
        self.webcam.stop()
        self.timer.stop()
        self.tray.hide()
        log('info', 'Aplicativo encerrado pelo operador')
        event.accept()
