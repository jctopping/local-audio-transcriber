#!/bin/bash
# Usage: ./setup.sh            (auto-detects AMD/NVIDIA GPU)
#        TORCH=cpu ./setup.sh  (force a backend: rocm | cuda | cpu)
set -e

if [ -z "$TORCH" ]; then
    if [ -e /dev/kfd ] && lspci 2>/dev/null | grep -qiE '(vga|display|3d).*(amd|ati)'; then
        TORCH=rocm
    elif command -v nvidia-smi >/dev/null; then
        TORCH=cuda
    else
        TORCH=cpu
    fi
fi
case "$TORCH" in
    rocm) TORCH_INDEX=https://download.pytorch.org/whl/rocm6.4 ;;
    cuda) TORCH_INDEX=https://download.pytorch.org/whl/cu128 ;;
    cpu)  TORCH_INDEX=https://download.pytorch.org/whl/cpu ;;
    *) echo "Unknown TORCH=$TORCH (use rocm, cuda or cpu)"; exit 1 ;;
esac
echo "Torch backend: $TORCH"

# torch 2.8 ships wheels for Python 3.10-3.13 only.
echo "Creating virtual environment..."
rm -rf diarize_env
if command -v uv >/dev/null; then
    # uv is much faster, caches the multi-GB torch wheels, and fetches Python 3.12 if needed.
    uv venv -p 3.12 diarize_env
    source diarize_env/bin/activate
    PIP="uv pip"
else
    PY=""
    for v in 3.12 3.13 3.11 3.10; do
        if command -v "python$v" >/dev/null; then PY="python$v"; break; fi
    done
    if [ -z "$PY" ]; then
        echo "Need Python 3.10-3.13 (torch 2.8 has no wheels for newer versions). Install one, or install uv."
        exit 1
    fi
    "$PY" -m venv diarize_env
    source diarize_env/bin/activate
    PIP="pip"
    pip install --upgrade pip
fi

echo "Installing torch ($TORCH)..."
$PIP install "torch==2.8.*" "torchaudio==2.8.*" --index-url "$TORCH_INDEX"

echo "Installing dependencies..."
$PIP install -r requirements.txt

python -c "import torch; print('torch', torch.__version__, '| GPU available:', torch.cuda.is_available())"

if [ ! -f .env ]; then
    echo "Copying .env.sample to .env (edit your token inside)..."
    cp .env.sample .env
    echo "Setup complete. Edit .env to include your Hugging Face token."
else
    echo "Setup complete. Existing .env left untouched."
fi
