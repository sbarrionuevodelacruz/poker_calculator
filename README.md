# Calculadora de Probabilidades de Poker

Aplicación en Python para calcular las probabilidades de ganar en poker según las cartas propias y las cartas comunitarias que van saliendo.

## Características

- ✅ Interfaz gráfica intuitiva con tkinter
- ✅ Cálculo de probabilidades usando simulación Monte Carlo (20,000 simulaciones)
- ✅ Soporte para 2-10 jugadores
- ✅ Actualización en tiempo real según van saliendo las cartas (flop, turn, river)
- ✅ Evaluación de manos de poker
- ✅ Visualización del tipo de mano actual
- ✅ Muestra las 3 manos más probables que te ganen con sus porcentajes

## Requisitos

- Python 3.6 o superior
- tkinter (generalmente viene incluido con Python)

## Instalación

1. Clona o descarga este repositorio
2. Asegúrate de tener Python instalado
3. No se requieren dependencias adicionales (usa solo librerías estándar)

## Uso

### Ejecutar la aplicación

**Opción 1: Desde la línea de comandos**
```bash
python poker_probability_calculator.py
```

**Opción 2: Usando el archivo .bat**
```bash
ejecutar_poker.bat
```

**Opción 3: Crear acceso directo en el escritorio**

Ejecuta el script de PowerShell:
```bash
powershell -ExecutionPolicy Bypass -File crear_acceso_directo.ps1
```

O simplemente haz doble clic en `crear_acceso_directo.bat`

Esto creará un acceso directo llamado "Calculadora Poker" en tu escritorio que puedes usar para abrir la aplicación directamente.

### Cómo usar:

1. **Selecciona el número de jugadores** en la mesa (2-10)

2. **Ingresa tus 2 cartas** en el formato:
   - Rango: 2-10, J, Q, K, A (o T para 10)
   - Palo: ♠ (espadas), ♥ (corazones), ♦ (diamantes), ♣ (tréboles)
   - Ejemplos: `As♠`, `Kh`, `7d`, `T♣`, `2♥`
   - Puedes usar mayúsculas o minúsculas para los palos

3. **Añade las cartas comunitarias** conforme van saliendo:
   - Flop: 3 cartas
   - Turn: 1 carta adicional
   - River: 1 carta adicional

4. **Haz clic en "Calcular Probabilidad"** para ver tus probabilidades de ganar

5. La probabilidad se actualiza automáticamente cuando cambias el número de jugadores

## Ejemplos de formato de cartas

- `As♠` o `As` - As de espadas
- `Kh` o `KH` - Rey de corazones
- `7d` - 7 de diamantes
- `T♣` o `10c` - 10 de tréboles
- `2♥` - 2 de corazones

## Cómo funciona

La aplicación usa **simulación Monte Carlo** para calcular las probabilidades:

1. Toma tus cartas y las cartas comunitarias conocidas
2. Simula miles de manos posibles repartiendo cartas aleatorias a los otros jugadores
3. Completa las cartas comunitarias faltantes
4. Evalúa todas las manos y cuenta cuántas veces ganas
5. Calcula la probabilidad como: (veces que ganaste) / (total de simulaciones)

## Estrategia Preflop - Guía de Situaciones y Acciones

La aplicación incluye un sistema de recomendaciones preflop basado en tablas profesionales de microlímites. Esta sección explica qué hacer en cada situación del juego.

### 📍 Posiciones en la Mesa

Las posiciones determinan cuándo actúas en la ronda de apuestas:

- **EP (Early Position)**: Posiciones tempranas (UTG, UTG+1). Actúas primero, así que necesitas manos más fuertes.
- **MP (Middle Position)**: Posiciones medias. Puedes jugar más manos que en EP.
- **CO (Cutoff)**: La posición antes del botón. Muy buena posición, puedes jugar muchas manos.
- **BTN (Button)**: La mejor posición. Actúas último, puedes jugar la mayoría de manos.
- **SB (Small Blind)**: Ciegas pequeñas. Actúas antes del botón, posición difícil.
- **BB (Big Blind)**: Ciegas grandes. Actúas último en la ronda inicial, pero ya pagaste.

### 🎯 Situaciones del Juego Preflop

La aplicación detecta automáticamente en qué situación estás y te da la recomendación correcta:

#### 1. **Open Raise (Abrir con Subida)**
**Cuándo ocurre**: Nadie ha subido antes de ti. Es tu turno y todos han pasado o igualado las ciegas.

**Qué significa**: Decides abrir la acción subiendo la apuesta (normalmente 2.5-3 veces la ciega grande).

**Qué hacer**:
- Si tu mano está en la lista de **"raise"**: Sube la apuesta (2.5-3bb típicamente)
- Si tu mano está en la lista de **"fold"**: Retírate, no juegues esa mano

**Ejemplo**: Tienes **AKs** en el **Button** y nadie ha subido → La aplicación te dirá **"Subir (Raise)"** porque AKs está en la lista de raise para BTN.

---

#### 2. **3Bet (Re-subir)**
**Cuándo ocurre**: Alguien ya hizo un Open Raise antes de ti, y ahora es tu turno.

**Qué significa**: Decides re-subir (normalmente 3-4 veces el raise inicial). Esto es agresivo y muestra fuerza.

**Qué hacer**:
- Si tu mano está en la lista de **"3bet"**: Re-sube la apuesta (3-4x el raise inicial)
- Si tu mano está en la lista de **"fold"**: Retírate, no es lo suficientemente fuerte
- Si tu mano está en la lista de **"call"**: Iguala la apuesta (raro en esta situación)

**Ejemplo**: Alguien hizo raise desde Early Position, tienes **QQ** en el **Button** → La aplicación te dirá **"Re-subir (3-Bet)"** porque QQ está en la lista de 3bet para BTN vs EP raise.

---

#### 3. **4Bet (Re-re-subir)**
**Cuándo ocurre**: Alguien hizo Open Raise, tú hiciste 3Bet, y ahora alguien re-subió tu 3Bet (eso es un 4Bet).

**Qué significa**: Decides si re-subir de nuevo (4Bet) o retirarte. Solo las manos más fuertes deben hacer 4Bet.

**Qué hacer**:
- Si tu mano está en la lista de **"4bet"**: Re-sube de nuevo (normalmente a 20-25bb)
- Si tu mano está en la lista de **"fold"**: Retírate, no es lo suficientemente fuerte para 4Bet

**Ejemplo**: Hiciste 3Bet con **AKs**, alguien te re-subió, y tienes **AA** → La aplicación te dirá **"Re-subir (4-Bet)"** porque AA está en la lista de 4bet.

---

#### 4. **Defender (Call/3Bet desde Blinds)**
**Cuándo ocurre**: Estás en Big Blind o Small Blind y alguien hizo Open Raise antes de ti.

**Qué significa**: Decides si defender tu ciega igualando (call) o re-subiendo (3bet), o retirarte (fold).

**Qué hacer**:
- Si tu mano está en la lista de **"defend"**: Defiende tu ciega (puedes igualar o hacer 3bet según la situación)
- Si tu mano está en la lista de **"fold"**: Retírate, no defiendas

**Ejemplo**: Estás en **Big Blind**, alguien hizo raise desde el **Button**, tienes **KQs** → La aplicación te dirá **"Defender"** porque KQs está en la lista de defend para BB vs BTN raise.

---

### 📋 Acciones Explicadas

| Acción | Qué Hacer | Cuándo Usarla |
|--------|-----------|---------------|
| **Fold** | Retirarte, no poner más dinero | Tu mano es débil para la situación |
| **Call** | Igualar la apuesta actual | Tu mano es decente pero no lo suficientemente fuerte para subir |
| **Raise** | Subir la apuesta (2.5-3bb típicamente) | Abres la acción con una mano fuerte |
| **3Bet** | Re-subir (3-4x el raise inicial) | Alguien hizo raise y tienes una mano muy fuerte |
| **4Bet** | Re-re-subir (20-25bb típicamente) | Alguien hizo 3Bet y tienes una mano premium (AA, KK, QQ, AK) |
| **Defend** | Defender tu ciega (call o 3bet) | Estás en BB/SB y alguien hizo raise, tienes una mano decente |

---

### 💡 Consejos Importantes

1. **La posición importa mucho**: Las mismas cartas pueden tener diferentes recomendaciones según tu posición. Por ejemplo, **AJo** puede ser "raise" en Button pero "fold" en Early Position.

2. **El número de jugadores afecta**: Con más jugadores, necesitas manos más fuertes. Con menos jugadores, puedes jugar más manos.

3. **Las acciones previas importan**: Si alguien ya subió, la aplicación automáticamente cambia a las tablas de 3Bet/4Bet en lugar de Open Raise.

4. **Suited vs Offsuit**: Las cartas del mismo palo (suited, con 's') son mejores que las de diferente palo (offsuit, con 'o'). Por ejemplo, **AKs** es mejor que **AKo**.

5. **Sigue las recomendaciones**: Estas tablas están basadas en análisis matemático y son óptimas para microlímites. Confía en ellas, especialmente si eres principiante.

---

### 📊 Ejemplo Práctico Completo

**Situación**: Mesa de 6 jugadores, estás en el **Button** (BTN), tienes **AKs**.

1. **Nadie ha subido antes de ti**:
   - La aplicación consulta: `open_raise → IP → OR_2.5bb_vs_3B_4x → BTN`
   - **AKs** está en la lista de "raise"
   - **Recomendación**: **"Subir (Raise)"** → Subes a 2.5-3bb

2. **Alguien hizo raise desde Early Position**:
   - La aplicación consulta: `vs_open_raise → 3bet_defend → BT_CO_MP_3x_vs_OR_2.5bb → BTN`
   - **AKs** está en la lista de "3bet"
   - **Recomendación**: **"Re-subir (3-Bet)"** → Re-subes a 9-12bb

3. **Alguien re-subió tu 3Bet (4Bet)**:
   - La aplicación consulta: `open_raise → IP → 4B_to_25bb → BTN`
   - **AKs** está en la lista de "4bet"
   - **Recomendación**: **"Re-subir (4-Bet)"** → Re-subes a 20-25bb

---

### 🔍 Cómo Leer las Tablas del JSON

El archivo `preflop_strategy2.json.txt` contiene todas las tablas organizadas así:

- **open_raise**: Situaciones donde abres con raise
  - **OOP**: Out of Position (fuera de posición)
  - **IP**: In Position (en posición)
- **vs_open_raise**: Situaciones donde alguien ya hizo raise
  - **3bet_defend**: Cuándo hacer 3Bet o defender
  - **bb_vs_IP_OR**: Defender desde Big Blind

Cada situación tiene listas de manos para cada posición (EP, MP, CO, BTN, SB) indicando qué acción tomar.

## Notas

- Las simulaciones por defecto son 20,000 para mayor precisión
- Puedes ajustar el número de simulaciones en el código si lo deseas (línea con `simulations=20000`)
- La aplicación valida que no uses la misma carta dos veces
- La evaluación de manos sigue las reglas estándar de poker Texas Hold'em
- Las "manos más probables que te ganen" muestran la mejor mano del oponente en cada simulación donde pierdes

## Mejoras futuras posibles

- Aumentar número de simulaciones para mayor precisión
- Mostrar probabilidades de diferentes tipos de manos
- Historial de probabilidades durante la mano
- Soporte para otros tipos de poker (Omaha, etc.)
- Estadísticas adicionales (probabilidad de empate, etc.)
