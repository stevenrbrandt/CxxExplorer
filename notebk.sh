echo "Starting notebook"
if [ "$PORT" =  "" ]
then
    PORT=8080
fi
H=/home/jovyan
echo jupyter notebook --notebook-dir=$H --ip=0.0.0.0 --port=${PORT} --no-browser --NotebookApp.token="${SECRET_TOKEN}"
jupyter notebook --notebook-dir=$H --ip=0.0.0.0 --port=${PORT} --no-browser --NotebookApp.token="${SECRET_TOKEN}"
