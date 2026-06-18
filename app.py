from flask import Flask, render_template, request, redirect, send_file
from supabase import create_client
import pandas as pd

app = Flask(__name__)

# 🔑 SUPABASE CONFIG (yaha apna data daalna)
SUPABASE_URL = "https://jbowwhgeknjelyeqojih.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Impib3d3aGdla25qZWx5ZXFvamloIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODE2MDc3NjgsImV4cCI6MjA5NzE4Mzc2OH0.PaC5ja4BQyaGsiPzIEd7wXA5v1sB_OtbS5vlzLqbpxo"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# 💾 ADD TRANSACTION
def add_transaction(date, invoice_no, t_type, party, purpose, mode, amount):

    data = {
        "date": date,
        "invoice_no": invoice_no,
        "transaction_type": t_type,
        "party": party,
        "purpose": purpose,
        "payment_mode": mode,
        "amount": amount
    }

    supabase.table("transactions").insert(data).execute()


# 📥 GET TRANSACTIONS
def get_transactions():
    response = supabase.table("transactions").select("*").order("date", desc=True).execute()
    return response.data


# 🏠 DASHBOARD
@app.route("/")
def home():

    transactions = get_transactions()

    total_cash_in = sum(t["amount"] for t in transactions if t["transaction_type"] == "Cash In")
    total_cash_out = sum(t["amount"] for t in transactions if t["transaction_type"] == "Cash Out")
    balance = total_cash_in - total_cash_out

    return render_template(
        "index.html",
        transactions=transactions,
        total_cash_in=total_cash_in,
        total_cash_out=total_cash_out,
        balance=balance,
        transaction_count=len(transactions)
    )


# 💰 CASH IN
@app.route("/cash-in", methods=["GET", "POST"])
def cash_in():

    if request.method == "POST":

        add_transaction(
            request.form["date"],
            request.form["invoice_no"],
            "Cash In",
            request.form["party"],
            request.form["purpose"],
            request.form["payment_mode"],
            float(request.form["amount"])
        )

        return redirect("/")

    return render_template("cash_in.html")


# 💸 CASH OUT
@app.route("/cash-out", methods=["GET", "POST"])
def cash_out():

    if request.method == "POST":

        add_transaction(
            request.form["date"],
            request.form["invoice_no"],
            "Cash Out",
            request.form["party"],
            request.form["purpose"],
            request.form["payment_mode"],
            float(request.form["amount"])
        )

        return redirect("/")

    return render_template("cash_out.html")


# ❌ DELETE
@app.route("/delete/<string:id>")
def delete(id):

    supabase.table("transactions").delete().eq("id", id).execute()

    return redirect("/")


# ✏️ EDIT (simple version)
@app.route("/edit/<string:id>", methods=["GET", "POST"])
def edit(id):

    if request.method == "POST":

        supabase.table("transactions").update({
            "date": request.form["date"],
            "invoice_no": request.form["invoice_no"],
            "party": request.form["party"],
            "purpose": request.form["purpose"],
            "amount": float(request.form["amount"]),
            "payment_mode": request.form["payment_mode"]
        }).eq("id", id).execute()

        return redirect("/")

    return render_template("edit.html")

# 📅 MONTHLY REPORT
@app.route("/monthly-report")
def monthly_report():

    transactions = get_transactions()

    df = pd.DataFrame(transactions)

    if df.empty:
        return render_template(
            "monthly_report.html",
            report=[],
            total_income=0,
            total_expense=0
        )

    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.strftime("%B %Y")

    report = df.groupby(["month", "transaction_type"])["amount"].sum().unstack(fill_value=0).reset_index()

    report = report.rename(columns={
        "Cash In": "Income",
        "Cash Out": "Expense"
    })

    report["Balance"] = report.get("Income", 0) - report.get("Expense", 0)

    return render_template(
        "monthly_report.html",
        report=report.to_dict(orient="records")
    )


# 📊 EXPORT EXCEL
@app.route("/export")
def export():

    data = get_transactions()

    df = pd.DataFrame(data)

    file_name = "transactions.xlsx"
    df.to_excel(file_name, index=False)

    return send_file(file_name, as_attachment=True)


# 🚀 RUN APP
if __name__ == "__main__":
    app.run(debug=True)
   