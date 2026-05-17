
import requests

def get_asset_price(ticker, asset_type):
    if asset_type == "share":
        url = f"https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities/{ticker}.json"
    elif asset_type == "index":
        url = f"https://iss.moex.com/iss/engines/stock/markets/index/boards/SNDX/securities/{ticker}.json"
    elif asset_type == "currency":
        url = f"https://iss.moex.com/iss/engines/currency/markets/selt/boards/CETS/securities/{ticker}.json"
    elif asset_type == "futures":
        url = f"https://iss.moex.com/iss/engines/futures/markets/forts/boards/RFUD/securities/{ticker}.json"
    else:
        return 0.0

    try:
        url += "?iss.meta=off&iss.only=marketdata"
        response = requests.get(url)
        data = response.json()['marketdata']
        
        if not data['data']:
            print(f"⚠️ Биржа не вернула данные по тикеру: {ticker}")
            return 0.0
            
        columns = data['columns']
        if 'LAST' in columns:
            idx = columns.index('LAST')
        elif 'CURRENTVALUE' in columns:
            idx = columns.index('CURRENTVALUE')
        else:
            idx = 11

        price = data['data'][0][idx]
        return float(price) if price else 0.0
    except Exception as e:
        print(f"❌ Ошибка при парсинге {ticker}: {e}")
        return 0.0