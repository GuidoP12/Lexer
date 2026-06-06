"1- Definicion de tokens"
"3- Tokenizacion"
"5- Manejo de erroes"

import sys
import os

class SmartHome:
    def __init__(self):

        #TOKENS
        self.TOKENS = {
            #Palabras de control
            "WHEN": "PR_WHEN",
            "EVERY": "PR_EVERY",
            "IF": "PR_IF",
            "THEN": "PR_THEN",
            "ELSE": "PR_ELSE",
            "DO": "PR_DO",
            "END": "PR_END",

            #Literales Booleanos
            "TRUE": "BOOL_LITERAL",
            "FALSE": "BOOL_LITERAL",
            "OFF": "BOOL_LITERAL",
            "ON": "BOOL_LITERAL",

            #Identificadores de Dispositivos
            "FOCO": "ID_FOCO",
            "AIRE": "ID_AIRE",
            "PERSIANA": "ID_PERSIANA",
            "CERRADURA": "ID_CERRADURA",
            "RELOJ": "ID_RELOJ",
            "ALTAVOZ": "ID_ALTAVOZ",
            "ALARMA": "ID_ALARMA",

            #Identificadores de Atributos
            "ESTADO": "ATTR_ESTADO",
            "BRILLO": "ATTR_BRILLO",
            "COLOR": "ATTR_COLOR",
            "MODO": "ATTR_MODO",
            "TEMP_OBJ": "ATTR_TEMP_OBJ",
            "TEMP_ACT": "ATTR_TEMP_ACT",
            "POSICION": "ATTR_POSICION",
            "HORA": "ATTR_HORA",
            "FECHA": "ATTR_FECHA",
            "VOLUMEN": "ATTR_VOLUMEN",
            "MURE": "ATTR_MUTE",
            "MENSAJE": "ATTR_MENSAJE",
            "EMAIL_NOTIFICACION": "ATTR_EMAIL_NOTIF", #tengo dudas de esta derivacion

            #Operadores y estructura
                #Asignacion
            "ASIGNACION": "OP_ASIG",
                #Aritmeticos
            "SUMA": "OP_SUMA",
            "RESTA": "OP_RESTA",
            "MULTIPLICACION": "OP_MULT",
            "DIVISION": "OP_DIV",
                #Relacionales
            "IGUAL": "OP_IGUAL",
            "DISTINTO": "OP_DISTINTO",
            "MAYOR": "OP_MAYOR",
            "MENOR": "OP_MENOR",
            "MAYOR_IGUAL": "OP_MAYOR_IGUAL",
            "MENOR_IGUAL": "OP_MENOR_IGUAL",
                #Logicos
            "AND": "OP_AND",
            "OR": "OP_OR",
            "NOT": "OP_NOT",
            
            #Delimitadores
            "PARENTESIS_IZQ": "PAREN_IZQ",
            "PARENTESIS_DER": "PAREN_DER",
            "PUNTO": "PUNTO",
            "FIN_LINEA": "FIN_LINEA"
        }

    #TOKENIZACION
    def tokenize(self, code_text):
        pos = 0
        current_line = 1
        last_was_fin_linea = False

        while pos < len(code_text):
            char = code_text[pos]

            # 1 - Espacios en blanco
            if char == ' ' or char == '\t':
                pos += 1
                continue

            # 2 - Saltos de linea
            if char == '\n':
                if not last_was_fin_linea:
                    yield('FIN_LINEA', '\n', current_line)
                    last_was_fin_linea = True
                current_line += 1
                pos += 1
                continue

            last_was_fin_linea = False

            # 3 - Cadenas de texto con comillas
            if char == '"':
                inicio = pos
                pos += 1 #Consumir comilla de apertura
                while pos < len(code_text) and code_text[pos] != '"' and code_text[pos] != 'n':
                    pos += 1
                if pos < len(code_text) and code_text[pos] == '"':
                    pos += 1 #consumir comilla de cierre
                    texto_completo = code_text[inicio:pos]
                    yield('STRING', texto_completo, current_line)
                else:
                    print(f"ERROR LEXICO: Cadena de texto sin cerrar en la línea {current_line}", file=sys.stderr)
                continue

            # 4 - Palabras (Identificadores, Atributos, Tokens)
            if char.isalpha() or char == '_':
                inicio = pos
                while pos < len(code_text) and (code_text[pos].isalnum() or code_text[pos] == '_'):
                    pos += 1
                palabra_original = code_text[inicio:pos].strip()

                palabra = palabra_original.upper()

                if palabra in self.TOKENS:
                    yield (self.TOKENS[palabra], palabra, current_line)

                #Valores discretos sin comillas aceptados por la gramatica
                elif palabra in ["rojo", "azul", "verde", "manual", "automatico", "invierno", "verano"]:
                    yield('VAL_DISCRETO', palabra, current_line)
                else:
                    print(f"ERROR LEXICO: Identificador o palabra desconocida '{palabra}' en la línea {current_line}", file=sys.stderr)
                continue

            # 5 - Valores numericos y unidades fisicas
            if char.isdigit():
                inicio = pos
                while pos < len(code_text) and (code_text[pos].isalnum() or code_text[pos] in [':', '/', '%']):
                        pos += 1
                valor_completo = code_text[inicio:pos]

                if valor_completo.endswith('C'):
                    yield ('VAL_TEMP', valor_completo, current_line)
                elif valor_completo.endswith('%'):
                    yield ('VAL_PORCENTAJE', valor_completo, current_line)
                elif valor_completo.endswith('lux'):
                    yield ('VAL_TIEMPO', valor_completo, current_line)
                elif ':' in valor_completo:
                    yield('VAL_HORA', valor_completo, current_line)
                elif '/' in valor_completo:
                    yield ('VAL_FECHA', valor_completo, current_line)
                elif valor_completo.isdigit():
                    yield ('VAL_NUMERO', valor_completo, current_line)
                else:
                    print(f"ERROR LEXICO: Formato de valor fisico desconocido '{valor_completo}' en la linea {current_line}", file=sys.stderr)
                continue

            # 6 - Operadores relacionales y asignacion
            if char == '=':
                if pos + 1 < len(code_text) and code_text[pos + 1] == '=':
                    yield ('OP_IGUAL', '==', current_line)
                    pos += 2
                else:
                    yield ('OP_ASIG', '=', current_line)
                    pos += 1
                continue

            if char == '>':
                if pos + 1 < len(code_text) and code_text[pos + 1] == '=':
                    yield ('OP_MAYOR_IGUAL', '>=', current_line)
                    pos += 2
                else:
                    yield ('OP_MAYOR', '>', current_line)
                    pos += 1
                continue

            if char == '<':
                if pos + 1 < len(code_text) and code_text[pos + 1] == '=':
                    yield ('OP_MENOR_IGUAL', '<=', current_line)
                    pos += 2
                else:
                    yield ('OP_MENOR', '<', current_line)
                    pos += 1
                continue

            if char == '!':
                if pos + 1 < len(code_text) and code_text[pos + 1] == '=':
                    yield ('OP_DISTINTO', '!=', current_line)
                    pos += 2
                else:
                    print(f"ERROR LEXICO: Simbolo '!' aislado invalidado en la linea {current_line}", file=sys.stderr)
                    pos += 1
                continue

            # 7 - Delimitadores y operadores aritmeticos simples
            if char == '.':
                yield('PUNTO', '.', current_line)
                pos += 1
                continue
            if char == '(':
                yield('PAREN_IZQ', '(', current_line)
                pos += 1
                continue
            if char == ')':
                yield('PAREN_DER', ')', current_line)
                pos += 1
                continue
            if char == '+':
                yield('OP_SUMA', '+', current_line)
                pos += 1
                continue
            if char == '-':
                yield('OP_RESTA', '-', current_line)
                pos += 1
                continue
            if char == '*':
                yield('OP_MULT', '*', current_line)
                pos += 1
                continue
            if char == '/':
                yield('OP_DIV', '/', current_line)
                pos += 1
                continue

            # 8 - Error critico
            print(f"ERROR LEXICO: Simbolo desconocido '{char}' en la linea {current_line}", file=sys.stderr)
            pos += 1

def Resultados(lexer, script_text):
    # Imprimimos el encabezado de la tabla con alineación fija (:<número)
    print(f"{'LINEA':<8} | {'TIPO DE TOKEN':<25} | {'VALOR ORIGINAL':<25}")
    print("-" * 65)

    lista_de_tokens = list(lexer.tokenize(script_text))
    
    for token_type, value, line in lista_de_tokens:
        # Imprimimos la fila aplicando el espaciado fijo para que queden columnas perfectas
        print(f"{line:<3} | {token_type:<25} | {value}")
        
    print("="*65)
    print(f" Total de tokens procesados exitosamente: {len(lista_de_tokens)}")
    print("="*65 + "\n")  

# =============================================================
# EXTRA: Prueba de Ejecución
# =============================================================
if __name__ == "__main__":
    lexer = SmartHome()

    while True:
        print("=" * 30)
        print(f"Menu")
        print("=" * 30)
        print("1. Escribir codigo.")
        print("2. Cargar un script.")
        print("3. Script de prueba")
        print("4. Salir")

        opcion = input("Seleccione una opcion(1-3): ").strip()
        if opcion == "1":
            print("\nEscriba el codigo línea por línea.")
            print("Cuando haya terminado, escriba la palabra FIN en una línea nueva para procesar:")
            print("-" * 60)
            
            lineas_usuario = []
            while True:
                linea = input()
                if linea.strip().upper() == "FIN":  # Si escribe 'FIN', salimos del bucle
                    break
                lineas_usuario.append(linea)
            
            # Unimos todas las líneas capturadas con saltos de línea
            codigo_consola = "\n".join(lineas_usuario)
            
            # Procesamos el código resultante
            Resultados(lexer, codigo_consola)

        elif opcion == "2":
            ruta_archivo = input("\n Ingrese la ruta del archivo: ").strip()
            if os.path.exists(ruta_archivo):
                try:
                    with open(ruta_archivo, 'r', encoding='utf-8') as archivo:
                        contenido = archivo.read()
                    print(f"\n Archivo '{ruta_archivo}' leido correctamente.")
                    Resultados(lexer, contenido)
                except Exception as e:
                    print(f"Ocurrio un error al leer el archivo: {e}\n", file=sys.stderr)
            else:
                print(f"El archivo '{ruta_archivo}' no existe en esta carpeta.\n", file=sys.stderr)
        elif opcion == "3":
            print("=" * 40)
            print("Script de prueba")
            print("=" * 40)
            script_domotica = """WHEN aire.temp_act > 25C DO
            foco.estado = ON
            altavoz.mensaje = "Alerta de calor"
            END
            """
            print(f"{script_domotica}")
            Resultados(lexer, script_domotica)
        elif opcion == "4":
            print("Proceso finalizado.")
            break
        else:
            print("Opcion invalida.")            

   

      
