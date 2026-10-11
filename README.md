# 🏧 ATM Cash Prediction System (Bangalore & Karnataka Focus)

An end-to-end Machine Learning web application designed to forecast whether an Automated Teller Machine (ATM) in **Bangalore and nearby areas in Karnataka** is likely to run out of cash on the next business day. Built with **Python Flask, Scikit-Learn, Leaflet (OpenStreetMap), HTML5, CSS3, and Vanilla JavaScript**.

---

## 📌 1. Project Overview & Objective

- **Project Title:** ATM Cash Prediction System
- **Geographic Area:** Bangalore, Karnataka (and neighboring Karnataka regions)
- **Objective:** Predict whether an ATM will run out of cash on the next day (`cash_out_next_day` = 0 or 1).
- **Target Variable:** `cash_out_next_day`
  - `0`: ATM is **NOT** expected to run out of cash (Reserves are safe/adequate).
  - `1`: ATM **IS** expected to run out of cash (Depletion risk / replenishment required).
- **Output Verdicts:**
  - *"Cash may run out tomorrow"* (High Risk / Depletion warning)
  - *"Cash is expected to be available tomorrow"* (Safe / Adequate reserves)

---

## 📍 2. Geographic Data & Bangalore Coverage

The project uses the actual dataset (`atm_cash_full_dataset.csv`) without modifying, creating fake records, or inventing synthetic locations. The dataset contains **81,783 Bangalore records** across **117 unique ATMs** distributed throughout the city.

### Available Bangalore Localities in the Dataset:
1. **Koramangala** (18 ATMs)
2. **Jayanagar** (16 ATMs)
3. **Hebbal** (14 ATMs)
4. **Whitefield** (13 ATMs)
5. **Yelahanka** (12 ATMs)
6. **Indiranagar** (10 ATMs)
7. **Anekal** (10 ATMs)
8. **BTM Layout** (9 ATMs)
9. **Marathahalli** (8 ATMs)
10. **Electronic City** (7 ATMs)
*(Also includes nearby Karnataka region: **Mysuru** with 36 ATMs across 4 localities).*

### Banks Represented in Bangalore:
- Axis Bank (18 ATMs)
- Bank of Baroda (15 ATMs)
- Kotak Mahindra Bank (15 ATMs)
- State Bank of India (12 ATMs)
- ICICI Bank (11 ATMs)
- Canara Bank (11 ATMs)
- IDFC First Bank (10 ATMs)
- HDFC Bank (9 ATMs)
- Union Bank of India (8 ATMs)
- Punjab National Bank (8 ATMs)

---

## 📏 3. Distance Feature: Haversine Formula

For every ATM, the actual `latitude` and `longitude` stored in the dataset are used to calculate the real great-circle distance to **Bangalore City Center (Majestic / Vidhana Soudha, 12.9716° N, 77.5946° E)** in kilometres.

### The Haversine Formula:
$$d = 2 R \arcsin\left(\sqrt{\sin^2\left(\frac{\Delta\phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta\lambda}{2}\right)}\right)$$

Where:
- $R = 6,371.0 \text{ km}$ (Earth's mean radius)
- $\phi_1, \phi_2$: Latitudes of the ATM and Bangalore City Center (in radians)
- $\Delta\phi = \phi_2 - \phi_1$
- $\Delta\lambda = \lambda_2 - \lambda_1$ (Difference in longitudes in radians)

### Real Distances in the System:
- **Whitefield:** ~2.20 km
- **BTM Layout:** ~2.45 km
- **Yelahanka:** ~2.86 km
- **Koramangala:** ~4.74 km
- **Marathahalli:** ~5.80 km
- **Electronic City:** ~6.02 km
- **Indiranagar:** ~11.13 km
- **Anekal:** ~13.44 km
- **Jayanagar:** ~18.27 km
- **Hebbal:** ~19.70 km

---

## 🗺️ 4. Interactive OpenStreetMap (Leaflet.js)

- Built using the open-source **Leaflet** library with **OpenStreetMap** standard tiles.
- Zero API keys required.
- Plots markers for Bangalore ATMs based on their authentic coordinates.
- Red circle markers highlight ATMs with low remaining cash (< 20%), while blue markers show ATMs with safe cash reserves.
- A distinctive red star marker marks **Bangalore City Center (Majestic / Vidhana Soudha)**.
- Selecting or checking any ATM dynamically centers the map on that location with a full informational popup.

---

## 🔍 5. Cascading Filter Feature

The dashboard includes a 3-tier cascading filter:
```
Location: [ Select Bangalore Area ]  (e.g., Koramangala, Whitefield, Electronic City)
Bank:     [ Select Bank ]            (e.g., HDFC, SBI, ICICI, Kotak, Axis)
ATM:      [ Select ATM ]             (Automatically populates matching ATMs with distance)

[ 🔍 Check ATM & Predict ]
```

When clicked, it displays:
1. **ATM ID & Bank**
2. **Area & City**
3. **GPS Coordinates (Latitude, Longitude)**
4. **Distance to Bangalore City Center (in km)**
5. **Total Cash Capacity (₹)**
6. **Current Available Cash (₹ closing balance)**
7. **Cash Percentage Remaining (with colored progress bar)**
8. **Recent Transaction and Demand Metrics**
9. **Next-Day Prediction Result & Cash-Out Risk Probability**
10. **Interactive Map Highlight**

---

## 🛡️ 6. Machine Learning Model & Preprocessing

- **Algorithm:** Standardized Logistic Regression
- **Data Leakage Elimination:**
  - `closing_balance_next_day`: Strictly excluded (tomorrow's closing balance is future information unknown today).
  - `cash_out_next_day`: Target variable, separated from feature matrix.
  - `refill_pending`: Removed because it is a collinear duplicate ($r = 1.00$) of `low_cash_flag`.
- **Chronological Split (80/20):**
  - Train: 2024-10-31 to 2026-05-12 (279,500 records)
  - Test: 2026-05-13 to 2026-09-29 (70,000 records)
- **Performance on Test Set:**
  - **Accuracy:** **92.71%**
  - **ROC-AUC Score:** **0.9638**
  - **Precision:** **72.33%**
  - **Recall:** **61.46%**
  - **F1-Score:** **0.6645**

---

## 📂 7. Project Directory Structure

```
atm_cash_prediction/
│
├── atm_cash_full_dataset.csv   # Original dataset (349,500 rows, 50 columns - UNTOUCHED)
├── train_model.py              # Script to train and evaluate Logistic Regression
├── app.py                      # Flask server with REST API & Haversine distance
│
├── model/
│   ├── atm_model.pkl           # Saved model, scaler, and metadata bundle
│   └── latest_atm_status.csv   # Cached latest status for instantaneous UI responses
│
├── templates/
│   └── index.html              # Dashboard with Bangalore filters & Leaflet map
│
├── static/
│   ├── style.css               # Clean styling
│   └── script.js               # Filter logic, Leaflet map, and API integration
│
├── index.html                  # Root copy
├── style.css                   # Root copy
├── script.js                   # Root copy
└── README.md                   # Full documentation
```

---

## 🚀 8. How to Run the Application

### 1. Install Dependencies
```bash
pip install pandas scikit-learn flask joblib
```

### 2. Start the Flask Server
```bash
python app.py
```

### 3. Open in Browser
Visit:
👉 **`http://127.0.0.1:5000/`**
