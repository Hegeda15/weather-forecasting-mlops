# 🌤️ Real-Time Weather Forecasting MLOps Pipeline

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/ML-XGBoost%20%7C%20LightGBM-green.svg)](https://xgboost.readthedocs.io/)
[![CI/CD Pipeline](https://github.com/YOUR_USERNAME/weather-forecasting-mlops/actions/workflows/data_pipeline.yml/badge.svg)](https://github.com/YOUR_USERNAME/weather-forecasting-mlops/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An end-to-end Machine Learning system that automatically ingests real-time weather data, engineers time-series features, retrains predictive models, and serves forecasts via an interactive dashboard and API.

🔗 **Live Demo:** [Streamlit Web App](https://your-app-name.streamlit.app) | [FastAPI Endpoint](https://your-api-url.com/docs)

---

## 📌 Project Overview

Traditional machine learning projects often stop at static Jupyter Notebooks. This project demonstrates an automated, production-ready MLOps workflow designed to tackle short-term weather forecasting using open-access meteorology APIs.

### Key Features
* **Automated Data Ingestion:** Scheduled daily pipelines fetching continuous hourly weather metrics (temperature, humidity, wind speed, pressure) via the Open-Meteo API.
* **Feature Engineering:** Circular time encoding (sine/cosine transformations), lagged variables (1h, 3h, 24h), and rolling statistics.
* **Automated Model Training:** Continuous evaluation of gradient-boosted trees (XGBoost) against baseline models using time-series cross-validation (`TimeSeriesSplit`).
* **CI/CD Orchestration:** GitHub Actions workflow executing data ingestion, validation, and model updates automatically.
* **Interactive Dashboard:** Live visualization built with Streamlit showing predicted vs. actual values and model explainability (SHAP).

---

## 🏗️ System Architecture

```text
[ Open-Meteo API ]
        │
        ▼
[ GitHub Actions ] ── (Scheduled Ingestion) ──► [ SQLite / PostgreSQL ]
        │                                                │
        ▼                                                ▼
[ Feature Engineering ] ──────────────────► [ XGBoost Training ]
                                                         │
                                                         ▼
[ Streamlit UI / FastAPI ] ◄── (Inference) ─── [ Saved Model (.pkl) ]
