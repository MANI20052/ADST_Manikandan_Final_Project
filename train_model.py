import os
import joblib
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_auc_score
)

def run():
    csv_path = r'C:\Users\Admin\OneDrive\Documents\Desktop\atm_cash_prediction\atm_cash_full_dataset.csv'
    model_dir = r'C:\Users\Admin\OneDrive\Documents\Desktop\atm_cash_prediction\model'
    os.makedirs(model_dir, exist_ok=True)
    
    print("=" * 70)
    print("      ATM CASH PREDICTION SYSTEM - MODEL TRAINING PIPELINE")
    print("=" * 70)
    
    print("\n[STEP 1] Loading dataset...")
    df = pd.read_csv(csv_path)
    print(f"-> Dataset successfully loaded! Shape: {df.shape[0]:,} rows, {df.shape[1]} columns")
    
    print("\n[STEP 2] Handling missing refill values logically...")
    # Missing refill data occurs because refills do not happen daily.
    # When refill_happened == 0, we logically impute without dropping rows:
    df['refill_amount_loaded'] = df['refill_amount_loaded'].fillna(0.0)
    df['refill_balance_before'] = df['refill_balance_before'].fillna(df['opening_balance'])
    df['refill_balance_after'] = df['refill_balance_after'].fillna(df['balance_after_refill'])
    df['refill_time'] = df['refill_time'].fillna('No Refill')
    df['refill_agent_id'] = df['refill_agent_id'].fillna('None')
    print("-> Logical imputation complete. Remaining missing values:", df.isnull().sum().sum())
    
    print("\n[STEP 3] Converting date and sorting chronologically...")
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(['date', 'atm_id']).reset_index(drop=True)
    
    print("\n[STEP 4] Feature Selection & Data Leakage Prevention...")
    print("-> REMOVING 'closing_balance_next_day' (future information leakage)")
    print("-> REMOVING 'cash_out_next_day' from features (target variable)")
    print("-> REMOVING 'refill_pending' (collinear duplicate of 'low_cash_flag')")
    print("-> RETAINING 'atm_id', 'date', 'latitude', 'longitude', 'area' for UI display")
    
    # 33 Core predictive features
    numeric_features = [
        'opening_balance', 'refill_amount', 'balance_after_refill',
        'num_transactions', 'total_withdrawn', 'avg_txn_amount', 'failed_txn_no_cash',
        'closing_balance', 'hours_cash_out', 'atm_offline_flag', 'rainfall_mm',
        'days_since_last_refill', 'low_cash_flag', 'cash_out_flag',
        'day_of_week', 'is_weekend', 'is_salary_period', 'is_holiday', 'pre_festival', 'month',
        'cash_capacity', 'base_daily_demand', 'installed_year', 'num_cassettes',
        'footfall_index', 'network_uptime_pct', 'replenish_lag_days',
        'withdrawn_lag1', 'withdrawn_lag7', 'withdrawn_roll7_mean', 'withdrawn_roll30_mean',
        'cash_pct_remaining', 'refill_happened'
    ]
    
    # Convert boolean is_24x7 to int
    df['is_24x7'] = df['is_24x7'].astype(int)
    numeric_features.append('is_24x7')
    
    categorical_features = ['bank', 'city', 'location_type']
    
    # One-hot encoding for categoricals
    df_encoded = pd.get_dummies(df[categorical_features], drop_first=True, dtype=int)
    all_feature_cols = numeric_features + list(df_encoded.columns)
    
    X = pd.concat([df[numeric_features], df_encoded], axis=1)
    y = df['cash_out_next_day']
    
    print(f"-> Total engineered feature count for model: {X.shape[1]}")
    
    print("\n[STEP 5] Performing 80/20 Chronological Train/Test Split...")
    unique_dates = df['date'].drop_duplicates().sort_values().values
    split_idx = int(len(unique_dates) * 0.8)
    split_date = unique_dates[split_idx]
    
    train_mask = df['date'] < split_date
    test_mask = df['date'] >= split_date
    
    X_train, y_train = X[train_mask], y[train_mask]
    X_test, y_test = X[test_mask], y[test_mask]
    
    print(f"-> Training Set: {len(X_train):,} records ({df['date'][train_mask].min().strftime('%Y-%m-%d')} to {df['date'][train_mask].max().strftime('%Y-%m-%d')})")
    print(f"-> Testing Set:  {len(X_test):,} records ({df['date'][test_mask].min().strftime('%Y-%m-%d')} to {df['date'][test_mask].max().strftime('%Y-%m-%d')})")
    print(f"-> Train Cash-Out Rate: {y_train.mean()*100:.2f}% | Test Cash-Out Rate: {y_test.mean()*100:.2f}%")
    
    print("\n[STEP 6] Feature Standardization...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    print("\n[STEP 7] Training Logistic Regression Model...")
    model = LogisticRegression(max_iter=1000, random_state=42)
    model.fit(X_train_scaled, y_train)
    print("-> Model training finished!")
    
    print("\n[STEP 8] Model Evaluation on Test Data:")
    y_pred = model.predict(X_test_scaled)
    y_proba = model.predict_proba(X_test_scaled)[:, 1]
    
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_proba)
    cm = confusion_matrix(y_test, y_pred)
    
    print("-" * 50)
    print(f"Accuracy:           {acc:.4f} ({acc*100:.2f}%)")
    print(f"Precision:          {prec:.4f} ({prec*100:.2f}%)")
    print(f"Recall:             {rec:.4f} ({rec*100:.2f}%)")
    print(f"F1-Score:           {f1:.4f}")
    print(f"ROC-AUC Score:      {roc_auc:.4f}")
    print("-" * 50)
    print("\nConfusion Matrix:")
    print(f"[[TN={cm[0,0]:5d}, FP={cm[0,1]:5d}]")
    print(f" [FN={cm[1,0]:5d}, TP={cm[1,1]:5d}]]")
    
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=["0 (Has Cash)", "1 (Cash Out)"]))
    
    print("\n[STEP 9] Model Coefficients (Viva Interpretability):")
    print(f"Model Intercept: {model.intercept_[0]:.4f}")
    coef_df = pd.DataFrame({'Feature': all_feature_cols, 'Coefficient': model.coef_[0]})
    coef_df['Absolute'] = coef_df['Coefficient'].abs()
    coef_df = coef_df.sort_values('Absolute', ascending=False).reset_index(drop=True)
    
    print("\nTop 10 Most Influential Features:")
    print(coef_df[['Feature', 'Coefficient']].head(10).to_string(index=False))
    
    print("\n[STEP 10] Sample Actual vs Predicted (Test Data):")
    sample_eval = pd.DataFrame({
        'Date': df.loc[test_mask, 'date'].dt.strftime('%Y-%m-%d').values[:10],
        'ATM_ID': df.loc[test_mask, 'atm_id'].values[:10],
        'Actual_Cash_Out': y_test.values[:10],
        'Predicted_Cash_Out': y_pred[:10],
        'Cash_Out_Prob': np.round(y_proba[:10], 4)
    })
    print(sample_eval.to_string(index=False))
    
    print("\n[STEP 11] Saving Model & Metadata Artifacts...")
    model_bundle = {
        'model': model,
        'scaler': scaler,
        'feature_cols': all_feature_cols,
        'numeric_features': numeric_features,
        'categorical_features': categorical_features,
        'cat_dummy_columns': list(df_encoded.columns),
        'metrics': {
            'accuracy': float(acc),
            'precision': float(prec),
            'recall': float(rec),
            'f1_score': float(f1),
            'roc_auc': float(roc_auc),
            'confusion_matrix': cm.tolist(),
            'intercept': float(model.intercept_[0])
        },
        'coefficients': coef_df[['Feature', 'Coefficient']].to_dict(orient='records')
    }
    
    model_path = os.path.join(model_dir, 'atm_model.pkl')
    joblib.dump(model_bundle, model_path)
    print(f"-> Model artifact successfully saved to: {model_path}")
    print("=" * 70)

if __name__ == '__main__':
    run()
