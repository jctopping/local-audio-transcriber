@echo off
SETLOCAL

echo Creating virtual environment...
python -m venv diarize_env

echo Activating virtual environment...
call diarize_env\Scripts\activate.bat

echo Upgrading pip...
pip install --upgrade pip

echo Installing torch (set TORCH_INDEX to override, e.g. https://download.pytorch.org/whl/cu128 for NVIDIA)...
IF "%TORCH_INDEX%"=="" SET TORCH_INDEX=https://download.pytorch.org/whl/cpu
pip install "torch==2.8.*" "torchaudio==2.8.*" --index-url %TORCH_INDEX%

echo Installing dependencies from requirements.txt...
pip install -r requirements.txt

echo Copying .env.sample to .env (if not already present)...
IF NOT EXIST ".env" (
    copy .env.sample .env
    echo .env file created. Be sure to add your Hugging Face token inside.
) ELSE (
    echo .env already exists. Skipping copy.
)

echo.
echo Setup complete. Edit the .env file and paste your Hugging Face token.
ENDLOCAL
pause