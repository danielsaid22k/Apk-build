from __future__ import annotations
import os, json, threading, traceback
from pathlib import Path
from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.gridlayout import GridLayout
from android_config import ensure_runtime, load_settings, save_settings

PACKAGE_ROOT=Path(__file__).resolve().parent

class CCSApp(App):
    title='Crypto Certified Switch'
    def build(self):
        runtime=Path(self.user_data_dir)
        self.cfg_path,self.env_path=ensure_runtime(PACKAGE_ROOT,runtime)
        self.config,self.env=load_settings(self.cfg_path,self.env_path)
        root=BoxLayout(orientation='vertical',spacing=dp(8),padding=dp(10))
        title=Label(text='[b]Crypto Certified Switch[/b]\nAndroid Config Center · v7.1',markup=True,size_hint_y=None,height=dp(70))
        root.add_widget(title)
        sc=ScrollView(); form=GridLayout(cols=1,spacing=dp(8),size_hint_y=None); form.bind(minimum_height=form.setter('height')); sc.add_widget(form); root.add_widget(sc)
        self.fields={}; self.checks={}
        self._section(form,'APIs / RPC')
        self._field(form,'HELIUS_API_KEY','Helius API Key',secret=True)
        self._field(form,'SOLANA_RPC_URL','Solana RPC URL')
        self._field(form,'SOLANA_RPC_FALLBACK_URL','Solana RPC fallback')
        self._field(form,'ETHEREUM_RPC_URL','Ethereum RPC URL')
        self._field(form,'BNB_RPC_URL','BNB Chain RPC URL')
        self._section(form,'Telegram')
        self._field(form,'TELEGRAM_BOT_TOKEN','Token do bot',secret=True)
        self._field(form,'TELEGRAM_CHAT_ID','Chat ID')
        self._field(form,'APPROVAL_BRIDGE_PUBLIC_URL','Bridge público HTTPS')
        self._section(form,'Carteiras de origem')
        for network,label in [('ethereum','Phantom Ethereum'),('bnb','Binance Web3 BNB'),('solana','Phantom Solana')]: self._wallet(form,network,label,False)
        self._section(form,'Carteiras de destino')
        for network,label in [('ethereum','Destino Ethereum'),('bnb','Destino BNB'),('solana','Destino Solana')]: self._wallet(form,network,label,True)
        self.status=Label(text='Configurações privadas ficam no armazenamento interno do app.',size_hint_y=None,height=dp(55))
        form.add_widget(self.status)
        buttons=BoxLayout(size_hint_y=None,height=dp(52),spacing=dp(8)); buttons.add_widget(Button(text='SALVAR',on_release=self.save)); buttons.add_widget(Button(text='TESTAR CONFIG',on_release=self.test_config)); root.add_widget(buttons)
        return root
    def _section(self,form,text): form.add_widget(Label(text=f'[b]{text}[/b]',markup=True,size_hint_y=None,height=dp(38)))
    def _field(self,form,key,label,secret=False):
        form.add_widget(Label(text=label,size_hint_y=None,height=dp(28),halign='left'))
        ti=TextInput(text=self.env.get(key,''),password=secret,multiline=False,size_hint_y=None,height=dp(48)); self.fields[key]=ti; form.add_widget(ti)
    def _wallet(self,form,network,label,destination):
        row=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(8)); cb=CheckBox(size_hint_x=None,width=dp(46)); inp=TextInput(multiline=False)
        if destination:
            item=self.config.get('destination_wallets',{}).get(network,{}); key=f'dest:{network}'
        else:
            item=next((w for w in self.config.get('wallets',[]) if w.get('network')==network),{}); key=f'orig:{network}'
        cb.active=bool(item.get('enabled')); inp.text=str(item.get('address','')); self.checks[key]=cb; self.fields[key]=inp
        row.add_widget(cb); row.add_widget(Label(text=label,size_hint_x=.36)); row.add_widget(inp); form.add_widget(row)
    def save(self,*_):
        for k,ti in self.fields.items():
            if ':' not in k: self.env[k]=ti.text.strip()
        nets=self.config.setdefault('networks',{}); nets.setdefault('ethereum',{})['rpc_url']=self.env['ETHEREUM_RPC_URL']; nets.setdefault('bnb',{})['rpc_url']=self.env['BNB_RPC_URL']
        for network in ('ethereum','bnb','solana'):
            w=next((x for x in self.config.get('wallets',[]) if x.get('network')==network),None)
            if w: w['address']=self.fields[f'orig:{network}'].text.strip(); w['enabled']=self.checks[f'orig:{network}'].active
            d=self.config.setdefault('destination_wallets',{}).setdefault(network,{}); d['address']=self.fields[f'dest:{network}'].text.strip(); d['enabled']=self.checks[f'dest:{network}'].active
        save_settings(self.cfg_path,self.env_path,self.config,self.env)
        for k,v in self.env.items(): os.environ[k]=v
        self.status.text='✅ Configurações salvas no armazenamento privado do aplicativo.'
    def test_config(self,*_):
        self.save(); from app.wallets import validate
        errors=validate(self.config)
        if not self.env.get('TELEGRAM_BOT_TOKEN'): errors.append('Telegram: token do bot ausente.')
        if not self.env.get('TELEGRAM_CHAT_ID'): errors.append('Telegram: Chat ID ausente.')
        if any(w.get('enabled') and w.get('network')=='solana' for w in self.config.get('wallets',[])) and not (self.env.get('SOLANA_RPC_URL') or self.env.get('HELIUS_API_KEY')): errors.append('Solana: configure RPC ou Helius API Key.')
        self.status.text='✅ Configuração básica válida.' if not errors else '⚠️ '+ ' | '.join(errors[:4])

if __name__=='__main__': CCSApp().run()
