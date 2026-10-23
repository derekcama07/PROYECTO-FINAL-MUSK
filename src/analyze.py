
import csv
import json
from pathlib import Path

import pandas as pd

from src.client import Client
from src.sale import Sale
from src.client_collection import ClientCollection
from src.sales_collection import SalesCollection
from src.functional_utils import filter_sales_by_category


BASE_DIR = Path(__file__).resolve().parent.parent


def generate_report():
    # 1. Leer los clientes del archivo JSON
    with open(BASE_DIR / "data" / "clients.json", encoding="utf-8") as file:
        clients_data = json.load(file)

    clients = [Client(**data) for data in clients_data]

    # 2. Leer las ventas del archivo CSV
    sales = []

    with open(BASE_DIR / "data" / "sales.csv", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            sales.append(
                Sale(
                    sale_id=row["sale_id"],
                    client_id=int(row["client_id"]),
                    product=row["product"],
                    category=row["category"],
                    amount=float(row["amount"]),
                    date=row["date"]
                )
            )

    client_collection = ClientCollection(clients)
    sales_collection = SalesCollection(sales)

    # 3. Calcular los datos generales
    total_clients = len(clients)
    total_sales = len(sales)
    total_revenue = round(sum(s.amount for s in sales), 2)

    # 4. Calcular gastos, cantidad y promedio por cliente
    clients_report = []

    for client in clients:
        total_spent = round(
            sales_collection.total_amount_by_client(client.client_id), 2
        )

        sale_count = len(
            sales_collection.sales_by_client(client.client_id)
        )

        average_sale = round(
            total_spent / sale_count, 2
        ) if sale_count > 0 else 0

        clients_report.append({
            "client_id": client.client_id,
            "name": client.name,
            "total_spent": total_spent,
            "sale_count": sale_count,
            "average_sale": average_sale
        })

    # 5. Cliente que más gasta en cada país
    top_client_by_country = {}

    for country in set(client.country for client in clients):
        country_clients = client_collection.clients_by_country(country)

        top_client = max(
            country_clients,
            key=lambda client: sales_collection.total_amount_by_client(
                client.client_id
            )
        )

        top_client_by_country[country] = top_client.name

    # 6. Crear un DataFrame con Pandas
    df = pd.DataFrame([sale.to_dict() for sale in sales])

    # 7. Ingresos por categoría
    sales_by_category = {
        category: round(float(amount), 2)
        for category, amount in
        df.groupby("category")["amount"].sum().items()
    }

    # 8. Cliente con más ventas de Electronics
    electronics_sales = filter_sales_by_category(sales, "Electronics")

    top_electronics_client = None
    max_sales = 0

    for client in clients:
        count = sum(
            1 for sale in electronics_sales
            if sale.client_id == client.client_id
        )

        if count > max_sales:
            max_sales = count
            top_electronics_client = client.name

    # 9. Clientes que gastaron más de 500
    high_spending_clients = []

    for client in clients:
        if sales_collection.total_amount_by_client(client.client_id) > 500:
            high_spending_clients.append(client.name)

    # 10. Ventas acumuladas por mes
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.to_period("M").astype(str)

    monthly_sales = {
        month: round(float(amount), 2)
        for month, amount in
        df.groupby("month")["amount"].sum().items()
    }

    # Construir el informe final
    report = {
        "summary": {
            "total_clients": total_clients,
            "total_sales": total_sales,
            "total_revenue": total_revenue
        },
        "clients": clients_report,
        "top_client_by_country": top_client_by_country,
        "sales_by_category": sales_by_category,
        "high_spending_clients": high_spending_clients,
        "monthly_sales": monthly_sales
    }

    return report


if __name__ == "__main__":
    report = generate_report()

    output_path = BASE_DIR / "final_report.json"

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=4, ensure_ascii=False)

    print("Informe generado correctamente:", output_path)
