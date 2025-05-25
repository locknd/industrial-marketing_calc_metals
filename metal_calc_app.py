# metal_calc_app.py
# FastAPI-приложение для калькуляции цены листового/рулонного металла по шести видам

from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

# Импортируем константы из utils
from utils import (
    BASE_PRICES,
    THICKNESS_UP,
    GRADE_UP,
    WIDTH_UP,
    WEIGHT_COST,
    SORT_COEF,
    USD_RATE,
    REGION_TARIFF
)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# ---------------------------------------------
# Вспомогательная функция для поиска надбавки по толщине
# ---------------------------------------------

def find_thickness_markup(metal: str, thickness_value: float) -> float:
    """
    Ищет диапазон толщины в THICKNESS_UP[metal],
    возвращает надбавку в USD, если попадает в любой key (формат "min-max"),
    иначе 0.
    """
    ranges = THICKNESS_UP.get(metal, {})
    for key, usd_markup in ranges.items():
        try:
            lo, hi = map(float, key.split('-'))
        except ValueError:
            continue
        if lo <= thickness_value <= hi:
            return usd_markup
    return 0.0

# ---------------------------------------------
# GET / — форма ввода параметров
# ---------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def form(request: Request):
    return templates.TemplateResponse(
        "metal_form.html",
        {"request": request,
         "regions": BASE_PRICES.keys(),
         "metals": list(BASE_PRICES['Урал'].keys())}
    )

# ---------------------------------------------
# POST /расчёт_металлов — расчёт и вывод результата
# ---------------------------------------------
@app.post("/расчёт_металлов", response_class=HTMLResponse)
async def calculate(
    request: Request,
    region: str = Form(...),
    metal: str = Form(...),
    thickness: float = Form(...),    # теперь float
    grade: str = Form(...),
    width: str = Form(...),
    volume: float = Form(...),
    sort: str = Form(...),
    credit_days: int = Form(..., ge=0)
):
    # 1. Базовая цена по региону и типу металла
    base_price = BASE_PRICES[region][metal]

    # 2. Надбавка за толщину: сначала ищем соответствующую USD-ставку, затем конвертируем
    t_up_usd = find_thickness_markup(metal, thickness)
    t_up     = USD_RATE * t_up_usd

    # 3. Надбавка за марку/допуск (USD -> RUB)
    g_up_usd = GRADE_UP.get(grade, 0)
    g_up     = USD_RATE * g_up_usd

    # 4. Надбавка за ширину (USD -> RUB)
    w_up_usd = WIDTH_UP.get(width, 0)
    w_up     = USD_RATE * w_up_usd

    # 5. Стоимость услуг по весу (руб.)
    cost_roll = WEIGHT_COST['рулон']
    cost_pack = WEIGHT_COST['пачка']

    # 6. Формируем цену за тонну
    price_per_t = (
        base_price + t_up + g_up + w_up + cost_roll + cost_pack
    )

    # 7. Применяем коэффициент сортности
    price_per_t *= SORT_COEF.get(sort, 1.0)

    # 8. Учёт ж/д тарифа региона
    price_per_t *= (1 + REGION_TARIFF[region])

    # 9. Надбавка за коммерческий кредит:
    #    базовый шаг – 0.5% за каждые 15 дней
    periods = credit_days / 15
    credit_markup = periods * 0.005   # 0.5% = 0.005

    # 10. Общая стоимость по заданному объёму
    total_price = price_per_t * volume

    # Округление
    price_per_t = round(price_per_t, 2)
    total_price = round(total_price, 2)

    return templates.TemplateResponse(
        "metal_report.html",
        {"request": request,
         "region": region,
         "metal": metal,
         "thickness": thickness,
         "grade": grade,
         "width": width,
         "volume": volume,
         "sort": sort,
         "price_per_t": price_per_t,
         "total_price": total_price,
        "credit_days": credit_days,
        "credit_markup_pct": round(credit_markup*100, 2)}
    )

# Запуск: uvicorn metal_calc_app:app --reload
