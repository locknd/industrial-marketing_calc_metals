# utils.py
# Вспомогательные функции и константы для калькуляторов

# ---------------------------------------------
# Методы расчёта аннуитетного платежа, накопления и инфляции
# ---------------------------------------------

def annuity_payment(principal: float, annual_rate: float, years: int) -> float:
    """
    Рассчитывает ежемесячный аннуитетный платёж по кредиту.
    :param principal: сумма кредита (руб.)
    :param annual_rate: годовая ставка (%)
    :param years: срок кредита (лет)
    :return: ежемесячный платёж (руб.)
    """
    r = annual_rate / 100 / 12
    n = years * 12
    return principal * r / (1 - (1 + r) ** -n)


def accumulate_deposit(monthly: float, annual_rate: float, years: int) -> float:
    """
    Итоговая сумма накоплений при ежемесячном пополнении вклада.
    :param monthly: сумма взноса в месяц (руб.)
    :param annual_rate: ставка вклада (%)
    :param years: срок (лет)
    :return: накопленная сумма (руб.)
    """
    r = annual_rate / 100 / 12
    n = years * 12
    return monthly * (((1 + r) ** n - 1) / r)


def adjust_inflation(amount: float, years: float, inflation: float) -> float:
    """
    Приведение будущей суммы к текущей стоимости с учётом инфляции.
    :param amount: будущая сумма (руб.)
    :param years: период (лет)
    :param inflation: инфляция (%)
    :return: приведённая стоимость (руб.)
    """
    return amount / ((1 + inflation / 100) ** years)


# ---------------------------------------------
# Константы и словари для металлопродукции
# ---------------------------------------------

# 1. Курс USD → RUB
USD_RATE = 100.0  # 1 USD = 100 RUB

# 2. Базовые цены за тонну по регионам (RUB/т)
BASE_PRICES = {
    'Урал': {
        'ГК_лист':   44167,
        'ГК_рулон':  40833,
        'ХК_лист':   47083,
        'ХК_рулон':  46250,
        'Оцинк':     59167,
        'Полимер':   72167,
        'Жесть':     80800,
    },
    'Сибирь': {
        'ГК_лист':   44667,
        'ГК_рулон':  41333,
        'ХК_лист':   47583,
        'ХК_рулон':  46750,
        'Оцинк':     59167,
        'Полимер':   72167,
        'Жесть':     80800,
    },
    'Центр Волгоград': {
        'ГК_лист':   43267,
        'ГК_рулон':  39933,
        'ХК_лист':   46183,
        'ХК_рулон':  45350,
        'Оцинк':     59167,
        'Полимер':   72167,
        'Жесть':     80800,
    },
    'Ростов': {
        'ГК_лист':   42167,
        'ГК_рулон':  38833,
        'ХК_лист':   45083,
        'ХК_рулон':  44250,
        'Оцинк':     59167,
        'Полимер':   72167,
        'Жесть':     80800,
    },
    'Москва и Санкт-Петербург': {
        'ГК_лист':   41367,
        'ГК_рулон':  38033,
        'ХК_лист':   44283,
        'ХК_рулон':  43450,
        'Оцинк':     59167,
        'Полимер':   72167,
        'Жесть':     80800,
    },
}

# 3. Надбавки за диапазоны толщины (USD)
#    (точно по вашим скринам: ГК, ХК, Оцинк, Полимер, Жесть)
THICKNESS_UP = {
    'ГК_лист': {
        '1.0-1.24':  115.0,
        '1.25-1.29': 110.0,
        '1.3-1.34':  105.0,
        '1.35-1.39':  95.0,
        '1.4-1.49':   75.0,
        '1.5-1.59':   50.0,
        '1.6-1.79':   40.0,
        '1.8-1.99':   25.0,
        '2.0-2.49':   10.0,
        '4.0-12.0':   -5.0
    },
    'ГК_рулон': {
        '1.0-1.24':  115.0,
        '1.25-1.29': 110.0,
        '1.3-1.34':  105.0,
        '1.35-1.39':  95.0,
        '1.4-1.49':   75.0,
        '1.5-1.59':   50.0,
        '1.6-1.79':   40.0,
        '1.8-1.99':   25.0,
        '2.0-2.49':   10.0,
        '4.0-12.0':   -5.0
    },
    'ХК_лист': {
        '0.7-0.89': 125.0,
        '0.9-0.99': 120.0
    },
    'ХК_рулон': {
        '0.7-0.89': 115.0,
        '0.9-0.99': 110.0
    },
    'Оцинк': {
        '0.35-0.39': 20.0,
        '0.5-0.5':   120.0
    },
    'Полимер': {
        '0.35-0.39': 20.0,
        '0.5-0.5':   150.0
    },
    'Жесть': {
        '0.25-0.25': 120.0
    }
}


def find_thickness_markup(metal: str, thickness_value: float) -> float:
    """
    Ищет диапазон толщины в THICKNESS_UP[metal],
    возвращает USD-приплату (float), если thickness_value попадает в любой ключ "min-max",
    иначе 0.0.
    """
    ranges = THICKNESS_UP.get(metal, {})
    for key, usd_markup in ranges.items():
        try:
            lo, hi = map(float, key.split('-'))
        except ValueError:
            lo = hi = float(key)
        if lo <= thickness_value <= hi:
            return usd_markup
    return 0.0


# 4. Надбавки за марку/допуск (USD)
GRADE_UP = {
    'обрезанная кромка': 15.0,
    'рифлёнка':         25.0,
    'нестанд допуск':    10.0,
    'сталь 09Г2С':       40.0,
    'сталь 09Г2Д':       40.0,
    'штрипс':            60.0,
    '20ГЮТ':            100.0
}

# 5. Надбавки за ширину (USD)
def find_width_markup(width_value: int) -> float:
    """
    Возвращает USD-приплату за ширину рулона:
    <1000 мм   → 10 $
    1000-1249  → 15 $
    1250-1499  → 20 $
    1500       → 25 $
    иначе      → 0 $
    """
    if width_value < 1000:
        return 10.0
    elif 1000 <= width_value < 1250:
        return 15.0
    elif 1250 <= width_value < 1500:
        return 20.0
    elif width_value == 1500:
        return 25.0
    else:
        return 0.0


# 6. Стоимость услуг по весу (USD за рулон/пачку)
#    Позволяет конвертировать 15 USD → 1 500 ₽ и 5 USD → 500 ₽
WEIGHT_COST_USD = {
    'рулон': 15.0,  # USD (если рулон < 10 т)
    'пачка':  5.0   # USD (если пачка < 6 т)
}

# 7. «Станции» (рублёвая фиксация, зависит от выбранной станции)
STATION_PRICES = {
    'АБАКАН': 4273,
    'АВТОВО': 6929,
    'АЛТАЙСКАЯ': 3127,
    'АНЗЕБИ': 5572,
    'АНТРОПШИНО': 6929,
    'АППАРАТНАЯ': 3861,
    'АРТЕМ-ПРИМОРСКИЙ-1': 7130,
    'АСТРАХАНЬ-1': 4855,
    'АЧИНСК-1': 4375,
    'АЧИНСК-2': 4375,
    'БАГУЛЬНАЯ': 5572,
    'БАЗАИХА': 4571,
    'БАЛАКОВО': 5161,
    'БАЛАШИХА': 6028,
    'БАРНАУЛ': 3127,
    'БАТАЙСК': 6109,
    'БАТАРЕЙНАЯ': 5919,
    'БАХАРЕВКА': 4246,
    'БЕЗЫМЯНКА': 4637,
    'БЕЛОРЕЦК': 3831,
    'БЕЛЫЙ РАСТ': 6214,
    'БЕРДСК': 3337,
    'БЕТОННАЯ ТОВАРНАЯ': 5308,
    'БИЙСК': 3307,
    'БИРЮЛЕВО ТОВАРНАЯ': 6028,
    'БИРЮЛИ': 4976,
    'БЛАГОВЕЩЕНСК': 8956,
    'БОКИНО': 5761,
    'ИЖОРЫ': 6929,
    'ИКША': 6134,
    'ИЛАНКА': 4845,
    'ИМ МАКСИМА ГОРЬКОГО': 5343,
    'ИРБИТ': 3996,
    'ИРКУТСК-ПАССАЖИРСКИЙ': 5919,
    'ИСЕТЬ': 3909,
    'ИШАНОВО': 3582,
    'ЙОШКАР-ОЛА': 5071,
    'КАМЕНОЛОМНИ': 6028,
    'КАМЫШТА': 4180,
    'КАНСК-ЕНИСЕЙСКИЙ': 4751,
    'КАРАБУЛА': 5137,
    'КАРБЫШЕВО-1': 2967,
    'КАЯ': 5919,
}

# 8. Коэффициенты сортности (без %, умножается)
SORT_COEF = {
    'беззаказка': 1.00,
    'второй': 0.90,  # −10%
    'третий': 0.80   # −20%
}

# 9. Ж/д тариф по регионам (применяется как multiplier (1 + tariff))
REGION_TARIFF = {
    'Урал':                     0.007,  # +0.7%
    'Сибирь':                   0.012,  # +1.2%
    'Москва и Санкт-Петербург': 0.010,  # +1.0%
    'Центр Волгоград':          0.009,  # +0.9%
    'Ростов':                   0.011   # +1.1%
}

# 10. Объёмные надбавки (применяются к цене за тонну)
#     '<500':     +2%,  '500-1000': +1%, '>1000': 0%
VOLUME_MARKUP = {
    '<500':     0.02,
    '500-1000': 0.01,
    '>1000':    0.00
}