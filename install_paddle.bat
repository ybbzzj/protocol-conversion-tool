@echo off
setlocal

echo ============================================================
echo Protocol Conversion Tool - Semantic Dependency Installer
echo Legacy filename: install_paddle.bat
echo ============================================================
echo.

python --version >nul 2>&1
if errorlevel 1 goto :NO_PYTHON
echo Python detected:
python --version
echo.

python -m pip install --upgrade pip
if errorlevel 1 echo WARNING: pip upgrade failed, continue...
echo.

python -c "import torch" >nul 2>&1
if not errorlevel 1 goto :TORCH_OK
echo Installing PyTorch CPU build...
python -m pip install torch==1.13.1+cpu --index-url https://download.pytorch.org/whl/cpu
if not errorlevel 1 goto :TORCH_OK
echo First attempt failed, trying PyPI torch 1.13.1 ...
python -m pip install torch==1.13.1
if errorlevel 1 goto :TORCH_FAIL
:TORCH_OK
echo PyTorch ready.
echo.

python -c "import transformers, tokenizers, safetensors, huggingface_hub, regex" >nul 2>&1
if not errorlevel 1 goto :TRANS_OK
echo Installing transformers stack...
python -m pip install transformers==4.30.2 tokenizers==0.13.3 safetensors==0.4.5 huggingface-hub==0.20.3 regex==2023.12.25
if errorlevel 1 goto :TRANS_FAIL
:TRANS_OK
echo Transformers stack ready.
echo.
echo ============================================================
echo Dependencies installed successfully.
echo ============================================================
goto :DONE

:NO_PYTHON
echo ERROR: Python not found. Please install Python 3.8 first.
goto :DONE

:TORCH_FAIL
echo ERROR: Failed to install torch.
echo Try this manually:
echo python -m pip install torch==1.13.1+cpu --index-url https://download.pytorch.org/whl/cpu
goto :DONE

:TRANS_FAIL
echo ERROR: Failed to install transformers stack.
echo Try this manually:
echo python -m pip install transformers==4.30.2 tokenizers==0.13.3 safetensors==0.4.5 huggingface-hub==0.20.3 regex==2023.12.25

:DONE
echo.
pause
exit /b 0
