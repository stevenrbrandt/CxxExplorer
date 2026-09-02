echo "Starting notebook"
export PATH=/usr/local/bin:${PATH}
export PYTHONPATH=/usr/local/python:${PYTHONPATH:-}
export LD_LIBRARY_PATH=/usr/local/lib:/usr/local/lib64:${LD_LIBRARY_PATH:-}
export LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libjemalloc.so.2
echo jupyter notebook --allow-root --ip=0.0.0.0 --port=${PORT} --no-browser --NotebookApp.token="${SECRET_TOKEN}" --LabApp.extension_manager=readonly
jupyter notebook --allow-root --ip=0.0.0.0 --port=${PORT} --no-browser --NotebookApp.token="${SECRET_TOKEN}" --LabApp.extension_manager=readonly
