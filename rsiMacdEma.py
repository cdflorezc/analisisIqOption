from iqoptionapi.stable_api import IQ_Option
import time

def validar_conexion(API):
    if API.check_connect():
        print('Conexión exitosa.')
        return True
    else:
        print('No se pudo conectar.')
        return False

def calcular_rsi(candles, periodo=14):
    close_prices = [float(candle['close']) for candle in candles]
    deltas = [close_prices[i + 1] - close_prices[i] for i in range(len(close_prices) - 1)]
    up_values = [delta if delta > 0 else 0 for delta in deltas]
    down_values = [-delta if delta < 0 else 0 for delta in deltas]

    avg_gain = sum(up_values[:periodo]) / periodo
    avg_loss = sum(down_values[:periodo]) / periodo

    for i in range(periodo, len(up_values)):
        avg_gain = (avg_gain * (periodo - 1) + up_values[i]) / periodo
        avg_loss = (avg_loss * (periodo - 1) + down_values[i]) / periodo

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calcular_macd(candles, periodo_lento=26, periodo_rapido=12, periodo_signal=9):
    close_prices = [float(candle['close']) for candle in candles]
    ema_lenta = calcular_ema(close_prices, periodo_lento)
    ema_rapida = calcular_ema(close_prices, periodo_rapido)
    macd_line = [ema_rapida[i] - ema_lenta[i] for i in range(len(ema_rapida))]
    signal_line = calcular_ema(macd_line, periodo_signal)
    histograma = [macd_line[i] - signal_line[i] for i in range(len(macd_line))]
    return macd_line, signal_line, histograma

def calcular_ema(data, periodo):
    ema = [data[0]]
    multiplier = 2 / (periodo + 1)
    for i in range(1, len(data)):
        ema.append((data[i] - ema[i - 1]) * multiplier + ema[i - 1])
    return ema

def abrir_operacion(API, symbol, amount, option_type, timeframe):
    status, response = API.buy(amount, symbol, option_type, timeframe)
    if status:
        print(f'Operación de {option_type} realizada en {symbol}.')
        return True
    else:
        print(f'Error al realizar la operación de {option_type} en {symbol}:', response)
        return False


def calcular_total_ganancia(API, amount):
    total_ganancia = 0
    positions = API.get_positions('forex')
    if isinstance(positions, list):
        for position in positions:
            if position['win']:
                total_ganancia += position['close_profit']
            else:
                total_ganancia -= amount
    return total_ganancia

def esperar_cierre_operaciones(API):
    max_intentos = 10  # Número máximo de intentos
    intentos = 0
    while intentos < max_intentos:
        positions = API.get_positions('forex')
        if not isinstance(positions, list) or len(positions) == 0:
            break
        intentos += 1
        time.sleep(20)

    if intentos == max_intentos:
        print("No se pudieron cerrar todas las posiciones correctamente. Verifica el estado manualmente.")

def cerrar_operaciones(API):
    positions = API.get_positions('forex')
    if isinstance(positions, list):
        for position in positions:
            API.close_position(position['id'])

def estrategia_rsi_macd(symbols, timeframe, amount, rsi_threshold=30, max_trades=5):
    API = IQ_Option('corre', 'clave')
    API.connect()

    if not validar_conexion(API):
        return

    API.change_balance('PRACTICE')

    operaciones_realizadas = 0
    trades_exitosos = 0
    total_ganancia = 0

    while operaciones_realizadas < max_trades:
        for symbol in symbols:
            candles = API.get_candles(symbol, timeframe, 100, time.time())
            if candles:
                rsi = calcular_rsi(candles)
                macd_line, signal_line, histograma = calcular_macd(candles)
                if rsi < rsi_threshold and macd_line[-1] > signal_line[-1] and histograma[-1] > 0:
                    if abrir_operacion(API, symbol, amount, 'call', timeframe):
                        trades_exitosos += 1
                        operaciones_realizadas += 1
                        if trades_exitosos == max_trades:
                            break
                    else:
                        continue
                elif rsi > 100 - rsi_threshold and macd_line[-1] < signal_line[-1] and histograma[-1] < 0:
                    if abrir_operacion(API, symbol, amount, 'put', timeframe):
                        trades_exitosos += 1
                        operaciones_realizadas += 1
                        if trades_exitosos == max_trades:
                            break

        time.sleep(5)

    print("Se alcanzó el límite de operaciones. Esperando cierre de todas las operaciones...")
    cerrar_operaciones(API)

    print("Esperando cierre de todas las operaciones...")
    esperar_cierre_operaciones(API)

    total_ganancia = calcular_total_ganancia(API, amount)

    print("Todas las operaciones se han cerrado. Finalizando estrategia.")
    print("Total ganado/perdido:", total_ganancia)

# Ejemplo de uso
symbols = ['GBPUSD', 'EURUSD', 'USDJPY', 'GBPJPY', 'AUDJPY', 'EURGBP', 'EURJPY' ]
timeframe = 1
amount = int(input("ingrese el valor de operacion en dolares: "))
rsi_threshold = 30
max_trades = int(input("ingrese en numero de trades que desea hacer: "))

estrategia_rsi_macd(symbols, timeframe, amount, rsi_threshold, max_trades)