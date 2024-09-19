import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import time
import os
from datetime import datetime
import csv

ledVermelho = 8
ledAmarelo = 10

GPIO.setmode(GPIO.BOARD)
GPIO.setup(ledAmarelo , GPIO.OUT)
GPIO.setup(ledVermelho , GPIO.OUT)

buzzer = 12
GPIO.setup(buzzer, GPIO.OUT)

pwmBuzzer = GPIO.PWM(buzzer, 1000)
pwmBuzzer.start(0)

def tocarBuzzer(quantidadeToques, tempo=0.5, volume=10):
    for _ in range(quantidadeToques):
        pwmBuzzer.ChangeDutyCycle(volume)
        time.sleep(tempo)
        pwmBuzzer.ChangeDutyCycle(0)
        time.sleep(tempo)

def salvarRegistrosCSV():
    with open('registros_acessos.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['idUser', 'nome', 'entrada', 'saida'])
        
        for idUser, dados in registros.items():
            nome = userCadastrado.get(idUser, 'Desconhecido')
            entradas = dados['entradas']
            saidas = dados['saidas']
            
            for i in range(len(entradas)):
                entrada = entradas[i]
                saida = saidas[i] if i < len(saidas) else "Ainda na sala"
                writer.writerow([idUser, nome, entrada, saida])

    print("Registros salvos no arquivo 'registros_acessos.csv'")

quantidadeTentativasDesconhecidos = 0

leitorRfid = SimpleMFRC522()

def limpaTela():
    os.system('clear')

userCadastrado = {
        626493689772 : "Anderson"
    }

funcionarios = {
        910479064598 : "Luis"
    }



def verificarUserCadastrados(tag):
    global quantidadeTentativasDesconhecidos
    limpaTela()
    if tag in userCadastrado:
        usuario = userCadastrado[tag]
        tocarBuzzer(1 , 0.2)
        return usuario
    if tag in funcionarios:
        func = funcionarios[tag]
        print("Você não tem acesso a esse projeto" , func)
        registrarTentativaDeEntrada(tag)
        tocarBuzzer(2 , 0.2)
        GPIO.output(ledVermelho, GPIO.HIGH)
        time.sleep(5)
        GPIO.output(ledVermelho, GPIO.LOW)

        print("Esperando...")
    else:
        print("Usuário desconhecido")
        print("Esperando...")
        tocarBuzzer(3 , 0.2)
        quantidadeTentativasDesconhecidos += 1
        for _ in range(10):
            GPIO.output(ledVermelho, GPIO.HIGH)
            time.sleep(0.1)
            GPIO.output(ledVermelho, GPIO.LOW)
            time.sleep(0.1)
    

registros = {}
registrosDePessoasSemAcesso = {}

def registrarTentativaDeEntrada(idUser):
    horaAtual = datetime.now()
    if idUser not in registrosDePessoasSemAcesso:
        registrosDePessoasSemAcesso[idUser] = {'TentativasEntradas': []}
    registrosDePessoasSemAcesso[idUser]['TentativasEntradas'].append(horaAtual)

def registrarEntrada(idUser , nome):
    """Registra a entrada de um colaborador."""
    horaAtual = datetime.now()
    if idUser  in registros:
        print("Bem-vindo de volta," , nome)
    if idUser not in registros:
        registros[idUser] = {'entradas': [], 'saidas': []}
        print("Bem-vindo," , nome)
    registros[idUser]['entradas'].append(horaAtual)
    print(f"Entrada registrada para colaborador {nome} às {horaAtual}")
    GPIO.output(ledAmarelo, GPIO.HIGH)
    time.sleep(5)
    GPIO.output(ledAmarelo, GPIO.LOW)

def registrarSaida(idUser , nome):
    """Registra a saída de um colaborador e calcula o tempo de permanência."""
    horaAtual = datetime.now()
    if idUser not in registros:
        print(f"Nenhuma entrada registrada para colaborador {nome}")
        return
    if not registros[idUser]['entradas']:
        print(f"Erro: Não há registro de entrada para o colaborador {nome}")
        return
    
    registros[idUser]['saidas'].append(horaAtual)
    print(f"Saída registrada para colaborador {nome} às {horaAtual}")

def calcularTempoSala(idUser , nome):
    """Calcula o tempo total de permanência do colaborador."""
    if idUser not in registros:
        print(f"Nenhum registro encontrado para colaborador {nome}")
        return
    entradas = registros[idUser]['entradas']
    saidas = registros[idUser]['saidas']
    if len(saidas) < len(entradas):
        print(f"Erro: O colaborador {nome} não registrou saída para cada entrada.")
        return
    
    tempo = 0
    for i in range(len(saidas)):
        entrada = entradas[i]
        saida = saidas[i] if i < len(saidas) else datetime.now()
        tempo += (saida - entrada).total_seconds()
    
    horas = tempo // 3600
    minutos = (tempo % 3600) // 60
    segundos = tempo % 60
    
    print(f"Tempo total de permanência para colaborador {nome}: {int(horas)} horas, {int(minutos)} minutos e {int(segundos)} segundos")
    GPIO.output(ledAmarelo, GPIO.HIGH)
    time.sleep(5)
    GPIO.output(ledAmarelo, GPIO.LOW)


def verificaEntradasSaidas(idUser , nome):
    if nome != None:
        if idUser not in registros or not registros[idUser]['entradas'] or (len(registros[idUser]['saidas']) >= len(registros[idUser]['entradas'])):
            registrarEntrada(idUser , nome)
        else:
            registrarSaida(idUser , nome)
            calcularTempoSala(idUser , nome)
            print("Esperando...")
            time.sleep(4)


try:
    loop = True
    while loop:
        limpaTela()
        print("LENDO...")
        tag , text= leitorRfid.read()
        nome = verificarUserCadastrados(tag)
        time.sleep(0.2)
        verificaEntradasSaidas(tag , nome)

finally:
    GPIO.cleanup()
    pwmBuzzer.stop()
    limpaTela()
    print("\n\nREGISTROS:\n\n" , registros)
    print("\n\nREGISTROS DE PESSOAS SEM ACESSO:\n\n" , registrosDePessoasSemAcesso)
    print("\n\nQUANTIDADE DE ACESSOS DESCONHECIDOS\n\n" , quantidadeTentativasDesconhecidos)
    salvarRegistrosCSV() 