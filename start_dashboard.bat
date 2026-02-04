@echo off
echo ==========================================
echo    AquaRegWatch Norway - Dashboard
echo ==========================================
echo.
echo Starting dashboard at http://localhost:8501
echo Press Ctrl+C to stop
echo.
streamlit run dashboard.py --server.port=8501 --server.address=localhost --theme.base=dark
