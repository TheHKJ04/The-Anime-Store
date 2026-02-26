from decimal import Decimal

CURRENCY_RATES = {
    'INR': Decimal('1.0'),      # Base currency
    'USD': Decimal('0.012'),
    'EUR': Decimal('0.011'),
    'JPY': Decimal('1.8'),
    'CNY': Decimal('0.085'),    # China Yuan
    'RUB': Decimal('1.05'),     # Russia Ruble
    'GBP': Decimal('0.0095'),   # UK Pound
}

CURRENCY_SYMBOLS = {
    'INR': '₹',
    'USD': '$',
    'EUR': '€',
    'JPY': '¥',
    'CNY': '¥',
    'RUB': '₽',
    'GBP': '£',
}


def convert_price(amount, currency):
    rate = CURRENCY_RATES.get(currency, Decimal('1.0'))
    return amount * rate
