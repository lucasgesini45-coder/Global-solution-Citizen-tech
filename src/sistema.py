"""Ponto de entrada exigido pela FIAP: python src/sistema.py."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.src.sistema import main

if __name__ == "__main__":
    main()
