import os
import math
import joblib
import pandas as pd
import numpy as np
from flask import Flask, render_template, jsonify, request, send_from_directory

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'model', 'atm_model.pkl')
STATUS_PATH = os.path.join(BASE_DIR, 'model', 'latest_atm_status.csv')
FULL_CSV_PATH = os.path.join(BASE_DIR, 'atm_cash_full_dataset.csv')

# Bangalore City Center reference coordinates (Majestic / Vidhana Soudha)
BLR_CENTER_LAT = 12.9716
BLR_CENTER_LON = 77.5946

def haversine_distance(lat1, lon1, lat2=BLR_CENTER_LAT, lon2=BLR_CENTER_LON):
    """Calculate exact great-circle distance in kilometers using Haversine formula."""
    try:
        lat1, lon1 = float(lat1), float(lon1)
        lat2, lon2 = float(lat2), float(lon2)
        R = 6371.0  # Earth mean radius in kilometers
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return round(R * c, 2)
    except Exception:
        return 0.0

# Initialize Flask
app = Flask(__name__, template_folder='templates', static_folder='static')

# Load trained model bundle
print("[Flask] Loading model from:", MODEL_PATH)
bundle = joblib.load(MODEL_PATH)
model = bundle['model']
scaler = bundle['scaler']
feature_cols = bundle['feature_cols']
numeric_features = bundle['numeric_features']
categorical_features = bundle['categorical_features']
cat_dummy_columns = bundle['cat_dummy_columns']
metrics = bundle['metrics']

# Load latest ATM status dataset
if os.path.exists(STATUS_PATH):
    latest_df = pd.read_csv(STATUS_PATH)
else:
    df_full = pd.read_csv(FULL_CSV_PATH)
    latest_date = df_full['date'].max()
    latest_df = df_full[df_full['date'] == latest_date].copy()
    latest_df.to_csv(STATUS_PATH, index=False)

# Add precalculated distance to Bangalore center for all ATMs
latest_df['dist_to_blr_center_km'] = latest_df.apply(
    lambda r: haversine_distance(r['latitude'], r['longitude']), axis=1
)

print(f"[Flask] Loaded {len(latest_df)} total ATMs. Bangalore ATMs: {(latest_df['city'] == 'Bengaluru').sum()}")

@app.route('/')
def home():
    """Render the Bangalore ATM Cash Prediction dashboard."""
    return render_template('index.html')

@app.route('/index.html')
def home_html():
    return render_template('index.html')

@app.route('/style.css')
def serve_root_css():
    return send_from_directory(os.path.join(BASE_DIR, 'static'), 'style.css')

@app.route('/script.js')
def serve_root_js():
    return send_from_directory(os.path.join(BASE_DIR, 'static'), 'script.js')

@app.route('/api/bangalore-meta', methods=['GET'])
def get_bangalore_meta():
    """Return available Bangalore and Karnataka areas and banks from the dataset."""
    blr_df = latest_df[latest_df['city'] == 'Bengaluru']
    karnataka_df = latest_df[latest_df['city'].isin(['Bengaluru', 'Mysuru'])]
    
    blr_areas = sorted(blr_df['area'].unique().tolist())
    all_karnataka_areas = sorted(karnataka_df['area'].unique().tolist())
    banks = sorted(latest_df['bank'].unique().tolist())
    
    return jsonify({
        'city_center': {
            'name': 'Bangalore City Center (Majestic / Vidhana Soudha)',
            'latitude': BLR_CENTER_LAT,
            'longitude': BLR_CENTER_LON
        },
        'bangalore_areas': blr_areas,
        'karnataka_areas': all_karnataka_areas,
        'banks': banks,
        'total_bangalore_atms': int(len(blr_df)),
        'total_karnataka_atms': int(len(karnataka_df))
    })

@app.route('/api/atms', methods=['GET'])
def get_atms():
    """Return filtered list of ATMs based on Location and Bank selection."""
    area = request.args.get('area', '').strip()
    bank = request.args.get('bank', '').strip()
    city = request.args.get('city', 'Bengaluru').strip()

    filtered = latest_df.copy()

    # If city filter is applied
    if city and city.lower() != 'all':
        filtered = filtered[filtered['city'] == city]

    # If specific area is selected
    if area and area.lower() != 'all':
        filtered = filtered[filtered['area'] == area]

    # If specific bank is selected
    if bank and bank.lower() != 'all':
        filtered = filtered[filtered['bank'] == bank]

    atm_list = []
    for _, row in filtered.sort_values('atm_id').iterrows():
        atm_list.append({
            'atm_id': str(row['atm_id']),
            'bank': str(row['bank']),
            'city': str(row['city']),
            'area': str(row['area']),
            'location_type': str(row['location_type']),
            'latitude': float(row['latitude']),
            'longitude': float(row['longitude']),
            'dist_to_center_km': float(row['dist_to_blr_center_km']),
            'display': f"{row['atm_id']} - {row['bank']} ({row['area']})"
        })

    return jsonify({
        'total': len(atm_list),
        'atms': atm_list
    })

@app.route('/api/atm/<atm_id>', methods=['GET'])
def get_atm_details(atm_id):
    """Return comprehensive live status for selected ATM including Haversine distance."""
    row = latest_df[latest_df['atm_id'] == atm_id]
    if row.empty:
        return jsonify({'error': f'ATM {atm_id} not found'}), 404

    r = row.iloc[0].to_dict()
    lat = float(r.get('latitude', 0.0))
    lon = float(r.get('longitude', 0.0))
    dist_km = haversine_distance(lat, lon)

    details = {
        'atm_id': str(r.get('atm_id')),
        'date': str(r.get('date')),
        'bank': str(r.get('bank')),
        'city': str(r.get('city')),
        'area': str(r.get('area')),
        'location_type': str(r.get('location_type')),
        'latitude': lat,
        'longitude': lon,
        'dist_to_center_km': dist_km,
        
        # Financial & Cash details
        'closing_balance': int(r.get('closing_balance', 0)),
        'opening_balance': int(r.get('opening_balance', 0)),
        'cash_capacity': int(r.get('cash_capacity', 0)),
        'cash_pct_remaining': float(r.get('cash_pct_remaining', 0.0)),
        'base_daily_demand': int(r.get('base_daily_demand', 0)),

        # Today's activity
        'total_withdrawn': int(r.get('total_withdrawn', 0)),
        'num_transactions': int(r.get('num_transactions', 0)),
        'avg_txn_amount': int(r.get('avg_txn_amount', 0)),
        'failed_txn_no_cash': int(r.get('failed_txn_no_cash', 0)),

        # Operations
        'days_since_last_refill': int(r.get('days_since_last_refill', 0)),
        'refill_happened': int(r.get('refill_happened', 0)),
        'low_cash_flag': int(r.get('low_cash_flag', 0)),
        'replenish_lag_days': int(r.get('replenish_lag_days', 1)),
        'footfall_index': float(r.get('footfall_index', 0.0)),
        'withdrawn_lag1': int(r.get('withdrawn_lag1', 0)),
        'withdrawn_roll7_mean': int(r.get('withdrawn_roll7_mean', 0))
    }
    return jsonify(details)

@app.route('/api/predict/<atm_id>', methods=['GET', 'POST'])
def predict_atm(atm_id):
    """Run Logistic Regression inference and return prediction with Bangalore location context."""
    row = latest_df[latest_df['atm_id'] == atm_id]
    if row.empty:
        return jsonify({'error': f'ATM {atm_id} not found'}), 404

    r = row.iloc[0].to_dict()
    lat = float(r.get('latitude', 0.0))
    lon = float(r.get('longitude', 0.0))
    dist_km = haversine_distance(lat, lon)

    atm_df = pd.DataFrame([r])
    atm_df['is_24x7'] = atm_df['is_24x7'].astype(int)

    # Dummies alignment
    encoded_dummies = pd.get_dummies(atm_df[categorical_features], drop_first=True, dtype=int)
    for col in cat_dummy_columns:
        if col not in encoded_dummies.columns:
            encoded_dummies[col] = 0
    encoded_dummies = encoded_dummies[cat_dummy_columns]

    X_input = pd.concat([atm_df[numeric_features], encoded_dummies], axis=1)[feature_cols]
    X_scaled = scaler.transform(X_input)

    pred = int(model.predict(X_scaled)[0])
    prob_cash_out = float(model.predict_proba(X_scaled)[0, 1])

    # Contributing reasons
    reasons = []
    cash_pct = float(r.get('cash_pct_remaining', 0.0))
    closing_bal = int(r.get('closing_balance', 0))
    daily_demand = int(r.get('base_daily_demand', 0))
    days_refill = int(r.get('days_since_last_refill', 0))
    failed_txns = int(r.get('failed_txn_no_cash', 0))
    replenish_lag = int(r.get('replenish_lag_days', 1))

    if pred == 1:
        verdict = "Cash may run out tomorrow"
        status_color = "danger"
        risk_level = "HIGH RISK"

        if cash_pct <= 15.0:
            reasons.append(f"Critical low cash level: Only {cash_pct:.1f}% capacity remaining (₹{closing_bal:,}).")
        if closing_bal < daily_demand:
            reasons.append(f"Closing cash balance is less than standard daily withdrawal demand (₹{daily_demand:,}).")
        if days_refill >= 3:
            reasons.append(f"ATM has not been refilled for {days_refill} days.")
        if replenish_lag > 1:
            reasons.append(f"Replenishment lead time is {replenish_lag} days.")
        if failed_txns > 0:
            reasons.append(f"Recorded {failed_txns} failed transactions due to cash shortage today.")
        if not reasons:
            reasons.append("High projected withdrawal volume based on recent rolling demand.")
    else:
        verdict = "Cash is expected to be available tomorrow"
        status_color = "success"
        risk_level = "SAFE"

        if cash_pct >= 40.0:
            reasons.append(f"Adequate cash buffer: {cash_pct:.1f}% capacity remaining (₹{closing_bal:,}).")
        if closing_bal >= daily_demand * 1.5:
            reasons.append(f"Current cash covers {closing_bal / max(1, daily_demand):.1f}x the daily demand.")
        if days_refill <= 1:
            reasons.append("Recently refilled with fresh currency.")
        if not reasons:
            reasons.append("Healthy cash reserves relative to typical demand in this location.")

    return jsonify({
        'atm_id': atm_id,
        'bank': str(r.get('bank')),
        'city': str(r.get('city')),
        'area': str(r.get('area')),
        'latitude': lat,
        'longitude': lon,
        'dist_to_center_km': dist_km,
        'prediction': verdict,
        'pred_class': pred,
        'risk_level': risk_level,
        'status_color': status_color,
        'cash_out_probability': round(prob_cash_out * 100, 2),
        'cash_capacity': int(r.get('cash_capacity', 0)),
        'closing_balance': closing_bal,
        'cash_pct_remaining': cash_pct,
        'reasons': reasons
    })

@app.route('/api/bangalore-map-points', methods=['GET'])
def get_bangalore_map_points():
    """Return all Bangalore ATMs with coordinates and current cash status for Leaflet map markers."""
    blr_df = latest_df[latest_df['city'] == 'Bengaluru']
    points = []
    for _, r in blr_df.iterrows():
        points.append({
            'atm_id': str(r['atm_id']),
            'bank': str(r['bank']),
            'area': str(r['area']),
            'latitude': float(r['latitude']),
            'longitude': float(r['longitude']),
            'closing_balance': int(r['closing_balance']),
            'cash_pct_remaining': float(r['cash_pct_remaining']),
            'dist_km': float(r['dist_to_blr_center_km'])
        })
    return jsonify({'points': points})

if __name__ == '__main__':
    print("\n" + "="*60)
    print("  ATM Cash Prediction System (Bangalore Focus)")
    print("  Server running on http://127.0.0.1:5000")
    print("="*60 + "\n")
    app.run(debug=True, host='127.0.0.1', port=5000)
