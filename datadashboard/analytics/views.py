from django.shortcuts import render
from django.http import HttpResponse 
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from django.conf import settings

def dashboard(request):
    return render(request, 'analytics/dashboard.html')
uploaded_df = None  # global variable to store uploaded data temporarily

def upload_data(request):
    global uploaded_df
    context = {}

    # 🧹 CLEAR DATA
    if request.method == "POST" and "clear" in request.POST:
        uploaded_df = None
        context["success"] = "🧹 Data cleared successfully."
        return render(request, "analytics/upload.html", context)

    # 📁 UPLOAD FILE
    if request.method == "POST" and "file" in request.FILES:
        file = request.FILES["file"]
        filename = file.name.lower()

        try:
            # 🟢 Check file type
            if filename.endswith('.csv'):
                uploaded_df = pd.read_csv(file)

            elif filename.endswith('.xlsx'):
                uploaded_df = pd.read_excel(file)

            elif filename.endswith('.xls'):
                uploaded_df = pd.read_excel(file, engine="xlrd")

            else:
                context["error"] = "❌ Unsupported file format. Upload .csv or .xlsx only."
                return render(request, "analytics/upload.html", context)

            context["success"] = f"✔ File uploaded successfully: {filename}"
            context["columns"] = list(uploaded_df.columns)
            context["table"] = uploaded_df.head().to_html(classes="table table-striped", index=False)

        except Exception as e:
            uploaded_df = None
            context["error"] = f"⚠ Error reading file: {e}"

        return render(request, "analytics/upload.html", context)

    # 🔍 FILTER DATA
    if request.method == "POST" and "filter" in request.POST:
        if uploaded_df is None:
            context["error"] = "⚠ Upload a file first."
            return render(request, "analytics/upload.html", context)

        col = request.POST.get("column")
        query = request.POST.get("query", "")

        context["columns"] = list(uploaded_df.columns)
        context["filter_column"] = col
        context["filter_query"] = query

        if col and query:
            df_filtered = uploaded_df[uploaded_df[col].astype(str).str.contains(query, case=False, na=False)]
        else:
            df_filtered = uploaded_df

        # show filtered table
        context["table"] = df_filtered.to_html(classes="table table-striped", index=False)

        # 📤 EXPORT OPTIONS
        if "export_csv" in request.POST:
            return export_csv(df_filtered)
        if "export_excel" in request.POST:
            return export_excel(df_filtered)

        return render(request, "analytics/upload.html", context)

    return render(request, "analytics/upload.html", context)

# 📤 EXPORT AS CSV
def export_csv(df):
    response = HttpResponse(df.to_csv(index=False), content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="filtered_data.csv"'
    return response

# 📤 EXPORT AS EXCEL
def export_excel(df):
    response = HttpResponse(content_type="application/vnd.ms-excel")
    response["Content-Disposition"] = 'attachment; filename="filtered_data.xlsx"'
    df.to_excel(response, index=False)
    return response

# ============================================================
# 📌 SUMMARY VIEW (FIXED)
# ============================================================

def summary(request):
    global uploaded_df

    if uploaded_df is None:
        return render(request, 'analytics/summary.html', {
            "error": "⚠ No file uploaded. Please upload a CSV first."
        })

    df = uploaded_df

    if df.empty or len(df.columns) == 0:
        return render(request, 'analytics/summary.html', {
            "error": "⚠ CSV has no valid columns."
        })

    total_rows, total_cols = df.shape
    columns = df.columns.tolist()
    dtypes = df.dtypes.apply(lambda x: str(x)).to_dict()
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns

    if len(numeric_cols) > 0:
        summary_stats = df[numeric_cols].describe().to_html(classes="table table-bordered")
    else:
        summary_stats = "<p>No numeric columns available.</p>"

    missing_values = df.isnull().sum().to_dict()

    context = {
        "error": None,
        "total_rows": total_rows,
        "total_cols": total_cols,
        "dtypes_list": list(dtypes.items()),  # 👈 KEY FIX
        "missing_values": list(missing_values.items()),  # 👈 KEY FIX
        "summary_stats": summary_stats,
    }

    return render(request, 'analytics/summary.html', context)


# ============================================================
# 📌 CHARTS VIEW (FIXED)
# ============================================================

def charts(request):
    global uploaded_df

    if uploaded_df is None:
        return render(request, 'analytics/charts.html', {
            "error": "⚠ No file uploaded. Please upload a CSV first."
        })

    df = uploaded_df.copy()

    charts_dir = os.path.join(settings.MEDIA_ROOT, "charts")
    os.makedirs(charts_dir, exist_ok=True)

    charts_paths = []

    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
    cat_cols = df.select_dtypes(include=['object']).columns

    # 1️⃣ Bar Chart
    if len(numeric_cols) > 0:
        mean_values = df[numeric_cols].mean()
        plt.figure()
        mean_values.plot(kind='bar')
        plt.title("Mean of Numeric Columns")
        plt.tight_layout()
        bar_path = os.path.join(charts_dir, "mean_bar.png")
        plt.savefig(bar_path)
        charts_paths.append("charts/mean_bar.png")
        plt.close()

    # 2️⃣ Line Chart
    if len(numeric_cols) > 0:
        first_col = numeric_cols[0]
        plt.figure()
        df[first_col].plot(kind='line')
        plt.title(f"Trend of {first_col}")
        plt.tight_layout()
        line_path = os.path.join(charts_dir, "line_chart.png")
        plt.savefig(line_path)
        charts_paths.append("charts/line_chart.png")
        plt.close()

    # 3️⃣ Pie Chart
    if len(cat_cols) > 0:
        first_cat = cat_cols[0]
        plt.figure()
        df[first_cat].value_counts().head(5).plot(kind='pie', autopct="%0.1f%%")
        plt.title(f"Top Categories of {first_cat}")
        plt.ylabel("")
        pie_path = os.path.join(charts_dir, "pie_chart.png")
        plt.savefig(pie_path)
        charts_paths.append("charts/pie_chart.png")
        plt.close()

    return render(request, 'analytics/charts.html', {"charts": charts_paths})
