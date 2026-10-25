#!/usr/bin/env bash
# notebooks/src/*.py(jupytext percent 형식)를 .ipynb로 변환하고 실행해 결과를 저장한다.
# 사용: bash scripts/build_notebooks.sh [notebooks/src/NN_이름.py ...]  (인자가 없으면 전부)
set -euo pipefail

cd "$(dirname "$0")/.."
export DEVSIM_MATH_LIBS="libopenblas.so.0:liblapack.so.3:libblas.so.3"
# 저장된 설계안이 섞이지 않도록 빈 작업 폴더에서 기준 설계안으로 실행한다.
export MEMDEV_WORK="$(mktemp -d)"

if [ "$#" -eq 0 ]; then
  set -- notebooks/src/*.py
fi

for src in "$@"; do
  name="$(basename "${src%.py}")"
  out="notebooks/${name}.ipynb"
  echo "== ${src} -> ${out}"
  jupytext --quiet --to ipynb --output "${out}" "${src}"
  jupyter nbconvert --to notebook --execute --inplace \
    --ExecutePreprocessor.timeout=900 --ExecutePreprocessor.kernel_name=python3 "${out}"
done
