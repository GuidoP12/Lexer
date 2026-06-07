import sys
import os

class SmartHome:
    def __init__(self):
        # TOKENS: Solo palabras reservadas, atributos, booleanos y operadores
        # Los identificadores de dispositivos (foco_, aire_) se evalúan dinámicamente.
        self.TOKENS = {
            # Palabras de control
            "WHEN": "PR_WHEN",
            "EVERY": "PR_EVERY",
            "IF": "PR_IF",
            "THEN": "PR_THEN",
            "ELSE": "PR_ELSE",
            "DO": "PR_DO",
            "END": "PR_END",

            # Literales Booleanos
            "TRUE": "BOOL_LITERAL",
            "FALSE": "BOOL_LITERAL",
            "OFF": "BOOL_LITERAL",
            "ON": "BOOL_LITERAL",

            # Identificadores de Atributos
            "ESTADO": "ATTR_ESTADO",
            "BRILLO": "ATTR_BRILLO",
            "COLOR": "ATTR_COLOR",
            "MODO": "ATTR_MODO",
            "TEMP_OBJ": "ATTR_TEMP_OBJ",
            "TEMP_OBJETIVO": "ATTR_TEMP_OBJ", # Variante vista en ejemplos
            "TEMP_ACT": "ATTR_TEMP_ACT",
            "POSICION": "ATTR_POSICION",
            "HORA": "ATTR_HORA",
            "FECHA": "ATTR_FECHA",
            "VOLUMEN": "ATTR_VOLUMEN",
            "MUTE": "ATTR_MUTE", # Corregido typo MURE -> MUTE
            "MENSAJE": "ATTR_MENSAJE",
            "EMAIL_NOTIF": "ATTR_EMAIL_NOTIF",
            "EMAIL": "ATTR_EMAIL", # Variante vista en ejemplos

            # Operadores logicos
            "AND": "OP_AND",
            "OR": "OP_OR",
            "NOT": "OP_NOT",
        }

    # TOKENIZACION
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

            # 3 - Comentarios y Division
            if char == '/':
                if pos + 1 < len(code_text) and code_text[pos + 1] == '/':
                    # Es un comentario //, avanzamos hasta el final de la linea
                    while pos < len(code_text) and code_text[pos] != '\n':
                        pos += 1
                    continue
                else:
                    # Es el operador de division
                    yield('OP_DIV', '/', current_line)
                    pos += 1
                    continue

            # 4 - Cadenas de texto con comillas
            if char == '"':
                inicio = pos
                pos += 1 # Consumir comilla de apertura
                while pos < len(code_text) and code_text[pos] != '"' and code_text[pos] != '\n':
                    pos += 1
                if pos < len(code_text) and code_text[pos] == '"':
                    pos += 1 # consumir comilla de cierre
                    texto_completo = code_text[inicio:pos]
                    yield('STRING', texto_completo, current_line)
                else:
                    print(f"ERROR LEXICO: Cadena de texto sin cerrar en la línea {current_line}", file=sys.stderr)
                continue

            # 5 - Correos Electronicos (Lookahead)
            # Verificamos si la secuencia actual parece ser un email
            temp_pos = pos
            is_email = False
            # Miramos hacia adelante hasta un espacio o delimitador
            while temp_pos < len(code_text) and not code_text[temp_pos].isspace() and code_text[temp_pos] not in ['=', '<', '>', '!', '(', ')', '\n']:
                if code_text[temp_pos] == '@':
                    is_email = True
                    break
                temp_pos += 1

            if is_email:
                inicio = pos
                # Capturamos todos los caracteres validos de un email incluyendo multiples puntos
                while pos < len(code_text) and (code_text[pos].isalnum() or code_text[pos] in ['_', '-', '.', '+', '@']):
                    pos += 1
                yield('VAL_EMAIL', code_text[inicio:pos], current_line)
                continue

            # 6 - Palabras (Identificadores Dinámicos, Atributos, Palabras Reservadas)
            if char.isalpha() or char == '_':
                inicio = pos
                while pos < len(code_text) and (code_text[pos].isalnum() or code_text[pos] == '_'):
                    pos += 1
                palabra_original = code_text[inicio:pos]
                palabra = palabra_original.upper()

                if palabra in self.TOKENS:
                    yield (self.TOKENS[palabra], palabra_original, current_line)
                # Valores discretos de los actuadores
                elif palabra_original.lower() in ["rojo", "azul", "verde", "blanco", "frio", "calor", "vent"]:
                    yield('VAL_DISCRETO', palabra_original, current_line)
                # Identificadores dinamicos (Analisis por Prefijo)
                elif palabra_original.startswith("foco_"):
                    yield ('ID_FOCO', palabra_original, current_line)
                elif palabra_original.startswith("aire_"):
                    yield ('ID_AIRE', palabra_original, current_line)
                elif palabra_original.startswith("persiana_"):
                    yield ('ID_PERSIANA', palabra_original, current_line)
                elif palabra_original.startswith("cerradura_"):
                    yield ('ID_CERRADURA', palabra_original, current_line)
                elif palabra_original.startswith("reloj_"):
                    yield ('ID_RELOJ', palabra_original, current_line)
                elif palabra_original.startswith("altavoz_"):
                    yield ('ID_ALTAVOZ', palabra_original, current_line)
                elif palabra_original.startswith("alarma_"):
                    yield ('ID_ALARMA', palabra_original, current_line)
                elif palabra_original.startswith("sensor_"):
                    yield ('ID_SENSOR', palabra_original, current_line)
                else:
                    print(f"ERROR LEXICO: Identificador o palabra desconocida '{palabra_original}' en la línea {current_line}", file=sys.stderr)
                continue

            # 7 - Valores numericos (Enteros, Decimales, Negativos) y unidades fisicas
            # Se detecta el negativo '-' solo si le sigue un numero, sino es resta.
            if char.isdigit() or (char == '-' and pos + 1 < len(code_text) and code_text[pos+1].isdigit()):
                inicio = pos
                pos += 1 # Consumir el primer digito o el guion
                # Permitimos punto decimal, grados °, dos puntos y barras para fechas
                while pos < len(code_text) and (code_text[pos].isalnum() or code_text[pos] in ['.', '°', ':', '/', '%']):
                    pos += 1
                valor_completo = code_text[inicio:pos]

                if valor_completo.endswith('C') or valor_completo.endswith('°C'):
                    yield ('VAL_TEMP', valor_completo, current_line)
                elif valor_completo.endswith('%'):
                    yield ('VAL_PORCENTAJE', valor_completo, current_line)
                elif valor_completo.endswith('s') or valor_completo.endswith('m') or valor_completo.endswith('h') or valor_completo.endswith('lux'):
                    yield ('VAL_TIEMPO_LUZ', valor_completo, current_line)
                elif ':' in valor_completo:
                    yield('VAL_HORA', valor_completo, current_line)
                elif '/' in valor_completo:
                    yield ('VAL_FECHA', valor_completo, current_line)
                elif '.' in valor_completo:
                    yield ('VAL_NUMERO_DECIMAL', valor_completo, current_line)
                else:
                    try:
                        int(valor_completo)
                        yield ('VAL_NUMERO', valor_completo, current_line)
                    except ValueError:
                        print(f"ERROR LEXICO: Formato fisico o numerico desconocido '{valor_completo}' en la linea {current_line}", file=sys.stderr)
                continue

            # 8 - Operadores relacionales y de asignacion
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
                    print(f"ERROR LEXICO: Simbolo '!' aislado invalido en la linea {current_line}", file=sys.stderr)
                    pos += 1
                continue

            # 9 - Delimitadores y operadores aritmeticos restantes
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
                # Si llega hasta acá, es porque no era un número negativo
                yield('OP_RESTA', '-', current_line)
                pos += 1
                continue
            if char == '*':
                yield('OP_MULT', '*', current_line)
                pos += 1
                continue

            # 10 - Error critico (Caracteres no contemplados en el lenguaje)
            print(f"ERROR LEXICO: Simbolo desconocido '{char}' en la linea {current_line}", file=sys.stderr)
            pos += 1

def Resultados(lexer, script_text):
    print(f"{'LINEA':<8} | {'TIPO DE TOKEN':<25} | {'VALOR ORIGINAL':<25}")
    print("-" * 65)

    lista_de_tokens = list(lexer.tokenize(script_text))
    
    for token_type, value, line in lista_de_tokens:
        print(f"{line:<8} | {token_type:<25} | {value}")
        
    print("="*65)
    print(f" Total de tokens procesados exitosamente: {len(lista_de_tokens)}")
    print("="*65 + "\n")  

# =============================================================
# Prueba de Ejecución
# =============================================================
if __name__ == "__main__":
    lexer = SmartHome()

    while True:
        print("=" * 30)
        print("Menú Principal")
        print("=" * 30)
        print("1. Escribir codigo.")
        print("2. Cargar un script.")
        print("3. Script de prueba")
        print("4. Salir")

        opcion = input("Seleccione una opcion (1-4): ").strip()
        if opcion == "1":
            print("\nEscriba el codigo línea por línea.")
            print("Cuando haya terminado, escriba la palabra FIN en una línea nueva para procesar:")
            print("-" * 60)
            
            lineas_usuario = []
            while True:
                linea = input()
                if linea.strip().upper() == "FIN":
                    break
                lineas_usuario.append(linea)
            
            codigo_consola = "\n".join(lineas_usuario)
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
            # Ejemplo avanzado para testear todo: decimales, negativos, emails, prefijos y comentarios
            script_domotica = """// Prueba del lexer avanzado
WHEN sensor_humedad < 45.5% DO
  foco_patio.estado = ON
  aire_comedor.temp_objetivo = -5°C
  altavoz_sala.email = admin@utn.frre.edu.ar
END
"""
            print(f"{script_domotica}")
            Resultados(lexer, script_domotica)
        elif opcion == "4":
            print("Proceso finalizado.")
            break
        else:
            print("Opcion invalida.")