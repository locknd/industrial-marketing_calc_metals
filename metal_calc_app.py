# metal_calc_app.py
# FastAPI-приложение для калькуляции цены листового/рулонного металла

from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

# Импортируем константы и функции из utils
from utils import (
    BASE_PRICES,
    find_thickness_markup,
    GRADE_UP,
    find_width_markup,
    WEIGHT_COST_USD,
    STATION_PRICES,
    SORT_COEF,
    USD_RATE,
    REGION_TARIFF,
    VOLUME_MARKUP
)

app = FastAPI()
templates = Jinja2Templates(directory="templates")


# ---------------------------------------------
# GET / — форма ввода параметров
# ---------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def form(request: Request):
    """
    Отдаёт страницу с формой metal_form.html.
    Передаёт списки регионов, металлов и (опционально) подтягивает списки для select.
    """
    return templates.TemplateResponse(
        "metal_form.html",
        {
            "request":  request,
            "regions":  list(BASE_PRICES.keys()),
            "metals":   list(BASE_PRICES['Урал'].keys()),
            "grades":   list(GRADE_UP.keys()),
            "stations": list(STATION_PRICES.keys())
        }
    )


# ---------------------------------------------
# POST /расчёт_металлов — расчёт и вывод результата
# ---------------------------------------------
@app.post("/расчёт_металлов", response_class=HTMLResponse)
async def calculate(
    request: Request,
    region: str       = Form(...),
    metal: str        = Form(...),
    thickness: float  = Form(...),
    grade: str        = Form(...),
    width: str        = Form(...),
    volume: float     = Form(...),
    sort: str         = Form(...),
    credit_days: int  = Form(..., ge=0),
    station: str      = Form(...)
):
    """
    Внутри функции собираем цену за тонну по этапам (как на доске):
    1) базовая рублёвая цена
    2) USD-приплаты (толщина, марка, ширина, малый вес), переведённые в рубли
    3) рублёвая «станция»
    4) умножение на коэффициент сортности
    5) умножение на ж/д тариф региона
    6) умножение на объёмную надбавку
    7) умножение на кредитную надбавку
    8) итоговая сумма = price_per_t * volume
    """

    # -------------------------------
    # 1. Базовая цена за тонну (RUB/т)
    # -------------------------------
    base_price = BASE_PRICES[region][metal]

    # ---------------------------------------------
    # 2. USD-приплаты → переведём в RUB и добавим
    # ---------------------------------------------

    # 2.1) Приплата за толщину (USD → RUB)
    t_up_usd = find_thickness_markup(metal, thickness)  # возвращает USD
    t_up = t_up_usd * USD_RATE                          # переводим в рубли

    # 2.2) Приплата за марку/допуск (USD → RUB)
    g_up_usd = GRADE_UP.get(grade, 0.0)
    g_up = g_up_usd * USD_RATE

    # 2.3) Приплата за ширину (USD → RUB)
    try:
        width_int = int(width)
    except ValueError:
        width_int = 0
    w_up_usd = find_width_markup(width_int)
    w_up = w_up_usd * USD_RATE

    # 2.4) Приплата за «малый вес» (USD → RUB)
    #      (если рулон < 10 т → 15$; если лист/пачка < 6 т → 5$)
    is_roll_light = metal.endswith('рулон') and (volume < 10)
    is_pack_light = metal.endswith('лист') and (volume < 6)

    cost_roll_rub = (WEIGHT_COST_USD['рулон'] * USD_RATE) if is_roll_light else 0.0
    cost_pack_rub = (WEIGHT_COST_USD['пачка'] * USD_RATE) if is_pack_light else 0.0

    # -----------------------------------
    # 3. «Станция» (фиксированная RUB)
    # -----------------------------------
    station_cost = STATION_PRICES.get(station, 0)

    # -------------------------------
    # 4. Сборка «цены за тонну» до скидки
    # -------------------------------
    price_per_t = (
        base_price       # базовая ₽
        + t_up           # приплата за толщину (₽)
        + g_up           # приплата за марку/допуск (₽)
        + w_up           # приплата за ширину (₽)
        + cost_roll_rub  # приплата за малый вес рулона (₽)
        + cost_pack_rub  # приплата за малый вес пачки (₽)
        + station_cost   # рублёвая надбавка станции (₽)
    )

    # -----------------------------------
    # 5. Применяем коэффициент сортности
    # -----------------------------------
    price_per_t *= SORT_COEF.get(sort, 1.0)

    # -----------------------------------
    # 6. Применяем ж/д тариф региона
    # -----------------------------------
    price_per_t *= (1 + REGION_TARIFF.get(region, 0.0))

    # -----------------------------------
    # 7. Применяем объёмную надбавку
    # -----------------------------------
    if volume < 500:
        price_per_t *= (1 + VOLUME_MARKUP['<500'])      # +2%
    elif 500 <= volume <= 1000:
        price_per_t *= (1 + VOLUME_MARKUP['500-1000'])  # +1%
    else:
        price_per_t *= (1 + VOLUME_MARKUP['>1000'])     # +0%

    # -----------------------------------
    # 8. Применяем надбавку за кредит (0.5% / 15 дней)
    # -----------------------------------
    periods = credit_days / 15.0
    credit_markup = periods * 0.005       # 0.5% = 0.005
    price_per_t *= (1 + credit_markup)

    # -----------------------------------
    # 9. Итоговая сумма по объёму
    # -----------------------------------
    total_price = price_per_t * volume

    # Округление (два знака после запятой)
    price_per_t = round(price_per_t, 2)
    total_price = round(total_price, 2)

    # -----------------------------------
    # Возвращаем шаблон с результатами
    # -----------------------------------
    return templates.TemplateResponse(
        "metal_report.html",
        {
            "request":          request,
            "region":           region,
            "metal":            metal,
            "thickness":        thickness,
            "grade":            grade,
            "width":            width,
            "volume":           volume,
            "sort":             sort,
            "station":          station,
            "credit_days":      credit_days,
            "price_per_t":      price_per_t,
            "total_price":      total_price,
            "credit_markup_pct": round(credit_markup * 100, 2)
        }
    )

# Запуск: uvicorn metal_calc_app:app --reload