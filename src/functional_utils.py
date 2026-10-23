def filter_sales_by_category(sales, category):
    return list(filter(
        lambda sale: sale.category == category,
        sales
    ))


def filter_sales_by_date(sales, date):
    return list(filter(
        lambda sale: sale.date == date,
        sales
    ))